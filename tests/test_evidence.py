import json
from pathlib import Path

import pytest

from litreview_construct.evidence import prepare_evidence_packet, save_evidence_map
from litreview_construct.project import init_project


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _seed_landscape_project(root: Path) -> None:
    init_project(root, name="Evidence Test")
    state_root = root / ".litreview"
    state = json.loads((state_root / "state.json").read_text(encoding="utf-8"))
    state["stages"]["research_intent"]["status"] = "accepted"
    state["stages"]["literature_discovery"]["status"] = "ready_for_review"
    (state_root / "state.json").write_text(json.dumps(state), encoding="utf-8")

    papers = [
        {
            "paper_id": "p1",
            "title": "Working Capital and Firm Performance",
            "authors": ["A. Researcher"],
            "year": 2024,
            "journal": "Journal A",
            "doi": "10.1000/a",
            "source_origin": "openalex",
            "status": "unresolved",
            "landscape_roles": ["anchor", "stream_member"],
            "abstract": "The study reports a nonlinear association between working capital and performance.",
            "file_instances": [],
        },
        {
            "paper_id": "p2",
            "title": "Liquidity Policy and Profitability",
            "authors": ["B. Researcher"],
            "year": 2023,
            "journal": "Journal B",
            "doi": "10.1000/b",
            "source_origin": "openalex",
            "status": "unresolved",
            "landscape_roles": ["stream_member"],
            "abstract": "The study uses panel regression and reports heterogeneous results across firms.",
            "file_instances": [],
        },
    ]
    _write_jsonl(state_root / "data" / "papers.jsonl", papers)
    _write_json(
        state_root / "data" / "landscape.json",
        {
            "summary": "Initial landscape",
            "anchor_paper_ids": ["p1"],
            "streams": [
                {
                    "name": "Efficiency",
                    "description": "Working-capital efficiency research",
                    "paper_ids": ["p1", "p2"],
                    "anchor_paper_ids": ["p1"],
                }
            ],
            "major_debates": [],
            "methodological_clusters": [],
            "unresolved_questions": [],
        },
    )


def test_prepare_evidence_packet_is_landscape_bounded(tmp_path: Path) -> None:
    _seed_landscape_project(tmp_path)
    result = prepare_evidence_packet(tmp_path)

    assert result["landscape_papers"] == 2
    assert result["packet_papers"] == 2
    packet = json.loads(Path(result["packet_file"]).read_text(encoding="utf-8"))
    assert {paper["paper_id"] for paper in packet["papers"]} == {"p1", "p2"}
    assert packet["analysis_contract"]["purpose"].startswith("Construct a traceable Evidence Map")


def test_save_evidence_map_rejects_source_reported_metadata_claim(tmp_path: Path) -> None:
    _seed_landscape_project(tmp_path)
    submission = tmp_path / "submission.json"
    _write_json(
        submission,
        {
            "summary": "Evidence summary",
            "evidence_items": [
                {
                    "paper_id": "p1",
                    "evidence_type": "association",
                    "claim": "Working capital is associated with performance.",
                    "provenance": "source_reported",
                    "source_basis": "metadata",
                }
            ],
        },
    )

    with pytest.raises(ValueError):
        save_evidence_map(tmp_path, submission)


def test_save_evidence_map_persists_provenance_and_state(tmp_path: Path) -> None:
    _seed_landscape_project(tmp_path)
    submission = tmp_path / "submission.json"
    _write_json(
        submission,
        {
            "summary": "Evidence summary",
            "evidence_items": [
                {
                    "paper_id": "p1",
                    "evidence_type": "association",
                    "claim": "The abstract reports a nonlinear association between working capital and performance.",
                    "provenance": "source_reported",
                    "source_basis": "abstract",
                    "source_locator": "abstract",
                    "certainty": "medium",
                },
                {
                    "paper_id": "p2",
                    "evidence_type": "method",
                    "claim": "The abstract identifies panel regression as the study method.",
                    "provenance": "source_reported",
                    "source_basis": "abstract",
                    "source_locator": "abstract",
                    "methods": ["panel regression"],
                    "certainty": "medium",
                },
            ],
            "papers_requiring_full_text": ["p1", "p2"],
        },
    )

    result = save_evidence_map(tmp_path, submission)

    assert result["status"] == "ready_for_review"
    assert result["evidence_items"] == 2
    assert result["requires_full_text"] == 2
    rows = [
        json.loads(line)
        for line in (tmp_path / ".litreview" / "data" / "evidence.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert rows[0]["provenance"] == "source_reported"
    assert rows[0]["evidence_id"]
    state = json.loads((tmp_path / ".litreview" / "state.json").read_text(encoding="utf-8"))
    assert state["stages"]["evidence_mapping"]["status"] == "ready_for_review"
    assert (tmp_path / "outputs" / "04_evidence_map.md").is_file()
