from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field, field_validator

from .project import PROJECT_DIR, _atomic_write_text, _write_json

QueryPhase = Literal["broad", "focused"]
QueryRole = Literal[
    "direct_construct",
    "synonym",
    "mechanism",
    "theory",
    "context",
    "method",
    "focused_followup",
]


class QueryFamilySubmission(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: QueryRole
    query: str = Field(min_length=2, max_length=500)
    rationale: str = Field(min_length=1, max_length=800)
    concepts: list[str] = []
    priority: Literal["high", "medium", "low"] = "medium"

    @field_validator("name", "query", "rationale")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()


class QueryPlanSubmission(BaseModel):
    phase: QueryPhase
    summary: str = Field(min_length=1, max_length=2000)
    query_families: list[QueryFamilySubmission] = Field(min_length=2, max_length=12)
    coverage_notes: list[str] = []
    limitations: list[str] = []

    @field_validator("query_families")
    @classmethod
    def _unique_queries(cls, value: list[QueryFamilySubmission]) -> list[QueryFamilySubmission]:
        normalized = [" ".join(item.query.lower().split()) for item in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Query families must contain unique query strings.")
        return value


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


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    _atomic_write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _campaign(root: Path) -> dict[str, object] | None:
    path = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_query_plan(
    root: Path,
    *,
    phase: QueryPhase = "broad",
    max_seed_papers: int = 20,
) -> dict[str, object]:
    if not 0 <= max_seed_papers <= 50:
        raise ValueError("max_seed_papers must be between 0 and 50.")
    root, project, state = _load(root)
    if state["stages"]["research_intent"]["status"] != "accepted":
        raise ValueError("Research Intent must be accepted before planning discovery queries.")

    campaign = _campaign(root)
    selected_focuses: list[str] = []
    previous_queries: list[str] = []
    review: dict[str, object] | None = None
    if campaign:
        selected_focuses = [str(value) for value in campaign.get("selected_focuses") or []]
        for iteration in campaign.get("iterations") or []:
            if isinstance(iteration, dict):
                previous_queries.extend(str(value) for value in iteration.get("queries") or [])
        review_file = root / PROJECT_DIR / "data" / "discovery_review.json"
        if review_file.exists():
            review = json.loads(review_file.read_text(encoding="utf-8"))

    if phase == "focused" and not selected_focuses:
        raise ValueError(
            "Focused query planning requires a researcher-selected discovery focus. "
            "Record a focus decision first."
        )

    papers = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    seed_rows = [row for row in papers if row.get("source_origin") == "user_seed"][:max_seed_papers]
    seed_papers = [
        {
            "paper_id": row.get("paper_id"),
            "title": row.get("title"),
            "year": row.get("year"),
            "doi": row.get("doi"),
            "abstract": row.get("abstract"),
        }
        for row in seed_rows
    ]

    candidate_focuses = []
    if isinstance(review, dict):
        for focus in review.get("candidate_focuses") or []:
            if isinstance(focus, dict):
                candidate_focuses.append(
                    {
                        "name": focus.get("name"),
                        "rationale": focus.get("rationale"),
                        "query_suggestions": focus.get("query_suggestions") or [],
                    }
                )

    packet = {
        "packet_type": "discovery_query_plan",
        "packet_schema_version": 1,
        "packet_id": str(uuid4()),
        "created_at": _now(),
        "phase": phase,
        "research_intent": project.get("research") or {},
        "selected_focuses": selected_focuses,
        "seed_papers": seed_papers,
        "previous_query_families": list(dict.fromkeys(previous_queries)),
        "previous_candidate_focuses": candidate_focuses,
        "analysis_contract": {
            "purpose": (
                "Design a small set of interpretable query families for broad multi-source retrieval."
                if phase == "broad"
                else "Design focused follow-up query families around researcher-selected literature directions."
            ),
            "required": [
                "use multiple query families rather than one opaque giant query",
                "make each query family interpretable and give a short rationale",
                "cover direct constructs and important terminology variants",
                "use mechanism, theory, context, or method queries only when they materially improve coverage",
                "avoid silently replacing the accepted Research Intent",
                "avoid duplicating previous queries unless repetition is justified by a changed focus",
            ],
            "broad_guidance": [
                "normally include at least one direct-construct query",
                "normally include at least one terminology/synonym query",
                "consider mechanism/theory/context families when the topic is broad enough",
            ],
            "focused_guidance": [
                "center queries on selected_focuses",
                "use previous query suggestions as inputs, not mandatory text",
                "seek adjacent terminology that could falsify or broaden the selected focus",
            ],
            "prohibited": [
                "claiming that the query plan guarantees exhaustive retrieval",
                "using citation count as a search query design criterion",
                "making a definitive research-gap claim during query planning",
            ],
        },
        "expected_output_schema": {
            "phase": phase,
            "summary": "string",
            "query_families": [
                {
                    "name": "string",
                    "role": "direct_construct|synonym|mechanism|theory|context|method|focused_followup",
                    "query": "string",
                    "rationale": "string",
                    "concepts": ["string"],
                    "priority": "high|medium|low",
                }
            ],
            "coverage_notes": ["string"],
            "limitations": ["string"],
        },
    }
    packet_file = root / PROJECT_DIR / "packets" / "query_plan.json"
    _write_json(packet_file, packet)
    return {
        "packet_file": str(packet_file),
        "phase": phase,
        "seed_papers": len(seed_papers),
        "previous_queries": len(packet["previous_query_families"]),
        "selected_focuses": selected_focuses,
    }


def save_query_plan(root: Path, input_file: Path) -> dict[str, object]:
    root, _, state = _load(root)
    packet_file = root / PROJECT_DIR / "packets" / "query_plan.json"
    if not packet_file.exists():
        raise ValueError("Prepare a discovery query-plan packet before saving a plan.")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))

    input_path = input_file.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Query-plan input file not found: {input_path}")
    submission = QueryPlanSubmission.model_validate_json(input_path.read_text(encoding="utf-8"))
    if submission.phase != packet.get("phase"):
        raise ValueError(
            f"Query-plan phase mismatch: packet={packet.get('phase')}, submission={submission.phase}."
        )

    now = _now()
    plan_id = str(uuid4())
    saved = submission.model_dump()
    saved.update(
        {
            "schema_version": 1,
            "plan_id": plan_id,
            "saved_at": now,
            "packet_id": packet.get("packet_id"),
            "research_intent_revision": state["stages"]["research_intent"].get("revision", 0),
            "provenance": "ai_synthesis",
        }
    )
    current_file = root / PROJECT_DIR / "data" / "discovery_query_plan.json"
    _write_json(current_file, saved)
    history_file = root / PROJECT_DIR / "data" / "discovery_query_plans.jsonl"
    history = _load_jsonl(history_file)
    history.append(saved)
    _write_jsonl(history_file, history)

    return {
        "plan_id": plan_id,
        "phase": submission.phase,
        "query_count": len(submission.query_families),
        "queries": [item.query for item in submission.query_families],
        "current_plan_file": str(current_file),
        "history_file": str(history_file),
    }


def load_current_query_plan(root: Path) -> dict[str, object]:
    root, _, _ = _load(root)
    path = root / PROJECT_DIR / "data" / "discovery_query_plan.json"
    if not path.exists():
        raise ValueError("No saved discovery query plan exists.")
    return json.loads(path.read_text(encoding="utf-8"))
