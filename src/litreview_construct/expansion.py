from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from uuid import uuid4

import httpx

from .campaign import (
    OPENALEX_BASE_URL,
    S2_BASE_URL,
    _campaign_path,
    _import_records,
    _load_jsonl,
    _openalex_record,
    _request_with_backoff,
    _s2_record,
    _write_jsonl,
)
from .papers import resolve_bibliography
from .project import PROJECT_DIR, _write_json

GraphRelation = Literal["references", "citations", "both", "related"]
GraphProvider = Literal["openalex", "semantic_scholar"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_project(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    import yaml

    root = root.expanduser().resolve()
    project_file = root / PROJECT_DIR / "project.yaml"
    state_file = root / PROJECT_DIR / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    state = json.loads(state_file.read_text(encoding="utf-8"))
    return root, project, state


def _short_openalex_id(value: str) -> str:
    return value.rstrip("/").split("/")[-1]


def _openalex_params(extra: dict[str, object] | None = None) -> dict[str, object]:
    params = dict(extra or {})
    api_key = os.environ.get("OPENALEX_API_KEY")
    if api_key:
        params["api_key"] = api_key
    return params


def _resolve_openalex_seed(client: httpx.Client, row: dict[str, object]) -> dict[str, object] | None:
    identifier = row.get("openalex_id")
    if identifier:
        path_id = _short_openalex_id(str(identifier))
    elif row.get("doi"):
        path_id = "doi:" + str(row["doi"])
    else:
        return None
    response = _request_with_backoff(
        client,
        f"{OPENALEX_BASE_URL}/works/{quote(path_id, safe=':')}",
        params=_openalex_params(),
    )
    payload = response.json()
    if not isinstance(payload, dict):
        return None
    return payload


def _openalex_fetch_ids(
    client: httpx.Client,
    ids: list[str],
    *,
    max_results: int,
) -> tuple[list[dict[str, object]], int]:
    rows: list[dict[str, object]] = []
    calls = 0
    short_ids = [_short_openalex_id(value) for value in ids if value]
    for start in range(0, min(len(short_ids), max_results), 100):
        chunk = short_ids[start : start + 100]
        if not chunk:
            continue
        params = _openalex_params(
            {
                "filter": "openalex_id:" + "|".join(chunk),
                "per_page": min(100, len(chunk)),
            }
        )
        response = _request_with_backoff(client, f"{OPENALEX_BASE_URL}/works", params=params)
        payload = response.json()
        calls += 1
        batch = payload.get("results") if isinstance(payload, dict) else []
        rows.extend(_openalex_record(item) for item in batch or [] if isinstance(item, dict))
        if len(rows) >= max_results:
            break
    return rows[:max_results], calls


def _openalex_filter_expand(
    client: httpx.Client,
    seed_openalex_id: str,
    relation: str,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[dict[str, object]], int]:
    results: list[dict[str, object]] = []
    cursor = "*"
    calls = 0
    seed_id = _short_openalex_id(seed_openalex_id)
    relation_filter = "cites" if relation == "citations" else "related_to"
    while len(results) < max_results:
        per_page = min(100, max_results - len(results))
        filters = [
            f"{relation_filter}:{seed_id}",
            f"from_publication_date:{start_year}-01-01",
            f"to_publication_date:{end_year}-12-31",
        ]
        params = _openalex_params(
            {
                "filter": ",".join(filters),
                "per_page": per_page,
                "cursor": cursor,
            }
        )
        response = _request_with_backoff(client, f"{OPENALEX_BASE_URL}/works", params=params)
        payload = response.json()
        calls += 1
        batch = payload.get("results") if isinstance(payload, dict) else []
        normalized = [_openalex_record(item) for item in batch or [] if isinstance(item, dict)]
        results.extend(normalized)
        meta = payload.get("meta") if isinstance(payload, dict) and isinstance(payload.get("meta"), dict) else {}
        next_cursor = meta.get("next_cursor")
        if not normalized or not next_cursor:
            break
        cursor = str(next_cursor)
    return results[:max_results], calls


def _expand_openalex_seed(
    client: httpx.Client,
    seed: dict[str, object],
    relation: GraphRelation,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[tuple[str, dict[str, object]]], dict[str, object]]:
    work = _resolve_openalex_seed(client, seed)
    if not work:
        return [], {"calls": 0, "resolved": False, "reason": "No OpenAlex ID or DOI available."}
    seed_openalex = str(work.get("id") or "")
    if seed_openalex and not seed.get("openalex_id"):
        seed["openalex_id"] = seed_openalex
    discovered: list[tuple[str, dict[str, object]]] = []
    calls = 1

    if relation in {"references", "both"}:
        reference_ids = [str(value) for value in work.get("referenced_works") or [] if value]
        rows, extra_calls = _openalex_fetch_ids(client, reference_ids, max_results=max_results)
        calls += extra_calls
        discovered.extend(("references", row) for row in rows if _year_in_scope(row, start_year, end_year))

    if relation in {"citations", "both"}:
        rows, extra_calls = _openalex_filter_expand(
            client, seed_openalex, "citations", start_year, end_year, max_results
        )
        calls += extra_calls
        discovered.extend(("citations", row) for row in rows)

    if relation == "related":
        rows, extra_calls = _openalex_filter_expand(
            client, seed_openalex, "related", start_year, end_year, max_results
        )
        calls += extra_calls
        discovered.extend(("related", row) for row in rows)

    return discovered, {
        "calls": calls,
        "resolved": True,
        "seed_provider_id": seed_openalex,
        "api_key_used": bool(os.environ.get("OPENALEX_API_KEY")),
    }


def _s2_seed_identifier(seed: dict[str, object]) -> str | None:
    if seed.get("s2_paper_id"):
        return str(seed["s2_paper_id"])
    if seed.get("doi"):
        return "DOI:" + str(seed["doi"])
    return None


def _expand_s2_endpoint(
    client: httpx.Client,
    seed_identifier: str,
    endpoint: str,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[dict[str, object]], int]:
    results: list[dict[str, object]] = []
    offset = 0
    calls = 0
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    headers = {"x-api-key": api_key} if api_key else None
    nested = "citedPaper" if endpoint == "references" else "citingPaper"
    while len(results) < max_results:
        limit = min(1000, max_results - len(results))
        params: dict[str, object] = {
            "offset": offset,
            "limit": limit,
            "fields": "title,abstract,year,authors,venue,citationCount,publicationTypes,externalIds",
        }
        url = f"{S2_BASE_URL}/paper/{quote(seed_identifier, safe='')}/{endpoint}"
        response = _request_with_backoff(client, url, params=params, headers=headers)
        payload = response.json()
        calls += 1
        batch = payload.get("data") if isinstance(payload, dict) else []
        normalized: list[dict[str, object]] = []
        for item in batch or []:
            if not isinstance(item, dict) or not isinstance(item.get(nested), dict):
                continue
            row = _s2_record(item[nested])
            if _year_in_scope(row, start_year, end_year):
                normalized.append(row)
        results.extend(normalized)
        next_offset = payload.get("next") if isinstance(payload, dict) else None
        if next_offset is None or not batch:
            break
        offset = int(next_offset)
    return results[:max_results], calls


def _expand_s2_seed(
    client: httpx.Client,
    seed: dict[str, object],
    relation: GraphRelation,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[tuple[str, dict[str, object]]], dict[str, object]]:
    identifier = _s2_seed_identifier(seed)
    if not identifier:
        return [], {"calls": 0, "resolved": False, "reason": "No Semantic Scholar ID or DOI available."}
    if relation == "related":
        return [], {
            "calls": 0,
            "resolved": False,
            "reason": "Related-paper expansion uses OpenAlex in v0.1; Semantic Scholar is used for references/citations.",
        }
    discovered: list[tuple[str, dict[str, object]]] = []
    calls = 0
    endpoints = ["references", "citations"] if relation == "both" else [relation]
    for endpoint in endpoints:
        rows, extra_calls = _expand_s2_endpoint(
            client,
            identifier,
            endpoint,
            start_year,
            end_year,
            max_results,
        )
        calls += extra_calls
        discovered.extend((endpoint, row) for row in rows)
    return discovered, {
        "calls": calls,
        "resolved": True,
        "seed_provider_id": identifier,
        "api_key_used": bool(os.environ.get("SEMANTIC_SCHOLAR_API_KEY")),
    }


def _year_in_scope(row: dict[str, object], start_year: int, end_year: int) -> bool:
    try:
        year = int(row.get("year") or 0)
    except (TypeError, ValueError):
        return True
    if not year:
        return True
    return start_year <= year <= end_year


def _default_seed_ids(records: list[dict[str, object]], limit: int = 10) -> list[str]:
    rank = {"core_candidate": 0, "high": 1, "medium": 2, "low": 3}
    candidates = [
        row
        for row in records
        if row.get("triage_label") == "relevant" or row.get("landscape_roles") and "anchor" in row.get("landscape_roles")
    ]
    candidates.sort(
        key=lambda row: (
            rank.get(str(row.get("triage_priority") or "medium"), 9),
            -(int(row.get("citation_count") or 0)),
            -(int(row.get("year") or 0)),
        )
    )
    return [str(row["paper_id"]) for row in candidates[:limit] if row.get("paper_id")]


def _find_target(records: list[dict[str, object]], incoming: dict[str, object]) -> dict[str, object] | None:
    doi = incoming.get("doi")
    oa = incoming.get("openalex_id")
    s2 = incoming.get("s2_paper_id")
    normalized = incoming.get("normalized_title")
    year = incoming.get("year")
    for row in records:
        if doi and row.get("doi") == doi:
            return row
        if oa and row.get("openalex_id") == oa:
            return row
        if s2 and row.get("s2_paper_id") == s2:
            return row
    if normalized:
        for row in records:
            if row.get("normalized_title") == normalized and (not year or not row.get("year") or row.get("year") == year):
                return row
    return None


def expand_citation_graph(
    root: Path,
    *,
    paper_ids: list[str] | None = None,
    relation: GraphRelation = "both",
    providers: list[str] | None = None,
    max_per_seed_provider: int = 100,
    timeout: float = 45.0,
) -> dict[str, object]:
    """Expand selected papers through references/citations/related-work graph links."""
    if not 10 <= max_per_seed_provider <= 500:
        raise ValueError("max_per_seed_provider must be between 10 and 500.")
    selected_providers = providers or ["openalex", "semantic_scholar"]
    invalid = sorted(set(selected_providers) - {"openalex", "semantic_scholar"})
    if invalid:
        raise ValueError("Graph expansion supports only OpenAlex and Semantic Scholar: " + ", ".join(invalid))

    root, project, state = _load_project(root)
    campaign_file = _campaign_path(root)
    if not campaign_file.exists():
        raise ValueError("A discovery campaign is required before citation expansion.")
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    if campaign.get("status") == "complete":
        raise ValueError("Discovery campaign is complete. Start/reset it before expanding the graph.")
    papers_file = root / PROJECT_DIR / "data" / "papers.jsonl"
    records = _load_jsonl(papers_file)
    by_id = {str(row.get("paper_id")): row for row in records if row.get("paper_id")}
    seed_ids = list(dict.fromkeys(paper_ids or _default_seed_ids(records)))
    if not seed_ids:
        raise ValueError("No graph-expansion seeds were supplied and no relevant/core candidate papers are available.")
    if len(seed_ids) > 20:
        raise ValueError("Use at most 20 graph-expansion seeds per iteration to prevent uncontrolled snowballing.")
    unknown = sorted(set(seed_ids) - set(by_id))
    if unknown:
        raise ValueError("Unknown graph-expansion paper IDs: " + ", ".join(unknown))

    research = project.get("research") if isinstance(project.get("research"), dict) else {}
    period = research.get("publication_period") if isinstance(research.get("publication_period"), dict) else {}
    start_year = int(period.get("from"))
    end_year = int(period.get("to"))
    languages = [str(value).lower() for value in research.get("languages") or []]

    graph_file = root / PROJECT_DIR / "data" / "paper_graph.jsonl"
    graph_edges = _load_jsonl(graph_file)
    existing_edge_keys = {
        (str(edge.get("source_paper_id")), str(edge.get("target_paper_id")), str(edge.get("relation")), str(edge.get("provider")))
        for edge in graph_edges
    }
    provider_runs: list[dict[str, object]] = []
    total_raw = 0
    total_imported = 0
    total_enriched = 0
    new_edges = 0

    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "LitReviewConstruct/0.1"}) as client:
        for seed_id in seed_ids:
            seed = by_id[seed_id]
            for provider in selected_providers:
                if provider == "openalex":
                    discovered, meta = _expand_openalex_seed(
                        client, seed, relation, start_year, end_year, max_per_seed_provider
                    )
                else:
                    discovered, meta = _expand_s2_seed(
                        client, seed, relation, start_year, end_year, max_per_seed_provider
                    )
                incoming_rows = [row for _, row in discovered]
                imported, enriched, language_unknown = _import_records(records, incoming_rows, languages)
                total_raw += len(incoming_rows)
                total_imported += imported
                total_enriched += enriched
                for relation_name, incoming in discovered:
                    target = _find_target(records, incoming)
                    if not target or not target.get("paper_id") or target.get("paper_id") == seed_id:
                        continue
                    key = (seed_id, str(target["paper_id"]), relation_name, provider)
                    if key in existing_edge_keys:
                        continue
                    existing_edge_keys.add(key)
                    graph_edges.append(
                        {
                            "edge_id": str(uuid4()),
                            "timestamp": _now(),
                            "source_paper_id": seed_id,
                            "target_paper_id": str(target["paper_id"]),
                            "relation": relation_name,
                            "provider": provider,
                            "source_provider_id": meta.get("seed_provider_id"),
                            "target_provider_id": incoming.get("openalex_id") or incoming.get("s2_paper_id") or incoming.get("doi"),
                        }
                    )
                    new_edges += 1
                provider_runs.append(
                    {
                        "seed_paper_id": seed_id,
                        "provider": provider,
                        "relation": relation,
                        "raw_results": len(incoming_rows),
                        "new_records": imported,
                        "existing_records_enriched": enriched,
                        "language_unknown": language_unknown,
                        "meta": meta,
                    }
                )

    records.sort(key=lambda row: (-(int(row.get("year") or 0)), str(row.get("title") or "").lower()))
    _write_jsonl(papers_file, records)
    _write_jsonl(graph_file, graph_edges)
    relation_summary = resolve_bibliography(root)

    iteration_id = str(uuid4())
    iteration = {
        "iteration_id": iteration_id,
        "timestamp": _now(),
        "phase": "citation_expansion",
        "queries": [],
        "seed_paper_ids": seed_ids,
        "graph_relation": relation,
        "providers": selected_providers,
        "max_per_seed_provider": max_per_seed_provider,
        "provider_runs": provider_runs,
        "raw_results": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "new_graph_edges": new_edges,
        "corpus_records_after_iteration": len(records),
        "bibliographic_relation_candidates": relation_summary["relation_candidates"],
    }
    campaign["iterations"].append(iteration)
    campaign["revision"] = int(campaign.get("revision") or 0) + 1
    campaign["status"] = "collecting" if campaign.get("status") != "focused" else "focused"
    campaign["updated_at"] = _now()
    _write_json(campaign_file, campaign)
    _write_json(root / PROJECT_DIR / "searches" / f"campaign-{iteration_id}.json", iteration)

    # New graph papers have not yet been triaged, so any accepted discovery/downstream artifact becomes stale.
    state["stages"]["literature_discovery"]["status"] = "in_progress"
    for stage in ("evidence_mapping", "research_direction", "literature_review_blueprint", "researcher_handoff"):
        if state["stages"][stage]["status"] != "not_started":
            state["stages"][stage]["status"] = "needs_refresh"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)

    return {
        "iteration_id": iteration_id,
        "seed_papers": len(seed_ids),
        "providers": selected_providers,
        "relation": relation,
        "raw_graph_records": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "new_graph_edges": new_edges,
        "corpus_records": len(records),
        "relation_candidates": relation_summary["relation_candidates"],
        "graph_file": str(graph_file),
    }
