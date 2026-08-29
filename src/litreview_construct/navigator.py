from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import yaml

from .project import PROJECT_DIR

NextAction = Literal[
    "complete_research_intent",
    "start_discovery",
    "prepare_broad_query_plan",
    "run_saved_query_plan",
    "prepare_early_review",
    "researcher_decision_required",
    "revise_research_intent",
    "prepare_focused_query_plan",
    "continue_triage",
    "prepare_narrowing_review",
    "refine",
    "prepare_final_landscape",
]

AUTO_REFINE_MAX_ROUNDS = 3
FOCUSED_SATURATION_NEW_RECORDS = 5
GRAPH_LOW_GAIN_NEW_RECORDS = 50


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    """Load JSONL defensively so one malformed provider record cannot strand a project."""
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _plan_is_after_decision(
    plan: dict[str, object] | None,
    decision: dict[str, object] | None,
    *,
    phase: str,
) -> bool:
    if not plan or plan.get("phase") != phase or not decision:
        return False
    saved_at = str(plan.get("saved_at") or "")
    decided_at = str(decision.get("timestamp") or "")
    return bool(saved_at and decided_at and saved_at > decided_at)


def _latest_timestamp(rows: list[dict[str, object]]) -> str:
    values = [str(row.get("timestamp") or "") for row in rows if row.get("timestamp")]
    return max(values) if values else ""


def _has_triage_after(
    triage_runs: list[dict[str, object]],
    *,
    campaign_id: str,
    timestamp: str,
) -> bool:
    if not timestamp:
        return False
    return any(
        str(run.get("campaign_id") or "") == campaign_id
        and str(run.get("timestamp") or "") > timestamp
        for run in triage_runs
    )


def _narrowing_action(
    *,
    campaign_status: str,
    papers: list[dict[str, object]],
    triaged: list[dict[str, object]],
    untriaged: int,
    reason: str,
) -> dict[str, object]:
    return {
        "next_action": "prepare_narrowing_review",
        "human_checkpoint_required": False,
        "reason": reason,
        "campaign_status": campaign_status,
        "indexed_records": len(papers),
        "triaged_records": len(triaged),
        "untriaged_records": untriaged,
        "commands": ["lrc discover prepare-review . --after-triage --json"],
    }


def _discovery_metrics(
    campaign: dict[str, object],
    papers: list[dict[str, object]],
) -> dict[str, object]:
    campaign_id = str(campaign.get("campaign_id") or "")
    triaged = [
        row
        for row in papers
        if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")
    ]
    iterations = [row for row in campaign.get("iterations") or [] if isinstance(row, dict)]
    focused = [row for row in iterations if row.get("phase") == "focused"]
    graph = [row for row in iterations if row.get("phase") == "citation_expansion"]
    latest_focused_new = int(focused[-1].get("new_records") or 0) if focused else None
    latest_graph_new = int(graph[-1].get("new_records") or 0) if graph else None
    previous_graph_new = int(graph[-2].get("new_records") or 0) if len(graph) >= 2 else None
    core_candidates = sum(
        str(row.get("triage_label") or "") == "relevant"
        and str(row.get("triage_priority") or "") == "core_candidate"
        for row in triaged
    )
    relevant_records = sum(str(row.get("triage_label") or "") == "relevant" for row in triaged)
    focused_saturated = latest_focused_new is not None and latest_focused_new <= FOCUSED_SATURATION_NEW_RECORDS
    graph_low_gain = latest_graph_new is not None and latest_graph_new <= GRAPH_LOW_GAIN_NEW_RECORDS
    graph_gain_drop = (
        latest_graph_new is not None
        and previous_graph_new is not None
        and previous_graph_new > 0
        and latest_graph_new < previous_graph_new * 0.5
    )
    graph_saturated = bool(graph) and (
        len(graph) >= AUTO_REFINE_MAX_ROUNDS or graph_low_gain or graph_gain_drop
    )
    selected_focuses = [str(v) for v in campaign.get("selected_focuses") or []]
    auto_refine = bool(
        selected_focuses
        and focused_saturated
        and core_candidates >= 5
        and len(graph) < AUTO_REFINE_MAX_ROUNDS
        and not graph_saturated
    )
    discovery_saturated = bool(selected_focuses and focused_saturated and graph_saturated)
    return {
        "triaged": triaged,
        "untriaged": max(0, len(papers) - len(triaged)),
        "iterations": iterations,
        "focused_iterations": focused,
        "citation_expansions": graph,
        "latest_focused_new_records": latest_focused_new,
        "latest_graph_new_records": latest_graph_new,
        "previous_graph_new_records": previous_graph_new,
        "core_candidates": core_candidates,
        "relevant_records": relevant_records,
        "selected_focuses": selected_focuses,
        "focused_saturated": focused_saturated,
        "graph_saturated": graph_saturated,
        "auto_refine": auto_refine,
        "discovery_saturated": discovery_saturated,
    }


def discovery_next_step(root: Path) -> dict[str, object]:
    """Return the deterministic structural next step for the narrative-review discovery funnel.

    Researcher decisions remain human: scope, focus, changing scope, and declaring discovery
    sufficient. Technical narrowing does not require a click after every batch. Once a focus is
    selected and focused retrieval is saturated, up to three bounded priority-triage + citation-
    chaining refinement rounds may run automatically, with early stopping when graph gain drops.
    """
    root = root.expanduser().resolve()
    project_file = root / PROJECT_DIR / "project.yaml"
    state_file = root / PROJECT_DIR / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")

    state = json.loads(state_file.read_text(encoding="utf-8"))
    intent_status = str(state["stages"]["research_intent"]["status"])
    if intent_status != "accepted":
        return {
            "next_action": "complete_research_intent",
            "human_checkpoint_required": True,
            "reason": "Research Intent is not yet accepted.",
            "campaign_status": "not_started",
            "commands": ["lrc intent show . --json"],
        }

    campaign_file = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    campaign = _read_json(campaign_file)
    if campaign is None:
        return {
            "next_action": "start_discovery",
            "human_checkpoint_required": False,
            "reason": "Research Intent is accepted but no discovery campaign exists.",
            "campaign_status": "not_started",
            "commands": ["lrc discover start .", "lrc discover prepare-plan . --phase broad --json"],
        }

    campaign_status = str(campaign.get("status") or "collecting")
    papers = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    metrics = _discovery_metrics(campaign, papers)
    triaged = metrics["triaged"]
    assert isinstance(triaged, list)
    untriaged = int(metrics["untriaged"])

    if campaign_status == "awaiting_researcher":
        if metrics["auto_refine"]:
            return {
                "next_action": "refine",
                "human_checkpoint_required": False,
                "reason": "Focused retrieval is saturated, but bounded citation chaining has not yet reached the beta saturation budget. Continue technical narrowing automatically before asking the researcher to decide again.",
                "campaign_status": campaign_status,
                "indexed_records": len(papers),
                "triaged_records": len(triaged),
                "untriaged_records": untriaged,
                "relevant_records": metrics["relevant_records"],
                "core_candidates": metrics["core_candidates"],
                "citation_expansion_rounds": len(metrics["citation_expansions"]),
                "latest_graph_new_records": metrics["latest_graph_new_records"],
                "selected_focuses": metrics["selected_focuses"],
                "action_bundle": [
                    "priority_triage_existing_corpus",
                    "citation_chain_from_core_seeds",
                    "priority_triage_graph_additions",
                    "rebuild_narrowing_review",
                ],
                "commands": [
                    "lrc discover prepare-triage . --batch-size 100 --json",
                    "lrc discover expand . --relation both --max-per-seed-provider 100 --json",
                    "lrc discover prepare-triage . --batch-size 100 --json",
                    "lrc discover prepare-review . --after-triage --json",
                ],
            }
        reason = (
            "Technical narrowing has reached the configured saturation/budget for a narrative review. The researcher should now decide whether the current literature is sufficient, whether the scholarly focus should change, or whether broader discovery is needed."
            if metrics["discovery_saturated"]
            else "A discovery review is saved and a genuine researcher decision is required: choose or revise the scholarly focus, broaden/change scope, explicitly filter more, or finish discovery."
        )
        return {
            "next_action": "researcher_decision_required",
            "human_checkpoint_required": True,
            "reason": reason,
            "campaign_status": campaign_status,
            "indexed_records": len(papers),
            "triaged_records": len(triaged),
            "untriaged_records": untriaged,
            "relevant_records": metrics["relevant_records"],
            "core_candidates": metrics["core_candidates"],
            "citation_expansion_rounds": len(metrics["citation_expansions"]),
            "latest_focused_new_records": metrics["latest_focused_new_records"],
            "latest_graph_new_records": metrics["latest_graph_new_records"],
            "discovery_saturated": metrics["discovery_saturated"],
            "recommended_option": "finish" if metrics["discovery_saturated"] else "researcher_choice",
            "selected_focuses": metrics["selected_focuses"],
            "commands": [
                "lrc discover readiness . --json",
                "lrc discover filter .",
                "lrc discover decide . --action <continue|focus|change_scope|finish>",
            ],
        }
    if campaign_status == "scope_change_requested":
        return {
            "next_action": "revise_research_intent",
            "human_checkpoint_required": True,
            "reason": "The researcher requested a discovery scope change.",
            "campaign_status": campaign_status,
            "commands": ["lrc intent show . --json", "lrc intent set . <revised-fields>"],
        }
    if campaign_status == "complete":
        return {
            "next_action": "prepare_final_landscape",
            "human_checkpoint_required": False,
            "reason": "The researcher explicitly finished discovery; the retained corpus can now be prepared for the current Research Landscape.",
            "campaign_status": campaign_status,
            "commands": ["lrc discover prepare-landscape . --json"],
        }

    iterations = metrics["iterations"]
    assert isinstance(iterations, list)
    current_plan = _read_json(root / PROJECT_DIR / "data" / "discovery_query_plan.json")
    checkpoints = [row for row in campaign.get("review_checkpoints") or [] if isinstance(row, dict)]

    if not iterations:
        if current_plan and current_plan.get("phase") == "broad":
            return {
                "next_action": "run_saved_query_plan",
                "human_checkpoint_required": False,
                "reason": "A broad Query Plan is saved but no discovery iteration has run yet.",
                "campaign_status": campaign_status,
                "commands": ["lrc discover run-plan ."],
            }
        return {
            "next_action": "prepare_broad_query_plan",
            "human_checkpoint_required": False,
            "reason": "The discovery campaign has started but no broad Query Plan has been executed.",
            "campaign_status": campaign_status,
            "commands": ["lrc discover prepare-plan . --phase broad --json"],
        }

    latest_checkpoint = checkpoints[-1] if checkpoints else None
    latest_decision = latest_checkpoint.get("decision") if isinstance(latest_checkpoint, dict) else None
    decision_dict = latest_decision if isinstance(latest_decision, dict) else None
    campaign_revision = int(campaign.get("revision") or 0)
    reviewed_revision = int(latest_checkpoint.get("iteration_revision") or 0) if latest_checkpoint else -1
    new_retrieval_since_review = campaign_revision > reviewed_revision

    if campaign_status == "collecting" and decision_dict:
        if decision_dict.get("action") == "continue" and not new_retrieval_since_review:
            if _plan_is_after_decision(current_plan, decision_dict, phase="broad"):
                return {
                    "next_action": "run_saved_query_plan",
                    "human_checkpoint_required": False,
                    "reason": "The researcher chose to continue and a new broad Query Plan has already been saved.",
                    "campaign_status": campaign_status,
                    "commands": ["lrc discover run-plan ."],
                }
            return {
                "next_action": "prepare_broad_query_plan",
                "human_checkpoint_required": False,
                "reason": "The researcher chose to continue broad discovery; prepare complementary query families before the next retrieval iteration.",
                "campaign_status": campaign_status,
                "commands": ["lrc discover prepare-plan . --phase broad --json"],
            }

    if campaign_status == "focused" and decision_dict:
        if decision_dict.get("action") == "focus" and not new_retrieval_since_review:
            if _plan_is_after_decision(current_plan, decision_dict, phase="focused"):
                return {
                    "next_action": "run_saved_query_plan",
                    "human_checkpoint_required": False,
                    "reason": "The researcher selected a focus and a new focused Query Plan has already been saved.",
                    "campaign_status": campaign_status,
                    "selected_focuses": campaign.get("selected_focuses") or [],
                    "commands": ["lrc discover run-plan ."],
                }
            return {
                "next_action": "prepare_focused_query_plan",
                "human_checkpoint_required": False,
                "reason": "The researcher selected a focus and no focused retrieval has run since that checkpoint.",
                "campaign_status": campaign_status,
                "selected_focuses": campaign.get("selected_focuses") or [],
                "commands": ["lrc discover prepare-plan . --phase focused --json"],
            }

    campaign_id = str(campaign.get("campaign_id") or "")
    triage_runs = [
        row
        for row in _load_jsonl(root / PROJECT_DIR / "data" / "triage_runs.jsonl")
        if str(row.get("campaign_id") or "") == campaign_id
    ]
    latest_iteration_at = _latest_timestamp(iterations)
    triage_after_latest_retrieval = _has_triage_after(
        triage_runs,
        campaign_id=campaign_id,
        timestamp=latest_iteration_at,
    )

    if decision_dict and decision_dict.get("action") == "filter":
        decision_at = str(decision_dict.get("timestamp") or "")
        triage_after_filter_choice = _has_triage_after(
            triage_runs,
            campaign_id=campaign_id,
            timestamp=decision_at,
        )
        if untriaged > 0 and not triage_after_filter_choice:
            return {
                "next_action": "continue_triage",
                "human_checkpoint_required": False,
                "reason": "The researcher explicitly chose to filter more of the existing corpus without additional retrieval.",
                "campaign_status": campaign_status,
                "indexed_records": len(papers),
                "triaged_records": len(triaged),
                "untriaged_records": untriaged,
                "commands": ["lrc discover prepare-triage . --batch-size 100 --json"],
            }
        if triaged:
            return _narrowing_action(
                campaign_status=campaign_status,
                papers=papers,
                triaged=triaged,
                untriaged=untriaged,
                reason="A researcher-requested additional triage batch is complete; return to a narrowing review instead of exhaustively screening the corpus.",
            )

    if not checkpoints:
        return {
            "next_action": "prepare_early_review",
            "human_checkpoint_required": False,
            "reason": "Broad retrieval exists but the researcher has not yet seen an early provisional map.",
            "campaign_status": campaign_status,
            "indexed_records": len(papers),
            "commands": ["lrc discover prepare-review . --json"],
        }

    if new_retrieval_since_review and untriaged > 0:
        if triage_after_latest_retrieval and triaged:
            return _narrowing_action(
                campaign_status=campaign_status,
                papers=papers,
                triaged=triaged,
                untriaged=untriaged,
                reason="A bounded priority triage batch has been completed for the newly retrieved literature. Return to the narrowing map; exhaustive triage is not required for a narrative review.",
            )
        return {
            "next_action": "continue_triage",
            "human_checkpoint_required": False,
            "reason": "New literature has been retrieved since the last review; triage one bounded priority batch before rebuilding the narrowing map.",
            "campaign_status": campaign_status,
            "indexed_records": len(papers),
            "triaged_records": len(triaged),
            "untriaged_records": untriaged,
            "commands": ["lrc discover prepare-triage . --batch-size 100 --json"],
        }

    if triaged:
        return _narrowing_action(
            campaign_status=campaign_status,
            papers=papers,
            triaged=triaged,
            untriaged=untriaged,
            reason="The current corpus has progressive triage information and is ready for an updated narrowing map.",
        )

    return {
        "next_action": "continue_triage",
        "human_checkpoint_required": False,
        "reason": "A researcher checkpoint exists, but no relevance triage has been saved for the current campaign.",
        "campaign_status": campaign_status,
        "indexed_records": len(papers),
        "triaged_records": 0,
        "untriaged_records": len(papers),
        "commands": ["lrc discover prepare-triage . --batch-size 100 --json"],
    }
