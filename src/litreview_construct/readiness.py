from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .project import PROJECT_DIR


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def assess_discovery_readiness(root: Path) -> dict[str, object]:
    """Describe discovery coverage before a researcher decides to finish.

    This is intentionally diagnostic rather than a numeric sufficiency score. Narrative-review
    topics differ too much for a universal paper-count or screening threshold.
    """
    root = root.expanduser().resolve()
    campaign_file = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not campaign_file.exists():
        raise ValueError("No discovery campaign exists.")
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    papers = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    campaign_id = str(campaign.get("campaign_id") or "")

    successful_providers: set[str] = set()
    successful_queries: set[str] = set()
    focused_iterations = 0
    graph_iterations = 0
    provider_failures = 0
    for iteration in campaign.get("iterations") or []:
        if not isinstance(iteration, dict):
            continue
        phase = str(iteration.get("phase") or "")
        if phase == "focused":
            focused_iterations += 1
        if phase == "citation_expansion":
            graph_iterations += 1
        runs = iteration.get("provider_runs") or []
        successful_query_in_iteration: set[str] = set()
        if isinstance(runs, list) and runs:
            for run in runs:
                if not isinstance(run, dict):
                    continue
                if run.get("status") == "success" or "status" not in run:
                    provider = run.get("provider")
                    if provider:
                        successful_providers.add(str(provider))
                    query = run.get("query")
                    if query:
                        successful_queries.add(str(query))
                        successful_query_in_iteration.add(str(query))
                if run.get("status") == "failed":
                    provider_failures += 1
        else:
            # Backward-compatible fallback for early development campaign records.
            successful_providers.update(str(value) for value in iteration.get("providers") or [])
            successful_queries.update(str(value) for value in iteration.get("queries") or [])

        # Graph iterations normally have no keyword queries; do not count them as query families.
        if not successful_query_in_iteration and phase != "citation_expansion" and not runs:
            successful_queries.update(str(value) for value in iteration.get("queries") or [])

    triaged = [
        row
        for row in papers
        if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")
    ]
    labels = Counter(str(row.get("triage_label")) for row in triaged)
    triaged_count = len(triaged)
    indexed_count = len(papers)
    untriaged_count = max(0, indexed_count - triaged_count)
    triage_ratio = triaged_count / indexed_count if indexed_count else 0.0
    unresolved_count = labels.get("unresolved", 0)
    retained_count = sum(labels.get(label, 0) for label in ("relevant", "background", "adjacent"))

    plan_history = _load_jsonl(root / PROJECT_DIR / "data" / "discovery_query_plans.jsonl")
    review_checkpoints = len(campaign.get("review_checkpoints") or [])
    selected_focuses = [str(value) for value in campaign.get("selected_focuses") or []]
    graph_edges = _load_jsonl(root / PROJECT_DIR / "data" / "paper_graph.jsonl")

    strengths: list[str] = []
    warnings: list[str] = []
    if len(successful_providers) >= 2:
        strengths.append("Multiple scholarly providers returned usable results.")
    else:
        warnings.append("Fewer than two scholarly providers returned usable results.")

    if len(successful_queries) >= 2:
        strengths.append("Multiple successful keyword/concept query families were used.")
    else:
        warnings.append("Fewer than two successful keyword/concept query families were used.")

    if plan_history:
        strengths.append("Structured query planning was saved for auditability.")
    else:
        warnings.append("No structured Query Plan was saved for this project.")

    if review_checkpoints:
        strengths.append("At least one researcher discovery-review checkpoint was completed.")
    else:
        warnings.append("No researcher discovery-review checkpoint has been completed.")

    if triaged_count:
        strengths.append(f"{triaged_count} papers were triaged for relevance in the current campaign.")
    else:
        warnings.append("No papers have been triaged in the current campaign.")

    if untriaged_count:
        warnings.append(
            f"{untriaged_count} of {indexed_count} indexed records remain untriaged "
            f"({(1.0 - triage_ratio):.1%} of the corpus)."
        )
    elif indexed_count:
        strengths.append("All currently indexed records have a triage decision.")

    if unresolved_count:
        warnings.append(f"{unresolved_count} triaged records remain unresolved.")
    if selected_focuses and focused_iterations:
        strengths.append("Researcher-selected focus areas received focused follow-up retrieval.")
    elif selected_focuses:
        warnings.append("A researcher-selected focus exists but no focused retrieval iteration is recorded.")

    if graph_iterations or graph_edges:
        strengths.append("Citation/reference network expansion was used around selected papers.")

    if retained_count == 0 and triaged_count:
        warnings.append("Triage retained no relevant/background/adjacent papers for a final Research Landscape.")

    return {
        "campaign_id": campaign_id,
        "campaign_status": campaign.get("status"),
        "indexed_records": indexed_count,
        "successful_providers": sorted(successful_providers),
        "successful_provider_count": len(successful_providers),
        "successful_query_families": sorted(successful_queries),
        "successful_query_family_count": len(successful_queries),
        "saved_query_plans": len(plan_history),
        "review_checkpoints": review_checkpoints,
        "selected_focuses": selected_focuses,
        "focused_iterations": focused_iterations,
        "citation_expansion_iterations": graph_iterations,
        "graph_edges": len(graph_edges),
        "provider_failures": provider_failures,
        "triaged_records": triaged_count,
        "triage_ratio": round(triage_ratio, 4),
        "triage_labels": dict(sorted(labels.items())),
        "retained_records": retained_count,
        "untriaged_records": untriaged_count,
        "unresolved_records": unresolved_count,
        "strengths": strengths,
        "warnings": warnings,
        "advisory_only": True,
        "note": (
            "Discovery readiness is a coverage diagnostic, not a universal sufficiency score. "
            "The researcher retains the final decision to continue or finish discovery."
        ),
    }
