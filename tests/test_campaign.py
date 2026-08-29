import json
from pathlib import Path

from litreview_construct import campaign
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


def _provider_record(provider: str, title: str, doi: str | None, *, citations: int = 0):
    return {
        "title": title,
        "normalized_title": title.lower(),
        "authors": ["Researcher One"],
        "year": 2024,
        "doi": doi,
        "openalex_id": "https://openalex.org/W1" if provider == "openalex" else None,
        "s2_paper_id": "S2-2" if provider == "semantic_scholar" else None,
        "journal": "Journal",
        "language": "en" if provider != "semantic_scholar" else None,
        "citation_count": citations,
        "publication_type": "article",
        "abstract": "Working capital management is associated with firm performance.",
        "provider": provider,
    }


def _init(tmp_path: Path) -> Path:
    init_project(tmp_path, name="Campaign Test")
    set_intent(
        tmp_path,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(tmp_path)
    return tmp_path


def test_multi_source_iteration_merges_strong_identifier_matches(tmp_path: Path, monkeypatch) -> None:
    root = _init(tmp_path)
    shared_doi = "10.1000/shared"

    monkeypatch.setattr(
        campaign,
        "_search_openalex",
        lambda *args, **kwargs: ([_provider_record("openalex", "Shared Paper", shared_doi, citations=10)], {"calls": 1}),
    )
    monkeypatch.setattr(
        campaign,
        "_search_crossref",
        lambda *args, **kwargs: ([_provider_record("crossref", "Shared Paper", shared_doi, citations=12)], {"calls": 1}),
    )
    monkeypatch.setattr(
        campaign,
        "_search_semantic_scholar",
        lambda *args, **kwargs: ([_provider_record("semantic_scholar", "Second Paper", "10.1000/second", citations=5)], {"calls": 1}),
    )

    campaign.start_discovery_campaign(root)
    result = campaign.run_discovery_iteration(
        root,
        ["working capital firm performance"],
        max_per_query_provider=50,
    )

    assert result["raw_results"] == 3
    assert result["new_records"] == 2
    assert result["existing_records_enriched"] == 1

    rows = [
        json.loads(line)
        for line in (root / ".litreview" / "data" / "papers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 2
    shared = next(row for row in rows if row["doi"] == shared_doi)
    assert set(shared["discovery_sources"]) == {"openalex", "crossref"}
    assert shared["citation_count"] == 12


def test_discovery_review_requires_researcher_decision(tmp_path: Path, monkeypatch) -> None:
    root = _init(tmp_path)
    monkeypatch.setattr(
        campaign,
        "_search_openalex",
        lambda *args, **kwargs: ([_provider_record("openalex", "Paper A", "10.1000/a")], {"calls": 1}),
    )
    monkeypatch.setattr(
        campaign,
        "_search_crossref",
        lambda *args, **kwargs: ([_provider_record("crossref", "Paper B", "10.1000/b")], {"calls": 1}),
    )
    monkeypatch.setattr(
        campaign,
        "_search_semantic_scholar",
        lambda *args, **kwargs: ([_provider_record("semantic_scholar", "Paper C", "10.1000/c")], {"calls": 1}),
    )

    campaign.start_discovery_campaign(root)
    campaign.run_discovery_iteration(root, ["working capital", "cash conversion cycle"], max_per_query_provider=50)
    packet = campaign.prepare_discovery_review(root)
    packet_data = json.loads(Path(packet["packet_file"]).read_text(encoding="utf-8"))
    ids = [row["paper_id"] for row in packet_data["representative_papers"]]

    review = {
        "summary": "The broad corpus contains several provisional working-capital streams.",
        "provisional_streams": [
            {
                "name": "Working-capital efficiency",
                "description": "Studies connecting working-capital policy and firm outcomes.",
                "representative_paper_ids": ids[:2],
                "indicative_terms": ["working capital", "cash conversion cycle"],
                "provisional_questions": ["Are nonlinear effects important?"],
                "confidence": "medium",
            }
        ],
        "candidate_focuses": [
            {
                "name": "Nonlinear optimization",
                "rationale": "A plausible focus for the next retrieval iteration.",
                "representative_paper_ids": ids[:1],
                "query_suggestions": ["optimal working capital firm performance"],
                "why_promising": ["Connects efficiency and performance"],
                "risks": ["Requires broader verification"],
            }
        ],
        "coverage_observations": ["Multiple providers have been used."],
        "recommended_next_actions": ["Run a focused iteration."],
        "limitations": ["This is not a final gap assessment."],
    }
    submission = root / "review.json"
    submission.write_text(json.dumps(review), encoding="utf-8")
    saved = campaign.save_discovery_review(root, submission)
    assert saved["status"] == "awaiting_researcher"

    focused = campaign.record_discovery_decision(
        root,
        action="focus",
        selected_focuses=["Nonlinear optimization"],
    )
    assert focused["status"] == "focused"


def test_discovery_status_warns_when_coverage_is_thin(tmp_path: Path) -> None:
    root = _init(tmp_path)
    campaign.start_discovery_campaign(root)
    status = campaign.discovery_status(root)
    assert status["status"] == "collecting"
    assert status["warnings"]
