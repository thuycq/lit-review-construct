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
    return {
        "eligible_retained_records": len(eligible),
        "local_full_text_records": local,
        "toolkit_oa_full_text_records": len(toolkit_oa),
        "latest_toolkit_oa_acquired_at": max(acquired_at) if acquired_at else None,
        "oa_resolution_attempted_without_local_pdf": attempted,
        "remaining_resolution_candidates": remaining,
        "coverage_complete": remaining == 0,
    }


def finalize_oa_report(root: Path, report: dict[str, object]) -> dict[str, object]:
    root = root.expanduser().resolve()
    coverage = oa_coverage_status(root)
    report.update(coverage)
    _write_json(root / PROJECT_DIR / "data" / "fulltext_resolution.json", report)
    return report
