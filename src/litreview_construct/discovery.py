from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import yaml

from .bibliography import normalize_doi, normalize_title
from .papers import resolve_bibliography
from .project import PROJECT_DIR, _atomic_write_text, _write_json

OPENALEX_BASE_URL = "https://api.openalex.org"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_project(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    root = root.expanduser().resolve()
    state_root = root / PROJECT_DIR
    project_file = state_root / "project.yaml"
    state_file = state_root / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    state = json.loads(state_file.read_text(encoding="utf-8"))
    return root, project, state


def _require_accepted_intent(project: dict[str, object], state: dict[str, object]) -> dict[str, object]:
    intent_state = state["stages"]["research_intent"]
    if intent_state["status"] != "accepted":
        raise ValueError("Research Intent must be accepted before literature discovery.")
    research = project.get("research")
    if not isinstance(research, dict):
        raise ValueError("Research Intent is missing from project state.")
    return research


def _reconstruct_abstract(inverted: object) -> str | None:
    if not isinstance(inverted, dict) or not inverted:
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted.items():
        if not isinstance(positions, list):
            continue
        for position in positions:
            if isinstance(position, int):
                positioned.append((position, str(word)))
    if not positioned:
        return None
    positioned.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned)


def _authors(work: dict[str, object]) -> list[str]:
    values: list[str] = []
    authorships = work.get("authorships")
    if not isinstance(authorships, list):
        return values
    for authorship in authorships:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author")
        if isinstance(author, dict) and author.get("display_name"):
            values.append(str(author["display_name"]))
    return values


def _source_name(work: dict[str, object]) -> str | None:
    primary = work.get("primary_location")
    if not isinstance(primary, dict):
        return None
    source = primary.get("source")
    if not isinstance(source, dict):
        return None
    value = source.get("display_name")
    return str(value) if value else None


def _normalize_work(work: dict[str, object]) -> dict[str, object]:
    openalex_id = str(work.get("id") or "") or None
    title = str(work.get("display_name") or work.get("title") or "Untitled")
    doi = normalize_doi(str(work.get("doi"))) if work.get("doi") else None
    return {
        "paper_id": str(uuid4()),
        "title": title,
        "normalized_title": normalize_title(title),
        "authors": _authors(work),
        "year": work.get("publication_year"),
        "doi": doi,
        "openalex_id": openalex_id,
        "journal": _source_name(work),
        "language": work.get("language"),
        "citation_count": work.get("cited_by_count"),
        "publication_type": work.get("type"),
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "source_origin": "openalex",
        "location_type": "metadata_only",
        "file_reference": None,
        "file_instances": [],
        "file_hash": None,
        "page_count": None,
        "parse_status": "metadata_only",
        "parse_error": None,
        "status": "unresolved",
        "created_at": _now(),
        "updated_at": _now(),
    }


def _load_papers(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _identity_indexes(records: list[dict[str, object]]) -> tuple[set[str], set[str]]:
    openalex_ids = {
        str(record["openalex_id"])
        for record in records
        if record.get("openalex_id")
    }
    dois = {
        str(record["doi"])
        for record in records
        if record.get("doi")
    }
    return openalex_ids, dois


def search_openalex(
    root: Path,
    query: str,
    *,
    limit: int = 25,
    timeout: float = 30.0,
) -> dict[str, object]:
    """Search OpenAlex within accepted Publication period and language scope."""
    if not query.strip():
        raise ValueError("OpenAlex query cannot be empty.")
    if not 1 <= limit <= 100:
        raise ValueError("OpenAlex search limit must be between 1 and 100.")

    root, project, state = _load_project(root)
    research = _require_accepted_intent(project, state)
    period = research.get("publication_period") or {}
    if not isinstance(period, dict):
        raise ValueError("Publication period is missing from Research Intent.")
    start_year = int(period["from"])
    end_year = int(period["to"])
    languages = [str(item).lower() for item in research.get("languages", [])]

    filters = [
        f"from_publication_date:{start_year}-01-01",
        f"to_publication_date:{end_year}-12-31",
    ]
    params: dict[str, object] = {
        "search": query.strip(),
        "filter": ",".join(filters),
        "per_page": limit,
    }
    api_key = os.environ.get("OPENALEX_API_KEY")
    if api_key:
        params["api_key"] = api_key

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(f"{OPENALEX_BASE_URL}/works", params=params)
        response.raise_for_status()
        payload = response.json()

    raw_results = payload.get("results") or []
    if not isinstance(raw_results, list):
        raw_results = []
    # Language scope is enforced client-side so multi-language projects do not
    # depend on provider-specific OR filter syntax.
    scoped_results = [
        item
        for item in raw_results
        if isinstance(item, dict)
        and (not languages or str(item.get("language") or "").lower() in languages)
    ]

    state_root = root / PROJECT_DIR
    papers_file = state_root / "data" / "papers.jsonl"
    records = _load_papers(papers_file)
    openalex_ids, dois = _identity_indexes(records)
    imported_ids: list[str] = []
    already_known = 0

    for raw_work in scoped_results:
        record = _normalize_work(raw_work)
        oa_id = str(record.get("openalex_id") or "")
        doi = str(record.get("doi") or "")
        if (oa_id and oa_id in openalex_ids) or (doi and doi in dois):
            already_known += 1
            continue
        records.append(record)
        imported_ids.append(str(record["paper_id"]))
        if oa_id:
            openalex_ids.add(oa_id)
        if doi:
            dois.add(doi)

    records.sort(key=lambda item: (-(int(item.get("year") or 0)), str(item.get("title") or "").lower()))
    _atomic_write_text(
        papers_file,
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
    )
    relation_summary = resolve_bibliography(root)

    search_run_id = str(uuid4())
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    run = {
        "search_run_id": search_run_id,
        "provider": "openalex",
        "timestamp": _now(),
        "query": query.strip(),
        "filters": {
            "publication_period": {"from": start_year, "to": end_year},
            "languages": languages,
        },
        "requested_limit": limit,
        "provider_results_returned": len(raw_results),
        "scope_results_returned": len(scoped_results),
        "imported_records": len(imported_ids),
        "already_known": already_known,
        "imported_paper_ids": imported_ids,
        "provider_meta": {
            "count": meta.get("count"),
            "page": meta.get("page"),
            "per_page": meta.get("per_page"),
            "cost_usd": meta.get("cost_usd"),
        },
        "api_key_used": bool(api_key),
    }
    run_file = state_root / "searches" / f"{search_run_id}.json"
    _write_json(run_file, run)

    state["stages"]["literature_discovery"]["status"] = "in_progress"
    state["stages"]["literature_discovery"]["revision"] += 1
    state["current_stage"] = "literature_discovery"
    _write_json(state_root / "state.json", state)

    activity_file = state_root / "activity" / "activity.jsonl"
    event = {
        "event_id": str(uuid4()),
        "timestamp": _now(),
        "category": "literature_discovery",
        "actor": "toolkit",
        "host": None,
        "model": None,
        "inputs": {
            "provider": "openalex",
            "query": query.strip(),
            "publication_period": {"from": start_year, "to": end_year},
            "languages": languages,
        },
        "outputs": [
            str(run_file.relative_to(root)),
            ".litreview/data/papers.jsonl",
            ".litreview/data/paper_relations.jsonl",
        ],
        "source_ids": imported_ids,
        "notes": None,
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "search_run_id": search_run_id,
        "query": query.strip(),
        "provider_results": len(raw_results),
        "scope_results": len(scoped_results),
        "imported": len(imported_ids),
        "already_known": already_known,
        "cost_usd": meta.get("cost_usd"),
        "api_key_used": bool(api_key),
        "relation_candidates": relation_summary["relation_candidates"],
        "search_run_file": str(run_file),
    }


def search_history(root: Path) -> list[dict[str, object]]:
    root, _, _ = _load_project(root)
    search_dir = root / PROJECT_DIR / "searches"
    runs: list[dict[str, object]] = []
    for path in sorted(search_dir.glob("*.json"), reverse=True):
        try:
            runs.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return runs
