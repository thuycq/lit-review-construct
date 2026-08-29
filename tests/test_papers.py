import json
from pathlib import Path

from pypdf import PdfWriter

from litreview_construct.papers import scan_seed_papers
from litreview_construct.project import init_project


def _make_pdf(path: Path, title: str = "Seed Paper") -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": title, "/Author": "Researcher One"})
    with path.open("wb") as handle:
        writer.write(handle)


def test_seed_scan_indexes_pdf_and_creates_inventory(tmp_path: Path) -> None:
    init_project(tmp_path, name="Seed Test")
    pdf = tmp_path / "papers" / "seed.pdf"
    _make_pdf(pdf)

    result = scan_seed_papers(tmp_path)

    assert result["pdfs_detected"] == 1
    assert result["records_total"] == 1
    records_path = tmp_path / ".litreview" / "data" / "papers.jsonl"
    record = json.loads(records_path.read_text(encoding="utf-8").strip())
    assert record["title"] == "Seed Paper"
    assert record["location_type"] == "managed"
    assert record["status"] == "user_seed"
    assert (tmp_path / "outputs" / "02_seed_inventory.md").is_file()


def test_seed_scan_deduplicates_exact_file_hash(tmp_path: Path) -> None:
    init_project(tmp_path)
    first = tmp_path / "papers" / "first.pdf"
    second = tmp_path / "papers" / "second.pdf"
    _make_pdf(first)
    second.write_bytes(first.read_bytes())

    result = scan_seed_papers(tmp_path)

    assert result["pdfs_detected"] == 2
    assert result["records_total"] == 1
    assert result["duplicates_seen"] == 1


def test_external_seed_folder_is_referenced_in_place(tmp_path: Path) -> None:
    project = tmp_path / "project"
    external = tmp_path / "external"
    external.mkdir()
    init_project(project)
    _make_pdf(external / "external.pdf", title="External Paper")

    scan_seed_papers(project, source=external)

    record = json.loads(
        (project / ".litreview" / "data" / "papers.jsonl").read_text(encoding="utf-8").strip()
    )
    assert record["location_type"] == "external"
    assert Path(record["file_reference"]).resolve() == (external / "external.pdf").resolve()
