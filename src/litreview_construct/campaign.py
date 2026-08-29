from __future__ import annotations

import html
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import httpx
import yaml
from pydantic import BaseModel, Field

from .bibliography import normalize_doi, normalize_title
from .papers import resolve_bibliography
from .project import PROJECT_DIR, _atomic_write_text, _write_json

ProviderName = Literal["openalex", "crossref", "semantic_scholar"]
DiscoveryPhase = Literal["broad", "focused", "citation_expansion"]
DecisionAction = Literal["continue", "focus", "change_scope", "finish"]

SUPPORTED_PROVIDERS: tuple[str, ...] = ("openalex", "crossref", "semantic_scholar")
OPENALEX_BASE_URL = "https://api.openalex.org"
CROSSREF_BASE_URL = "https://api.crossref.org"
S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"


class ProvisionalStream(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    representative_paper_ids: list[str] = []
    indicative_terms: list[str] = []
    provisional_questions: list[str] = []
    confidence: Literal["low", "medium", "high"] = "medium"


class CandidateFocus(BaseModel):
    name: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    representative_paper_ids: list[str] = []
    query_suggestions: list[str] = []
    why_promising: list[str] = []
    risks: list[str] = []


class DiscoveryReviewSubmission(BaseModel):
    summary: str = Field(min_length=1)
    provisional_streams: list[ProvisionalStream] = Field(min_length=1)
    candidate_focuses: list[CandidateFocus] = Field(min_length=1, max_length=8)
    coverage_observations: list[str] = []
    recommended_next_actions: list[str] = []
    limitations: list[str] = []


class DiscoveryDecision(BaseModel):
    action: DecisionAction
    selected_focuses: list[str] = []
    researcher_notes: str | None = None


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


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    _atomic_write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _require_accepted_intent(project: dict[str, object], state: dict[str, object]) -> dict[str, object]:
    if state["stages"]["research_intent"]["status"] != "accepted":
        raise ValueError("Research Intent must be accepted before starting discovery.")
    research = project.get("research")
    if not isinstance(research, dict):
        raise ValueError("Research Intent is missing from project state.")
    return research


def _strip_markup(value: object) -> str | None:
    if not value:
        return None
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _first_text(value: object) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0]) if value[0] else None
    if isinstance(value, str):
        return value
    return None


def _crossref_year(item: dict[str, object]) -> int | None:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        value = item.get(key)
        if not isinstance(value, dict):
            continue
        date_parts = value.get("date-parts")
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            try:
                return int(date_parts[0][0])
            except (TypeError, ValueError):
                pass
    return None


def _openalex_abstract(inverted: object) -> str | None:
    if not isinstance(inverted, dict) or not inverted:
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted.items():
        if isinstance(positions, list):
            positioned.extend((position, str(word)) for position in positions if isinstance(position, int))
    if not positioned:
        return None
    positioned.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned)


def _openalex_record(work: dict[str, object]) -> dict[str, object]:
    authors: list[str] = []
    for authorship in work.get("authorships") or []:
        if isinstance(authorship, dict) and isinstance(authorship.get("author"), dict):
            name = authorship["author"].get("display_name")
            if name:
                authors.append(str(name))
    source = None
    primary = work.get("primary_location")
    if isinstance(primary, dict) and isinstance(primary.get("source"), dict):
        source = primary["source"].get("display_name")
    title = str(work.get("display_name") or work.get("title") or "Untitled")
    return {
        "title": title,
        "normalized_title": normalize_title(title),
        "authors": authors,
        "year": work.get("publication_year"),
        "doi": normalize_doi(str(work.get("doi"))) if work.get("doi") else None,
        "openalex_id": str(work.get("id")) if work.get("id") else None,
        "s2_paper_id": None,
        "journal": str(source) if source else None,
        "language": work.get("language"),
        "citation_count": work.get("cited_by_count"),
        "publication_type": work.get("type"),
        "abstract": _openalex_abstract(work.get("abstract_inverted_index")),
        "provider": "openalex",
    }


def _crossref_record(item: dict[str, object]) -> dict[str, object]:
    title = _first_text(item.get("title")) or "Untitled"
    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        name = " ".join(str(part) for part in (author.get("given"), author.get("family")) if part).strip()
        if name:
            authors.append(name)
    return {
        "title": title,
        "normalized_title": normalize_title(title),
        "authors": authors,
        "year": _crossref_year(item),
        "doi": normalize_doi(str(item.get("DOI"))) if item.get("DOI") else None,
        "openalex_id": None,
        "s2_paper_id": None,
        "journal": _first_text(item.get("container-title")),
        "language": item.get("language"),
        "citation_count": item.get("is-referenced-by-count"),
        "publication_type": item.get("type"),
        "abstract": _strip_markup(item.get("abstract")),
        "provider": "crossref",
    }


def _s2_record(item: dict[str, object]) -> dict[str, object]:
    title = str(item.get("title") or "Untitled")
    authors = [
        str(author.get("name"))
        for author in item.get("authors") or []
        if isinstance(author, dict) and author.get("name")
    ]
    external = item.get("externalIds") if isinstance(item.get("externalIds"), dict) else {}
    doi_value = external.get("DOI") if isinstance(external, dict) else None
    publication_types = item.get("publicationTypes")
    publication_type = None
    if isinstance(publication_types, list) and publication_types:
        publication_type = str(publication_types[0])
    return {
        "title": title,
        "normalized_title": normalize_title(title),
        "authors": authors,
        "year": item.get("year"),
        "doi": normalize_doi(str(doi_value)) if doi_value else None,
        "openalex_id": None,
        "s2_paper_id": str(item.get("paperId")) if item.get("paperId") else None,
        "journal": item.get("venue"),
        "language": None,
        "citation_count": item.get("citationCount"),
        "publication_type": publication_type,
        "abstract": item.get("abstract"),
        "provider": "semantic_scholar",
    }


def _request_with_backoff(
    client: httpx.Client,
    url: str,
    *,
    params: dict[str, object],
    headers: dict[str, str] | None = None,
    attempts: int = 4,
) -> httpx.Response:
    delay = 1.0
    for attempt in range(attempts):
        response = client.get(url, params=params, headers=headers)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        if attempt == attempts - 1:
            response.raise_for_status()
        time.sleep(delay)
        delay *= 2
    raise RuntimeError("Unreachable retry state")


def _search_openalex(
    client: httpx.Client,
    query: str,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    results: list[dict[str, object]] = []
    cursor = "*"
    calls = 0
    cost = 0.0
    while len(results) < max_results:
        per_page = min(100, max_results - len(results))
        params: dict[str, object] = {
            "search": query,
            "filter": f"from_publication_date:{start_year}-01-01,to_publication_date:{end_year}-12-31",
            "per_page": per_page,
            "cursor": cursor,
        }
        api_key = os.environ.get("OPENALEX_API_KEY")
        if api_key:
            params["api_key"] = api_key
        response = _request_with_backoff(client, f"{OPENALEX_BASE_URL}/works", params=params)
        payload = response.json()
        calls += 1
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if meta.get("cost_usd") is not None:
            try:
                cost += float(meta["cost_usd"])
            except (TypeError, ValueError):
                pass
        batch = payload.get("results") or []
        normalized = [_openalex_record(row) for row in batch if isinstance(row, dict)]
        results.extend(normalized)
        next_cursor = meta.get("next_cursor")
        if not normalized or not next_cursor:
            break
        cursor = str(next_cursor)
    return results[:max_results], {"calls": calls, "cost_usd": round(cost, 6), "api_key_used": bool(os.environ.get("OPENALEX_API_KEY"))}


def _search_crossref(
    client: httpx.Client,
    query: str,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    results: list[dict[str, object]] = []
    cursor = "*"
    calls = 0
    while len(results) < max_results:
        rows = min(1000, max_results - len(results))
        params: dict[str, object] = {
            "query.bibliographic": query,
            "filter": f"from-pub-date:{start_year}-01-01,until-pub-date:{end_year}-12-31",
            "rows": rows,
            "cursor": cursor,
        }
        mailto = os.environ.get("CROSSREF_MAILTO")
        if mailto:
            params["mailto"] = mailto
        response = _request_with_backoff(client, f"{CROSSREF_BASE_URL}/works", params=params)
        payload = response.json()
        calls += 1
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        batch = message.get("items") or []
        normalized = [_crossref_record(row) for row in batch if isinstance(row, dict)]
        results.extend(normalized)
        next_cursor = message.get("next-cursor")
        if not normalized or not next_cursor or str(next_cursor) == cursor:
            break
        cursor = str(next_cursor)
    return results[:max_results], {"calls": calls, "mailto_used": bool(os.environ.get("CROSSREF_MAILTO"))}


def _search_semantic_scholar(
    client: httpx.Client,
    query: str,
    start_year: int,
    end_year: int,
    max_results: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    results: list[dict[str, object]] = []
    token: str | None = None
    calls = 0
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    headers = {"x-api-key": api_key} if api_key else None
    while len(results) < max_results:
        params: dict[str, object] = {
            "query": query,
            "year": f"{start_year}-{end_year}",
            "fields": "title,abstract,year,authors,venue,citationCount,publicationTypes,externalIds,publicationDate",
            "limit": min(1000, max_results - len(results)),
        }
        if token:
            params["token"] = token
        response = _request_with_backoff(
            client,
            f"{S2_BASE_URL}/paper/search/bulk",
            params=params,
            headers=headers,
        )
        payload = response.json()
        calls += 1
        batch = payload.get("data") or []
        normalized = [_s2_record(row) for row in batch if isinstance(row, dict)]
        results.extend(normalized)
        next_token = payload.get("token")
        if not normalized or not next_token:
            break
        token = str(next_token)
    return results[:max_results], {"calls": calls, "api_key_used": bool(api_key)}


def _language_in_scope(record: dict[str, object], languages: list[str]) -> bool:
    if not languages:
        return True
    language = record.get("language")
    if language is None:
        return True  # retain unknown-language metadata for later triage instead of silently discarding it
    return str(language).lower() in languages


def _identity_indexes(records: list[dict[str, object]]) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    doi_index: dict[str, int] = {}
    openalex_index: dict[str, int] = {}
    s2_index: dict[str, int] = {}
    for index, record in enumerate(records):
        if record.get("doi"):
            doi_index[str(record["doi"])] = index
        if record.get("openalex_id"):
            openalex_index[str(record["openalex_id"])] = index
        if record.get("s2_paper_id"):
            s2_index[str(record["s2_paper_id"])] = index
    return doi_index, openalex_index, s2_index


def _merge_provider_record(existing: dict[str, object], incoming: dict[str, object]) -> None:
    provider = str(incoming["provider"])
    sources = existing.get("discovery_sources")
    if not isinstance(sources, list):
        sources = [existing.get("source_origin")] if existing.get("source_origin") else []
    if provider not in sources:
        sources.append(provider)
    existing["discovery_sources"] = sources
    for field in (
        "title",
        "normalized_title",
        "authors",
        "year",
        "doi",
        "openalex_id",
        "s2_paper_id",
        "journal",
        "language",
        "publication_type",
        "abstract",
    ):
        if not existing.get(field) and incoming.get(field):
            existing[field] = incoming[field]
    try:
        old_count = int(existing.get("citation_count") or 0)
        new_count = int(incoming.get("citation_count") or 0)
        existing["citation_count"] = max(old_count, new_count)
    except (TypeError, ValueError):
        pass
    existing["updated_at"] = _now()


def _new_paper_record(incoming: dict[str, object]) -> dict[str, object]:
    provider = str(incoming["provider"])
    now = _now()
    return {
        "paper_id": str(uuid4()),
        "title": incoming.get("title") or "Untitled",
        "normalized_title": incoming.get("normalized_title") or "",
        "authors": incoming.get("authors") or [],
        "year": incoming.get("year"),
        "doi": incoming.get("doi"),
        "openalex_id": incoming.get("openalex_id"),
        "s2_paper_id": incoming.get("s2_paper_id"),
        "journal": incoming.get("journal"),
        "language": incoming.get("language"),
        "citation_count": incoming.get("citation_count"),
        "publication_type": incoming.get("publication_type"),
        "abstract": incoming.get("abstract"),
        "source_origin": provider,
        "discovery_sources": [provider],
        "location_type": "metadata_only",
        "file_reference": None,
        "file_instances": [],
        "file_hash": None,
        "page_count": None,
        "parse_status": "metadata_only",
        "parse_error": None,
        "status": "unresolved",
        "created_at": now,
        "updated_at": now,
    }


def _import_records(
    records: list[dict[str, object]],
    incoming_rows: list[dict[str, object]],
    languages: list[str],
) -> tuple[int, int, int]:
    doi_index, openalex_index, s2_index = _identity_indexes(records)
    imported = 0
    enriched = 0
    language_unknown = 0
    for incoming in incoming_rows:
        if incoming.get("language") is None:
            language_unknown += 1
        if not _language_in_scope(incoming, languages):
            continue
        existing_index = None
        doi = str(incoming.get("doi") or "")
        openalex_id = str(incoming.get("openalex_id") or "")
        s2_id = str(incoming.get("s2_paper_id") or "")
        if doi and doi in doi_index:
            existing_index = doi_index[doi]
        elif openalex_id and openalex_id in openalex_index:
            existing_index = openalex_index[openalex_id]
        elif s2_id and s2_id in s2_index:
            existing_index = s2_index[s2_id]
        if existing_index is not None:
            _merge_provider_record(records[existing_index], incoming)
            enriched += 1
            continue
        record = _new_paper_record(incoming)
        records.append(record)
        index = len(records) - 1
        if record.get("doi"):
            doi_index[str(record["doi"])] = index
        if record.get("openalex_id"):
            openalex_index[str(record["openalex_id"])] = index
        if record.get("s2_paper_id"):
            s2_index[str(record["s2_paper_id"])] = index
        imported += 1
    return imported, enriched, language_unknown


def _campaign_path(root: Path) -> Path:
    return root / PROJECT_DIR / "data" / "discovery_campaign.json"


def start_discovery_campaign(root: Path, *, reset: bool = False) -> dict[str, object]:
    root, project, state = _load_project(root)
    research = _require_accepted_intent(project, state)
    path = _campaign_path(root)
    if path.exists() and not reset:
        campaign = json.loads(path.read_text(encoding="utf-8"))
        return {
            "created": False,
            "status": campaign.get("status"),
            "revision": campaign.get("revision"),
            "campaign_file": str(path),
        }
    now = _now()
    campaign = {
        "schema_version": 1,
        "campaign_id": str(uuid4()),
        "created_at": now,
        "updated_at": now,
        "status": "collecting",
        "revision": 0,
        "research_intent_revision": state["stages"]["research_intent"].get("revision", 0),
        "providers": list(SUPPORTED_PROVIDERS),
        "publication_period": research.get("publication_period") or {},
        "languages": research.get("languages") or [],
        "iterations": [],
        "review_checkpoints": [],
        "selected_focuses": [],
        "researcher_completion": None,
    }
    _write_json(path, campaign)
    # Existing downstream artifacts were vertical-slice/test outputs until a real discovery campaign completes.
    for stage in ("literature_discovery", "evidence_mapping", "research_direction", "literature_review_blueprint", "researcher_handoff"):
        if state["stages"][stage]["status"] != "not_started":
            state["stages"][stage]["status"] = "needs_refresh"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)
    return {"created": True, "status": "collecting", "revision": 0, "campaign_file": str(path)}


def run_discovery_iteration(
    root: Path,
    queries: list[str],
    *,
    providers: list[str] | None = None,
    phase: DiscoveryPhase = "broad",
    max_per_query_provider: int = 300,
    timeout: float = 45.0,
) -> dict[str, object]:
    if not queries or not any(query.strip() for query in queries):
        raise ValueError("At least one discovery query is required.")
    if not 10 <= max_per_query_provider <= 2000:
        raise ValueError("max_per_query_provider must be between 10 and 2000.")
    selected_providers = providers or list(SUPPORTED_PROVIDERS)
    invalid = sorted(set(selected_providers) - set(SUPPORTED_PROVIDERS))
    if invalid:
        raise ValueError("Unsupported discovery providers: " + ", ".join(invalid))

    root, project, state = _load_project(root)
    research = _require_accepted_intent(project, state)
    campaign_file = _campaign_path(root)
    if not campaign_file.exists():
        start_discovery_campaign(root)
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    if campaign.get("status") == "complete":
        raise ValueError("Discovery campaign is complete. Start/reset a campaign before collecting more papers.")

    period = research.get("publication_period") or {}
    start_year = int(period["from"])
    end_year = int(period["to"])
    languages = [str(value).lower() for value in research.get("languages") or []]
    papers_file = root / PROJECT_DIR / "data" / "papers.jsonl"
    records = _load_jsonl(papers_file)

    provider_runs: list[dict[str, object]] = []
    total_raw = 0
    total_imported = 0
    total_enriched = 0
    language_unknown = 0
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "LitReviewConstruct/0.1"}) as client:
        for query in [value.strip() for value in queries if value.strip()]:
            for provider in selected_providers:
                if provider == "openalex":
                    rows, meta = _search_openalex(client, query, start_year, end_year, max_per_query_provider)
                elif provider == "crossref":
                    rows, meta = _search_crossref(client, query, start_year, end_year, max_per_query_provider)
                else:
                    rows, meta = _search_semantic_scholar(client, query, start_year, end_year, max_per_query_provider)
                imported, enriched, unknown = _import_records(records, rows, languages)
                total_raw += len(rows)
                total_imported += imported
                total_enriched += enriched
                language_unknown += unknown
                provider_runs.append(
                    {
                        "provider": provider,
                        "query": query,
                        "raw_results": len(rows),
                        "new_records": imported,
                        "existing_records_enriched": enriched,
                        "language_unknown": unknown,
                        "meta": meta,
                    }
                )

    records.sort(key=lambda row: (-(int(row.get("year") or 0)), str(row.get("title") or "").lower()))
    _write_jsonl(papers_file, records)
    relation_summary = resolve_bibliography(root)

    iteration_id = str(uuid4())
    iteration = {
        "iteration_id": iteration_id,
        "timestamp": _now(),
        "phase": phase,
        "queries": [value.strip() for value in queries if value.strip()],
        "providers": selected_providers,
        "max_per_query_provider": max_per_query_provider,
        "provider_runs": provider_runs,
        "raw_results": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "language_unknown": language_unknown,
        "corpus_records_after_iteration": len(records),
        "bibliographic_relation_candidates": relation_summary["relation_candidates"],
    }
    campaign["iterations"].append(iteration)
    campaign["revision"] = int(campaign.get("revision") or 0) + 1
    campaign["updated_at"] = _now()
    campaign["status"] = "collecting"
    _write_json(campaign_file, campaign)

    run_file = root / PROJECT_DIR / "searches" / f"campaign-{iteration_id}.json"
    _write_json(run_file, iteration)
    state["stages"]["literature_discovery"]["status"] = "in_progress"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)

    return {
        "iteration_id": iteration_id,
        "phase": phase,
        "queries": len(iteration["queries"]),
        "providers": len(selected_providers),
        "raw_results": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "corpus_records": len(records),
        "relation_candidates": relation_summary["relation_candidates"],
        "language_unknown": language_unknown,
        "campaign_file": str(campaign_file),
    }


def _intent_tokens(project: dict[str, object]) -> set[str]:
    research = project.get("research") if isinstance(project.get("research"), dict) else {}
    text = " ".join(str(research.get(key) or "") for key in ("topic", "research_question"))
    return {token for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower()) if token not in {"the", "and", "for", "with", "from", "that", "this", "what", "how", "does", "are"}}


def _representative_records(
    records: list[dict[str, object]],
    project: dict[str, object],
    max_papers: int,
) -> list[dict[str, object]]:
    tokens = _intent_tokens(project)
    def lexical(row: dict[str, object]) -> int:
        text = f"{row.get('title') or ''} {row.get('abstract') or ''}".lower()
        return sum(1 for token in tokens if token in text)
    buckets = [
        sorted(records, key=lambda row: (-lexical(row), -(int(row.get("citation_count") or 0)), -(int(row.get("year") or 0)))),
        sorted(records, key=lambda row: (-(int(row.get("citation_count") or 0)), -lexical(row))),
        sorted(records, key=lambda row: (-(int(row.get("year") or 0)), -lexical(row))),
        sorted(records, key=lambda row: (-len(row.get("discovery_sources") or []), -lexical(row))),
    ]
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    positions = [0] * len(buckets)
    target = min(max_papers, len(records))
    while len(selected) < target:
        progressed = False
        for index, bucket in enumerate(buckets):
            while positions[index] < len(bucket):
                row = bucket[positions[index]]
                positions[index] += 1
                paper_id = str(row.get("paper_id") or "")
                if not paper_id or paper_id in seen:
                    continue
                seen.add(paper_id)
                selected.append(row)
                progressed = True
                break
            if len(selected) >= target:
                break
        if not progressed:
            break
    return selected


def _provider_coverage(records: list[dict[str, object]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in records:
        sources = row.get("discovery_sources")
        if isinstance(sources, list):
            for source in sources:
                if source:
                    counter[str(source)] += 1
        elif row.get("source_origin"):
            counter[str(row["source_origin"])] += 1
    return dict(sorted(counter.items()))


def prepare_discovery_review(root: Path, *, max_papers: int = 120, abstract_chars: int = 1800) -> dict[str, object]:
    if not 20 <= max_papers <= 250:
        raise ValueError("Discovery review max_papers must be between 20 and 250.")
    root, project, state = _load_project(root)
    _require_accepted_intent(project, state)
    campaign_file = _campaign_path(root)
    if not campaign_file.exists():
        raise ValueError("Start and run a discovery campaign before preparing a review checkpoint.")
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    if not campaign.get("iterations"):
        raise ValueError("No discovery iterations have been run yet.")
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    representative = _representative_records(records, project, max_papers)
    papers = []
    for row in representative:
        abstract = row.get("abstract")
        if isinstance(abstract, str) and len(abstract) > abstract_chars:
            abstract = abstract[:abstract_chars].rstrip() + "…"
        papers.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "authors": row.get("authors") or [],
                "year": row.get("year"),
                "journal": row.get("journal"),
                "citation_count": row.get("citation_count"),
                "doi": row.get("doi"),
                "abstract": abstract,
                "source_origin": row.get("source_origin"),
                "discovery_sources": row.get("discovery_sources") or [row.get("source_origin")],
                "status": row.get("status"),
            }
        )
    query_families = []
    for iteration in campaign.get("iterations") or []:
        if isinstance(iteration, dict):
            query_families.extend(str(query) for query in iteration.get("queries") or [])
    packet = {
        "packet_type": "discovery_review",
        "packet_schema_version": 1,
        "packet_id": str(uuid4()),
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "campaign_summary": {
            "status": campaign.get("status"),
            "iterations": len(campaign.get("iterations") or []),
            "query_families": list(dict.fromkeys(query_families)),
            "providers_used": sorted({provider for iteration in campaign.get("iterations") or [] if isinstance(iteration, dict) for provider in iteration.get("providers") or []}),
            "indexed_records": len(records),
            "provider_coverage": _provider_coverage(records),
            "review_checkpoints": len(campaign.get("review_checkpoints") or []),
        },
        "representative_papers": papers,
        "analysis_contract": {
            "purpose": "Provide an exploratory map of the broad discovery universe so the researcher can decide whether to continue, focus, or change scope.",
            "required": [
                "identify provisional research streams rather than definitive gaps",
                "suggest several candidate focus areas with query suggestions",
                "distinguish broad coverage observations from paper-level substantive evidence",
                "preserve paper_id references",
                "state where the corpus is thin, noisy, or dominated by one terminology family",
                "recommend whether another discovery iteration is useful",
            ],
            "prohibited": [
                "claiming a definitive research gap",
                "claiming systematic-review completeness",
                "treating representative packet papers as the entire discovery universe",
                "choosing the research focus without researcher approval",
                "writing a complete final literature review",
            ],
            "human_checkpoint": "After saving this review, stop and ask the researcher to continue broadly, focus on one or more areas, change scope, or finish discovery for the current narrative-review purpose.",
        },
        "expected_output_schema": {
            "summary": "string",
            "provisional_streams": [{"name": "string", "description": "string", "representative_paper_ids": ["paper_id"], "indicative_terms": ["string"], "provisional_questions": ["string"], "confidence": "low|medium|high"}],
            "candidate_focuses": [{"name": "string", "rationale": "string", "representative_paper_ids": ["paper_id"], "query_suggestions": ["string"], "why_promising": ["string"], "risks": ["string"]}],
            "coverage_observations": ["string"],
            "recommended_next_actions": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = root / PROJECT_DIR / "packets" / "discovery_review.json"
    _write_json(packet_file, packet)
    return {"packet_file": str(packet_file), "indexed_records": len(records), "representative_papers": len(papers), "iterations": len(campaign.get("iterations") or [])}


def save_discovery_review(root: Path, input_file: Path) -> dict[str, object]:
    root, _, state = _load_project(root)
    campaign_file = _campaign_path(root)
    if not campaign_file.exists():
        raise ValueError("No discovery campaign exists.")
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Discovery review input file not found: {input_path}")
    submission = DiscoveryReviewSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    known_ids = {str(row.get("paper_id")) for row in records if row.get("paper_id")}
    referenced = {paper_id for stream in submission.provisional_streams for paper_id in stream.representative_paper_ids}
    referenced.update(paper_id for focus in submission.candidate_focuses for paper_id in focus.representative_paper_ids)
    unknown = sorted(referenced - known_ids)
    if unknown:
        raise ValueError("Discovery review references unknown paper IDs: " + ", ".join(unknown))
    saved_at = _now()
    review = submission.model_dump()
    review.update({"schema_version": 1, "saved_at": saved_at, "provenance": "ai_synthesis"})
    review_file = root / PROJECT_DIR / "data" / "discovery_review.json"
    _write_json(review_file, review)

    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    checkpoint = {
        "checkpoint_id": str(uuid4()),
        "timestamp": saved_at,
        "iteration_revision": campaign.get("revision"),
        "review_file": ".litreview/data/discovery_review.json",
        "decision": None,
    }
    campaign["review_checkpoints"].append(checkpoint)
    campaign["status"] = "awaiting_researcher"
    campaign["updated_at"] = saved_at
    _write_json(campaign_file, campaign)

    lines = ["# Discovery Review", "", submission.summary, "", "## Provisional research streams", ""]
    for number, stream in enumerate(submission.provisional_streams, start=1):
        lines.extend([f"### {number}. {stream.name}", "", stream.description, ""])
        if stream.indicative_terms:
            lines.append("Indicative terms: " + ", ".join(stream.indicative_terms))
            lines.append("")
    lines.extend(["## Candidate focus areas", ""])
    for number, focus in enumerate(submission.candidate_focuses, start=1):
        lines.extend([f"### {number}. {focus.name}", "", focus.rationale, ""])
        if focus.query_suggestions:
            lines.extend(["Suggested next queries:", *[f"- {query}" for query in focus.query_suggestions], ""])
    if submission.coverage_observations:
        lines.extend(["## Coverage observations", "", *[f"- {item}" for item in submission.coverage_observations], ""])
    if submission.recommended_next_actions:
        lines.extend(["## Suggested next actions", "", *[f"- {item}" for item in submission.recommended_next_actions], ""])
    lines.extend(["> This is an exploratory discovery checkpoint, not evidence of a definitive research gap.", ""])
    output = root / "outputs" / "03_discovery_review.md"
    _atomic_write_text(output, "\n".join(lines))
    state["stages"]["literature_discovery"]["status"] = "ready_for_review"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)
    return {"status": "awaiting_researcher", "streams": len(submission.provisional_streams), "candidate_focuses": len(submission.candidate_focuses), "output": str(output)}


def record_discovery_decision(
    root: Path,
    *,
    action: DecisionAction,
    selected_focuses: list[str] | None = None,
    researcher_notes: str | None = None,
) -> dict[str, object]:
    root, _, state = _load_project(root)
    campaign_file = _campaign_path(root)
    if not campaign_file.exists():
        raise ValueError("No discovery campaign exists.")
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    checkpoints = campaign.get("review_checkpoints") or []
    if not checkpoints or campaign.get("status") != "awaiting_researcher":
        raise ValueError("A saved discovery review checkpoint is required before recording a decision.")
    decision = DiscoveryDecision(action=action, selected_focuses=selected_focuses or [], researcher_notes=researcher_notes)
    if action == "focus" and not decision.selected_focuses:
        raise ValueError("focus requires at least one selected focus name.")
    if action != "focus" and decision.selected_focuses:
        raise ValueError("selected_focuses are only valid for the focus action.")
    event = {"timestamp": _now(), **decision.model_dump()}
    checkpoints[-1]["decision"] = event
    campaign["review_checkpoints"] = checkpoints
    campaign["updated_at"] = event["timestamp"]
    if action == "continue":
        campaign["status"] = "collecting"
        campaign["selected_focuses"] = []
    elif action == "focus":
        campaign["status"] = "focused"
        campaign["selected_focuses"] = decision.selected_focuses
    elif action == "change_scope":
        campaign["status"] = "scope_change_requested"
        campaign["selected_focuses"] = []
    else:
        campaign["status"] = "complete"
        campaign["researcher_completion"] = event
        campaign["selected_focuses"] = campaign.get("selected_focuses") or []
    _write_json(campaign_file, campaign)
    state["stages"]["literature_discovery"]["status"] = "accepted" if action == "finish" else "in_progress"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)
    return {"action": action, "status": campaign["status"], "selected_focuses": campaign.get("selected_focuses") or [], "campaign_file": str(campaign_file)}


def discovery_status(root: Path) -> dict[str, object]:
    root, _, _ = _load_project(root)
    campaign_file = _campaign_path(root)
    if not campaign_file.exists():
        return {"exists": False, "status": "not_started", "campaign_file": str(campaign_file)}
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    queries: list[str] = []
    providers: set[str] = set()
    for iteration in campaign.get("iterations") or []:
        if isinstance(iteration, dict):
            queries.extend(str(value) for value in iteration.get("queries") or [])
            providers.update(str(value) for value in iteration.get("providers") or [])
    warnings: list[str] = []
    if len(providers) < 2:
        warnings.append("Fewer than two scholarly providers have been used.")
    if len(set(queries)) < 2:
        warnings.append("Only one query family has been used; terminology coverage may be narrow.")
    if len(records) < 50:
        warnings.append("The indexed corpus is small for broad discovery; this may be appropriate only for a narrow topic.")
    if not campaign.get("review_checkpoints"):
        warnings.append("No researcher discovery-review checkpoint has been completed.")
    return {
        "exists": True,
        "status": campaign.get("status"),
        "revision": campaign.get("revision"),
        "iterations": len(campaign.get("iterations") or []),
        "query_families": len(set(queries)),
        "providers_used": sorted(providers),
        "indexed_records": len(records),
        "provider_coverage": _provider_coverage(records),
        "review_checkpoints": len(campaign.get("review_checkpoints") or []),
        "selected_focuses": campaign.get("selected_focuses") or [],
        "warnings": warnings,
        "campaign_file": str(campaign_file),
    }
