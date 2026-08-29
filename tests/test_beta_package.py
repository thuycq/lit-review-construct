import json
from pathlib import Path

from litreview_construct.project import init_project
from litreview_construct.researcher_package import canonical_paper_stem, prepare_researcher_package


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_init_creates_researcher_facing_library(tmp_path: Path) -> None:
    init_project(tmp_path)
    assert (tmp_path / "papers" / "full_text").is_dir()
    assert (tmp_path / "papers" / "abstract_only").is_dir()
    assert (tmp_path / "papers" / "user_uploads").is_dir()
    assert (tmp_path / "references").is_dir()


def test_doi_filename_is_windows_safe_and_recognizable() -> None:
    row = {"doi": "https://doi.org/10.1016/j.jbankfin.2024.107123", "paper_id": "p1"}
    stem = canonical_paper_stem(row)
    assert stem == "doi_10.1016__j.jbankfin.2024.107123"
    assert "/" not in stem
    assert ":" not in stem


def test_package_exports_working_refs_and_abstract_only_notes(tmp_path: Path) -> None:
    init_project(tmp_path)
    cache = tmp_path / ".litreview" / "cache" / "fulltext"
    cache.mkdir(parents=True, exist_ok=True)
    cached_pdf = cache / "p1.pdf"
    cached_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    papers = [
        {
            "paper_id": "p1",
            "title": "Bank Efficiency and Ownership",
            "authors": ["Nguyen, An", "Tran, Binh"],
            "year": 2024,
            "journal": "Journal of Banking Research",
            "doi": "10.1016/j.jbankfin.2024.107123",
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "file_reference": ".litreview/cache/fulltext/p1.pdf",
            "file_instances": [{"file_reference": ".litreview/cache/fulltext/p1.pdf", "location_type": "managed"}],
            "file_hash": "abc",
            "full_text_provenance": {"access": "open_access", "provider": "openalex"},
        },
        {
            "paper_id": "p2",
            "title": "Governance Heterogeneity in Vietnamese Banks",
            "authors": ["Le, Chi"],
            "year": 2022,
            "journal": "Finance Review",
            "doi": "10.1234/example.2",
            "abstract": "This study reports ownership heterogeneity in the sample.",
            "triage_label": "relevant",
            "triage_priority": "high",
        },
        {
            "paper_id": "p3",
            "title": "Unused Discovery Record",
            "authors": ["Other, Author"],
            "year": 2020,
            "doi": "10.9999/unused",
            "abstract": "Should not be exported because it is not used by the working draft.",
            "triage_label": "relevant",
            "triage_priority": "medium",
        },
    ]
    _write_jsonl(tmp_path / ".litreview" / "data" / "papers.jsonl", papers)
    (tmp_path / ".litreview" / "data" / "working_draft.json").write_text(
        json.dumps(
            {
                "saved_at": "2026-08-29T10:00:00+00:00",
                "sections": [
                    {
                        "section_id": "s1",
                        "title": "Ownership and governance",
                        "fragments": [{"paper_ids": ["p1", "p2"]}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = prepare_researcher_package(tmp_path, export_word=False)

    assert result["working_reference_count"] == 2
    assert result["working_full_text_count"] == 1
    assert result["working_abstract_only_count"] == 1
    assert (tmp_path / "papers" / "full_text" / "doi_10.1016__j.jbankfin.2024.107123.pdf").is_file()
    assert (tmp_path / "papers" / "abstract_only" / "doi_10.1234__example.2.md").is_file()
    assert not (tmp_path / "papers" / "abstract_only" / "doi_10.9999__unused.md").exists()

    enw = (tmp_path / "references" / "references_used.enw").read_text(encoding="utf-8")
    assert "%T Bank Efficiency and Ownership" in enw
    assert "%A Nguyen, An" in enw
    assert "%R 10.1016/j.jbankfin.2024.107123" in enw
    assert "%T Governance Heterogeneity in Vietnamese Banks" in enw
    assert "Unused Discovery Record" not in enw

    csv_text = (tmp_path / "references" / "references_used.csv").read_text(encoding="utf-8")
    assert "Ownership and governance" in csv_text
    assert "pending" in csv_text
