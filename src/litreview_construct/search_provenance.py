from __future__ import annotations

from collections import Counter
from typing import Iterable

from .bibliography import normalize_doi, normalize_title


def _identity_indexes(records: list[dict[str, object]]) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict], dict[tuple[str, object], list[dict]]]:
    doi_index: dict[str, dict] = {}
    openalex_index: dict[str, dict] = {}
    s2_index: dict[str, dict] = {}
    title_year_index: dict[tuple[str, object], list[dict]] = {}
    for row in records:
        doi = normalize_doi(str(row.get("doi"))) if row.get("doi") else None
        if doi:
            doi_index[doi] = row
        if row.get("openalex_id"):
            openalex_index[str(row["openalex_id"])] = row
        if row.get("s2_paper_id"):
            s2_index[str(row["s2_paper_id"])] = row
        normalized = str(row.get("normalized_title") or normalize_title(str(row.get("title") or "")))
        if normalized:
            title_year_index.setdefault((normalized, row.get("year")), []).append(row)
    return doi_index, openalex_index, s2_index, title_year_index


def _find_record(
    incoming: dict[str, object],
    indexes: tuple[dict[str, dict], dict[str, dict], dict[str, dict], dict[tuple[str, object], list[dict]]],
) -> dict | None:
    doi_index, openalex_index, s2_index, title_year_index = indexes
    doi = normalize_doi(str(incoming.get("doi"))) if incoming.get("doi") else None
    if doi and doi in doi_index:
        return doi_index[doi]
    if incoming.get("openalex_id") and str(incoming["openalex_id"]) in openalex_index:
        return openalex_index[str(incoming["openalex_id"])]
    if incoming.get("s2_paper_id") and str(incoming["s2_paper_id"]) in s2_index:
        return s2_index[str(incoming["s2_paper_id"])]
    normalized = str(
        incoming.get("normalized_title") or normalize_title(str(incoming.get("title") or ""))
    )
    candidates = title_year_index.get((normalized, incoming.get("year")), [])
    return candidates[0] if len(candidates) == 1 else None


def attach_search_hits(
    records: list[dict[str, object]],
    incoming_rows: Iterable[dict[str, object]],
    *,
    iteration_id: str,
    phase: str,
    provider: str,
    query: str,
    retrieved_at: str,
) -> int:
    """Attach auditable query/provider retrieval provenance to matching paper records.

    Strong identifiers are preferred. Title+year is used only when it resolves to exactly one
    record, avoiding ambiguous provenance assignment.
    """
    indexes = _identity_indexes(records)
    attached = 0
    hit = {
        "iteration_id": iteration_id,
        "phase": phase,
        "provider": provider,
        "query": query,
        "retrieved_at": retrieved_at,
    }
    for incoming in incoming_rows:
        row = _find_record(incoming, indexes)
        if row is None:
            continue
        hits = row.get("discovery_hits")
        if not isinstance(hits, list):
            hits = []
            row["discovery_hits"] = hits
        key = (iteration_id, phase, provider, query)
        existing_keys = {
            (
                str(existing.get("iteration_id")),
                str(existing.get("phase")),
                str(existing.get("provider")),
                str(existing.get("query")),
            )
            for existing in hits
            if isinstance(existing, dict)
        }
        if key not in existing_keys:
            hits.append(dict(hit))
            attached += 1
    return attached


def query_coverage(records: Iterable[dict[str, object]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in records:
        for hit in row.get("discovery_hits") or []:
            if isinstance(hit, dict) and hit.get("query"):
                counter[str(hit["query"])] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0].lower())))


def provider_query_coverage(records: Iterable[dict[str, object]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in records:
        for hit in row.get("discovery_hits") or []:
            if not isinstance(hit, dict):
                continue
            provider = str(hit.get("provider") or "unknown")
            query = str(hit.get("query") or "")
            if query:
                counter[f"{provider} | {query}"] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0].lower())))
