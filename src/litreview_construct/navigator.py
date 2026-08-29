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
    "prepare_final_landscape",
]


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def discovery_next_step(root: Path) -> dict[str, object]:
    """Return the deterministic structural next step for the discovery funnel.

    This navigator does not make scholarly choices. In particular, it never chooses a research
    focus or decides that discovery is sufficient; those remain researcher decisions.

    Narrative-review triage is progressive rather than exhaustive. After a bounded triage batch
    has been completed for newly retrieved literature, the workflow returns to a researcher-facing
    narrowing review even when many corpus records remain untriaged. The researcher may then
    explicitly request more filtering without another search.
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
    if campaign_status == "awaiting_researcher":
        return {
            "next_action": "researcher_decision_required",
            "human_checkpoint_required": True,
            "reason": "A discovery review is saved and the researcher must choose whether to filter more, broaden/search, focus, change scope, or finish.",
            "campaign_status": campaign_status,
            "commands": [
                "lrc discover readiness . --json",
                "lrc discover filter .  # continue filtering current corpus without retrieval",
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

    iterations = [row for row in campaign.get("iterations") or [] if isinstance(row, dict)]
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

    papers = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    campaign_id = str(campaign.get("campaign_id") or "")
    triaged = [
        row
        for row in papers
        if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")
    ]
    untriaged = max(0, len(papers) - len(triaged))
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
                reason="A bounded priority triage batch has been completed for the newly retrieved literature. Return to the researcher with an updated narrowing map; exhaustive triage is not required for a narrative review.",
            )
        return {
            "next_action": "continue_triage",
            "human_checkpoint_required": False,
            "reason": "New literature has been retrieved since the last researcher checkpoint; triage one bounded priority batch before rebuilding the narrowing map.",
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
            reason="The current corpus has progressive triage information and is ready for an updated researcher-facing narrowing map.",
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
