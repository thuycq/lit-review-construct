import json
from pathlib import Path

from litreview_construct.oa_coverage import (
    finalize_oa_report,
    missing_fulltext_queue,
    next_oa_batch,
    oa_coverage_status,
)
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


def test_missing_queue_contains_only_attempted_records_without_local_full_text(tmp_path: Path) -> None:
    init_project(tmp_path)
    rows = [
        {
            "paper_id": "local",
            "title": "Local Paper",
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "file_hash": "abc",
        },
        {
            "paper_id": "action",
            "title": "Needs Library Access",
            "year": 2025,
            "doi": "10.1000/action",
            "triage_label": "relevant",
            "triage_priority": "high",
            "oa_resolved_at": "2026-09-03T01:00:00+00:00",
            "oa_resolution_status": "resolved_landing",
            "oa_best_location": {
                "provider": "unpaywall",
                "landing_url": "https://example.org/paper",
                "pdf_url": None,
            },
        },
        {
            "paper_id": "pending",
            "title": "Resolver Has Not Tried Yet",
            "triage_label": "background",
            "triage_priority": "medium",
        },
    ]
    _write(tmp_path, rows)

    queue = missing_fulltext_queue(tmp_path)
    assert [item["paper_id"] for item in queue] == ["action"]
    assert queue[0]["best_landing_url"] == "https://example.org/paper"
    assert queue[0]["best_provider"] == "unpaywall"

    status = oa_coverage_status(tmp_path)
    assert status["missing_fulltext_records"] == 1
    assert status["remaining_resolution_candidates"] == 1
    assert status["coverage_complete"] is False


def test_finalize_report_writes_missing_fulltext_queue_file(tmp_path: Path) -> None:
    init_project(tmp_path)
    rows = [
        {
            "paper_id": "missing",
            "title": "Closed After OA Check",
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "oa_resolved_at": "2026-09-03T01:00:00+00:00",
            "oa_resolution_status": "unresolved_or_closed",
        }
    ]
    _write(tmp_path, rows)

    report = finalize_oa_report(tmp_path, {"selected_papers": 0})
    assert report["missing_fulltext_records"] == 1

    queue_path = tmp_path / ".litreview" / "data" / "missing_fulltext.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["papers"][0]["paper_id"] == "missing"
    assert "no paywall" in payload["policy"].lower()
