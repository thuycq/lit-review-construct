import json
from pathlib import Path

import httpx

from litreview_construct import campaign, graph_resilient
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


def _setup(root: Path) -> None:
    init_project(root, name="Graph Resilient Test")
    set_intent(
        root,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    campaign.start_discovery_campaign(root)
    seed = {
        "paper_id": "seed",
        "title": "Working capital seed",
        "normalized_title": "working capital seed",
        "authors": ["A"],
        "year": 2024,
        "doi": "10.1000/seed",
        "openalex_id": None,
        "s2_paper_id": None,
        "journal": "J",
        "language": "en",
        "citation_count": 10,
        "abstract": "Working capital.",
        "source_origin": "crossref",
        "discovery_sources": ["crossref"],
        "status": "relevant",
        "triage_label": "relevant",
        "triage_priority": "core_candidate",
    }
    (root / ".litreview" / "data" / "papers.jsonl").write_text(
        json.dumps(seed) + "\n", encoding="utf-8"
    )


def test_graph_continues_when_openalex_fails(tmp_path: Path, monkeypatch) -> None:
    _setup(tmp_path)

    def fail_openalex(*args, **kwargs):
        request = httpx.Request("GET", "https://api.openalex.org/works")
        response = httpx.Response(403, request=request)
        raise httpx.HTTPStatusError("forbidden", request=request, response=response)

    incoming = {
        "title": "Citing paper",
        "normalized_title": "citing paper",
        "authors": ["B"],
        "year": 2025,
        "doi": "10.1000/citing",
        "openalex_id": None,
        "s2_paper_id": "S2CITING",
        "journal": "J2",
        "language": None,
        "citation_count": 1,
        "publication_type": "JournalArticle",
        "abstract": "Citing working capital evidence.",
        "provider": "semantic_scholar",
    }

    monkeypatch.setattr(graph_resilient, "_expand_openalex_seed", fail_openalex)
    monkeypatch.setattr(
        graph_resilient,
        "_expand_s2_seed",
        lambda *args, **kwargs: (
            [("citations", incoming)],
            {"calls": 1, "resolved": True, "seed_provider_id": "DOI:10.1000/seed"},
        ),
    )

    result = graph_resilient.expand_resilient_citation_graph(
        tmp_path,
        paper_ids=["seed"],
        relation="both",
        max_per_seed_provider=20,
    )
    assert result["new_records"] == 1
    assert result["new_graph_edges"] == 1
    assert result["providers_succeeded"] == ["semantic_scholar"]
    assert result["provider_failures"][0]["provider"] == "openalex"
