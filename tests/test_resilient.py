import json
from pathlib import Path

import httpx

from litreview_construct import campaign, resilient
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


def _record(provider: str, title: str, doi: str) -> dict:
    return {
        "title": title,
        "normalized_title": title.lower(),
        "authors": ["Researcher"],
        "year": 2024,
        "doi": doi,
        "openalex_id": None,
        "s2_paper_id": None,
        "journal": "Journal",
        "language": "en",
        "citation_count": 1,
        "publication_type": "article",
        "abstract": "Working capital and firm performance.",
        "provider": provider,
    }


def _init(tmp_path: Path) -> Path:
    init_project(tmp_path, name="Resilient Test")
    set_intent(
        tmp_path,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(tmp_path)
    campaign.start_discovery_campaign(tmp_path)
    return tmp_path


def test_one_provider_failure_does_not_discard_other_sources(tmp_path: Path, monkeypatch) -> None:
    root = _init(tmp_path)

    def fail_openalex(*args, **kwargs):
        request = httpx.Request("GET", "https://api.openalex.org/works")
        response = httpx.Response(403, request=request)
        raise httpx.HTTPStatusError("forbidden", request=request, response=response)

    monkeypatch.setattr(resilient, "_search_openalex", fail_openalex)
    monkeypatch.setattr(
        resilient,
        "_search_crossref",
        lambda *args, **kwargs: ([_record("crossref", "Crossref paper", "10.1000/crossref")], {"calls": 1}),
    )
    monkeypatch.setattr(
        resilient,
        "_search_semantic_scholar",
        lambda *args, **kwargs: ([_record("semantic_scholar", "S2 paper", "10.1000/s2")], {"calls": 1}),
    )

    result = resilient.run_resilient_discovery_iteration(
        root,
        ["working capital", "cash conversion cycle"],
        max_per_query_provider=20,
    )

    assert "crossref" in result["providers_succeeded"]
    assert "semantic_scholar" in result["providers_succeeded"]
    assert result["provider_failures"][0]["provider"] == "openalex"
    assert result["provider_failures"][0]["error_type"] == "authentication_or_access"
    # OpenAlex should be skipped for the second query after an auth/access failure.
    campaign_data = json.loads(
        (root / ".litreview" / "data" / "discovery_campaign.json").read_text(encoding="utf-8")
    )
    latest = campaign_data["iterations"][-1]
    skipped = [
        row
        for row in latest["provider_runs"]
        if row["provider"] == "openalex" and row["status"] == "skipped_after_failure"
    ]
    assert skipped
    papers = [
        json.loads(line)
        for line in (root / ".litreview" / "data" / "papers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert {row["doi"] for row in papers} == {"10.1000/crossref", "10.1000/s2"}
