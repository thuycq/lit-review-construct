from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field, model_validator

from .project import PROJECT_DIR, _atomic_write_text, _write_json

EvidenceType = Literal[
    "theory",
    "method",
    "data",
    "association",
    "prediction",
    "causal_finding",
    "null_finding",
    "heterogeneous_finding",
    "limitation",
    "gap_claim",
]
ProvenanceType = Literal[
    "source_reported",
    "tool_derived",
    "ai_synthesis",
    "ai_inference",
    "methodological_interpretation",
    "researcher_judgment",
]
SourceBasis = Literal["full_text", "abstract", "metadata", "researcher_note"]
Confidence = Literal["low", "medium", "high"]


class EvidenceItemSubmission(BaseModel):
    paper_id: str = Field(min_length=1)
    evidence_type: EvidenceType
    claim: str = Field(min_length=1)
    provenance: ProvenanceType
    source_basis: SourceBasis
    source_locator: str | None = None
    source_excerpt: str | None = Field(default=None, max_length=500)
    topic: str | None = None
    variables: list[str] = []
    theories: list[str] = []
    methods: list[str] = []
    data_context: list[str] = []
    certainty: Confidence = "medium"

    @model_validator(mode="after")
    def validate_epistemic_boundary(self) -> "EvidenceItemSubmission":
        if self.provenance == "source_reported" and self.source_basis not in {
            "full_text",
            "abstract",
        }:
            raise ValueError(
                "source_reported evidence must be grounded in full_text or abstract content."
            )
        substantive = {
            "theory",
            "method",
            "data",
            "association",
            "prediction",
            "causal_finding",
            "null_finding",
            "heterogeneous_finding",
            "limitation",
            "gap_claim",
        }
        if self.evidence_type in substantive and self.provenance == "source_reported":
            if self.source_basis == "metadata":
                raise ValueError(
                    "Substantive source-reported evidence cannot be grounded in metadata alone."
                )
        if self.source_excerpt and self.source_basis == "metadata":
            raise ValueError("Metadata-grounded records cannot contain a source excerpt.")
        return self


class ContradictionSubmission(BaseModel):
    statement: str = Field(min_length=1)
    paper_ids: list[str] = Field(min_length=2)
    interpretation: str | None = None
    certainty: Confidence = "medium"


class EvidenceMapSubmission(BaseModel):
    summary: str = Field(min_length=1)
    evidence_items: list[EvidenceItemSubmission] = Field(min_length=1)
    cross_paper_patterns: list[str] = []
    contradictions: list[ContradictionSubmission] = []
    evidence_gaps: list[str] = []
    papers_requiring_full_text: list[str] = []
    limitations: list[str] = []


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


def _landscape_ids(landscape: dict[str, object]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for paper_id in landscape.get("anchor_paper_ids") or []:
        value = str(paper_id)
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    for stream in landscape.get("streams") or []:
        if not isinstance(stream, dict):
            continue
        for paper_id in stream.get("paper_ids") or []:
            value = str(paper_id)
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
    return ordered


def _paper_packet(row: dict[str, object], abstract_chars: int) -> dict[str, object]:
    abstract = row.get("abstract")
    if isinstance(abstract, str) and len(abstract) > abstract_chars:
        abstract = abstract[:abstract_chars].rstrip() + "…"
    instances = row.get("file_instances") if isinstance(row.get("file_instances"), list) else []
    file_references = [
        str(item.get("file_reference"))
        for item in instances
        if isinstance(item, dict) and item.get("file_reference")
    ]
    if row.get("file_reference") and str(row.get("file_reference")) not in file_references:
        file_references.append(str(row.get("file_reference")))
    return {
        "paper_id": row.get("paper_id"),
        "title": row.get("title"),
        "authors": row.get("authors") or [],
        "year": row.get("year"),
        "journal": row.get("journal"),
        "doi": row.get("doi"),
        "source_origin": row.get("source_origin"),
        "status": row.get("status"),
        "landscape_roles": row.get("landscape_roles") or [],
        "abstract": abstract,
        "full_text_available": bool(file_references),
        "file_references": file_references,
    }


def prepare_evidence_packet(
    root: Path,
    *,
    max_papers: int = 30,
    abstract_chars: int = 2200,
) -> dict[str, object]:
    """Create a bounded packet for source-disciplined Evidence Map construction."""
    if not 1 <= max_papers <= 60:
        raise ValueError("Evidence packet max_papers must be between 1 and 60.")
    if not 300 <= abstract_chars <= 5000:
        raise ValueError("abstract_chars must be between 300 and 5000.")

    root, project, state = _load_project(root)
    state_root = root / PROJECT_DIR
    landscape_file = state_root / "data" / "landscape.json"
    if not landscape_file.exists():
        raise ValueError("A saved Research Landscape is required before Evidence Mapping.")
    if state["stages"]["literature_discovery"]["status"] not in {
        "ready_for_review",
        "accepted",
    }:
        raise ValueError("Research Landscape must be ready for review before Evidence Mapping.")

    landscape = json.loads(landscape_file.read_text(encoding="utf-8"))
    records = _load_jsonl(state_root / "data" / "papers.jsonl")
    papers_by_id = {str(row.get("paper_id")): row for row in records if row.get("paper_id")}
    landscape_ids = _landscape_ids(landscape)
    selected_ids = landscape_ids[:max_papers]
    selected = [papers_by_id[paper_id] for paper_id in selected_ids if paper_id in papers_by_id]
    if not selected:
        raise ValueError("The saved Research Landscape does not reference any available papers.")

    packet_id = str(uuid4())
    packet = {
        "packet_type": "evidence_map",
        "packet_schema_version": 1,
        "packet_id": packet_id,
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "landscape": {
            "summary": landscape.get("summary"),
            "anchor_paper_ids": landscape.get("anchor_paper_ids") or [],
            "streams": landscape.get("streams") or [],
            "major_debates": landscape.get("major_debates") or [],
            "methodological_clusters": landscape.get("methodological_clusters") or [],
            "unresolved_questions": landscape.get("unresolved_questions") or [],
        },
        "papers": [_paper_packet(row, abstract_chars) for row in selected],
        "analysis_contract": {
            "purpose": "Construct a traceable Evidence Map for a narrative review.",
            "epistemic_classes": [
                "source_reported",
                "tool_derived",
                "ai_synthesis",
                "ai_inference",
                "methodological_interpretation",
                "researcher_judgment",
            ],
            "evidence_types": [
                "theory",
                "method",
                "data",
                "association",
                "prediction",
                "causal_finding",
                "null_finding",
                "heterogeneous_finding",
                "limitation",
                "gap_claim",
            ],
            "required": [
                "preserve paper_id on every evidence record",
                "label source basis as full_text, abstract, metadata, or researcher_note",
                "use source_reported only for claims explicitly supported by paper content",
                "distinguish association, prediction, and causal claims",
                "flag papers whose abstract is insufficient and full text is needed",
                "keep source excerpts short and optional",
                "surface contradictions and evidence gaps without manufacturing consensus",
            ],
            "prohibited": [
                "treating metadata or titles as substantive evidence",
                "upgrading association to causality without explicit study support",
                "inventing variables, samples, methods, findings, limitations, or theories",
                "silently treating AI inference as source-reported evidence",
                "writing a complete final literature review",
            ],
        },
        "expected_output_schema": {
            "summary": "string",
            "evidence_items": [
                {
                    "paper_id": "paper_id",
                    "evidence_type": "theory|method|data|association|prediction|causal_finding|null_finding|heterogeneous_finding|limitation|gap_claim",
                    "claim": "string",
                    "provenance": "source_reported|tool_derived|ai_synthesis|ai_inference|methodological_interpretation|researcher_judgment",
                    "source_basis": "full_text|abstract|metadata|researcher_note",
                    "source_locator": "string|null",
                    "source_excerpt": "optional short excerpt <=500 chars",
                    "topic": "string|null",
                    "variables": ["string"],
                    "theories": ["string"],
                    "methods": ["string"],
                    "data_context": ["string"],
                    "certainty": "low|medium|high",
                }
            ],
            "cross_paper_patterns": ["string"],
            "contradictions": [
                {
                    "statement": "string",
                    "paper_ids": ["paper_id", "paper_id"],
                    "interpretation": "string|null",
                    "certainty": "low|medium|high",
                }
            ],
            "evidence_gaps": ["string"],
            "papers_requiring_full_text": ["paper_id"],
            "limitations": ["string"],
        },
    }
    packet_file = state_root / "packets" / "evidence.json"
    _write_json(packet_file, packet)
    return {
        "packet_id": packet_id,
        "landscape_papers": len(landscape_ids),
        "packet_papers": len(selected),
        "full_text_available": sum(bool(_paper_packet(row, abstract_chars)["full_text_available"]) for row in selected),
        "packet_file": str(packet_file),
    }


def _validate_submission(
    submission: EvidenceMapSubmission,
    known_ids: set[str],
    landscape_ids: set[str],
) -> None:
    referenced = {item.paper_id for item in submission.evidence_items}
    referenced.update(submission.papers_requiring_full_text)
    for contradiction in submission.contradictions:
        referenced.update(contradiction.paper_ids)
    unknown = sorted(referenced - known_ids)
    if unknown:
        raise ValueError("Evidence Map references unknown paper IDs: " + ", ".join(unknown))
    outside = sorted(referenced - landscape_ids)
    if outside:
        raise ValueError(
            "Evidence Map references papers outside the saved Research Landscape: "
            + ", ".join(outside)
        )


def _render_evidence_map(
    submission: EvidenceMapSubmission,
    papers_by_id: dict[str, dict[str, object]],
) -> str:
    lines = ["# Evidence Map", "", submission.summary, ""]
    grouped: dict[str, list[EvidenceItemSubmission]] = {}
    for item in submission.evidence_items:
        grouped.setdefault(item.evidence_type, []).append(item)

    for evidence_type in [
        "theory",
        "method",
        "data",
        "association",
        "prediction",
        "causal_finding",
        "null_finding",
        "heterogeneous_finding",
        "limitation",
        "gap_claim",
    ]:
        items = grouped.get(evidence_type) or []
        if not items:
            continue
        lines.extend([f"## {evidence_type.replace('_', ' ').title()}", ""])
        for item in items:
            paper = papers_by_id[item.paper_id]
            lines.append(f"- **{paper.get('title', 'Untitled')}** — {item.claim}")
            lines.append(
                f"  - `{item.paper_id}` | provenance: `{item.provenance}` | basis: `{item.source_basis}` | certainty: `{item.certainty}`"
            )
            if item.source_locator:
                lines.append(f"  - Source locator: {item.source_locator}")
        lines.append("")

    sections = [
        ("Cross-paper patterns", submission.cross_paper_patterns),
        ("Evidence gaps", submission.evidence_gaps),
        ("Current limitations", submission.limitations),
    ]
    for title, values in sections:
        if values:
            lines.extend([f"## {title}", "", *[f"- {value}" for value in values], ""])

    if submission.contradictions:
        lines.extend(["## Contradictions", ""])
        for item in submission.contradictions:
            lines.append(f"- {item.statement}")
            lines.append("  - Papers: " + ", ".join(f"`{paper_id}`" for paper_id in item.paper_ids))
            if item.interpretation:
                lines.append(f"  - Interpretation: {item.interpretation}")
            lines.append(f"  - Certainty: `{item.certainty}`")
        lines.append("")

    if submission.papers_requiring_full_text:
        lines.extend(["## Papers requiring fuller source verification", ""])
        for paper_id in submission.papers_requiring_full_text:
            paper = papers_by_id[paper_id]
            lines.append(f"- {paper.get('title', 'Untitled')} — `{paper_id}`")
        lines.append("")

    lines.extend(
        [
            "> Evidence records preserve epistemic provenance. AI synthesis or inference is not treated as a source-reported finding, and abstract-only evidence should be revisited when fuller text is available.",
            "",
        ]
    )
    return "\n".join(lines)


def save_evidence_map(root: Path, input_file: Path) -> dict[str, object]:
    root, _, state = _load_project(root)
    state_root = root / PROJECT_DIR
    landscape_file = state_root / "data" / "landscape.json"
    if not landscape_file.exists():
        raise ValueError("A saved Research Landscape is required before Evidence Mapping.")
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Evidence Map input file not found: {input_path}")

    submission = EvidenceMapSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    records = _load_jsonl(state_root / "data" / "papers.jsonl")
    papers_by_id = {str(row["paper_id"]): row for row in records if row.get("paper_id")}
    landscape = json.loads(landscape_file.read_text(encoding="utf-8"))
    landscape_ids = set(_landscape_ids(landscape))
    _validate_submission(submission, set(papers_by_id), landscape_ids)

    revision = int(state["stages"]["evidence_mapping"].get("revision") or 0) + 1
    saved_at = _now()
    evidence_rows: list[dict[str, object]] = []
    for item in submission.evidence_items:
        row = item.model_dump()
        row.update(
            {
                "evidence_id": str(uuid4()),
                "created_at": saved_at,
                "created_by": "ai_assisted",
                "evidence_map_revision": revision,
            }
        )
        evidence_rows.append(row)

    evidence_file = state_root / "data" / "evidence.jsonl"
    _atomic_write_text(
        evidence_file,
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in evidence_rows),
    )
    map_data = submission.model_dump()
    map_data.update(
        {
            "schema_version": 1,
            "revision": revision,
            "saved_at": saved_at,
            "provenance": "ai_synthesis",
        }
    )
    map_file = state_root / "data" / "evidence_map.json"
    _write_json(map_file, map_data)

    output = root / "outputs" / "04_evidence_map.md"
    _atomic_write_text(output, _render_evidence_map(submission, papers_by_id))

    state["stages"]["evidence_mapping"]["status"] = "ready_for_review"
    state["stages"]["evidence_mapping"]["revision"] = revision
    state["current_stage"] = "evidence_mapping"
    for downstream in [
        "research_direction",
        "literature_review_blueprint",
        "researcher_handoff",
    ]:
        if state["stages"][downstream]["status"] != "not_started":
            state["stages"][downstream]["status"] = "needs_refresh"
    _write_json(state_root / "state.json", state)

    source_ids = sorted({item.paper_id for item in submission.evidence_items})
    activity_file = state_root / "activity" / "activity.jsonl"
    event = {
        "event_id": str(uuid4()),
        "timestamp": saved_at,
        "category": "evidence_mapping",
        "actor": "ai_assisted",
        "host": None,
        "model": None,
        "inputs": [str(input_path)],
        "outputs": [
            ".litreview/data/evidence.jsonl",
            ".litreview/data/evidence_map.json",
            "outputs/04_evidence_map.md",
        ],
        "source_ids": source_ids,
        "notes": "Evidence records preserve source basis and epistemic provenance.",
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    counts = Counter(row["evidence_type"] for row in evidence_rows)
    return {
        "status": "ready_for_review",
        "revision": revision,
        "evidence_items": len(evidence_rows),
        "evidence_types": dict(sorted(counts.items())),
        "papers": len(source_ids),
        "requires_full_text": len(submission.papers_requiring_full_text),
        "output": str(output),
        "evidence_file": str(evidence_file),
        "map_file": str(map_file),
    }


def show_evidence_map(root: Path) -> dict[str, object]:
    root, _, state = _load_project(root)
    state_root = root / PROJECT_DIR
    map_file = state_root / "data" / "evidence_map.json"
    evidence_file = state_root / "data" / "evidence.jsonl"
    if not map_file.exists() or not evidence_file.exists():
        raise FileNotFoundError("No Evidence Map has been saved yet.")
    data = json.loads(map_file.read_text(encoding="utf-8"))
    rows = _load_jsonl(evidence_file)
    counts = Counter(str(row.get("evidence_type")) for row in rows)
    return {
        "status": state["stages"]["evidence_mapping"]["status"],
        "revision": data.get("revision"),
        "evidence_items": len(rows),
        "evidence_types": dict(sorted(counts.items())),
        "papers": len({str(row.get("paper_id")) for row in rows if row.get("paper_id")}),
        "requires_full_text": len(data.get("papers_requiring_full_text") or []),
        "output": str(root / "outputs" / "04_evidence_map.md"),
        "map_file": str(map_file),
    }
