from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import httpx

from .campaign import _campaign_path, _import_records, _load_jsonl, _write_jsonl
from .expansion import (
    _default_seed_ids,
    _expand_openalex_seed,
    _expand_s2_seed,
    _find_target,
    _load_project,
)
from .papers import resolve_bibliography
from .project import PROJECT_DIR, _write_json


def _failure(provider: str, seed_id: str, exc: httpx.HTTPError) -> dict[str, object]:
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
        "seed_paper_id": seed_id,
        "error_type": error_type,
        "status_code": status_code,
        "message": str(exc)[:500],
    }


def expand_resilient_citation_graph(
    root: Path,
    *,
    paper_ids: list[str] | None = None,
    relation: str = "both",
    providers: list[str] | None = None,
    max_per_seed_provider: int = 100,
    timeout: float = 45.0,
) -> dict[str, object]:
    if relation not in {"references", "citations", "both", "related"}:
        raise ValueError("relation must be references, citations, both, or related.")
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
    edge_keys = {
        (
            str(edge.get("source_paper_id")),
            str(edge.get("target_paper_id")),
            str(edge.get("relation")),
            str(edge.get("provider")),
        )
        for edge in graph_edges
    }
    provider_runs: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    disabled_providers: set[str] = set()
    successful_calls = 0
    total_raw = 0
    total_imported = 0
    total_enriched = 0
    new_edges = 0

    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "LitReviewConstruct/0.1"},
    ) as client:
        for seed_id in seed_ids:
            seed = by_id[seed_id]
            for provider in selected_providers:
                if provider in disabled_providers:
                    provider_runs.append(
                        {
                            "seed_paper_id": seed_id,
                            "provider": provider,
                            "status": "skipped_after_failure",
                            "raw_results": 0,
                        }
                    )
                    continue
                try:
                    if provider == "openalex":
                        discovered, meta = _expand_openalex_seed(
                            client,
                            seed,
                            relation,  # type: ignore[arg-type]
                            start_year,
                            end_year,
                            max_per_seed_provider,
                        )
                    else:
                        discovered, meta = _expand_s2_seed(
                            client,
                            seed,
                            relation,  # type: ignore[arg-type]
                            start_year,
                            end_year,
                            max_per_seed_provider,
                        )
                except httpx.HTTPError as exc:
                    failure = _failure(provider, seed_id, exc)
                    failures.append(failure)
                    provider_runs.append(
                        {
                            "seed_paper_id": seed_id,
                            "provider": provider,
                            "status": "failed",
                            "raw_results": 0,
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
                    if key in edge_keys:
                        continue
                    edge_keys.add(key)
                    graph_edges.append(
                        {
                            "edge_id": str(uuid4()),
                            "source_paper_id": seed_id,
                            "target_paper_id": str(target["paper_id"]),
                            "relation": relation_name,
                            "provider": provider,
                            "source_provider_id": meta.get("seed_provider_id"),
                            "target_provider_id": incoming.get("openalex_id")
                            or incoming.get("s2_paper_id")
                            or incoming.get("doi"),
                        }
                    )
                    new_edges += 1
                provider_runs.append(
                    {
                        "seed_paper_id": seed_id,
                        "provider": provider,
                        "status": "success",
                        "raw_results": len(incoming_rows),
                        "new_records": imported,
                        "existing_records_enriched": enriched,
                        "language_unknown": language_unknown,
                        "meta": meta,
                    }
                )

    if successful_calls == 0:
        summary = "; ".join(
            f"{row['provider']}: {row['error_type']}"
            + (f" ({row['status_code']})" if row.get("status_code") else "")
            for row in failures
        )
        raise ValueError("All citation-graph providers failed. " + (summary or "No provider succeeded."))

    records.sort(key=lambda row: (-(int(row.get("year") or 0)), str(row.get("title") or "").lower()))
    _write_jsonl(papers_file, records)
    _write_jsonl(graph_file, graph_edges)
    relation_summary = resolve_bibliography(root)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    iteration_id = str(uuid4())
    iteration = {
        "iteration_id": iteration_id,
        "timestamp": now,
        "phase": "citation_expansion",
        "queries": [],
        "seed_paper_ids": seed_ids,
        "graph_relation": relation,
        "providers": selected_providers,
        "successful_provider_calls": successful_calls,
        "provider_failures": failures,
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
    campaign["updated_at"] = now
    _write_json(campaign_file, campaign)
    _write_json(root / PROJECT_DIR / "searches" / f"campaign-{iteration_id}.json", iteration)

    state["stages"]["literature_discovery"]["status"] = "in_progress"
    state["current_stage"] = "literature_discovery"
    for stage in ("evidence_mapping", "research_direction", "literature_review_blueprint", "researcher_handoff"):
        if state["stages"][stage]["status"] != "not_started":
            state["stages"][stage]["status"] = "needs_refresh"
    _write_json(root / PROJECT_DIR / "state.json", state)

    return {
        "iteration_id": iteration_id,
        "seed_papers": len(seed_ids),
        "providers": selected_providers,
        "providers_succeeded": sorted(
            {str(row["provider"]) for row in provider_runs if row.get("status") == "success"}
        ),
        "provider_failures": failures,
        "relation": relation,
        "raw_graph_records": total_raw,
        "new_records": total_imported,
        "existing_records_enriched": total_enriched,
        "new_graph_edges": new_edges,
        "corpus_records": len(records),
        "relation_candidates": relation_summary["relation_candidates"],
        "graph_file": str(graph_file),
    }
