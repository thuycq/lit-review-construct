from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

from .campaign import (
    SUPPORTED_PROVIDERS,
    _campaign_path,
    _import_records,
    _load_jsonl,
    _load_project,
    _require_accepted_intent,
    _search_crossref,
    _search_openalex,
    _search_semantic_scholar,
    _write_jsonl,
    start_discovery_campaign,
)
from .papers import resolve_bibliography
from .project import PROJECT_DIR, _write_json
from .search_provenance import attach_search_hits


def _provider_error(provider: str, query: str, exc: httpx.HTTPError) -> dict[str, object]:
    status_code = None
    error_type = "http_error"
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if status_code in {401, 403}:
            error_type = "authentication_or_access"
        elif status_code == 429:
            error_type = "rate_limit"
        elif status_code >= 500:
            error_type = "provider_server_error"
    return {
        "provider": provider,
        "query": query,
        "error_type": error_type,
        "status_code": status_code,
        "message": str(exc)[:500],
    }


def run_resilient_discovery_iteration(
    root: Path,
    queries: list[str],
    *,
    providers: list[str] | None = None,
    phase: str = "broad",
    max_per_query_provider: int = 300,
    timeout: float = 45.0,
) -> dict[str, object]:
    """Run one multi-source iteration without losing successful provider results when another fails."""
    clean_queries = [value.strip() for value in queries if value.strip()]
    if not clean_queries:
        raise ValueError("At least one discovery query is required.")
    if phase not in {"broad", "focused", "citation_expansion"}:
        raise ValueError("phase must be broad, focused, or citation_expansion.")
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

    iteration_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    provider_runs: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    disabled_providers: set[str] = set()
    successful_calls = 0
    total_raw = 0
    total_imported = 0
    total_enriched = 0
    language_unknown = 0
    provenance_hits_attached = 0

    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "LitReviewConstruct/0.1"},
    ) as client:
        for query in clean_queries:
            for provider in selected_providers:
                if provider in disabled_providers:
                    provider_runs.append(
                        {
                            "provider": provider,
                            "query": query,
                            "status": "skipped_after_failure",
                            "raw_results": 0,
                            "new_records": 0,
                            "existing_records_enriched": 0,
                        }
                    )
                    continue
                try:
                    if provider == "openalex":
                        rows, meta = _search_openalex(
                            client,
                            query,
                            start_year,
                            end_year,
                            max_per_query_provider,
                        )
                    elif provider == "crossref":
                        rows, meta = _search_crossref(
                            client,
                            query,
                            start_year,
                            end_year,
                            max_per_query_provider,
                        )
                    else:
                        rows, meta = _search_semantic_scholar(
                            client,
                            query,
                            start_year,
                            end_year,
                            max_per_query_provider,
                        )
                except httpx.HTTPError as exc:
                    failure = _provider_error(provider, query, exc)
                    failures.append(failure)
                    provider_runs.append(
                        {
                            "provider": provider,
                            "query": query,
                            "status": "failed",
                            "raw_results": 0,
                            "new_records": 0,
                            "existing_records_enriched": 0,
                            "error": failure,
                        }
                    )
                    if failure["error_type"] in {
                        "authentication_or_access",
                        "rate_limit",
                        "provider_server_error",
                    }:
                        disabled_providers.add(provider)
                    continue

                successful_calls += 1
                imported, enriched, unknown = _import_records(records, rows, languages)
                attached = attach_search_hits(
                    records,
                    rows,
                    iteration_id=iteration_id,
                    phase=phase,
                    provider=provider,
                    query=query,
                    retrieved_at=now,
                )
                total_raw += len(rows)
                total_imported += imported
                total_enriched += enriched
                language_unknown += unknown
                provenance_hits_attached += attached
                provider_runs.append(
                    {
                        "provider": provider,
                        "query": query,
                        "status": "success",
                        "raw_results": len(rows),
                        "new_records": imported,
                        "existing_records_enriched": enriched,
                        "language_unknown": unknown,
                        "provenance_hits_attached": attached,
                        "meta": meta,
                    }
                )

    if successful_calls == 0:
        summary = "; ".join(
            f"{row['provider']}: {row['error_type']}"
            + (f" ({row['status_code']})" if row.get("status_code") else "")
            for row in failures
        )
        raise ValueError(
            "All scholarly providers failed for this discovery iteration. "
            + (summary or "No provider returned successfully.")
        )

    records.sort(
        key=lambda row: (
            -(int(row.get("year") or 0)),
            str(row.get("title") or "").lower(),
        )
    )
    _write_jsonl(papers_file, records)
    relation_summary = resolve_bibliography(root)

    iteration = {
        "iteration_id": iteration_id,
        "timestamp": now,
        "phase": phase,
        "queries": clean_queries,
        "providers": selected_providers,
        "successful_provider_calls": successful_calls,
        "provider_failures": failures,
        "disabled_providers_for_iteration": sorted(disabled_providers),
        "max_per_query_provider": max_per_query_provider,
        "provider_runs": provider_runs,
        "raw_results": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "language_unknown": language_unknown,
        "provenance_hits_attached": provenance_hits_attached,
        "corpus_records_after_iteration": len(records),
        "bibliographic_relation_candidates": relation_summary["relation_candidates"],
    }
    campaign["iterations"].append(iteration)
    campaign["revision"] = int(campaign.get("revision") or 0) + 1
    campaign["updated_at"] = now
    campaign["status"] = "focused" if campaign.get("status") == "focused" or phase == "focused" else "collecting"
    _write_json(campaign_file, campaign)
    _write_json(root / PROJECT_DIR / "searches" / f"campaign-{iteration_id}.json", iteration)

    state["stages"]["literature_discovery"]["status"] = "in_progress"
    state["current_stage"] = "literature_discovery"
    for stage in (
        "evidence_mapping",
        "research_direction",
        "literature_review_blueprint",
        "researcher_handoff",
    ):
        if state["stages"][stage]["status"] != "not_started":
            state["stages"][stage]["status"] = "needs_refresh"
    _write_json(root / PROJECT_DIR / "state.json", state)

    return {
        "iteration_id": iteration_id,
        "phase": phase,
        "queries": len(clean_queries),
        "providers_requested": len(selected_providers),
        "providers_succeeded": sorted(
            {
                str(row["provider"])
                for row in provider_runs
                if row.get("status") == "success"
            }
        ),
        "provider_failures": failures,
        "raw_results": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "provenance_hits_attached": provenance_hits_attached,
        "corpus_records": len(records),
        "relation_candidates": relation_summary["relation_candidates"],
        "language_unknown": language_unknown,
        "campaign_file": str(campaign_file),
    }
