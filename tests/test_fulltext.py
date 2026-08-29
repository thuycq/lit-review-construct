import json
from pathlib import Path

from litreview_construct.fulltext import full_text_status, reconcile_full_text_links
from litreview_construct.project import init_project


def test_same_doi_local_pdf_is_linked_to_discovered_record(tmp_path: Path) -> None:
    init_project(tmp_path, name="Full Text Test")
    data = tmp_path / ".litreview" / "data"
    papers = [
        {
            "paper_id": "seed-pdf",
            "title": "Working Capital and Performance",
            "doi": "10.1000/test",
            "source_origin": "user_seed",
            "status": "user_seed",
            "file_reference": "papers/paper.pdf",
            "file_instances": [
                {"file_reference": "papers/paper.pdf", "location_type": "managed"}
            ],
            "location_type": "managed",
            "file_hash": "abc",
            "page_count": 12,
            "parse_status": "metadata_only",
        },
        {
            "paper_id": "discovered",
            "title": "Working Capital and Performance",
            "doi": "10.1000/test",
            "source_origin": "openalex",
            "status": "relevant",
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "citation_count": 100,
            "year": 2024,
            "file_reference": None,
            "file_instances": [],
            "file_hash": None,
        },
    ]
    (data / "papers.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in papers), encoding="utf-8"
    )
    relations = [
        {
            "left_paper_id": "seed-pdf",
            "right_paper_id": "discovered",
            "relation": "same_work",
            "confidence": "high",
            "basis": ["same_doi"],
            "resolution": "unresolved",
        }
    ]
    (data / "paper_relations.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in relations), encoding="utf-8"
    )

    result = reconcile_full_text_links(tmp_path)
    assert result["full_text_links_added"] == 1
    stored = [
        json.loads(line)
        for line in (data / "papers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    discovered = next(row for row in stored if row["paper_id"] == "discovered")
    assert discovered["file_reference"] == "papers/paper.pdf"
    assert discovered["full_text_link_basis"] == "same_doi"
    assert discovered["source_origin"] == "openalex"

    status = full_text_status(tmp_path)
    assert status["full_text_available"] == 2
    assert status["retained_missing_full_text"] == 0
