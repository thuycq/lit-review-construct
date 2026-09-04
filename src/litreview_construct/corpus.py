from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .project import PROJECT_DIR, _write_json

Tier = Literal["retained", "evidence", "core"]
RETAINED_LABELS = {"relevant", "background", "adjacent"}
MAX_AUTOMATIC_RETRIES = 2


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _state_file(root: Path) -> Path:
    return root / PROJECT_DIR / "data" / "corpus_refinement.json"


def _load_refinement(root: Path) -> dict[str, object]:
    value = _load_json(_state_file(root))
    if value is None:
        value = {
            "schema_version": 1,
            "created_at": _now(),
            "updated_at": _now(),
            "decisions": [],
        }
    if not isinstance(value.get("decisions"), list):
        value["decisions"] = []
    return value


def _campaign(root: Path) -> dict[str, object]:
    campaign = _load_json(root / PROJECT_DIR / "data" / "discovery_campaign.json")
    if not campaign:
        raise ValueError("A completed discovery campaign is required before corpus refinement.")
    if campaign.get("status") != "complete":
        raise ValueError("Finish the discovery campaign before corpus refinement.")
    return campaign


def _current_campaign_records(root: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    campaign = _campaign(root)
    campaign_id = str(campaign.get("campaign_id") or "")
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    triaged = [
        row
        for row in records
        if row.get("triage_campaign_id") == campaign_id and row.get("triage_label")
    ]
    # Backward compatibility for beta projects created before triage campaign IDs were
    # persisted on every classified record. Prefer campaign-scoped rows whenever they exist.
    if not triaged:
        triaged = [row for row in records if row.get("triage_label")]
    return campaign, triaged


def _has_full_text(row: dict[str, object]) -> bool:
    if row.get("file_reference") or row.get("file_hash"):
        return True
    instances = row.get("file_instances")
    return isinstance(instances, list) and any(
        isinstance(item, dict) and item.get("file_reference") for item in instances
    )


def _retryable(row: dict[str, object]) -> bool:
    if str(row.get("oa_resolution_status") or "") == "retryable_error":
        return int(row.get("oa_retry_count") or 0) < MAX_AUTOMATIC_RETRIES
    return bool(
        row.get("oa_download_error")
        and not row.get("oa_download_attempts")
        and int(row.get("oa_resolution_attempts") or 0) < MAX_AUTOMATIC_RETRIES
    )


def _stream_tags(row: dict[str, object]) -> list[str]:
    raw = row.get("triage_stream_tags")
    if not isinstance(raw, list):
        return []
    seen: list[str] = []
    for value in raw:
        tag = " ".join(str(value).strip().lower().split())
        if tag and tag not in seen:
            seen.append(tag)
    return seen


def _confidence_points(value: object) -> float:
    text = str(value or "").lower()
    return {"high": 6.0, "medium": 4.0, "low": 2.0}.get(text, 3.0)


def _score(row: dict[str, object], *, newest_year: int, focuses: list[str]) -> dict[str, float]:
    label_points = {"relevant": 30.0, "background": 18.0, "adjacent": 12.0}
    priority_points = {"core_candidate": 18.0, "high": 13.0, "medium": 8.0, "low": 3.0}

    abstract = str(row.get("abstract") or "").strip()
    abstract_points = 0.0 if not abstract else min(8.0, 2.0 + len(abstract) / 350.0)
    provenance = row.get("discovery_sources")
    source_count = (
        len(provenance)
        if isinstance(provenance, list)
        else 1 if row.get("source_origin") else 0
    )
    provenance_points = min(6.0, float(source_count) * 2.0)

    bibliographic_points = 0.0
    if row.get("doi"):
        bibliographic_points += 2.5
    if row.get("journal"):
        bibliographic_points += 2.5
    if row.get("authors"):
        bibliographic_points += 1.0

    citations = max(0, int(row.get("citation_count") or 0))
    # Citation value is deliberately capped so older highly cited papers cannot dominate relevance.
    anchor_points = min(8.0, math.log10(citations + 1) * 3.0)

    year = int(row.get("year") or 0)
    age = max(0, newest_year - year) if year else 99
    if age <= 3:
        recency_points = 6.0
    elif age <= 7:
        recency_points = 4.0
    elif age <= 15:
        recency_points = 2.0
    else:
        recency_points = 1.0 if year else 0.0

    tags = _stream_tags(row)
    normalized_focuses = [" ".join(value.lower().split()) for value in focuses if value.strip()]
    focus_points = 0.0
    if tags and normalized_focuses:
        for tag in tags:
            if any(tag in focus or focus in tag for focus in normalized_focuses):
                focus_points = 7.0
                break

    components = {
        "research_relevance": label_points.get(str(row.get("triage_label") or ""), 0.0),
        "triage_priority": priority_points.get(
            str(row.get("triage_priority") or "medium"), 6.0
        ),
        "triage_confidence": _confidence_points(row.get("triage_confidence")),
        "evidence_potential": abstract_points,
        "bibliographic_quality": bibliographic_points,
        "multi_source_provenance": provenance_points,
        "citation_anchor_value": anchor_points,
        "temporal_relevance": recency_points,
        "selected_focus_alignment": focus_points,
    }
    components["total"] = round(sum(components.values()), 3)
    return components


def _adaptive_target(source_count: int, tier: Tier) -> int:
    if source_count <= 0:
        return 0
    if tier == "evidence":
        if source_count <= 40:
            return source_count
        return min(90, max(35, round(source_count * 0.45)))
    if tier == "core":
        if source_count <= 18:
            return source_count
        return min(45, max(18, round(source_count * 0.42)))
    return source_count


def _select_with_stream_coverage(
    ranked: list[dict[str, object]],
    target: int,
) -> list[dict[str, object]]:
    if target >= len(ranked):
        return ranked

    selected: list[dict[str, object]] = []
    selected_ids: set[str] = set()
    streams: dict[str, list[dict[str, object]]] = {}
    for item in ranked:
        tags = item.get("stream_tags")
        tag_list = tags if isinstance(tags, list) and tags else ["__untagged__"]
        for tag in tag_list:
            streams.setdefault(str(tag), []).append(item)

    # Preserve representation across available streams first, then fill by score.
    ordered_streams = sorted(streams.items(), key=lambda pair: (-len(pair[1]), pair[0]))
    for _, items in ordered_streams:
        if len(selected) >= target:
            break
        candidate = items[0]
        paper_id = str(candidate.get("paper_id") or "")
        if paper_id and paper_id not in selected_ids:
            selected.append(candidate)
            selected_ids.add(paper_id)

    for item in ranked:
        if len(selected) >= target:
            break
        paper_id = str(item.get("paper_id") or "")
        if paper_id and paper_id not in selected_ids:
            selected.append(item)
            selected_ids.add(paper_id)
    return selected


def _ranking_rows(
    rows: list[dict[str, object]],
    *,
    focuses: list[str],
) -> list[dict[str, object]]:
    years = [int(row.get("year") or 0) for row in rows if int(row.get("year") or 0) > 0]
    newest_year = max(years) if years else datetime.now(timezone.utc).year
    ranked: list[dict[str, object]] = []
    for row in rows:
        score = _score(row, newest_year=newest_year, focuses=focuses)
        ranked.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year": row.get("year"),
                "doi": row.get("doi"),
                "journal": row.get("journal"),
                "triage_label": row.get("triage_label"),
                "triage_priority": row.get("triage_priority"),
                "triage_confidence": row.get("triage_confidence"),
                "stream_tags": _stream_tags(row),
                "full_text_available": _has_full_text(row),
                "ranking_basis": "metadata+abstract",
                "ranking_confidence": (
                    "moderate" if str(row.get("abstract") or "").strip() else "low"
                ),
                "score": score,
            }
        )
    ranked.sort(
        key=lambda item: (
            -float((item.get("score") or {}).get("total", 0.0)),  # type: ignore[union-attr]
            -int(item.get("year") or 0),
            str(item.get("title") or "").lower(),
        )
    )
    return ranked


def _persist_retained_snapshot(
    refinement: dict[str, object],
    retained: list[dict[str, object]],
) -> None:
    refinement["retained"] = {
        "count": len(retained),
        "paper_ids": [str(row.get("paper_id")) for row in retained if row.get("paper_id")],
        "updated_at": _now(),
    }


def rank_corpus(
    root: Path,
    *,
    to_tier: Literal["evidence", "core"],
    max_papers: int | None = None,
) -> dict[str, object]:
    root = _project_root(root)
    campaign, triaged = _current_campaign_records(root)
    retained = [row for row in triaged if row.get("triage_label") in RETAINED_LABELS]
    if not retained:
        raise ValueError("No retained papers are available for corpus refinement.")

    refinement = _load_refinement(root)
    refinement["campaign_id"] = campaign.get("campaign_id")
    _persist_retained_snapshot(refinement, retained)
    focuses = [str(value) for value in campaign.get("selected_focuses") or []]

    if to_tier == "evidence":
        source_rows = retained
        source_tier: Tier = "retained"
        target_tier: Tier = "evidence"
        state_key = "evidence_candidates"
    else:
        evidence = refinement.get("evidence_candidates")
        if not isinstance(evidence, dict) or not evidence.get("paper_ids"):
            raise ValueError("Rank Evidence Candidates before selecting Core Papers.")
        evidence_ids = {str(value) for value in evidence.get("paper_ids") or []}
        source_rows = [
            row for row in retained if str(row.get("paper_id") or "") in evidence_ids
        ]
        source_tier = "evidence"
        target_tier = "core"
        state_key = "core_papers"

    ranked = _ranking_rows(source_rows, focuses=focuses)
    recommended = _adaptive_target(len(ranked), target_tier)
    target = recommended if max_papers is None else min(max(1, max_papers), len(ranked))
    selected = _select_with_stream_coverage(ranked, target)

    refinement[state_key] = {
        "source_tier": source_tier,
        "count": len(selected),
        "recommended_count": recommended,
        "paper_ids": [str(item.get("paper_id")) for item in selected if item.get("paper_id")],
        "ranked_at": _now(),
        "ranking_version": "v1-explainable-metadata-abstract",
        "ranking_principles": [
            "research-intent relevance",
            "triage priority and confidence",
            "evidence potential",
            "bibliographic quality",
            "multi-provider provenance",
            "capped citation/anchor value",
            "temporal relevance",
            "selected-focus alignment",
            "research-stream coverage",
        ],
        "citation_count_is_not_sole_criterion": True,
        "selected": selected,
    }
    # Re-ranking evidence invalidates any older core selection and downstream decision.
    decisions = refinement.get("decisions")
    if to_tier == "evidence":
        refinement.pop("core_papers", None)
        if isinstance(decisions, list):
            refinement["decisions"] = [
                row
                for row in decisions
                if not (
                    isinstance(row, dict) and row.get("stage") in {"evidence", "core"}
                )
            ]
    elif isinstance(decisions, list):
        refinement["decisions"] = [
            row
            for row in decisions
            if not (isinstance(row, dict) and row.get("stage") == "core")
        ]
    refinement["updated_at"] = _now()
    _write_json(_state_file(root), refinement)

    return {
        "source_tier": source_tier,
        "target_tier": target_tier,
        "source_records": len(source_rows),
        "selected_records": len(selected),
        "recommended_count": recommended,
        "full_text_available_in_selection": sum(
            bool(item.get("full_text_available")) for item in selected
        ),
        "ranking_basis": "metadata+abstract",
        "state_file": str(_state_file(root)),
        "papers": selected,
    }


def _normalize_tier(tier: str) -> Tier:
    normalized = tier.strip().lower().replace("_", "-")
    aliases = {
        "retained": "retained",
        "evidence": "evidence",
        "evidence-candidates": "evidence",
        "candidate": "evidence",
        "candidates": "evidence",
        "core": "core",
        "core-papers": "core",
    }
    if normalized not in aliases:
        raise ValueError("tier must be retained, evidence, or core")
    return aliases[normalized]  # type: ignore[return-value]


def selection_ids(root: Path, tier: str) -> list[str]:
    root = _project_root(root)
    normalized = _normalize_tier(tier)
    campaign, triaged = _current_campaign_records(root)
    del campaign
    retained = [row for row in triaged if row.get("triage_label") in RETAINED_LABELS]
    if normalized == "retained":
        return [str(row.get("paper_id")) for row in retained if row.get("paper_id")]
    refinement = _load_refinement(root)
    key = "evidence_candidates" if normalized == "evidence" else "core_papers"
    block = refinement.get(key)
    if not isinstance(block, dict) or not block.get("paper_ids"):
        raise ValueError(f"No {key.replace('_', ' ')} selection exists yet.")
    return [str(value) for value in block.get("paper_ids") or []]


def tier_coverage(root: Path, tier: str) -> dict[str, object]:
    root = _project_root(root)
    normalized = _normalize_tier(tier)
    ids = selection_ids(root, normalized)
    selected = set(ids)
    records = [
        row
        for row in _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
        if str(row.get("paper_id") or "") in selected
    ]
    local = [row for row in records if _has_full_text(row)]
    pending = [
        row
        for row in records
        if not _has_full_text(row) and (not row.get("oa_resolved_at") or _retryable(row))
    ]
    attempted_missing = [
        row
        for row in records
        if not _has_full_text(row) and row.get("oa_resolved_at") and not _retryable(row)
    ]
    return {
        "tier": normalized,
        "selected_records": len(ids),
        "local_full_text": len(local),
        "missing_full_text": max(0, len(ids) - len(local)),
        "automatic_resolution_pending": len(pending),
        "resolved_but_missing": len(attempted_missing),
        "automatic_pass_complete": len(pending) == 0,
    }


def pending_acquisition_ids(root: Path, tier: str, *, max_papers: int = 100) -> list[str]:
    root = _project_root(root)
    ids = selection_ids(root, tier)
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    by_id = {str(row.get("paper_id") or ""): row for row in records}
    pending: list[str] = []
    for paper_id in ids:
        row = by_id.get(paper_id)
        if not row or _has_full_text(row):
            continue
        if not row.get("oa_resolved_at") or _retryable(row):
            pending.append(paper_id)
        if len(pending) >= max_papers:
            break
    return pending


def _latest_decision(refinement: dict[str, object], stage: str) -> dict[str, object] | None:
    decisions = refinement.get("decisions")
    if not isinstance(decisions, list):
        return None
    matches = [
        row for row in decisions if isinstance(row, dict) and row.get("stage") == stage
    ]
    return matches[-1] if matches else None


def record_decision(
    root: Path,
    *,
    stage: Literal["retained", "evidence", "core"],
    action: Literal["acquire", "refine", "continue"],
    note: str | None = None,
) -> dict[str, object]:
    root = _project_root(root)
    _campaign(root)
    valid = {
        "retained": {"acquire", "refine"},
        "evidence": {"acquire", "refine"},
        "core": {"acquire", "continue"},
    }
    if action not in valid[stage]:
        allowed = ", ".join(sorted(valid[stage]))
        raise ValueError(f"For {stage}, action must be one of: {allowed}")

    # Validate that the referenced tier exists before recording the choice.
    selection_ids(root, stage)
    refinement = _load_refinement(root)
    decision = {
        "stage": stage,
        "action": action,
        "timestamp": _now(),
        "note": note,
    }
    decisions = refinement.setdefault("decisions", [])
    assert isinstance(decisions, list)
    decisions.append(decision)
    refinement["updated_at"] = _now()
    _write_json(_state_file(root), refinement)
    return decision


def refinement_next_step(root: Path) -> dict[str, object]:
    root = _project_root(root)
    campaign, triaged = _current_campaign_records(root)
    retained = [row for row in triaged if row.get("triage_label") in RETAINED_LABELS]
    if not retained:
        raise ValueError("No retained papers are available after triage.")
    refinement = _load_refinement(root)
    refinement["campaign_id"] = campaign.get("campaign_id")
    _persist_retained_snapshot(refinement, retained)
    _write_json(_state_file(root), refinement)

    evidence = refinement.get("evidence_candidates")
    core = refinement.get("core_papers")

    if not isinstance(evidence, dict) or not evidence.get("paper_ids"):
        decision = _latest_decision(refinement, "retained")
        coverage = tier_coverage(root, "retained")
        if decision is None:
            return {
                "next_action": "retained_corpus_checkpoint",
                "skill": "litreview-corpus",
                "human_checkpoint_required": True,
                "reason": (
                    "Triage is complete. The researcher chooses whether to acquire the current "
                    "retained corpus locally now or narrow it first."
                ),
                "corpus_tier": "retained",
                "records": len(retained),
                "coverage": coverage,
                "options": [
                    {
                        "action": "acquire",
                        "meaning": (
                            "Try lawful local full-text acquisition for all retained papers, "
                            "then continue ranking."
                        ),
                        "ai_usage": "none for the acquisition command",
                        "command": "lrc corpus decide . --stage retained --action acquire",
                    },
                    {
                        "action": "refine",
                        "meaning": (
                            "Use ranking/relevance analysis to narrow to Evidence Candidates "
                            "before downloading."
                        ),
                        "command": "lrc corpus decide . --stage retained --action refine",
                    },
                ],
            }
        if decision.get("action") == "acquire" and not coverage["automatic_pass_complete"]:
            return {
                "next_action": "acquire_retained_locally",
                "skill": "litreview-fulltext",
                "human_checkpoint_required": False,
                "reason": (
                    "The researcher chose local acquisition for the retained corpus. Continue "
                    "the deterministic Python runtime pass without model-by-model downloading."
                ),
                "corpus_tier": "retained",
                "coverage": coverage,
                "commands": ["lrc fulltext acquire . --tier retained --max-papers 100 --json"],
                "ai_usage": "none inside the acquisition runtime",
            }
        return {
            "next_action": "rank_evidence_candidates",
            "skill": "litreview-corpus",
            "human_checkpoint_required": False,
            "reason": (
                "Rank retained papers into a smaller, coverage-aware Evidence Candidate corpus."
            ),
            "commands": ["lrc corpus rank . --to evidence --json"],
        }

    if not isinstance(core, dict) or not core.get("paper_ids"):
        decision = _latest_decision(refinement, "evidence")
        coverage = tier_coverage(root, "evidence")
        if decision is None:
            return {
                "next_action": "evidence_candidate_checkpoint",
                "skill": "litreview-corpus",
                "human_checkpoint_required": True,
                "reason": (
                    "Evidence Candidates are ranked. The researcher chooses whether to acquire "
                    "this smaller corpus now or narrow once more to Core Papers first."
                ),
                "corpus_tier": "evidence",
                "records": int(evidence.get("count") or len(evidence.get("paper_ids") or [])),
                "coverage": coverage,
                "options": [
                    {
                        "action": "acquire",
                        "meaning": (
                            "Try lawful local full-text acquisition for all Evidence Candidates, "
                            "then continue to Core Paper ranking."
                        ),
                        "ai_usage": "none for the acquisition command",
                        "command": "lrc corpus decide . --stage evidence --action acquire",
                    },
                    {
                        "action": "refine",
                        "meaning": "Continue ranking to Core Papers before downloading.",
                        "command": "lrc corpus decide . --stage evidence --action refine",
                    },
                ],
            }
        if decision.get("action") == "acquire" and not coverage["automatic_pass_complete"]:
            return {
                "next_action": "acquire_evidence_candidates_locally",
                "skill": "litreview-fulltext",
                "human_checkpoint_required": False,
                "reason": (
                    "The researcher chose local acquisition for Evidence Candidates. Continue "
                    "the deterministic Python runtime pass."
                ),
                "corpus_tier": "evidence",
                "coverage": coverage,
                "commands": ["lrc fulltext acquire . --tier evidence --max-papers 100 --json"],
                "ai_usage": "none inside the acquisition runtime",
            }
        return {
            "next_action": "rank_core_papers",
            "skill": "litreview-corpus",
            "human_checkpoint_required": False,
            "reason": (
                "Rank Evidence Candidates into the Core Paper set used for deep reading and "
                "evidence construction."
            ),
            "commands": ["lrc corpus rank . --to core --json"],
        }

    decision = _latest_decision(refinement, "core")
    coverage = tier_coverage(root, "core")
    if decision is None:
        return {
            "next_action": "core_paper_checkpoint",
            "skill": "litreview-corpus",
            "human_checkpoint_required": True,
            "reason": (
                "Core Papers are selected. The researcher chooses whether to run a local "
                "acquisition pass for all Core Papers before evidence construction or continue "
                "with the full text already available."
            ),
            "corpus_tier": "core",
            "records": int(core.get("count") or len(core.get("paper_ids") or [])),
            "coverage": coverage,
            "options": [
                {
                    "action": "acquire",
                    "meaning": (
                        "Try lawful local full-text acquisition for all Core Papers before deep "
                        "evidence work."
                    ),
                    "ai_usage": "none for the acquisition command",
                    "command": "lrc corpus decide . --stage core --action acquire",
                },
                {
                    "action": "continue",
                    "meaning": (
                        "Continue with currently available full text; missing core papers remain "
                        "explicit limitations/verification tasks."
                    ),
                    "command": "lrc corpus decide . --stage core --action continue",
                },
            ],
        }
    if decision.get("action") == "acquire" and not coverage["automatic_pass_complete"]:
        return {
            "next_action": "acquire_core_papers_locally",
            "skill": "litreview-fulltext",
            "human_checkpoint_required": False,
            "reason": (
                "The researcher chose local acquisition for Core Papers. Continue the "
                "deterministic Python runtime pass."
            ),
            "corpus_tier": "core",
            "coverage": coverage,
            "commands": ["lrc fulltext acquire . --tier core --max-papers 100 --json"],
            "ai_usage": "none inside the acquisition runtime",
        }

    return {
        "next_action": "proceed_to_landscape",
        "skill": "litreview-discover",
        "human_checkpoint_required": False,
        "reason": (
            "The Core Paper corpus is selected and the acquisition choice is recorded. Build "
            "the Research Landscape from this refined corpus."
        ),
        "corpus_tier": "core",
        "coverage": coverage,
        "commands": ["lrc discover prepare-landscape . --json"],
    }


def corpus_status(root: Path) -> dict[str, object]:
    root = _project_root(root)
    _, triaged = _current_campaign_records(root)
    retained = [row for row in triaged if row.get("triage_label") in RETAINED_LABELS]
    refinement = _load_refinement(root)
    evidence = refinement.get("evidence_candidates")
    core = refinement.get("core_papers")
    return {
        "retained_records": len(retained),
        "evidence_candidate_records": (
            int(evidence.get("count") or 0) if isinstance(evidence, dict) else 0
        ),
        "core_paper_records": int(core.get("count") or 0) if isinstance(core, dict) else 0,
        "retained_coverage": tier_coverage(root, "retained"),
        "evidence_coverage": (
            tier_coverage(root, "evidence")
            if isinstance(evidence, dict) and evidence.get("paper_ids")
            else None
        ),
        "core_coverage": (
            tier_coverage(root, "core")
            if isinstance(core, dict) and core.get("paper_ids")
            else None
        ),
        "next": refinement_next_step(root),
    }
