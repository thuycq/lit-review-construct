from __future__ import annotations

import json
from pathlib import Path

import yaml

from .navigator import discovery_next_step
from .project import PROJECT_DIR


def _load(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    root = root.expanduser().resolve()
    project_file = root / PROJECT_DIR / "project.yaml"
    state_file = root / PROJECT_DIR / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return (
        root,
        yaml.safe_load(project_file.read_text(encoding="utf-8")),
        json.loads(state_file.read_text(encoding="utf-8")),
    )


def _jsonl(root: Path, relative: str) -> list[dict[str, object]]:
    path = root / PROJECT_DIR / relative
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stage(state: dict[str, object], name: str) -> str:
    stages = state.get("stages") or {}
    assert isinstance(stages, dict)
    row = stages.get(name) or {}
    assert isinstance(row, dict)
    return str(row.get("status") or "not_started")


def project_next_step(root: Path) -> dict[str, object]:
    """Return the next structural step for the complete Lit Review Construct workflow.

    This function routes workflow state only. It never decides scholarly relevance, research focus,
    discovery sufficiency, research direction, or Blueprint acceptance on the researcher's behalf.
    """
    root, project, state = _load(root)

    intent = _stage(state, "research_intent")
    if intent != "accepted":
        return {
            "next_action": "complete_research_intent",
            "stage": "research_intent",
            "skill": "litreview-start",
            "human_checkpoint_required": True,
            "reason": "The Research Intent must be completed and explicitly accepted before discovery proceeds.",
            "commands": ["lrc intent show . --json"],
        }

    seed = _stage(state, "seed_literature")
    seed_decision = root / PROJECT_DIR / "data" / "seed_decision.json"
    if seed != "accepted" or not seed_decision.exists():
        user_seeds = [row for row in _jsonl(root, "data/papers.jsonl") if row.get("source_origin") == "user_seed"]
        if user_seeds:
            return {
                "next_action": "review_seed_inventory",
                "stage": "seed_literature",
                "skill": "litreview-seeds",
                "human_checkpoint_required": True,
                "reason": "Researcher-provided papers are indexed but the seed inventory has not yet been acknowledged. Acknowledgement does not imply relevance.",
                "indexed_seed_records": len(user_seeds),
                "commands": ["lrc seed accept ."],
            }
        return {
            "next_action": "ask_seed_literature",
            "stage": "seed_literature",
            "skill": "litreview-seeds",
            "human_checkpoint_required": True,
            "reason": "The workflow must record whether the researcher already has related papers before broad discovery.",
            "researcher_prompt": "Do you already have papers related to this research?",
            "commands": [
                "lrc seed scan .  # if papers were added to papers/",
                "lrc seed scan . --source <external-folder>  # if using an external folder",
                "lrc seed skip .  # if no seed papers are available",
            ],
        }

    campaign_file = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not campaign_file.exists():
        discovery = discovery_next_step(root)
        return {
            **discovery,
            "stage": "literature_discovery",
            "skill": "litreview-discover",
        }

    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    if campaign.get("status") != "complete":
        discovery = discovery_next_step(root)
        return {
            **discovery,
            "stage": "literature_discovery",
            "skill": "litreview-discover",
        }

    landscape_status = _stage(state, "literature_discovery")
    landscape_file = root / PROJECT_DIR / "data" / "landscape.json"
    if not landscape_file.exists() or landscape_status in {"needs_refresh", "in_progress"}:
        return {
            "next_action": "construct_current_research_landscape",
            "stage": "literature_discovery",
            "skill": "litreview-discover",
            "human_checkpoint_required": False,
            "reason": "Discovery is researcher-finished; the current Research Landscape must now be rebuilt from retained triaged literature.",
            "commands": ["lrc discover prepare-landscape . --json"],
        }

    evidence_status = _stage(state, "evidence_mapping")
    evidence_file = root / PROJECT_DIR / "data" / "evidence_map.json"
    fulltext_resolution = root / PROJECT_DIR / "data" / "fulltext_resolution.json"
    # For new projects, attempt lawful OA acquisition before the first Evidence Map. Existing
    # evidence artifacts are not invalidated automatically merely because this capability was added.
    if not evidence_file.exists() and not fulltext_resolution.exists():
        return {
            "next_action": "resolve_priority_full_text",
            "stage": "evidence_mapping",
            "skill": "litreview-fulltext",
            "human_checkpoint_required": False,
            "reason": "A current Research Landscape exists. Resolve and acquire lawful OA full text for priority papers before constructing the first Evidence Map.",
            "commands": ["lrc fulltext acquire . --max-papers 30 --json"],
        }
    if not evidence_file.exists() or evidence_status in {"not_started", "in_progress", "needs_refresh", "blocked"}:
        return {
            "next_action": "construct_evidence_map",
            "stage": "evidence_mapping",
            "skill": "litreview-map",
            "human_checkpoint_required": False,
            "reason": "A current Research Landscape exists; the next step is source-disciplined Evidence Mapping before gap/direction reasoning.",
            "commands": ["lrc evidence prepare . --json"],
        }

    direction_status = _stage(state, "research_direction")
    selected_direction = root / PROJECT_DIR / "data" / "selected_direction.json"
    if direction_status == "ready_for_review":
        return {
            "next_action": "researcher_direction_decision",
            "stage": "research_direction",
            "skill": "litreview-direction",
            "human_checkpoint_required": True,
            "reason": "Candidate Research Directions are ready. The researcher must select, modify, combine, or reject them.",
            "commands": ["lrc direction show ."],
        }
    if direction_status != "accepted" or not selected_direction.exists():
        return {
            "next_action": "propose_research_directions",
            "stage": "research_direction",
            "skill": "litreview-direction",
            "human_checkpoint_required": False,
            "reason": "Landscape and Evidence Map are available; AI may now propose provisional directions, but must stop before choosing one.",
            "commands": ["lrc direction prepare . --json"],
        }

    blueprint_status = _stage(state, "literature_review_blueprint")
    blueprint_file = root / PROJECT_DIR / "data" / "blueprint.json"
    if blueprint_status == "ready_for_review":
        return {
            "next_action": "researcher_blueprint_review",
            "stage": "literature_review_blueprint",
            "skill": "litreview-blueprint",
            "human_checkpoint_required": True,
            "reason": "The Literature Review Blueprint is ready for researcher review. It must not be silently accepted or expanded into a final review.",
            "commands": ["lrc blueprint show .", "lrc blueprint accept .  # only after explicit researcher approval"],
        }
    if blueprint_status != "accepted" or not blueprint_file.exists():
        return {
            "next_action": "construct_literature_review_blueprint",
            "stage": "literature_review_blueprint",
            "skill": "litreview-blueprint",
            "human_checkpoint_required": False,
            "reason": "A researcher-selected direction exists; construct the evidence-linked review architecture without writing the final review.",
            "commands": ["lrc blueprint prepare . --json"],
        }

    working_draft = root / PROJECT_DIR / "data" / "working_draft.json"
    if not working_draft.exists():
        return {
            "next_action": "construct_working_draft",
            "stage": "researcher_handoff",
            "skill": "litreview-draft",
            "human_checkpoint_required": False,
            "reason": "The Blueprint is accepted. Construct an evidence-linked researcher working draft before final handoff so the researcher has prose to verify, rewrite, and develop.",
            "commands": ["lrc draft prepare . --json"],
        }

    return {
        "next_action": "researcher_handoff",
        "stage": "researcher_handoff",
        "skill": "litreview-ai-use",
        "human_checkpoint_required": True,
        "reason": "The accepted Blueprint and researcher working draft are available. The researcher now verifies sources, rewrites and approves final prose; the toolkit can export Word and optionally generate an activity-grounded AI-use statement.",
        "researcher_responsibility": "Verify sources and citations, rewrite/approve the working draft, and author the final literature-review text.",
        "optional_commands": [
            "lrc draft show .",
            "lrc export docx . --artifact working-draft",
            "lrc export docx . --artifact handoff",
            "lrc ai-use summary . --json",
            "lrc ai-use generate . --style standard",
        ],
        "prohibited_next_step": "present_unverified_ai_draft_as_submission_ready_final_review",
    }
