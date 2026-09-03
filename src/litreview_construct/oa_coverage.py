from __future__ import annotations

import json
from pathlib import Path

from .project import PROJECT_DIR, _write_json


def _load_jsonl(path: Path) -> list[dict[str, object]]:
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


def _has_local(row: dict[str, object]) -> bool:
    return bool(row.get("file_reference") or row.get("file_hash"))


def _eligible(records: list[dict[str, object]]) -> list[dict[str, object]]:
    priority_rank = {"core_candidate": 0, "high": 1, "medium": 2, "low": 3}
    retained = [
        row
        for row in records
        if row.get("triage_label") in {"relevant", "background", "adjacent"}
    ]
    retained.sort(
        key=lambda row: (
            priority_rank.get(str(row.get("triage_priority") or "medium"), 9),
            -(int(row.get("citation_count") or 0)),
            -(int(row.get("year") or 0)),
        )
    )
    return retained


def next_oa_batch(root: Path, *, max_papers: int = 100) -> list[str]:
    root = root.expanduser().resolve()
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    candidates = [
        row
        for row in _eligible(records)
        if not _has_local(row) and not row.get("oa_resolved_at")
    ]
    return [str(row["paper_id"]) for row in candidates[:max_papers] if row.get("paper_id")]


def missing_fulltext_queue(root: Path) -> list[dict[str, object]]:
    """Return retained papers that still need a researcher-supplied full text.

    The queue intentionally contains only bibliographic/provenance information and
    lawful resolution results. It never attempts paywall, login, CAPTCHA, or other
    access-control bypasses.
    """
    root = root.expanduser().resolve()
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    queue: list[dict[str, object]] = []
    for row in _eligible(records):
        if _has_local(row):
            continue
        status = str(row.get("oa_resolution_status") or "not_attempted")
        if status in {"downloaded", "already_local"}:
            continue
        candidates = row.get("oa_candidates")
        candidate_list = candidates if isinstance(candidates, list) else []
        best = candidate_list[0] if candidate_list and isinstance(candidate_list[0], dict) else {}
        queue.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year": row.get("year"),
                "doi": row.get("doi"),
                "triage_label": row.get("triage_label"),
                "triage_priority": row.get("triage_priority"),
                "oa_resolution_status": status,
                "oa_resolved_at": row.get("oa_resolved_at"),
                "best_landing_url": best.get("landing_url") if isinstance(best, dict) else None,
                "best_provider": best.get("provider") if isinstance(best, dict) else None,
                "researcher_action": (
                    "Open the lawful landing page or institutional library and add a PDF to papers/full_text."
                    if best
                    else "Provide a legally obtained PDF in papers/full_text when available."
                ),
            }
        )
    return queue


def oa_coverage_status(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    eligible = _eligible(records)
    local = sum(_has_local(row) for row in eligible)
    attempted = sum(bool(row.get("oa_resolved_at")) for row in eligible if not _has_local(row))
    remaining = sum(
        not _has_local(row) and not row.get("oa_resolved_at")
        for row in eligible
    )
    toolkit_oa = []
    for row in eligible:
        provenance = row.get("full_text_provenance")
        if isinstance(provenance, dict) and provenance.get("access") == "open_access" and _has_local(row):
            toolkit_oa.append(row)
    acquired_at = [
        str(row.get("full_text_provenance", {}).get("acquired_at") or "")
        for row in toolkit_oa
        if isinstance(row.get("full_text_provenance"), dict)
        and row.get("full_text_provenance", {}).get("acquired_at")
    ]
    missing_queue = missing_fulltext_queue(root)
    return {
        "eligible_retained_records": len(eligible),
        "local_full_text_records": local,
        "toolkit_oa_full_text_records": len(toolkit_oa),
        "latest_toolkit_oa_acquired_at": max(acquired_at) if acquired_at else None,
        "oa_resolution_attempted_without_local_pdf": attempted,
        "remaining_resolution_candidates": remaining,
        "missing_fulltext_records": len(missing_queue),
        "coverage_complete": remaining == 0,
    }


def finalize_oa_report(root: Path, report: dict[str, object]) -> dict[str, object]:
    root = root.expanduser().resolve()
    coverage = oa_coverage_status(root)
    report.update(coverage)
    queue = missing_fulltext_queue(root)
    _write_json(root / PROJECT_DIR / "data" / "fulltext_resolution.json", report)
    _write_json(
        root / PROJECT_DIR / "data" / "missing_fulltext.json",
        {
            "count": len(queue),
            "policy": "Lawful sources only; no paywall, login, CAPTCHA, or access-control bypassing.",
            "papers": queue,
        },
    )
    return report
