from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from .activity import append_activity
from .project import PROJECT_DIR, _atomic_write_text, _write_json


class BlueprintSectionSubmission(BaseModel):
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    key_arguments: list[str] = Field(min_length=1)
    anchor_paper_ids: list[str] = []
    supporting_paper_ids: list[str] = []
    conflicting_paper_ids: list[str] = []
    evidence_ids: list[str] = []
    theoretical_foundations: list[str] = []
    methodological_context: list[str] = []
    hypothesis_or_proposition_links: list[str] = []
    unresolved_questions: list[str] = []
    transition_logic: str | None = None


class BlueprintSubmission(BaseModel):
    title: str = Field(min_length=1)
    organizing_logic: str = Field(min_length=1)
    opening_tasks: list[str] = []
    sections: list[BlueprintSectionSubmission] = Field(min_length=2, max_length=12)
    cross_section_synthesis_tasks: list[str] = []
    closing_tasks: list[str] = []
    verification_priorities: list[str] = []
    limitations: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise ValueError(f"Required project artifact is missing: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _bounded_evidence(rows: list[dict[str, object]], max_evidence: int) -> list[dict[str, object]]:
    priority = {
        "theory": 0,
        "causal_finding": 1,
        "association": 2,
        "prediction": 2,
        "heterogeneous_finding": 3,
        "null_finding": 3,
        "method": 4,
        "data": 5,
        "limitation": 6,
        "gap_claim": 7,
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


def prepare_blueprint_packet(root: Path, *, max_evidence: int = 120) -> dict[str, object]:
    if not 20 <= max_evidence <= 250:
        raise ValueError("Blueprint packet max_evidence must be between 20 and 250.")

    root, project, state = _load(root)
    state_root = root / PROJECT_DIR
    if state["stages"]["research_direction"]["status"] != "accepted":
        raise ValueError("A researcher-accepted Research Direction is required before the Literature Review Blueprint.")

    selected_direction = _load_json(state_root / "data" / "selected_direction.json")
    landscape = _load_json(state_root / "data" / "landscape.json")
    evidence_map = _load_json(state_root / "data" / "evidence_map.json")
    evidence_rows = _load_jsonl(state_root / "data" / "evidence.jsonl")
    papers = _load_jsonl(state_root / "data" / "papers.jsonl")
    selected_evidence = _bounded_evidence(evidence_rows, max_evidence)

    paper_by_id = {str(row.get("paper_id")): row for row in papers if row.get("paper_id")}
    relevant_ids: set[str] = set()
    for stream in landscape.get("streams") or []:
        if isinstance(stream, dict):
            relevant_ids.update(str(value) for value in stream.get("paper_ids") or [])
            relevant_ids.update(str(value) for value in stream.get("anchor_paper_ids") or [])
    relevant_ids.update(str(value) for value in landscape.get("anchor_paper_ids") or [])
    relevant_ids.update(str(value) for value in selected_direction.get("supporting_paper_ids") or [])

    packet_papers = []
    for paper_id in sorted(relevant_ids):
        row = paper_by_id.get(paper_id)
        if not row:
            continue
        packet_papers.append(
            {
                "paper_id": paper_id,
                "title": row.get("title"),
                "authors": row.get("authors") or [],
                "year": row.get("year"),
                "journal": row.get("journal"),
                "triage_label": row.get("triage_label"),
                "triage_priority": row.get("triage_priority"),
                "full_text_available": bool(row.get("file_reference") or row.get("file_hash")),
            }
        )

    packet_id = str(uuid4())
    packet = {
        "packet_type": "literature_review_blueprint",
        "packet_schema_version": 1,
        "packet_id": packet_id,
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "selected_research_direction": selected_direction,
        "research_landscape": {
            "summary": landscape.get("summary"),
            "streams": landscape.get("streams") or [],
            "major_debates": landscape.get("major_debates") or [],
            "methodological_clusters": landscape.get("methodological_clusters") or [],
            "recent_developments": landscape.get("recent_developments") or [],
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
        "paper_index": packet_papers,
        "evidence_items": [
            {
                "evidence_id": row.get("evidence_id"),
                "paper_id": row.get("paper_id"),
                "evidence_type": row.get("evidence_type"),
                "claim": row.get("claim"),
                "provenance": row.get("provenance"),
                "source_basis": row.get("source_basis"),
                "certainty": row.get("certainty"),
                "theories": row.get("theories") or [],
                "variables": row.get("variables") or [],
                "methods": row.get("methods") or [],
                "data_context": row.get("data_context") or [],
            }
            for row in selected_evidence
        ],
        "analysis_contract": {
            "purpose": "Construct an evidence-linked architecture that the researcher can use to write the literature review.",
            "required": [
                "organize the review into a coherent argument sequence rather than a paper-by-paper list",
                "state what each section must establish and why it is necessary for the selected research direction",
                "identify anchor, supporting, and conflicting papers with paper_id traceability",
                "link substantive section claims to evidence_ids where available",
                "identify theoretical foundations, methodological context, contradictions, gaps, and unresolved questions",
                "show how sections connect and how the literature supports hypotheses or propositions when relevant",
                "carry forward verification needs and evidence limitations",
            ],
            "prohibited": [
                "writing continuous submission-ready literature-review prose",
                "producing complete paragraphs for every section that can be assembled into a final review",
                "inventing citations, findings, theories, methods, or gaps",
                "presenting provisional gap or novelty claims as established facts",
                "hiding abstract-only or AI-inferred evidence limitations",
            ],
            "authorship_boundary": "The blueprint may contain concise argument notes and transition logic, but the researcher writes the final literature-review prose.",
        },
        "expected_output_schema": {
            "title": "string",
            "organizing_logic": "string",
            "opening_tasks": ["string"],
            "sections": [
                {
                    "title": "string",
                    "purpose": "what this section must establish and why",
                    "key_arguments": ["concise argument notes, not finished paragraphs"],
                    "anchor_paper_ids": ["paper_id"],
                    "supporting_paper_ids": ["paper_id"],
                    "conflicting_paper_ids": ["paper_id"],
                    "evidence_ids": ["evidence_id"],
                    "theoretical_foundations": ["string"],
                    "methodological_context": ["string"],
                    "hypothesis_or_proposition_links": ["string"],
                    "unresolved_questions": ["string"],
                    "transition_logic": "string|null",
                }
            ],
            "cross_section_synthesis_tasks": ["string"],
            "closing_tasks": ["string"],
            "verification_priorities": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = state_root / "packets" / "blueprint.json"
    _write_json(packet_file, packet)
    return {
        "packet_id": packet_id,
        "packet_file": str(packet_file),
        "papers": len(packet_papers),
        "evidence_items": len(selected_evidence),
        "verification_flags": len(evidence_map.get("papers_requiring_full_text") or []),
    }


def _validate_references(root: Path, submission: BlueprintSubmission) -> None:
    state_root = root / PROJECT_DIR
    papers = _load_jsonl(state_root / "data" / "papers.jsonl")
    evidence = _load_jsonl(state_root / "data" / "evidence.jsonl")
    paper_ids = {str(row.get("paper_id")) for row in papers if row.get("paper_id")}
    evidence_ids = {str(row.get("evidence_id")) for row in evidence if row.get("evidence_id")}
    referenced_papers: set[str] = set()
    referenced_evidence: set[str] = set()
    for section in submission.sections:
        referenced_papers.update(section.anchor_paper_ids)
        referenced_papers.update(section.supporting_paper_ids)
        referenced_papers.update(section.conflicting_paper_ids)
        referenced_evidence.update(section.evidence_ids)
    unknown_papers = sorted(referenced_papers - paper_ids)
    unknown_evidence = sorted(referenced_evidence - evidence_ids)
    if unknown_papers:
        raise ValueError("Blueprint references unknown paper IDs: " + ", ".join(unknown_papers))
    if unknown_evidence:
        raise ValueError("Blueprint references unknown evidence IDs: " + ", ".join(unknown_evidence))


def _render(payload: dict[str, object]) -> str:
    lines = [
        "# Literature Review Blueprint",
        "",
        str(payload.get("title") or "Literature Review Blueprint"),
        "",
        "## Organizing logic",
        "",
        str(payload.get("organizing_logic") or ""),
        "",
    ]
    opening = payload.get("opening_tasks") or []
    if opening:
        lines.extend(["## Opening tasks", "", *[f"- {item}" for item in opening], ""])
    for index, section in enumerate(payload.get("sections") or [], start=1):
        if not isinstance(section, dict):
            continue
        lines.extend(
            [
                f"## {index}. {section.get('title')}",
                "",
                f"**Purpose:** {section.get('purpose')}",
                "",
                "### Arguments the researcher should establish",
                "",
                *[f"- {item}" for item in section.get("key_arguments") or []],
                "",
            ]
        )
        for label, key in [
            ("Anchor papers", "anchor_paper_ids"),
            ("Supporting papers", "supporting_paper_ids"),
            ("Conflicting papers", "conflicting_paper_ids"),
            ("Evidence records", "evidence_ids"),
            ("Theoretical foundations", "theoretical_foundations"),
            ("Methodological context", "methodological_context"),
            ("Hypothesis/proposition links", "hypothesis_or_proposition_links"),
            ("Unresolved questions", "unresolved_questions"),
        ]:
            values = section.get(key) or []
            if values:
                lines.extend([f"### {label}", "", *[f"- `{item}`" if key.endswith("_ids") else f"- {item}" for item in values], ""])
        if section.get("transition_logic"):
            lines.extend(["### Transition logic", "", str(section["transition_logic"]), ""])

    for title, key in [
        ("Cross-section synthesis tasks", "cross_section_synthesis_tasks"),
        ("Closing tasks", "closing_tasks"),
        ("Verification priorities", "verification_priorities"),
        ("Current limitations", "limitations"),
    ]:
        values = payload.get(key) or []
        if values:
            lines.extend([f"## {title}", "", *[f"- {item}" for item in values], ""])
    lines.extend(
        [
            "> This is a literature-review construction blueprint, not a submission-ready literature review. The researcher remains responsible for source verification, scholarly judgment, citation selection, and final prose.",
            "",
        ]
    )
    return "\n".join(lines)


def save_blueprint(root: Path, input_file: Path) -> dict[str, object]:
    root, _, state = _load(root)
    if state["stages"]["research_direction"]["status"] != "accepted":
        raise ValueError("A researcher-accepted Research Direction is required before saving the Blueprint.")
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Blueprint input file not found: {input_path}")
    submission = BlueprintSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    _validate_references(root, submission)

    state_root = root / PROJECT_DIR
    revision = int(state["stages"]["literature_review_blueprint"].get("revision") or 0) + 1
    saved_at = _now()
    sections: list[dict[str, object]] = []
    for order, section in enumerate(submission.sections, start=1):
        row = section.model_dump()
        row.update({"section_id": str(uuid4()), "order": order})
        sections.append(row)
    payload = submission.model_dump()
    payload.update(
        {
            "schema_version": 1,
            "revision": revision,
            "saved_at": saved_at,
            "provenance": "ai_synthesis",
            "authorship_boundary": "researcher_writes_final_prose",
            "sections": sections,
        }
    )
    _write_json(state_root / "data" / "blueprint.json", payload)
    output = root / "outputs" / "06_literature_review_blueprint.md"
    _atomic_write_text(output, _render(payload))

    state["stages"]["literature_review_blueprint"]["status"] = "ready_for_review"
    state["stages"]["literature_review_blueprint"]["revision"] = revision
    state["current_stage"] = "literature_review_blueprint"
    if state["stages"]["researcher_handoff"]["status"] != "not_started":
        state["stages"]["researcher_handoff"]["status"] = "needs_refresh"
    _write_json(state_root / "state.json", state)

    source_ids = sorted(
        {
            paper_id
            for section in sections
            for key in ("anchor_paper_ids", "supporting_paper_ids", "conflicting_paper_ids")
            for paper_id in section.get(key) or []
        }
    )
    append_activity(
        root,
        category="blueprint_generation",
        actor="ai_assisted",
        inputs={"submission": str(input_path), "sections": len(sections)},
        outputs=[".litreview/data/blueprint.json", "outputs/06_literature_review_blueprint.md"],
        source_ids=source_ids,
        notes="Generated an evidence-linked literature-review architecture; final prose remains researcher-authored.",
    )
    return {
        "status": "ready_for_review",
        "revision": revision,
        "sections": len(sections),
        "output": str(output),
    }


def accept_blueprint(root: Path) -> dict[str, object]:
    root, _, state = _load(root)
    state_root = root / PROJECT_DIR
    blueprint_file = state_root / "data" / "blueprint.json"
    if not blueprint_file.exists():
        raise ValueError("No saved Literature Review Blueprint exists.")
    if state["stages"]["literature_review_blueprint"]["status"] not in {"ready_for_review", "accepted"}:
        raise ValueError("The Literature Review Blueprint is not ready for researcher acceptance.")
    state["stages"]["literature_review_blueprint"]["status"] = "accepted"
    state["stages"]["researcher_handoff"]["status"] = "in_progress"
    state["current_stage"] = "researcher_handoff"
    _write_json(state_root / "state.json", state)
    append_activity(
        root,
        category="blueprint_acceptance",
        actor="researcher",
        inputs={},
        outputs=[".litreview/state.json"],
        notes="Researcher accepted the Literature Review Blueprint for handoff/writing.",
    )
    return {"status": "accepted", "next_stage": "researcher_handoff"}


def show_blueprint(root: Path) -> dict[str, object]:
    root, _, state = _load(root)
    blueprint = _load_json(root / PROJECT_DIR / "data" / "blueprint.json")
    output = root / "outputs" / "06_literature_review_blueprint.md"
    if not output.exists():
        _atomic_write_text(output, _render(blueprint))
    return {
        "status": state["stages"]["literature_review_blueprint"]["status"],
        "revision": blueprint.get("revision"),
        "sections": len(blueprint.get("sections") or []),
        "output": str(output),
    }
