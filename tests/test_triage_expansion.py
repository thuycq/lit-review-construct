import json
from pathlib import Path

from litreview_construct import expansion, triage
from litreview_construct.campaign import start_discovery_campaign
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


def _init(tmp_path: Path) -> Path:
    init_project(tmp_path, name="Discovery Funnel Test")
    set_intent(
        tmp_path,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(tmp_path)
    start_discovery_campaign(tmp_path)
    return tmp_path


def _paper(paper_id: str, title: str, *, doi: str | None = None, status: str = "unresolved") -> dict:
    return {
        "paper_id": paper_id,
        "title": title,
        "normalized_title": title.lower(),
        "authors": ["Researcher"],
        "year": 2024,
        "doi": doi,
        "openalex_id": None,
        "s2_paper_id": None,
        "journal": "Journal",
        "language": "en",
        "citation_count": 5,
        "publication_type": "article",
        "abstract": "This paper studies working capital management and firm performance.",
        "source_origin": "openalex",
        "discovery_sources": ["openalex"],
        "status": status,
        "location_type": "metadata_only",
        "file_reference": None,
        "file_instances": [],
        "file_hash": None,
        "parse_status": "metadata_only",
    }


def _write_papers(root: Path, rows: list[dict]) -> None:
    path = root / ".litreview" / "data" / "papers.jsonl"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_triage_batch_requires_complete_packet_and_persists_labels(tmp_path: Path) -> None:
    root = _init(tmp_path)
    campaign_file = root / ".litreview" / "data" / "discovery_campaign.json"
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    campaign["iterations"] = [{"iteration_id": "i1", "queries": ["working capital"], "providers": ["openalex"]}]
    campaign_file.write_text(json.dumps(campaign), encoding="utf-8")
    _write_papers(
        root,
        [
            _paper("p1", "Working capital and profitability"),
            _paper("p2", "Cash conversion cycle and performance"),
            _paper("p3", "Gold price sentiment and returns"),
        ],
    )

    prepared = triage.prepare_triage_batch(root, batch_size=20)
    packet = json.loads(Path(prepared["packet_file"]).read_text(encoding="utf-8"))
    ids = [row["paper_id"] for row in packet["papers"]]
    assert set(ids) == {"p1", "p2", "p3"}

    submission = {
        "batch_summary": "Two papers are directly relevant and one is out of scope.",
        "items": [
            {
                "paper_id": paper_id,
                "label": "out_of_scope" if paper_id == "p3" else "relevant",
                "priority": "low" if paper_id == "p3" else "high",
                "rationale": "Classified from title and abstract.",
                "stream_tags": ["working capital"] if paper_id != "p3" else [],
                "key_terms": ["working capital"] if paper_id != "p3" else ["gold"],
                "confidence": "high",
            }
            for paper_id in ids
        ],
        "emerging_terms": ["cash conversion cycle"],
        "emerging_streams": ["working-capital efficiency"],
        "notes": [],
    }
    submission_file = root / "triage_submission.json"
    submission_file.write_text(json.dumps(submission), encoding="utf-8")
    saved = triage.save_triage_batch(root, submission_file)
    assert saved["triaged_total"] == 3
    assert saved["remaining"] == 0
    status = triage.triage_status(root)
    assert status["labels"]["relevant"] == 2
    assert status["labels"]["out_of_scope"] == 1

    review = triage.prepare_narrowing_review(root, max_papers=20)
    review_packet = json.loads(Path(review["packet_file"]).read_text(encoding="utf-8"))
    retained_ids = {row["paper_id"] for row in review_packet["representative_papers"]}
    assert retained_ids == {"p1", "p2"}


def test_citation_expansion_imports_graph_records_and_edges(tmp_path: Path, monkeypatch) -> None:
    root = _init(tmp_path)
    _write_papers(root, [_paper("seed", "Working capital seed", doi="10.1000/seed")])

    incoming_openalex = {
        "title": "Referenced working capital paper",
        "normalized_title": "referenced working capital paper",
        "authors": ["Author A"],
        "year": 2023,
        "doi": "10.1000/ref",
        "openalex_id": "https://openalex.org/WREF",
        "s2_paper_id": None,
        "journal": "Journal A",
        "language": "en",
        "citation_count": 10,
        "publication_type": "article",
        "abstract": "Working capital evidence.",
        "provider": "openalex",
    }
    incoming_s2 = {
        "title": "Citing working capital paper",
        "normalized_title": "citing working capital paper",
        "authors": ["Author B"],
        "year": 2025,
        "doi": "10.1000/cite",
        "openalex_id": None,
        "s2_paper_id": "S2CITE",
        "journal": "Journal B",
        "language": None,
        "citation_count": 3,
        "publication_type": "JournalArticle",
        "abstract": "A citing study.",
        "provider": "semantic_scholar",
    }

    monkeypatch.setattr(
        expansion,
        "_expand_openalex_seed",
        lambda *args, **kwargs: ([('references', incoming_openalex)], {"calls": 1, "resolved": True, "seed_provider_id": "WSEED"}),
    )
    monkeypatch.setattr(
        expansion,
        "_expand_s2_seed",
        lambda *args, **kwargs: ([('citations', incoming_s2)], {"calls": 1, "resolved": True, "seed_provider_id": "DOI:10.1000/seed"}),
    )

    result = expansion.expand_citation_graph(
        root,
        paper_ids=["seed"],
        relation="both",
        max_per_seed_provider=20,
    )
    assert result["new_records"] == 2
    assert result["new_graph_edges"] == 2
    rows = [
        json.loads(line)
        for line in (root / ".litreview" / "data" / "papers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 3
    edges = [
        json.loads(line)
        for line in (root / ".litreview" / "data" / "paper_graph.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert {edge["relation"] for edge in edges} == {"references", "citations"}
