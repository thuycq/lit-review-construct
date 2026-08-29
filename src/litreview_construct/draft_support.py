from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from .activity import append_activity
from .project import PROJECT_DIR, _atomic_write_text, _write_json


class DraftFragmentSubmission(BaseModel):
    purpose: str = Field(min_length=1)
    draft_text: str = Field(min_length=1, max_length=2400)
    paper_ids: list[str] = []
    evidence_ids: list[str] = []
    researcher_tasks: list[str] = []
    verification_notes: list[str] = []


class DraftSectionSubmission(BaseModel):
    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    framing_note: str | None = None
    fragments: list[DraftFragmentSubmission] = Field(min_length=1, max_length=5)
    transition_draft: str | None = Field(default=None, max_length=1000)
    researcher_decisions: list[str] = []


class WorkingDraftSubmission(BaseModel):
    title: str = Field(min_length=1)
    opening_note: str | None = None
    sections: list[DraftSectionSubmission] = Field(min_length=2, max_length=12)
    cross_section_notes: list[str] = []
    final_researcher_tasks: list[str] = []
    limitations: list[str] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    root = root.expanduser().resolve()
    state_root = root / PROJECT_DIR
    project_file = state_root / "project.yaml"
    state_file = state_root / "state.json"
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


def prepare_working_draft_packet(root: Path) -> dict[str, object]:
    root, project, state = _load(root)
    state_root = root / PROJECT_DIR
    if state["stages"]["literature_review_blueprint"]["status"] != "accepted":
        raise ValueError("The Literature Review Blueprint must be researcher-accepted before draft support.")

    blueprint = _load_json(state_root / "data" / "blueprint.json")
    direction = _load_json(state_root / "data" / "selected_direction.json")
    evidence_rows = _load_jsonl(state_root / "data" / "evidence.jsonl")
    papers = _load_jsonl(state_root / "data" / "papers.jsonl")

    evidence_by_id = {
        str(row.get("evidence_id")): row for row in evidence_rows if row.get("evidence_id")
    }
    paper_by_id = {str(row.get("paper_id")): row for row in papers if row.get("paper_id")}

    packet_sections: list[dict[str, object]] = []
    referenced_papers: set[str] = set()
    referenced_evidence: set[str] = set()
    for section in blueprint.get("sections") or []:
        if not isinstance(section, dict):
            continue
        paper_ids = list(
            dict.fromkeys(
                [
                    *[str(v) for v in section.get("anchor_paper_ids") or []],
                    *[str(v) for v in section.get("supporting_paper_ids") or []],
                    *[str(v) for v in section.get("conflicting_paper_ids") or []],
                ]
            )
        )
        evidence_ids = [str(v) for v in section.get("evidence_ids") or []]
        referenced_papers.update(paper_ids)
        referenced_evidence.update(evidence_ids)
        packet_sections.append(
            {
                "section_id": section.get("section_id"),
                "order": section.get("order"),
                "title": section.get("title"),
                "purpose": section.get("purpose"),
                "key_arguments": section.get("key_arguments") or [],
                "paper_ids": paper_ids,
                "evidence_ids": evidence_ids,
                "theoretical_foundations": section.get("theoretical_foundations") or [],
                "methodological_context": section.get("methodological_context") or [],
                "hypothesis_or_proposition_links": section.get("hypothesis_or_proposition_links") or [],
                "unresolved_questions": section.get("unresolved_questions") or [],
                "transition_logic": section.get("transition_logic"),
            }
        )

    packet_papers = []
    for paper_id in sorted(referenced_papers):
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
                "doi": row.get("doi"),
                "full_text_available": bool(row.get("file_reference") or row.get("file_hash")),
                "triage_label": row.get("triage_label"),
                "triage_priority": row.get("triage_priority"),
            }
        )

    packet_evidence = []
    for evidence_id in sorted(referenced_evidence):
        row = evidence_by_id.get(evidence_id)
        if not row:
            continue
        packet_evidence.append(
            {
                "evidence_id": evidence_id,
                "paper_id": row.get("paper_id"),
                "evidence_type": row.get("evidence_type"),
                "claim": row.get("claim"),
                "provenance": row.get("provenance"),
                "source_basis": row.get("source_basis"),
                "certainty": row.get("certainty"),
                "source_locator": row.get("source_locator"),
            }
        )

    packet_id = str(uuid4())
    packet = {
        "packet_type": "researcher_working_draft",
        "packet_schema_version": 1,
        "packet_id": packet_id,
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "selected_research_direction": direction,
        "blueprint": {
            "title": blueprint.get("title"),
            "organizing_logic": blueprint.get("organizing_logic"),
            "opening_tasks": blueprint.get("opening_tasks") or [],
            "sections": packet_sections,
            "cross_section_synthesis_tasks": blueprint.get("cross_section_synthesis_tasks") or [],
            "closing_tasks": blueprint.get("closing_tasks") or [],
            "verification_priorities": blueprint.get("verification_priorities") or [],
            "limitations": blueprint.get("limitations") or [],
        },
        "paper_index": packet_papers,
        "evidence_items": packet_evidence,
        "analysis_contract": {
            "purpose": "Produce a researcher-editable working draft pack from the accepted evidence-linked Blueprint.",
            "required": [
                "cover every accepted Blueprint section",
                "write short draft fragments that advance the section argument rather than a polished final manuscript",
                "anchor each substantive fragment to paper_ids and evidence_ids when support exists",
                "preserve association-versus-causality boundaries from the evidence records",
                "surface abstract-only or otherwise unverified support explicitly",
                "include researcher tasks where construct choices, citation checks, interpretation, or source verification remain necessary",
                "keep section boundaries and verification labels visible so the researcher can revise deliberately",
            ],
            "prohibited": [
                "presenting the output as submission-ready prose",
                "inventing citations, findings, theories, methods, samples, or limitations",
                "smoothing all fragments into a seamless final literature review",
                "removing verification warnings simply to make the prose read more confidently",
                "using evidence outside the accepted Blueprint without explicit researcher-directed revision",
            ],
            "authorship_boundary": "This artifact is a working draft pack. The researcher rewrites, verifies, cites, and approves the final literature-review prose.",
        },
        "expected_output_schema": {
            "title": "string",
            "opening_note": "string|null",
            "sections": [
                {
                    "section_id": "accepted Blueprint section_id",
                    "title": "string",
                    "framing_note": "string|null",
                    "fragments": [
                        {
                            "purpose": "what this draft fragment does",
                            "draft_text": "researcher-editable draft prose",
                            "paper_ids": ["paper_id"],
                            "evidence_ids": ["evidence_id"],
                            "researcher_tasks": ["string"],
                            "verification_notes": ["string"],
                        }
                    ],
                    "transition_draft": "string|null",
                    "researcher_decisions": ["string"],
                }
            ],
            "cross_section_notes": ["string"],
            "final_researcher_tasks": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = state_root / "packets" / "working_draft.json"
    _write_json(packet_file, packet)
    return {
        "packet_id": packet_id,
        "packet_file": str(packet_file),
        "sections": len(packet_sections),
        "papers": len(packet_papers),
        "evidence_items": len(packet_evidence),
        "abstract_only_evidence": sum(
            str(row.get("source_basis") or "") == "abstract" for row in packet_evidence
        ),
    }


def _validate_submission(root: Path, submission: WorkingDraftSubmission) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    state_root = root / PROJECT_DIR
    blueprint = _load_json(state_root / "data" / "blueprint.json")
    evidence_rows = _load_jsonl(state_root / "data" / "evidence.jsonl")
    evidence_by_id = {
        str(row.get("evidence_id")): row for row in evidence_rows if row.get("evidence_id")
    }
    blueprint_sections = {
        str(row.get("section_id")): row
        for row in blueprint.get("sections") or []
        if isinstance(row, dict) and row.get("section_id")
    }
    submitted_ids = {section.section_id for section in submission.sections}
    if submitted_ids != set(blueprint_sections):
        missing = sorted(set(blueprint_sections) - submitted_ids)
        extra = sorted(submitted_ids - set(blueprint_sections))
        detail = []
        if missing:
            detail.append("missing sections: " + ", ".join(missing))
        if extra:
            detail.append("unknown sections: " + ", ".join(extra))
        raise ValueError("Working draft must cover every accepted Blueprint section (" + "; ".join(detail) + ").")

    for section in submission.sections:
        blueprint_section = blueprint_sections[section.section_id]
        allowed_papers = {
            str(v)
            for key in ("anchor_paper_ids", "supporting_paper_ids", "conflicting_paper_ids")
            for v in blueprint_section.get(key) or []
        }
        allowed_evidence = {str(v) for v in blueprint_section.get("evidence_ids") or []}
        for fragment in section.fragments:
            unknown_papers = sorted(set(fragment.paper_ids) - allowed_papers)
            unknown_evidence = sorted(set(fragment.evidence_ids) - allowed_evidence)
            if unknown_papers:
                raise ValueError(
                    f"Draft section {section.section_id} references papers outside its accepted Blueprint anchors: "
                    + ", ".join(unknown_papers)
                )
            if unknown_evidence:
                raise ValueError(
                    f"Draft section {section.section_id} references evidence outside its accepted Blueprint anchors: "
                    + ", ".join(unknown_evidence)
                )
            truly_unknown = sorted(value for value in fragment.evidence_ids if value not in evidence_by_id)
            if truly_unknown:
                raise ValueError("Working draft references unknown evidence IDs: " + ", ".join(truly_unknown))
    return blueprint, evidence_by_id


def _render(payload: dict[str, object]) -> str:
    lines = [
        "# Researcher Working Draft — Literature Review",
        "",
        "> **Working draft only.** This file is intentionally not submission-ready. Verify sources, rewrite prose in your own scholarly voice, confirm citations, and resolve all flagged decisions before using any text in a manuscript.",
        "",
        str(payload.get("title") or "Literature Review Working Draft"),
        "",
    ]
    if payload.get("opening_note"):
        lines.extend(["## Opening note", "", str(payload["opening_note"]), ""])

    for order, section in enumerate(payload.get("sections") or [], start=1):
        if not isinstance(section, dict):
            continue
        lines.extend([f"## {order}. {section.get('title')}", ""])
        if section.get("framing_note"):
            lines.extend([f"**Framing note:** {section.get('framing_note')}", ""])
        for index, fragment in enumerate(section.get("fragments") or [], start=1):
            if not isinstance(fragment, dict):
                continue
            lines.extend([f"### Draft fragment {index}", "", str(fragment.get("draft_text") or ""), ""])
            if fragment.get("paper_ids"):
                lines.append("**Paper anchors:** " + ", ".join(f"`{v}`" for v in fragment["paper_ids"]))
            if fragment.get("evidence_ids"):
                lines.append("**Evidence anchors:** " + ", ".join(f"`{v}`" for v in fragment["evidence_ids"]))
            bases = fragment.get("source_bases") or []
            if bases:
                lines.append("**Source basis:** " + ", ".join(str(v) for v in bases))
            if fragment.get("verification_required"):
                lines.append("**VERIFY BEFORE USE:** Yes")
            lines.append("")
            for title, key in [
                ("Researcher tasks", "researcher_tasks"),
                ("Verification notes", "verification_notes"),
            ]:
                values = fragment.get(key) or []
                if values:
                    lines.extend([f"**{title}:**", *[f"- {v}" for v in values], ""])
        if section.get("transition_draft"):
            lines.extend(["### Transition draft", "", str(section["transition_draft"]), ""])
        decisions = section.get("researcher_decisions") or []
        if decisions:
            lines.extend(["### Researcher decisions", "", *[f"- {v}" for v in decisions], ""])

    for title, key in [
        ("Cross-section notes", "cross_section_notes"),
        ("Final researcher tasks", "final_researcher_tasks"),
        ("Current limitations", "limitations"),
    ]:
        values = payload.get(key) or []
        if values:
            lines.extend([f"## {title}", "", *[f"- {v}" for v in values], ""])
    lines.extend(
        [
            "> The final literature review remains researcher-authored. This working draft records AI-assisted fragments and their evidence basis so they can be verified, rewritten, accepted, or rejected deliberately.",
            "",
        ]
    )
    return "\n".join(lines)


def save_working_draft(root: Path, input_file: Path) -> dict[str, object]:
    root, _, state = _load(root)
    if state["stages"]["literature_review_blueprint"]["status"] != "accepted":
        raise ValueError("The Literature Review Blueprint must be accepted before saving a working draft.")
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Working-draft input file not found: {input_path}")
    submission = WorkingDraftSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    blueprint, evidence_by_id = _validate_submission(root, submission)

    sections: list[dict[str, object]] = []
    source_ids: set[str] = set()
    verification_fragments = 0
    for order, section in enumerate(submission.sections, start=1):
        row = section.model_dump()
        row["order"] = order
        processed_fragments: list[dict[str, object]] = []
        for fragment in section.fragments:
            fragment_row = fragment.model_dump()
            bases = sorted(
                {
                    str(evidence_by_id[evidence_id].get("source_basis") or "unknown")
                    for evidence_id in fragment.evidence_ids
                    if evidence_id in evidence_by_id
                }
            )
            verification_required = (
                not fragment.evidence_ids
                or any(base != "full_text" for base in bases)
                or bool(fragment.verification_notes)
            )
            if verification_required:
                verification_fragments += 1
            fragment_row["source_bases"] = bases
            fragment_row["verification_required"] = verification_required
            processed_fragments.append(fragment_row)
            source_ids.update(fragment.paper_ids)
        row["fragments"] = processed_fragments
        sections.append(row)

    payload = submission.model_dump()
    payload.update(
        {
            "schema_version": 1,
            "saved_at": _now(),
            "provenance": "ai_synthesis",
            "authorship_boundary": "researcher_rewrites_verifies_and_approves_final_prose",
            "blueprint_revision": blueprint.get("revision"),
            "sections": sections,
        }
    )
    state_root = root / PROJECT_DIR
    _write_json(state_root / "data" / "working_draft.json", payload)
    output = root / "outputs" / "06b_literature_review_working_draft.md"
    _atomic_write_text(output, _render(payload))

    state["stages"]["researcher_handoff"]["status"] = "ready_for_review"
    state["current_stage"] = "researcher_handoff"
    _write_json(state_root / "state.json", state)
    append_activity(
        root,
        category="draft_fragment",
        actor="ai_assisted",
        inputs={"submission": str(input_path), "sections": len(sections)},
        outputs=[".litreview/data/working_draft.json", "outputs/06b_literature_review_working_draft.md"],
        source_ids=sorted(source_ids),
        notes=(
            "Produced an evidence-linked researcher working draft composed of bounded draft fragments. "
            "The output is not submission-ready and preserves verification flags and researcher tasks."
        ),
    )
    return {
        "status": "ready_for_researcher",
        "sections": len(sections),
        "verification_fragments": verification_fragments,
        "output": str(output),
    }


def show_working_draft(root: Path) -> dict[str, object]:
    root, _, state = _load(root)
    payload = _load_json(root / PROJECT_DIR / "data" / "working_draft.json")
    output = root / "outputs" / "06b_literature_review_working_draft.md"
    if not output.exists():
        _atomic_write_text(output, _render(payload))
    return {
        "status": state["stages"]["researcher_handoff"]["status"],
        "sections": len(payload.get("sections") or []),
        "output": str(output),
    }
