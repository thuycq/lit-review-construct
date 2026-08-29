from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field, model_validator

from .project import PROJECT_DIR, _atomic_write_text, _write_json

Confidence = Literal["low", "medium", "high"]
Difficulty = Literal["low", "medium", "high"]
DecisionAction = Literal["select", "modify", "combine", "reject_all"]


class DirectionCandidateSubmission(BaseModel):
    title: str = Field(min_length=1)
    research_idea: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    supporting_paper_ids: list[str] = []
    supporting_evidence_ids: list[str] = []
    what_is_known: list[str] = []
    possible_gap: str = Field(min_length=1)
    novelty: str = Field(min_length=1)
    data_feasibility: str = Field(min_length=1)
    methodological_feasibility: str = Field(min_length=1)
    difficulty: Difficulty = "medium"
    risks: list[str] = []
    limitations: list[str] = []
    verification_needs: list[str] = []
    confidence: Confidence = "medium"


class ResearchDirectionSubmission(BaseModel):
    summary: str = Field(min_length=1)
    directions: list[DirectionCandidateSubmission] = Field(min_length=2, max_length=5)
    cross_direction_notes: list[str] = []
    limitations: list[str] = []


class DirectionDecisionSubmission(BaseModel):
    action: DecisionAction
    direction_ids: list[str] = []
    final_direction: DirectionCandidateSubmission | None = None
    researcher_notes: str | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> "DirectionDecisionSubmission":
        if self.action == "select":
            if len(self.direction_ids) != 1:
                raise ValueError("select requires exactly one direction_id.")
            if self.final_direction is not None:
                raise ValueError("select uses the saved candidate directly; final_direction must be omitted.")
        elif self.action == "modify":
            if len(self.direction_ids) != 1 or self.final_direction is None:
                raise ValueError("modify requires one direction_id and a final_direction.")
        elif self.action == "combine":
            if len(self.direction_ids) < 2 or self.final_direction is None:
                raise ValueError("combine requires at least two direction_ids and a final_direction.")
        elif self.action == "reject_all":
            if self.direction_ids or self.final_direction is not None:
                raise ValueError("reject_all must not include direction_ids or final_direction.")
        return self


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
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _bounded_evidence(rows: list[dict[str, object]], max_evidence: int) -> list[dict[str, object]]:
    priority = {
        "causal_finding": 0,
        "association": 1,
        "prediction": 1,
        "heterogeneous_finding": 2,
        "null_finding": 2,
        "gap_claim": 3,
        "limitation": 3,
        "theory": 4,
        "method": 5,
        "data": 6,
    }
    ordered = sorted(
        rows,
        key=lambda row: (
            priority.get(str(row.get("evidence_type") or ""), 9),
            0 if row.get("source_basis") == "full_text" else 1,
            0 if row.get("provenance") == "source_reported" else 1,
            str(row.get("paper_id") or ""),
        ),
    )
    return ordered[:max_evidence]


def prepare_direction_packet(root: Path, *, max_evidence: int = 80) -> dict[str, object]:
    """Create a bounded packet for candidate Research Direction reasoning."""
    if not 10 <= max_evidence <= 200:
        raise ValueError("Direction packet max_evidence must be between 10 and 200.")

    root, project, state = _load_project(root)
    state_root = root / PROJECT_DIR
    landscape_file = state_root / "data" / "landscape.json"
    evidence_map_file = state_root / "data" / "evidence_map.json"
    evidence_file = state_root / "data" / "evidence.jsonl"
    if not landscape_file.exists() or not evidence_map_file.exists() or not evidence_file.exists():
        raise ValueError("Saved Research Landscape and Evidence Map are required before Research Direction.")
    if state["stages"]["evidence_mapping"]["status"] not in {"ready_for_review", "accepted"}:
        raise ValueError("Evidence Map must be ready for review before Research Direction.")

    landscape = json.loads(landscape_file.read_text(encoding="utf-8"))
    evidence_map = json.loads(evidence_map_file.read_text(encoding="utf-8"))
    evidence_rows = _load_jsonl(evidence_file)
    selected_evidence = _bounded_evidence(evidence_rows, max_evidence)

    packet_id = str(uuid4())
    packet = {
        "packet_type": "research_direction",
        "packet_schema_version": 1,
        "packet_id": packet_id,
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "research_landscape": {
            "summary": landscape.get("summary"),
            "anchor_paper_ids": landscape.get("anchor_paper_ids") or [],
            "streams": landscape.get("streams") or [],
            "major_debates": landscape.get("major_debates") or [],
            "unresolved_questions": landscape.get("unresolved_questions") or [],
            "limitations": landscape.get("limitations") or [],
        },
        "evidence_map": {
            "summary": evidence_map.get("summary"),
            "cross_paper_patterns": evidence_map.get("cross_paper_patterns") or [],
            "contradictions": evidence_map.get("contradictions") or [],
            "evidence_gaps": evidence_map.get("evidence_gaps") or [],
            "papers_requiring_full_text": evidence_map.get("papers_requiring_full_text") or [],
            "limitations": evidence_map.get("limitations") or [],
        },
        "evidence_items": [
            {
                "evidence_id": row.get("evidence_id"),
                "paper_id": row.get("paper_id"),
                "evidence_type": row.get("evidence_type"),
                "claim": row.get("claim"),
                "provenance": row.get("provenance"),
                "source_basis": row.get("source_basis"),
                "certainty": row.get("certainty"),
                "variables": row.get("variables") or [],
                "theories": row.get("theories") or [],
                "methods": row.get("methods") or [],
                "data_context": row.get("data_context") or [],
            }
            for row in selected_evidence
        ],
        "analysis_contract": {
            "purpose": "Propose a small set of defensible research directions for researcher judgment.",
            "required": [
                "propose 2 to 5 genuinely distinct candidate directions",
                "trace each direction to paper_ids and evidence_ids where available",
                "state what is known separately from the possible gap",
                "treat gap and novelty as provisional until fuller verification supports them",
                "assess data feasibility and methodological feasibility separately",
                "state difficulty, risks, limitations, and verification needs",
                "make clear where abstract-only evidence weakens confidence",
            ],
            "prohibited": [
                "claiming a definitive research gap from incomplete evidence",
                "inventing datasets or methods as if availability were verified",
                "automatically choosing a direction for the researcher",
                "treating AI preference as researcher judgment",
                "writing a complete final literature review",
            ],
            "human_checkpoint": "After candidates are saved, stop and ask the researcher to select, modify, combine, reject, or replace them.",
        },
        "expected_output_schema": {
            "summary": "string",
            "directions": [
                {
                    "title": "string",
                    "research_idea": "string",
                    "rationale": "string",
                    "supporting_paper_ids": ["paper_id"],
                    "supporting_evidence_ids": ["evidence_id"],
                    "what_is_known": ["string"],
                    "possible_gap": "string",
                    "novelty": "string",
                    "data_feasibility": "string",
                    "methodological_feasibility": "string",
                    "difficulty": "low|medium|high",
                    "risks": ["string"],
                    "limitations": ["string"],
                    "verification_needs": ["string"],
                    "confidence": "low|medium|high",
                }
            ],
            "cross_direction_notes": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = state_root / "packets" / "direction.json"
    _write_json(packet_file, packet)
    return {
        "packet_id": packet_id,
        "evidence_items": len(selected_evidence),
        "full_text_verification_flags": len(evidence_map.get("papers_requiring_full_text") or []),
        "packet_file": str(packet_file),
    }


def _validate_candidate_references(
    submission: ResearchDirectionSubmission,
    paper_ids: set[str],
    evidence_ids: set[str],
) -> None:
    unknown_papers: set[str] = set()
    unknown_evidence: set[str] = set()
    for direction in submission.directions:
        unknown_papers.update(set(direction.supporting_paper_ids) - paper_ids)
        unknown_evidence.update(set(direction.supporting_evidence_ids) - evidence_ids)
    if unknown_papers:
        raise ValueError("Research Direction references unknown paper IDs: " + ", ".join(sorted(unknown_papers)))
    if unknown_evidence:
        raise ValueError("Research Direction references unknown evidence IDs: " + ", ".join(sorted(unknown_evidence)))


def _render_candidates(
    summary: str,
    directions: list[dict[str, object]],
    cross_direction_notes: list[str],
    limitations: list[str],
    decision: dict[str, object] | None = None,
) -> str:
    lines = ["# Research Direction", "", summary, "", "## Candidate directions", ""]
    for number, item in enumerate(directions, start=1):
        lines.extend(
            [
                f"### {number}. {item['title']}",
                "",
                str(item["research_idea"]),
                "",
                f"**Direction ID:** `{item['direction_id']}`",
                f"**Status:** `{item.get('status', 'proposed')}`",
                f"**Confidence:** `{item.get('confidence', 'medium')}`",
                f"**Difficulty:** `{item.get('difficulty', 'medium')}`",
                "",
                "**Rationale**",
                str(item["rationale"]),
                "",
                "**Possible gap — provisional**",
                str(item["possible_gap"]),
                "",
                "**Potential novelty — provisional**",
                str(item["novelty"]),
                "",
                "**Data feasibility**",
                str(item["data_feasibility"]),
                "",
                "**Methodological feasibility**",
                str(item["methodological_feasibility"]),
                "",
            ]
        )
        for label, key in [
            ("What is currently supported", "what_is_known"),
            ("Risks", "risks"),
            ("Limitations", "limitations"),
            ("Verification needs", "verification_needs"),
        ]:
            values = item.get(key) or []
            if values:
                lines.extend([f"**{label}**", *[f"- {value}" for value in values], ""])
        papers = item.get("supporting_paper_ids") or []
        evidence = item.get("supporting_evidence_ids") or []
        if papers:
            lines.extend(["**Supporting papers**", *[f"- `{value}`" for value in papers], ""])
        if evidence:
            lines.extend(["**Supporting evidence records**", *[f"- `{value}`" for value in evidence], ""])

    if cross_direction_notes:
        lines.extend(["## Cross-direction notes", "", *[f"- {x}" for x in cross_direction_notes], ""])
    if limitations:
        lines.extend(["## Current limitations", "", *[f"- {x}" for x in limitations], ""])
    if decision:
        lines.extend(["## Researcher decision", ""])
        lines.append(f"Action: **{decision.get('action')}**")
        if decision.get("researcher_notes"):
            lines.append(f"Researcher notes: {decision['researcher_notes']}")
        if decision.get("selected_direction"):
            selected = decision["selected_direction"]
            lines.extend(
                [
                    "",
                    f"Selected/refined direction: **{selected.get('title')}**",
                    "",
                    str(selected.get("research_idea") or ""),
                ]
            )
        lines.append("")

    lines.extend(
        [
            "> Candidate gaps and novelty claims are provisional research-design propositions, not verified facts. The researcher must make the direction decision, and fuller source verification may change the assessment.",
            "",
        ]
    )
    return "\n".join(lines)


def save_direction_candidates(root: Path, input_file: Path) -> dict[str, object]:
    """Persist AI-assisted candidate directions, but do not choose one."""
    root, _, state = _load_project(root)
    state_root = root / PROJECT_DIR
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Research Direction input file not found: {input_path}")

    submission = ResearchDirectionSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    papers = _load_jsonl(state_root / "data" / "papers.jsonl")
    evidence = _load_jsonl(state_root / "data" / "evidence.jsonl")
    paper_ids = {str(row.get("paper_id")) for row in papers if row.get("paper_id")}
    evidence_ids = {str(row.get("evidence_id")) for row in evidence if row.get("evidence_id")}
    _validate_candidate_references(submission, paper_ids, evidence_ids)

    saved_at = _now()
    revision = int(state["stages"]["research_direction"].get("revision") or 0) + 1
    rows: list[dict[str, object]] = []
    for candidate in submission.directions:
        row = candidate.model_dump()
        row.update(
            {
                "direction_id": str(uuid4()),
                "status": "proposed",
                "provenance": "ai_synthesis",
                "created_at": saved_at,
            }
        )
        rows.append(row)

    _atomic_write_text(
        state_root / "data" / "directions.jsonl",
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
    )
    meta = {
        "schema_version": 1,
        "revision": revision,
        "saved_at": saved_at,
        "summary": submission.summary,
        "cross_direction_notes": submission.cross_direction_notes,
        "limitations": submission.limitations,
        "human_decision_required": True,
    }
    _write_json(state_root / "data" / "direction_set.json", meta)

    output = root / "outputs" / "05_research_direction.md"
    _atomic_write_text(
        output,
        _render_candidates(
            submission.summary,
            rows,
            submission.cross_direction_notes,
            submission.limitations,
        ),
    )

    state["stages"]["research_direction"]["status"] = "ready_for_review"
    state["stages"]["research_direction"]["revision"] = revision
    state["current_stage"] = "research_direction"
    for downstream in ["literature_review_blueprint", "researcher_handoff"]:
        if state["stages"][downstream]["status"] != "not_started":
            state["stages"][downstream]["status"] = "needs_refresh"
    _write_json(state_root / "state.json", state)

    event = {
        "event_id": str(uuid4()),
        "timestamp": saved_at,
        "category": "direction_suggestion",
        "actor": "ai_assisted",
        "host": None,
        "model": None,
        "inputs": [str(input_path)],
        "outputs": [".litreview/data/directions.jsonl", "outputs/05_research_direction.md"],
        "source_ids": sorted({paper_id for row in rows for paper_id in row["supporting_paper_ids"]}),
        "notes": "Candidate directions are provisional and require an explicit researcher decision.",
    }
    with (state_root / "activity" / "activity.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "status": "ready_for_review",
        "revision": revision,
        "directions": len(rows),
        "human_decision_required": True,
        "output": str(output),
    }


def apply_direction_decision(root: Path, input_file: Path) -> dict[str, object]:
    """Apply the researcher's explicit direction decision."""
    root, _, state = _load_project(root)
    state_root = root / PROJECT_DIR
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Research Direction decision file not found: {input_path}")

    decision = DirectionDecisionSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    rows = _load_jsonl(state_root / "data" / "directions.jsonl")
    if not rows:
        raise ValueError("No candidate Research Directions have been saved.")
    by_id = {str(row["direction_id"]): row for row in rows}
    unknown = sorted(set(decision.direction_ids) - set(by_id))
    if unknown:
        raise ValueError("Direction decision references unknown IDs: " + ", ".join(unknown))

    selected_direction: dict[str, object] | None = None
    now = _now()
    if decision.action == "select":
        selected_direction = dict(by_id[decision.direction_ids[0]])
        selected_direction["status"] = "selected"
        selected_direction["provenance"] = "researcher_judgment"
    elif decision.action in {"modify", "combine"}:
        assert decision.final_direction is not None
        selected_direction = decision.final_direction.model_dump()
        selected_direction.update(
            {
                "direction_id": str(uuid4()),
                "status": "modified" if decision.action == "modify" else "selected",
                "provenance": "researcher_judgment",
                "derived_from_direction_ids": decision.direction_ids,
                "created_at": now,
            }
        )

    selected_ids = set(decision.direction_ids)
    for row in rows:
        direction_id = str(row["direction_id"])
        if decision.action == "reject_all":
            row["status"] = "rejected"
        elif direction_id in selected_ids:
            row["status"] = "selected" if decision.action == "select" else "superseded"
        elif row.get("status") == "proposed":
            row["status"] = "rejected"
    _atomic_write_text(
        state_root / "data" / "directions.jsonl",
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
    )

    decision_record = {
        "schema_version": 1,
        "timestamp": now,
        "action": decision.action,
        "direction_ids": decision.direction_ids,
        "researcher_notes": decision.researcher_notes,
        "selected_direction": selected_direction,
        "provenance": "researcher_judgment",
    }
    _write_json(state_root / "data" / "direction_decision.json", decision_record)
    if selected_direction:
        _write_json(state_root / "data" / "selected_direction.json", selected_direction)
    else:
        selected_path = state_root / "data" / "selected_direction.json"
        if selected_path.exists():
            selected_path.unlink()

    meta_file = state_root / "data" / "direction_set.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
    output = root / "outputs" / "05_research_direction.md"
    _atomic_write_text(
        output,
        _render_candidates(
            str(meta.get("summary") or "Research Direction candidates."),
            rows,
            list(meta.get("cross_direction_notes") or []),
            list(meta.get("limitations") or []),
            decision_record,
        ),
    )

    if decision.action == "reject_all":
        state["stages"]["research_direction"]["status"] = "in_progress"
        status = "in_progress"
    else:
        state["stages"]["research_direction"]["status"] = "accepted"
        status = "accepted"
    state["stages"]["research_direction"]["revision"] = int(
        state["stages"]["research_direction"].get("revision") or 0
    ) + 1
    state["current_stage"] = "research_direction"
    _write_json(state_root / "state.json", state)

    event = {
        "event_id": str(uuid4()),
        "timestamp": now,
        "category": "researcher_direction_selection",
        "actor": "researcher",
        "host": None,
        "model": None,
        "inputs": decision.direction_ids,
        "outputs": [".litreview/data/direction_decision.json", "outputs/05_research_direction.md"],
        "source_ids": [],
        "notes": decision.researcher_notes,
    }
    with (state_root / "activity" / "activity.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "status": status,
        "action": decision.action,
        "selected": selected_direction.get("title") if selected_direction else None,
        "output": str(output),
    }


def show_direction(root: Path) -> dict[str, object]:
    root, _, state = _load_project(root)
    state_root = root / PROJECT_DIR
    rows = _load_jsonl(state_root / "data" / "directions.jsonl")
    if not rows:
        raise FileNotFoundError("No Research Direction candidates have been saved yet.")
    decision_file = state_root / "data" / "direction_decision.json"
    decision = json.loads(decision_file.read_text(encoding="utf-8")) if decision_file.exists() else None
    return {
        "status": state["stages"]["research_direction"]["status"],
        "revision": state["stages"]["research_direction"]["revision"],
        "directions": [
            {
                "direction_id": row.get("direction_id"),
                "title": row.get("title"),
                "status": row.get("status"),
                "confidence": row.get("confidence"),
                "difficulty": row.get("difficulty"),
            }
            for row in rows
        ],
        "decision": decision,
        "human_decision_required": state["stages"]["research_direction"]["status"] != "accepted",
        "output": str(root / "outputs" / "05_research_direction.md"),
    }
