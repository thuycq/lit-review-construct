import json
from pathlib import Path

from litreview_construct.oa_coverage import next_oa_batch, oa_coverage_status
from litreview_construct.project import init_project


def _write(root: Path, rows: list[dict[str, object]]) -> None:
    (root / ".litreview" / "data" / "papers.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def test_oa_batch_skips_local_and_already_attempted_records(tmp_path: Path) -> None:
    init_project(tmp_path)
    rows = [
        {"paper_id": "local", "triage_label": "relevant", "triage_priority": "core_candidate", "file_reference": "papers/user_uploads/local.pdf"},
        {"paper_id": "done", "triage_label": "relevant", "triage_priority": "core_candidate", "oa_resolved_at": "2026-08-29T01:00:00+00:00"},
        {"paper_id": "next1", "triage_label": "relevant", "triage_priority": "high", "citation_count": 20, "year": 2024},
        {"paper_id": "next2", "triage_label": "adjacent", "triage_priority": "medium", "citation_count": 5, "year": 2023},
        {"paper_id": "out", "triage_label": "out_of_scope", "triage_priority": "core_candidate"},
    ]
    _write(tmp_path, rows)
    batch = next_oa_batch(tmp_path, max_papers=1)
    assert batch == ["next1"]


def test_oa_coverage_completes_when_every_retained_record_is_local_or_attempted(tmp_path: Path) -> None:
    init_project(tmp_path)
    rows = [
        {"paper_id": "p1", "triage_label": "relevant", "triage_priority": "core_candidate", "file_hash": "abc"},
        {"paper_id": "p2", "triage_label": "background", "triage_priority": "high", "oa_resolved_at": "2026-08-29T01:00:00+00:00"},
        {"paper_id": "p3", "triage_label": "adjacent", "triage_priority": "medium", "oa_resolved_at": "2026-08-29T02:00:00+00:00"},
    ]
    _write(tmp_path, rows)
    status = oa_coverage_status(tmp_path)
    assert status["coverage_complete"] is True
    assert status["remaining_resolution_candidates"] == 0
    assert next_oa_batch(tmp_path, max_papers=100) == []
