import json
import shutil
from pathlib import Path

from pypdf import PdfWriter

from litreview_construct.papers import scan_seed_papers
from litreview_construct.project import init_project


def _make_pdf(path: Path, *, title: str, author: str, doi: str) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata(
        {
            "/Title": title,
            "/Author": author,
            "/Subject": f"DOI: {doi}",
        }
    )
    with path.open("wb") as handle:
        writer.write(handle)


def test_seed_scan_extracts_doi_and_collapses_exact_file_duplicates(tmp_path: Path) -> None:
    init_project(tmp_path, name="Seed Test")
    paper = tmp_path / "papers" / "paper.pdf"
    duplicate = tmp_path / "papers" / "paper-copy.pdf"
    _make_pdf(
        paper,
        title="Working Capital and Firm Performance",
        author="Anh Nguyen",
        doi="10.1234/Test.1",
    )
    shutil.copyfile(paper, duplicate)

    result = scan_seed_papers(tmp_path)

    assert result["pdfs_detected"] == 2
    assert result["records_total"] == 1
    assert result["duplicate_files"] == 1

    records_path = tmp_path / ".litreview" / "data" / "papers.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["doi"] == "10.1234/test.1"
    assert len(records[0]["file_instances"]) == 2

    inventory = (tmp_path / "outputs" / "02_seed_inventory.md").read_text(encoding="utf-8")
    assert "Working Capital and Firm Performance" in inventory
    assert "10.1234/test.1" in inventory
