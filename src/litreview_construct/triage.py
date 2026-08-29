from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from .project import PROJECT_DIR, _atomic_write_text, _write_json

TriageLabel = Literal["relevant", "background", "adjacent", "out_of_scope", "unresolved"]
TriagePriority = Literal["core_candidate", "high", "medium", "low"]
Confidence = Literal["low", "medium", "high"]


class TriageItemSubmission(BaseModel):
    paper_id: str = Field(min_length=1)
    label: TriageLabel
    priority: TriagePriority = "medium"
    rationale: str = Field(min_length=1, max_length=800)
    stream_tags: list[str] = []
    key_terms: list[str] = []
    confidence: Confidence = "medium"


class TriageBatchSubmission(BaseModel):
    batch_summary: str = Field(min_length=1)
    items: list[TriageItemSubmission] = Field(min_length=1)
    emerging_terms: list[str] = []
    emerging_streams: list[str] = []
    notes: list[str] = []


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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    _atomic_write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _campaign(root: Path) -> dict[str, object]:
    path = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not path.exists():
        raise ValueError("A discovery campaign is required before relevance triage.")
    campaign = json.loads(path.read_text(encoding="utf-8"))
    if not campaign.get("iterations"):
        raise ValueError("Run at least one discovery iteration before relevance triage.")
    return campaign


def _tokens(value: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "what", "how", "does", "are",
        "into", "between", "among", "using", "study", "research", "effect", "effects", "impact",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", value.lower())
        if token not in stop
    }


def _scope_tokens(project: dict[str, object], campaign: dict[str, object]) -> set[str]:
    research = project.get("research") if isinstance(project.get("research"), dict) else {}
    parts = [str(research.get("topic") or ""), str(research.get("research_question") or "")]
    parts.extend(str(value) for value in campaign.get("selected_focuses") or [])
    review_file = Path(str(project.get("__root__") or "."))  # marker only; not used for I/O
    del review_file
    return _tokens(" ".join(parts))


def _score(row: dict[str, object], tokens: set[str]) -> tuple[int, int, int, int, str]:
    title = str(row.get("title") or "").lower()
    abstract = str(row.get("abstract") or "").lower()
    title_hits = sum(1 for token in tokens if token in title)
    abstract_hits = sum(1 for token in tokens if token in abstract)
    sources = row.get("discovery_sources") if isinstance(row.get("discovery_sources"), list) else []
    citations = int(row.get("citation_count") or 0)
    year = int(row.get("year") or 0)
    return (
        title_hits * 4 + abstract_hits,
        len(sources),
        min(citations, 10000),
        year,
        str(row.get("title") or "").lower(),
    )


def prepare_triage_batch(
    root: Path,
    *,
    batch_size: int = 100,
    abstract_chars: int = 1600,
    revisit: bool = False,
) -> dict[str, object]:
    """Prepare one bounded title/abstract triage batch from a large discovery corpus."""
    if not 20 <= batch_size <= 200:
        raise ValueError("batch_size must be between 20 and 200.")
    if not 200 <= abstract_chars <= 4000:
        raise ValueError("abstract_chars must be between 200 and 4000.")

    root, project, state = _load_project(root)
    if state["stages"]["research_intent"]["status"] != "accepted":
        raise ValueError("Research Intent must be accepted before relevance triage.")
    campaign = _campaign(root)
    campaign_id = str(campaign.get("campaign_id") or "")
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    if not records:
        raise ValueError("No indexed papers are available for triage.")

    tokens = _scope_tokens(project, campaign)
    candidates = []
    for row in records:
        already = row.get("triage_campaign_id") == campaign_id and row.get("triage_label")
        if already and not revisit:
            continue
        candidates.append(row)
    if not candidates:
        raise ValueError("No untriaged papers remain in the current discovery campaign.")

    candidates.sort(key=lambda row: _score(row, tokens), reverse=True)
    selected = candidates[:batch_size]
    packet_papers: list[dict[str, object]] = []
    for row in selected:
        abstract = row.get("abstract")
        if isinstance(abstract, str) and len(abstract) > abstract_chars:
            abstract = abstract[:abstract_chars].rstrip() + "…"
        packet_papers.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "authors": row.get("authors") or [],
                "year": row.get("year"),
                "journal": row.get("journal"),
                "citation_count": row.get("citation_count"),
                "abstract": abstract,
                "source_origin": row.get("source_origin"),
                "discovery_sources": row.get("discovery_sources") or [row.get("source_origin")],
                "source_basis": "abstract" if abstract else "title_metadata",
                "existing_status": row.get("status"),
                "previous_triage_label": row.get("triage_label"),
            }
        )

    packet = {
        "packet_type": "relevance_triage",
        "packet_schema_version": 1,
        "packet_id": str(uuid4()),
        "created_at": _now(),
        "campaign_id": campaign_id,
        "research_intent": project.get("research") or {},
        "selected_focuses": campaign.get("selected_focuses") or [],
        "corpus_summary": {
            "indexed_records": len(records),
            "already_triaged": len(records) - len(candidates),
            "remaining_before_batch": len(candidates),
            "batch_records": len(selected),
        },
        "papers": packet_papers,
        "analysis_contract": {
            "purpose": "Triage a large literature-discovery corpus for progressive narrowing without claiming evidence-level findings.",
            "labels": ["relevant", "background", "adjacent", "out_of_scope", "unresolved"],
            "priorities": ["core_candidate", "high", "medium", "low"],
            "required": [
                "classify every paper in this batch",
                "base decisions only on title/abstract/metadata supplied in this packet",
                "keep unresolved when the available abstract or title is insufficient",
                "use background for useful framing literature that is not directly on the focal relationship",
                "use adjacent for substantively nearby work that may inform later directions",
                "preserve paper_id exactly",
                "keep rationale short and auditable",
            ],
            "prohibited": [
                "inferring detailed findings not present in the abstract",
                "declaring a research gap from triage",
                "automatically excluding user-seed papers from project history",
                "using citation count as a relevance decision by itself",
                "writing a complete final literature review",
            ],
        },
        "expected_output_schema": {
            "batch_summary": "string",
            "items": [
                {
                    "paper_id": "paper_id",
                    "label": "relevant|background|adjacent|out_of_scope|unresolved",
                    "priority": "core_candidate|high|medium|low",
                    "rationale": "short string",
                    "stream_tags": ["string"],
                    "key_terms": ["string"],
                    "confidence": "low|medium|high",
                }
            ],
            "emerging_terms": ["string"],
            "emerging_streams": ["string"],
            "notes": ["string"],
        },
    }
    packet_file = root / PROJECT_DIR / "packets" / "triage.json"
    _write_json(packet_file, packet)
    return {
        "packet_id": packet["packet_id"],
        "packet_file": str(packet_file),
        "batch_records": len(selected),
        "indexed_records": len(records),
        "remaining_before_batch": len(candidates),
    }


def save_triage_batch(root: Path, input_file: Path) -> dict[str, object]:
    root, _, state = _load_project(root)
    campaign = _campaign(root)
    campaign_id = str(campaign.get("campaign_id") or "")
    packet_file = root / PROJECT_DIR / "packets" / "triage.json"
    if not packet_file.exists():
        raise ValueError("Prepare a triage batch before saving triage results.")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if str(packet.get("campaign_id") or "") != campaign_id:
        raise ValueError("The current triage packet belongs to a different discovery campaign.")

    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Triage input file not found: {input_path}")
    submission = TriageBatchSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    expected_ids = {str(row.get("paper_id")) for row in packet.get("papers") or [] if row.get("paper_id")}
    submitted_ids = {item.paper_id for item in submission.items}
    if submitted_ids != expected_ids:
        missing = sorted(expected_ids - submitted_ids)
        extra = sorted(submitted_ids - expected_ids)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("outside packet: " + ", ".join(extra))
        raise ValueError("Triage submission must classify every packet paper (" + "; ".join(details) + ").")

    papers_file = root / PROJECT_DIR / "data" / "papers.jsonl"
    records = _load_jsonl(papers_file)
    by_id = {str(row.get("paper_id")): row for row in records if row.get("paper_id")}
    now = _now()
    counts: Counter[str] = Counter()
    for item in submission.items:
        row = by_id.get(item.paper_id)
        if row is None:
            raise ValueError(f"Unknown paper_id in triage submission: {item.paper_id}")
        row["triage_label"] = item.label
        row["triage_priority"] = item.priority
        row["triage_rationale"] = item.rationale
        row["triage_stream_tags"] = item.stream_tags
        row["triage_key_terms"] = item.key_terms
        row["triage_confidence"] = item.confidence
        row["triage_campaign_id"] = campaign_id
        row["triaged_at"] = now
        # Preserve user_seed as a durable provenance/status marker; discovered papers can use triage status directly.
        if row.get("source_origin") != "user_seed":
            row["status"] = item.label
        row["updated_at"] = now
        counts[item.label] += 1
    _write_jsonl(papers_file, records)

    run = {
        "triage_run_id": str(uuid4()),
        "timestamp": now,
        "campaign_id": campaign_id,
        "packet_id": packet.get("packet_id"),
        "batch_summary": submission.batch_summary,
        "counts": dict(counts),
        "emerging_terms": submission.emerging_terms,
        "emerging_streams": submission.emerging_streams,
        "notes": submission.notes,
        "paper_ids": sorted(submitted_ids),
        "provenance": "ai_synthesis",
    }
    runs_file = root / PROJECT_DIR / "data" / "triage_runs.jsonl"
    runs = _load_jsonl(runs_file)
    runs.append(run)
    _write_jsonl(runs_file, runs)

    state["stages"]["literature_discovery"]["status"] = "in_progress"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)
    status = triage_status(root)
    return {
        "triage_run_id": run["triage_run_id"],
        "batch_records": len(submission.items),
        "batch_counts": dict(counts),
        "triaged_total": status["triaged"],
        "remaining": status["remaining"],
    }


def triage_status(root: Path) -> dict[str, object]:
    root, _, _ = _load_project(root)
    campaign = _campaign(root)
    campaign_id = str(campaign.get("campaign_id") or "")
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    current = [row for row in records if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")]
    counts = Counter(str(row.get("triage_label")) for row in current)
    priority = Counter(str(row.get("triage_priority")) for row in current)
    return {
        "campaign_id": campaign_id,
        "indexed_records": len(records),
        "triaged": len(current),
        "remaining": len(records) - len(current),
        "labels": dict(sorted(counts.items())),
        "priorities": dict(sorted(priority.items())),
        "complete": len(current) == len(records) and bool(records),
    }


def prepare_narrowing_review(
    root: Path,
    *,
    max_papers: int = 150,
    abstract_chars: int = 1800,
) -> dict[str, object]:
    """Build a discovery-review packet after triage, emphasizing papers retained for narrowing."""
    if not 20 <= max_papers <= 250:
        raise ValueError("max_papers must be between 20 and 250.")
    root, project, _ = _load_project(root)
    campaign = _campaign(root)
    campaign_id = str(campaign.get("campaign_id") or "")
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    triaged = [row for row in records if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")]
    if not triaged:
        raise ValueError("Run and save at least one relevance-triage batch before preparing a narrowing review.")

    label_rank = {"relevant": 0, "background": 1, "adjacent": 2, "unresolved": 3, "out_of_scope": 4}
    priority_rank = {"core_candidate": 0, "high": 1, "medium": 2, "low": 3}
    retained = [row for row in triaged if row.get("triage_label") != "out_of_scope"]
    retained.sort(
        key=lambda row: (
            label_rank.get(str(row.get("triage_label")), 9),
            priority_rank.get(str(row.get("triage_priority")), 9),
            -(int(row.get("citation_count") or 0)),
            -(int(row.get("year") or 0)),
        )
    )
    selected = retained[:max_papers]
    papers = []
    for row in selected:
        abstract = row.get("abstract")
        if isinstance(abstract, str) and len(abstract) > abstract_chars:
            abstract = abstract[:abstract_chars].rstrip() + "…"
        papers.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year": row.get("year"),
                "journal": row.get("journal"),
                "citation_count": row.get("citation_count"),
                "abstract": abstract,
                "triage_label": row.get("triage_label"),
                "triage_priority": row.get("triage_priority"),
                "triage_rationale": row.get("triage_rationale"),
                "triage_stream_tags": row.get("triage_stream_tags") or [],
                "discovery_sources": row.get("discovery_sources") or [row.get("source_origin")],
            }
        )
    status = triage_status(root)
    runs = _load_jsonl(root / PROJECT_DIR / "data" / "triage_runs.jsonl")
    packet = {
        "packet_type": "discovery_review",
        "packet_schema_version": 2,
        "packet_id": str(uuid4()),
        "created_at": _now(),
        "research_intent": project.get("research") or {},
        "selected_focuses": campaign.get("selected_focuses") or [],
        "campaign_summary": {
            "status": campaign.get("status"),
            "iterations": len(campaign.get("iterations") or []),
            "indexed_records": len(records),
            "triage": status,
            "triage_runs": len(runs),
        },
        "triage_signals": {
            "emerging_terms": list(dict.fromkeys(term for run in runs for term in run.get("emerging_terms") or []))[:80],
            "emerging_streams": list(dict.fromkeys(term for run in runs for term in run.get("emerging_streams") or []))[:40],
        },
        "representative_papers": papers,
        "analysis_contract": {
            "purpose": "Analyze the progressively filtered discovery corpus and propose researcher-controlled narrowing choices.",
            "required": [
                "identify provisional research streams from retained papers",
                "propose candidate focus areas and concrete next-query suggestions",
                "state whether more broad collection, focused searching, citation expansion, or scope change is useful",
                "preserve paper_id references",
                "treat unresolved papers as uncertainty rather than irrelevant",
            ],
            "prohibited": [
                "claiming a definitive research gap",
                "treating triage as full-text evidence",
                "choosing a focus without researcher approval",
                "claiming systematic-review completeness",
            ],
            "human_checkpoint": "Stop after the review and ask the researcher whether to continue, focus, change scope, or finish discovery.",
        },
        "expected_output_schema": {
            "summary": "string",
            "provisional_streams": [
                {
                    "name": "string",
                    "description": "string",
                    "representative_paper_ids": ["paper_id"],
                    "indicative_terms": ["string"],
                    "provisional_questions": ["string"],
                    "confidence": "low|medium|high",
                }
            ],
            "candidate_focuses": [
                {
                    "name": "string",
                    "rationale": "string",
                    "representative_paper_ids": ["paper_id"],
                    "query_suggestions": ["string"],
                    "why_promising": ["string"],
                    "risks": ["string"],
                }
            ],
            "coverage_observations": ["string"],
            "recommended_next_actions": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = root / PROJECT_DIR / "packets" / "discovery_review.json"
    _write_json(packet_file, packet)
    return {
        "packet_file": str(packet_file),
        "indexed_records": len(records),
        "triaged_records": status["triaged"],
        "remaining_untriaged": status["remaining"],
        "representative_papers": len(papers),
    }
