import json
from pathlib import Path

from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.landscape import prepare_landscape_packet, save_landscape
from litreview_construct.project import init_project


def _write_papers(root: Path) -> list[str]:
    papers = [
        {
            "paper_id": "p1",
            "title": "Working Capital and Firm Performance",
            "authors": ["Author A"],
            "year": 2024,
            "journal": "Journal A",
            "doi": "10.1000/a",
            "openalex_id": "https://openalex.org/W1",
            "citation_count": 12,
            "publication_type": "article",
            "language": "en",
            "abstract": "This study examines working capital and firm performance.",
            "source_origin": "user_seed",
            "status": "user_seed",
            "file_hash": "abc",
        },
        {
            "paper_id": "p2",
            "title": "Cash Conversion Cycle and Profitability",
            "authors": ["Author B"],
            "year": 2025,
            "journal": "Journal B",
            "doi": "10.1000/b",
            "openalex_id": "https://openalex.org/W2",
            "citation_count": 5,
            "publication_type": "article",
            "language": "en",
            "abstract": "The paper studies the cash conversion cycle.",
            "source_origin": "openalex",
            "status": "unresolved",
            "file_hash": None,
        },
        {
            "paper_id": "p3",
            "title": "Liquidity Management in Manufacturing Firms",
            "authors": ["Author C"],
            "year": 2023,
            "journal": "Journal C",
            "doi": "10.1000/c",
            "openalex_id": "https://openalex.org/W3",
            "citation_count": 30,
            "publication_type": "article",
            "language": "en",
            "abstract": "Liquidity management is examined in manufacturing firms.",
            "source_origin": "openalex",
            "status": "unresolved",
            "file_hash": None,
        },
    ]
    path = root / ".litreview" / "data" / "papers.jsonl"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in papers),
        encoding="utf-8",
    )
    return [row["paper_id"] for row in papers]


def _accepted_project(root: Path) -> None:
    init_project(root)
    set_intent(
        root,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)


def test_prepare_landscape_packet_is_bounded_and_traceable(tmp_path: Path) -> None:
    _accepted_project(tmp_path)
    _write_papers(tmp_path)

    result = prepare_landscape_packet(tmp_path, max_papers=2, abstract_chars=300)

    assert result["indexed_records"] == 3
    assert result["packet_records"] == 2
    packet = json.loads(Path(result["packet_file"]).read_text(encoding="utf-8"))
    assert packet["packet_type"] == "research_landscape"
    assert len(packet["papers"]) == 2
    assert all(row["paper_id"] for row in packet["papers"])
    assert "expected_output_schema" in packet


def test_save_landscape_validates_ids_and_materializes_output(tmp_path: Path) -> None:
    _accepted_project(tmp_path)
    _write_papers(tmp_path)
    prepare_landscape_packet(tmp_path)

    submission = {
        "summary": "The literature can be organized around working-capital policy and liquidity mechanisms.",
        "anchor_paper_ids": ["p1"],
        "streams": [
            {
                "name": "Working-capital policy and performance",
                "description": "Studies linking working-capital choices with performance outcomes.",
                "paper_ids": ["p1", "p2"],
                "anchor_paper_ids": ["p1"],
                "main_theories": [],
                "main_methods": ["panel regression"],
                "major_findings": ["Reported associations vary by working-capital measure."],
                "contradictions": [],
                "recent_developments": [],
                "confidence": "medium",
            },
            {
                "name": "Liquidity mechanisms",
                "description": "Research focused on liquidity management mechanisms.",
                "paper_ids": ["p3"],
                "anchor_paper_ids": [],
                "main_theories": [],
                "main_methods": [],
                "major_findings": [],
                "contradictions": [],
                "recent_developments": [],
                "confidence": "low",
            },
        ],
        "major_debates": ["Whether shorter cash cycles always improve performance."],
        "methodological_clusters": ["Firm-level panel designs."],
        "recent_developments": [],
        "unresolved_questions": ["How effects differ across constrained firms."],
        "limitations": ["The current indexed corpus is intentionally bounded."],
    }
    input_file = tmp_path / "landscape_submission.json"
    input_file.write_text(json.dumps(submission), encoding="utf-8")

    result = save_landscape(tmp_path, input_file)

    assert result["anchors"] == 1
    assert result["streams"] == 2
    assert result["status"] == "ready_for_review"
    assert (tmp_path / "outputs" / "03_research_landscape.md").is_file()
    assert (tmp_path / ".litreview" / "data" / "landscape.json").is_file()
    assert (tmp_path / ".litreview" / "data" / "streams.jsonl").is_file()

    records = [
        json.loads(line)
        for line in (tmp_path / ".litreview" / "data" / "papers.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    roles = {row["paper_id"]: row["landscape_roles"] for row in records}
    assert roles["p1"] == ["anchor", "stream_member"]
    assert roles["p3"] == ["stream_member"]
