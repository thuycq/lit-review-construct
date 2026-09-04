import hashlib
import json
from pathlib import Path

from pypdf import PdfWriter

from litreview_construct import oa_fulltext
from litreview_construct.oa_fulltext import acquire_open_access_full_text
from litreview_construct.project import init_project


def _write_papers(root: Path, rows: list[dict]) -> None:
    path = root / ".litreview" / "data" / "papers.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_acquire_priority_oa_pdf_and_preserve_provenance(tmp_path: Path, monkeypatch) -> None:
    init_project(tmp_path, name="OA Test")
    _write_papers(
        tmp_path,
        [
            {
                "paper_id": "p1",
                "title": "Working capital constraints",
                "doi": "10.1234/example",
                "triage_label": "relevant",
                "triage_priority": "core_candidate",
                "citation_count": 20,
                "year": 2024,
            }
        ],
    )

    monkeypatch.setattr(
        oa_fulltext,
        "_openalex_candidates",
        lambda client, row: (
            [
                {
                    "provider": "openalex",
                    "pdf_url": "https://example.org/paper.pdf",
                    "landing_url": "https://example.org/paper",
                    "version": "publishedVersion",
                    "license": "cc-by",
                    "host_type": "repository",
                }
            ],
            "https://openalex.org/W1",
        ),
    )
    monkeypatch.setattr(oa_fulltext, "_s2_candidates", lambda client, row: ([], None))
    monkeypatch.setattr(oa_fulltext, "_unpaywall_candidates", lambda client, row: [])

    def fake_download(client, url, target, max_bytes):
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=400)
        with target.open("wb") as handle:
            writer.write(handle)
        payload = target.read_bytes()
        return {
            "file_hash": hashlib.sha256(payload).hexdigest(),
            "page_count": 1,
            "parse_status": "ok",
            "parse_error": None,
            "bytes": len(payload),
        }

    monkeypatch.setattr(oa_fulltext, "_download_pdf", fake_download)

    result = acquire_open_access_full_text(tmp_path, max_papers=1)
    assert result["downloaded"] == 1
    assert result["resolved_pdf"] == 1
    assert result["unresolved_or_closed"] == 0

    row = json.loads(
        (tmp_path / ".litreview" / "data" / "papers.jsonl").read_text(encoding="utf-8").strip()
    )
    assert row["openalex_id"] == "https://openalex.org/W1"
    assert row["oa_resolution_status"] == "downloaded"
    assert row["full_text_provenance"]["provider"] == "openalex"
    assert row["full_text_provenance"]["license"] == "cc-by"
    assert (tmp_path / row["file_reference"]).is_file()

    report = json.loads(
        (tmp_path / ".litreview" / "data" / "fulltext_resolution.json").read_text(
            encoding="utf-8"
        )
    )
    assert "does not bypass paywalls" in report["policy_note"]


def test_oa_resolution_keeps_closed_paper_in_project(tmp_path: Path, monkeypatch) -> None:
    init_project(tmp_path, name="OA Closed Test")
    _write_papers(
        tmp_path,
        [
            {
                "paper_id": "p1",
                "title": "Important closed paper",
                "doi": "10.9999/closed",
                "triage_label": "relevant",
                "triage_priority": "core_candidate",
            }
        ],
    )
    monkeypatch.setattr(oa_fulltext, "_openalex_candidates", lambda client, row: ([], None))
    monkeypatch.setattr(oa_fulltext, "_s2_candidates", lambda client, row: ([], None))
    monkeypatch.setattr(oa_fulltext, "_unpaywall_candidates", lambda client, row: [])

    result = acquire_open_access_full_text(tmp_path, max_papers=1)
    assert result["unresolved_or_closed"] == 1
    rows = [
        json.loads(line)
        for line in (tmp_path / ".litreview" / "data" / "papers.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert len(rows) == 1
    assert rows[0]["paper_id"] == "p1"
    assert rows[0]["oa_resolution_status"] == "unresolved_or_closed"
