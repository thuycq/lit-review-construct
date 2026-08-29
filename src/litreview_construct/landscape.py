from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from .project import PROJECT_DIR, _atomic_write_text, _write_json


class LandscapeStreamSubmission(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    paper_ids: list[str] = Field(min_length=1)
    anchor_paper_ids: list[str] = []
    main_theories: list[str] = []
    main_methods: list[str] = []
    major_findings: list[str] = []
    contradictions: list[str] = []
    recent_developments: list[str] = []
    confidence: Literal["low", "medium", "high"] = "medium"


class ResearchLandscapeSubmission(BaseModel):
    summary: str = Field(min_length=1)
    anchor_paper_ids: list[str] = []
    streams: list[LandscapeStreamSubmission] = Field(min_length=1)
    major_debates: list[str] = []
    methodological_clusters: list[str] = []
    recent_developments: list[str] = []
    unresolved_questions: list[str] = []
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
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _load_relations(path: Path) -> list[dict[str, object]]:
    return _load_jsonl(path)


def _search_summary(search_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(search_dir.glob("*.json"), reverse=True)[:20]:
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(
            {
                "search_run_id": run.get("search_run_id"),
                "query": run.get("query"),
                "timestamp": run.get("timestamp"),
                "imported_records": run.get("imported_records"),
                "already_known": run.get("already_known"),
            }
        )
    return rows


def _select_packet_records(
    records: list[dict[str, object]], max_papers: int
) -> list[dict[str, object]]:
    """Choose a bounded, diverse metadata set without declaring final importance."""
    if max_papers < 1:
        raise ValueError("max_papers must be at least 1.")

    seeds = sorted(
        (row for row in records if row.get("source_origin") == "user_seed"),
        key=lambda row: str(row.get("title") or "").lower(),
    )
    by_citations = sorted(
        records,
        key=lambda row: (
            -(int(row.get("citation_count") or 0)),
            -(int(row.get("year") or 0)),
            str(row.get("title") or "").lower(),
        ),
    )
    by_recency = sorted(
        records,
        key=lambda row: (
            -(int(row.get("year") or 0)),
            -(int(row.get("citation_count") or 0)),
            str(row.get("title") or "").lower(),
        ),
    )
    alphabetical = sorted(records, key=lambda row: str(row.get("title") or "").lower())

    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    buckets = [seeds, by_citations, by_recency, alphabetical]
    positions = [0 for _ in buckets]

    while len(selected) < min(max_papers, len(records)):
        progressed = False
        for index, bucket in enumerate(buckets):
            while positions[index] < len(bucket):
                row = bucket[positions[index]]
                positions[index] += 1
                paper_id = str(row.get("paper_id") or "")
                if not paper_id or paper_id in seen:
                    continue
                seen.add(paper_id)
                selected.append(row)
                progressed = True
                break
            if len(selected) >= min(max_papers, len(records)):
                break
        if not progressed:
            break
    return selected


def _paper_packet(row: dict[str, object], abstract_chars: int) -> dict[str, object]:
    abstract = row.get("abstract")
    if isinstance(abstract, str) and len(abstract) > abstract_chars:
        abstract = abstract[:abstract_chars].rstrip() + "…"
    return {
        "paper_id": row.get("paper_id"),
        "title": row.get("title"),
        "authors": row.get("authors") or [],
        "year": row.get("year"),
        "journal": row.get("journal"),
        "doi": row.get("doi"),
        "openalex_id": row.get("openalex_id"),
        "citation_count": row.get("citation_count"),
        "publication_type": row.get("publication_type"),
        "language": row.get("language"),
        "source_origin": row.get("source_origin"),
        "status": row.get("status"),
        "abstract": abstract,
        "signals": {
            "user_seed": row.get("source_origin") == "user_seed",
            "citation_count": row.get("citation_count"),
            "publication_year": row.get("year"),
            "has_local_pdf": bool(row.get("file_hash")),
        },
    }


def prepare_landscape_packet(
    root: Path,
    *,
    max_papers: int = 40,
    abstract_chars: int = 1600,
) -> dict[str, object]:
    """Create a bounded packet for host-model Research Landscape synthesis."""
    if not 1 <= max_papers <= 100:
        raise ValueError("Landscape packet max_papers must be between 1 and 100.")
    if not 200 <= abstract_chars <= 5000:
        raise ValueError("abstract_chars must be between 200 and 5000.")

    root, project, state = _load_project(root)
    if state["stages"]["research_intent"]["status"] != "accepted":
        raise ValueError("Research Intent must be accepted before preparing a Research Landscape.")

    state_root = root / PROJECT_DIR
    records = _load_jsonl(state_root / "data" / "papers.jsonl")
    if not records:
        raise ValueError("No indexed papers are available for Research Landscape construction.")

    selected = _select_packet_records(records, max_papers)
    relations = _load_relations(state_root / "data" / "paper_relations.jsonl")
    selected_ids = {str(row.get("paper_id") or "") for row in selected}
    relevant_relations = [
        relation
        for relation in relations
        if str(relation.get("paper_id_a") or "") in selected_ids
        and str(relation.get("paper_id_b") or "") in selected_ids
    ]

    packet_id = str(uuid4())
    packet = {
        "packet_type": "research_landscape",
        "packet_schema_version": 1,
        "packet_id": packet_id,
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "corpus_summary": {
            "indexed_records": len(records),
            "packet_records": len(selected),
            "user_seed_records": sum(row.get("source_origin") == "user_seed" for row in records),
            "openalex_records": sum(row.get("source_origin") == "openalex" for row in records),
        },
        "search_history": _search_summary(state_root / "searches"),
        "papers": [_paper_packet(row, abstract_chars) for row in selected],
        "bibliographic_relation_candidates": relevant_relations,
        "analysis_contract": {
            "purpose": "Construct a narrative-review Research Landscape, not a final literature review.",
            "required": [
                "identify a small set of anchor papers with explicit rationale",
                "organize literature into meaningful research streams",
                "surface major debates or contradictory positions",
                "identify methodological clusters and recent developments",
                "preserve paper_id references for traceability",
                "distinguish metadata/abstract-supported observations from inference",
            ],
            "prohibited": [
                "claiming systematic-review completeness",
                "treating citation count as the sole importance criterion",
                "inventing findings not supported by available paper content",
                "writing a complete final literature review",
            ],
        },
        "expected_output_schema": {
            "summary": "string",
            "anchor_paper_ids": ["paper_id"],
            "streams": [
                {
                    "name": "string",
                    "description": "string",
                    "paper_ids": ["paper_id"],
                    "anchor_paper_ids": ["paper_id"],
                    "main_theories": ["string"],
                    "main_methods": ["string"],
                    "major_findings": ["string"],
                    "contradictions": ["string"],
                    "recent_developments": ["string"],
                    "confidence": "low|medium|high",
                }
            ],
            "major_debates": ["string"],
            "methodological_clusters": ["string"],
            "recent_developments": ["string"],
            "unresolved_questions": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = state_root / "packets" / "landscape.json"
    _write_json(packet_file, packet)
    return {
        "packet_id": packet_id,
        "indexed_records": len(records),
        "packet_records": len(selected),
        "packet_file": str(packet_file),
    }


def _validate_paper_ids(
    submission: ResearchLandscapeSubmission,
    known_ids: set[str],
) -> None:
    referenced = set(submission.anchor_paper_ids)
    for stream in submission.streams:
        referenced.update(stream.paper_ids)
        referenced.update(stream.anchor_paper_ids)
    unknown = sorted(referenced - known_ids)
    if unknown:
        raise ValueError("Research Landscape references unknown paper IDs: " + ", ".join(unknown))


def _render_landscape(
    submission: ResearchLandscapeSubmission,
    papers_by_id: dict[str, dict[str, object]],
) -> str:
    lines = ["# Research Landscape", "", submission.summary, "", "## Anchor papers", ""]
    if submission.anchor_paper_ids:
        for paper_id in submission.anchor_paper_ids:
            paper = papers_by_id[paper_id]
            year = paper.get("year") or "n.d."
            lines.append(f"- **{paper.get('title', 'Untitled')}** ({year}) — `{paper_id}`")
    else:
        lines.append("- No anchor papers selected yet.")

    lines.extend(["", "## Research streams", ""])
    for number, stream in enumerate(submission.streams, start=1):
        lines.extend([f"### {number}. {stream.name}", "", stream.description, ""])
        lines.append("**Papers**")
        for paper_id in stream.paper_ids:
            paper = papers_by_id[paper_id]
            lines.append(f"- {paper.get('title', 'Untitled')} — `{paper_id}`")
        if stream.main_theories:
            lines.extend(["", "**Theories**", *[f"- {item}" for item in stream.main_theories]])
        if stream.main_methods:
            lines.extend(["", "**Methods**", *[f"- {item}" for item in stream.main_methods]])
        if stream.major_findings:
            lines.extend(["", "**Main findings / patterns**", *[f"- {item}" for item in stream.major_findings]])
        if stream.contradictions:
            lines.extend(["", "**Contradictions**", *[f"- {item}" for item in stream.contradictions]])
        if stream.recent_developments:
            lines.extend(["", "**Recent developments**", *[f"- {item}" for item in stream.recent_developments]])
        lines.extend(["", f"Confidence: **{stream.confidence}**", ""])

    sections = [
        ("Major debates", submission.major_debates),
        ("Methodological clusters", submission.methodological_clusters),
        ("Recent developments", submission.recent_developments),
        ("Unresolved questions", submission.unresolved_questions),
        ("Current limitations of this landscape", submission.limitations),
    ]
    for title, items in sections:
        if items:
            lines.extend([f"## {title}", "", *[f"- {item}" for item in items], ""])

    lines.extend(
        [
            "> This Research Landscape is an AI-assisted narrative synthesis of the currently indexed corpus. It does not claim exhaustive or systematic-review completeness.",
            "",
        ]
    )
    return "\n".join(lines)


def save_landscape(root: Path, input_file: Path) -> dict[str, object]:
    """Validate and persist a host-model Research Landscape submission."""
    root, _, state = _load_project(root)
    state_root = root / PROJECT_DIR
    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Research Landscape input file not found: {input_path}")

    raw = json.loads(input_path.read_text(encoding="utf-8"))
    submission = ResearchLandscapeSubmission.model_validate(raw)
    records = _load_jsonl(state_root / "data" / "papers.jsonl")
    papers_by_id = {str(row["paper_id"]): row for row in records if row.get("paper_id")}
    _validate_paper_ids(submission, set(papers_by_id))

    previous_landscape = state_root / "data" / "landscape.json"
    revision = int(state["stages"]["literature_discovery"].get("revision") or 0) + 1
    saved_at = _now()

    streams: list[dict[str, object]] = []
    for stream in submission.streams:
        row = stream.model_dump()
        row["stream_id"] = str(uuid4())
        streams.append(row)

    landscape = submission.model_dump()
    landscape.update(
        {
            "schema_version": 1,
            "revision": revision,
            "saved_at": saved_at,
            "provenance": "ai_synthesis",
        }
    )
    _write_json(previous_landscape, landscape)
    _atomic_write_text(
        state_root / "data" / "streams.jsonl",
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in streams),
    )

    # Landscape roles are derived annotations, not primary relevance decisions.
    anchor_ids = set(submission.anchor_paper_ids)
    stream_member_ids = {paper_id for stream in submission.streams for paper_id in stream.paper_ids}
    for record in records:
        paper_id = str(record.get("paper_id") or "")
        roles: list[str] = []
        if paper_id in anchor_ids:
            roles.append("anchor")
        if paper_id in stream_member_ids:
            roles.append("stream_member")
        record["landscape_roles"] = roles
    _atomic_write_text(
        state_root / "data" / "papers.jsonl",
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
    )

    output = root / "outputs" / "03_research_landscape.md"
    _atomic_write_text(output, _render_landscape(submission, papers_by_id))

    state["stages"]["literature_discovery"]["status"] = "ready_for_review"
    state["stages"]["literature_discovery"]["revision"] = revision
    state["current_stage"] = "literature_discovery"
    for downstream in [
        "evidence_mapping",
        "research_direction",
        "literature_review_blueprint",
        "researcher_handoff",
    ]:
        if state["stages"][downstream]["status"] != "not_started":
            state["stages"][downstream]["status"] = "needs_refresh"
    _write_json(state_root / "state.json", state)

    activity_file = state_root / "activity" / "activity.jsonl"
    event = {
        "event_id": str(uuid4()),
        "timestamp": saved_at,
        "category": "research_landscape_synthesis",
        "actor": "ai_assisted",
        "host": None,
        "model": None,
        "inputs": [str(input_path)],
        "outputs": [
            ".litreview/data/landscape.json",
            ".litreview/data/streams.jsonl",
            "outputs/03_research_landscape.md",
        ],
        "source_ids": sorted(
            anchor_ids | {paper_id for stream in submission.streams for paper_id in stream.paper_ids}
        ),
        "notes": "Landscape synthesis is stored as AI synthesis; paper findings require source verification.",
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "revision": revision,
        "anchors": len(anchor_ids),
        "streams": len(streams),
        "output": str(output),
        "landscape_file": str(previous_landscape),
        "status": "ready_for_review",
    }


def show_landscape(root: Path) -> dict[str, object]:
    root, _, state = _load_project(root)
    path = root / PROJECT_DIR / "data" / "landscape.json"
    if not path.exists():
        raise FileNotFoundError("No Research Landscape has been saved yet.")
    landscape = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": state["stages"]["literature_discovery"]["status"],
        "revision": landscape.get("revision"),
        "anchors": len(landscape.get("anchor_paper_ids") or []),
        "streams": len(landscape.get("streams") or []),
        "output": str(root / "outputs" / "03_research_landscape.md"),
        "landscape_file": str(path),
    }
