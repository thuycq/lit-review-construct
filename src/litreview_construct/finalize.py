from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml

from .project import PROJECT_DIR, _write_json


RETAINED_LABELS = {"relevant", "background", "adjacent"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_project(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    root = root.expanduser().resolve()
    project_file = root / PROJECT_DIR / "project.yaml"
    state_file = root / PROJECT_DIR / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    state = json.loads(state_file.read_text(encoding="utf-8"))
    return root, project, state


def _campaign(root: Path) -> dict[str, object]:
    path = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not path.exists():
        raise ValueError("A discovery campaign is required before final Research Landscape construction.")
    campaign = json.loads(path.read_text(encoding="utf-8"))
    if campaign.get("status") != "complete":
        raise ValueError(
            "Discovery campaign is not complete. The researcher must explicitly finish discovery before final Research Landscape construction."
        )
    return campaign


def _rank(row: dict[str, object], selected_focuses: list[str]) -> tuple[int, int, int, int, int, str]:
    label_rank = {"relevant": 0, "background": 1, "adjacent": 2}
    priority_rank = {"core_candidate": 0, "high": 1, "medium": 2, "low": 3}
    tags = " ".join(str(value).lower() for value in row.get("triage_stream_tags") or []).strip()
    focus_hit = 1
    if tags and selected_focuses:
        if any(
            focus.strip() and (focus.lower() in tags or tags in focus.lower())
            for focus in selected_focuses
        ):
            focus_hit = 0
    sources = row.get("discovery_sources") if isinstance(row.get("discovery_sources"), list) else []
    return (
        label_rank.get(str(row.get("triage_label")), 9),
        focus_hit,
        priority_rank.get(str(row.get("triage_priority") or "medium"), 9),
        -len(sources),
        -(int(row.get("citation_count") or 0)),
        str(row.get("title") or "").lower(),
    )


def prepare_final_landscape_packet(
    root: Path,
    *,
    max_papers: int = 80,
    abstract_chars: int = 2200,
) -> dict[str, object]:
    """Prepare the post-discovery Research Landscape packet from the retained triaged corpus."""
    if not 20 <= max_papers <= 150:
        raise ValueError("max_papers must be between 20 and 150.")
    if not 300 <= abstract_chars <= 5000:
        raise ValueError("abstract_chars must be between 300 and 5000.")

    root, project, state = _load_project(root)
    if state["stages"]["research_intent"]["status"] != "accepted":
        raise ValueError("Research Intent must be accepted before Research Landscape construction.")
    campaign = _campaign(root)
    campaign_id = str(campaign.get("campaign_id") or "")
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    if not records:
        raise ValueError("No indexed papers are available.")

    triaged_current = [
        row
        for row in records
        if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")
    ]
    if not triaged_current:
        raise ValueError("No papers were triaged in the completed discovery campaign.")
    retained = [row for row in triaged_current if row.get("triage_label") in RETAINED_LABELS]
    if not retained:
        raise ValueError("No relevant/background/adjacent papers remain after triage.")

    selected_focuses = [str(value) for value in campaign.get("selected_focuses") or []]
    retained.sort(key=lambda row: _rank(row, selected_focuses))
    selected = retained[:max_papers]
    untriaged = len(records) - len(triaged_current)
    unresolved = sum(row.get("triage_label") == "unresolved" for row in triaged_current)
    out_scope = sum(row.get("triage_label") == "out_of_scope" for row in triaged_current)
    label_counts = Counter(str(row.get("triage_label")) for row in triaged_current)

    papers = []
    for row in selected:
        abstract = row.get("abstract")
        if isinstance(abstract, str) and len(abstract) > abstract_chars:
            abstract = abstract[:abstract_chars].rstrip() + "…"
        papers.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "authors": row.get("authors") or [],
                "year": row.get("year"),
                "journal": row.get("journal"),
                "doi": row.get("doi"),
                "openalex_id": row.get("openalex_id"),
                "s2_paper_id": row.get("s2_paper_id"),
                "citation_count": row.get("citation_count"),
                "abstract": abstract,
                "source_origin": row.get("source_origin"),
                "discovery_sources": row.get("discovery_sources") or [row.get("source_origin")],
                "triage_label": row.get("triage_label"),
                "triage_priority": row.get("triage_priority"),
                "triage_rationale": row.get("triage_rationale"),
                "triage_stream_tags": row.get("triage_stream_tags") or [],
                "triage_confidence": row.get("triage_confidence"),
                "full_text_available": bool(row.get("file_reference") or row.get("file_hash")),
            }
        )

    graph_edges = _load_jsonl(root / PROJECT_DIR / "data" / "paper_graph.jsonl")
    selected_ids = {str(row.get("paper_id")) for row in selected if row.get("paper_id")}
    relevant_edges = [
        edge
        for edge in graph_edges
        if str(edge.get("source_paper_id")) in selected_ids
        and str(edge.get("target_paper_id")) in selected_ids
    ]
    bibliographic_relations = _load_jsonl(root / PROJECT_DIR / "data" / "paper_relations.jsonl")
    relevant_relations = [
        row
        for row in bibliographic_relations
        if str(row.get("paper_id_a")) in selected_ids
        and str(row.get("paper_id_b")) in selected_ids
    ]

    warnings: list[str] = []
    if untriaged:
        warnings.append(
            f"{untriaged} indexed records were not triaged in the completed campaign; final gap claims should acknowledge incomplete triage coverage."
        )
    if unresolved:
        warnings.append(
            f"{unresolved} triaged records remain unresolved and are excluded from the final landscape packet until clarified."
        )

    packet = {
        "packet_type": "research_landscape",
        "packet_schema_version": 2,
        "packet_id": str(uuid4()),
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "discovery_context": {
            "campaign_id": campaign_id,
            "campaign_status": campaign.get("status"),
            "iterations": len(campaign.get("iterations") or []),
            "review_checkpoints": len(campaign.get("review_checkpoints") or []),
            "selected_focuses": selected_focuses,
            "indexed_records": len(records),
            "triaged_records": len(triaged_current),
            "triage_label_counts": dict(sorted(label_counts.items())),
            "retained_records": len(retained),
            "packet_records": len(selected),
            "out_of_scope_excluded": out_scope,
            "unresolved_excluded": unresolved,
            "untriaged_records": untriaged,
            "graph_edges_total": len(graph_edges),
            "warnings": warnings,
        },
        "papers": papers,
        "paper_graph_edges": relevant_edges,
        "bibliographic_relation_candidates": relevant_relations,
        "analysis_contract": {
            "purpose": "Construct the current Research Landscape after researcher-finished multi-source discovery and progressive relevance triage.",
            "required": [
                "identify a small set of anchor papers with explicit rationale",
                "organize retained literature into meaningful research streams",
                "surface debates, contradictory positions, methodological clusters, and recent developments",
                "use discovery coverage and graph context when assessing importance",
                "preserve paper_id references for traceability",
                "distinguish abstract-supported observations from AI synthesis/inference",
                "carry discovery warnings forward when coverage remains incomplete",
            ],
            "prohibited": [
                "reintroducing out-of-scope papers as substantive landscape evidence",
                "claiming systematic-review completeness",
                "treating citation count as the sole importance criterion",
                "inventing findings not supported by available content",
                "declaring a definitive research gap solely from this bounded packet",
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
    packet_file = root / PROJECT_DIR / "packets" / "landscape.json"
    _write_json(packet_file, packet)
    return {
        "packet_file": str(packet_file),
        "indexed_records": len(records),
        "triaged_records": len(triaged_current),
        "retained_records": len(retained),
        "packet_records": len(selected),
        "warnings": warnings,
    }
