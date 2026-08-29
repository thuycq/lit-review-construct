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
    rows: list[dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _stage(state: dict[str, object], name: str) -> str:
    stages = state.get("stages") or {}
    assert isinstance(stages, dict)
    row = stages.get(name) or {}
    assert isinstance(row, dict)
    return str(row.get("status") or "not_started")


def project_next_step(root: Path) -> dict[str, object]:
    """Return the next structural step for the complete Lit Review Construct workflow.

    State routing never decides scholarly scope, focus, discovery sufficiency, research direction,
    or Blueprint acceptance for the researcher. Technical refinement, OA coverage, QA, and package
    preparation should not manufacture extra human checkpoints.
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
            "researcher_prompt": "Do you already have papers related to this research? If yes, place them in papers/user_uploads/ or point me to the folder.",
            "commands": [
                "lrc seed scan .",
                "lrc seed scan . --source <external-folder>",
                "lrc seed skip .",
            ],
        }

    campaign_file = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not campaign_file.exists():
        discovery = discovery_next_step(root)
        return {**discovery, "stage": "literature_discovery", "skill": "litreview-discover"}

    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    if campaign.get("status") != "complete":
        discovery = discovery_next_step(root)
        return {**discovery, "stage": "literature_discovery", "skill": "litreview-discover"}

    landscape_status = _stage(state, "literature_discovery")
    landscape_file = root / PROJECT_DIR / "data" / "landscape.json"
    if not landscape_file.exists() or landscape_status in {"needs_refresh", "in_progress"}:
        return {
            "next_action": "construct_current_research_landscape",
            "stage": "literature_discovery",
            "skill": "litreview-discover",
            "human_checkpoint_required": False,
            "reason": "Discovery is researcher-finished; rebuild the Research Landscape from retained triaged literature.",
            "commands": ["lrc discover prepare-landscape . --json"],
        }

    evidence_status = _stage(state, "evidence_mapping")
    evidence_file = root / PROJECT_DIR / "data" / "evidence_map.json"
    fulltext_resolution_file = root / PROJECT_DIR / "data" / "fulltext_resolution.json"
    evidence_map = _json(evidence_file)
    fulltext_resolution = _json(fulltext_resolution_file)
    papers_requiring_full_text = evidence_map.get("papers_requiring_full_text") or [] if evidence_map else []
    oa_coverage_complete = bool(fulltext_resolution and fulltext_resolution.get("coverage_complete"))

    # Beta behavior: OA acquisition is a coverage pass across retained/priority working literature,
    # performed in bounded batches. max_papers is a technical batch size, not a product-level cap.
    if not oa_coverage_complete and (not evidence_file.exists() or bool(papers_requiring_full_text)):
        return {
            "next_action": "resolve_priority_full_text",
            "stage": "evidence_mapping",
            "skill": "litreview-fulltext",
            "human_checkpoint_required": False,
            "reason": "Resolve lawful OA availability for the retained/priority working literature in bounded batches before relying on abstract-heavy Evidence Mapping.",
            "commands": ["lrc fulltext acquire . --max-papers 100 --json"],
            "coverage_complete": False,
        }

    # If a later OA pass downloaded new PDFs after an Evidence Map had already been saved, rebuild
    # the map. source_basis=full_text means AI checked against full text, not researcher-verified.
    if evidence_map and fulltext_resolution and int(fulltext_resolution.get("downloaded") or 0) > 0:
        evidence_saved_at = str(evidence_map.get("saved_at") or "")
        resolved_at = str(fulltext_resolution.get("timestamp") or "")
        if resolved_at and (not evidence_saved_at or resolved_at > evidence_saved_at):
            return {
                "next_action": "refresh_evidence_after_fulltext",
                "stage": "evidence_mapping",
                "skill": "litreview-map",
                "human_checkpoint_required": False,
                "reason": "New lawful OA full text was acquired after the current Evidence Map. Re-check affected evidence against the PDFs before downstream claims are treated as current.",
                "commands": ["lrc evidence prepare . --json"],
                "downloaded_full_text": int(fulltext_resolution.get("downloaded") or 0),
            }

    if not evidence_file.exists() or evidence_status in {"not_started", "in_progress", "needs_refresh", "blocked"}:
        return {
            "next_action": "construct_evidence_map",
            "stage": "evidence_mapping",
            "skill": "litreview-map",
            "human_checkpoint_required": False,
            "reason": "A current Research Landscape exists; construct the source-disciplined Evidence Map before gap/direction reasoning.",
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
            "reason": "Landscape and Evidence Map are available; AI may propose provisional directions, but must stop before choosing one.",
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
            "reason": "The quality-checked Literature Review Blueprint is ready for researcher review. It must not be silently accepted or expanded into a final review.",
            "commands": ["lrc blueprint show .", "lrc blueprint accept ."],
        }
    if blueprint_status != "accepted" or not blueprint_file.exists():
        return {
            "next_action": "construct_literature_review_blueprint",
            "stage": "literature_review_blueprint",
            "skill": "litreview-blueprint",
            "human_checkpoint_required": False,
            "reason": "A researcher-selected direction exists; construct and self-check the evidence-linked review architecture without writing the final review.",
            "commands": ["lrc blueprint prepare . --json"],
        }

    working_draft_file = root / PROJECT_DIR / "data" / "working_draft.json"
    if not working_draft_file.exists():
        return {
            "next_action": "construct_working_draft",
            "stage": "researcher_handoff",
            "skill": "litreview-draft",
            "human_checkpoint_required": False,
            "reason": "The Blueprint is accepted. Construct bounded evidence-linked researcher fragments, run draft-safety QA, and preserve verification states.",
            "commands": ["lrc draft prepare . --json"],
        }

    working_draft = _json(working_draft_file) or {}
    researcher_package = _json(root / PROJECT_DIR / "data" / "researcher_package.json")
    package_stale = (
        researcher_package is None
        or str(researcher_package.get("generated_at") or "") < str(working_draft.get("saved_at") or "")
    )
    if package_stale:
        return {
            "next_action": "prepare_researcher_package",
            "stage": "researcher_handoff",
            "skill": "litreview-workflow",
            "human_checkpoint_required": False,
            "reason": "The Working Draft is ready. Materialize the researcher-facing paper library, canonical references, EndNote export, audit manifest, and Word handoff before stopping.",
            "commands": ["lrc package prepare . --json"],
        }

    return {
        "next_action": "researcher_handoff",
        "stage": "researcher_handoff",
        "skill": "litreview-workflow",
        "human_checkpoint_required": True,
        "reason": "The accepted Blueprint, bounded Working Draft, paper library, canonical reference exports, and Word handoff are ready. The researcher now verifies sources and authors the final literature review.",
        "researcher_responsibility": "Verify sources and citations, resolve provisional evidence, rewrite/approve fragments, and author the final literature-review text.",
        "researcher_package": researcher_package,
        "optional_commands": [
            "lrc ai-use summary . --json",
            "lrc ai-use generate . --style standard",
            "lrc package prepare . --json",
        ],
        "prohibited_next_step": "present_unverified_ai_draft_as_submission_ready_final_review",
    }
