import json
from pathlib import Path

import pytest

from litreview_construct.corpus import rank_corpus, record_decision
from litreview_construct.finalize import prepare_final_landscape_packet
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


def _setup(root: Path) -> None:
    init_project(root, name="Finalize Test")
    set_intent(
        root,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    campaign = {
        "campaign_id": "campaign-1",
        "status": "collecting",
        "iterations": [{"iteration_id": "i1"}],
        "review_checkpoints": [],
        "selected_focuses": ["Nonlinear working capital"],
    }
    (root / ".litreview" / "data" / "discovery_campaign.json").write_text(
        json.dumps(campaign), encoding="utf-8"
    )
    papers = [
        {
            "paper_id": "relevant",
            "title": "Nonlinear working capital and performance",
            "authors": ["A"],
            "year": 2024,
            "journal": "J",
            "doi": "10.1/a",
            "citation_count": 10,
            "abstract": "Working capital has a nonlinear relationship with firm performance.",
            "source_origin": "openalex",
            "discovery_sources": ["openalex", "crossref"],
            "triage_campaign_id": "campaign-1",
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "triage_rationale": "Directly relevant.",
            "triage_stream_tags": ["Nonlinear working capital"],
            "triage_confidence": "high",
        },
        {
            "paper_id": "background",
            "title": "Working capital foundations",
            "authors": ["B"],
            "year": 2022,
            "journal": "J",
            "citation_count": 20,
            "abstract": "Background working capital literature.",
            "source_origin": "semantic_scholar",
            "discovery_sources": ["semantic_scholar"],
            "triage_campaign_id": "campaign-1",
            "triage_label": "background",
            "triage_priority": "medium",
            "triage_rationale": "Useful background.",
            "triage_stream_tags": ["working capital"],
            "triage_confidence": "high",
        },
        {
            "paper_id": "noise",
            "title": "Gold sentiment",
            "authors": ["C"],
            "year": 2024,
            "journal": "J",
            "citation_count": 100,
            "abstract": "Gold sentiment.",
            "source_origin": "crossref",
            "discovery_sources": ["crossref"],
            "triage_campaign_id": "campaign-1",
            "triage_label": "out_of_scope",
            "triage_priority": "low",
            "triage_rationale": "Outside scope.",
            "triage_stream_tags": [],
            "triage_confidence": "high",
        },
    ]
    (root / ".litreview" / "data" / "papers.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in papers), encoding="utf-8"
    )


def test_final_landscape_requires_researcher_finished_campaign_and_core_selection(
    tmp_path: Path,
) -> None:
    _setup(tmp_path)
    with pytest.raises(ValueError, match="not complete"):
        prepare_final_landscape_packet(tmp_path, max_papers=20)

    campaign_file = tmp_path / ".litreview" / "data" / "discovery_campaign.json"
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    campaign["status"] = "complete"
    campaign_file.write_text(json.dumps(campaign), encoding="utf-8")

    with pytest.raises(ValueError, match="Core Papers have not been selected"):
        prepare_final_landscape_packet(tmp_path, max_papers=20)

    record_decision(tmp_path, stage="retained", action="refine")
    rank_corpus(tmp_path, to_tier="evidence")
    record_decision(tmp_path, stage="evidence", action="refine")
    rank_corpus(tmp_path, to_tier="core")
    record_decision(tmp_path, stage="core", action="continue")

    result = prepare_final_landscape_packet(tmp_path, max_papers=20)
    packet = json.loads(Path(result["packet_file"]).read_text(encoding="utf-8"))
    ids = {row["paper_id"] for row in packet["papers"]}
    assert ids == {"relevant", "background"}
    assert packet["discovery_context"]["out_of_scope_excluded"] == 1
