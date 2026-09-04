import json
from pathlib import Path

from litreview_construct.corpus import (
    rank_corpus,
    record_decision,
    refinement_next_step,
    selection_ids,
    tier_coverage,
)
from litreview_construct.project import init_project


def _write_fixture(root: Path, count: int = 100) -> None:
    init_project(root, name="Corpus Refinement Test")
    state_root = root / ".litreview"
    campaign_id = "campaign-corpus"
    (state_root / "data" / "discovery_campaign.json").write_text(
        json.dumps(
            {
                "campaign_id": campaign_id,
                "status": "complete",
                "selected_focuses": ["stream a"],
                "iterations": [],
                "review_checkpoints": [],
            }
        ),
        encoding="utf-8",
    )
    streams = ["stream a", "stream b", "stream c", "stream d"]
    rows = []
    for index in range(count):
        rows.append(
            {
                "paper_id": f"p{index:03d}",
                "title": f"Paper {index}",
                "authors": [f"Author {index}"],
                "year": 2026 - (index % 12),
                "journal": "Journal of Finance Research",
                "doi": f"10.1000/p{index}",
                "abstract": "Relevant empirical evidence about the research topic. " * 8,
                "citation_count": index * 20,
                "discovery_sources": (
                    ["openalex", "crossref"] if index % 2 == 0 else ["openalex"]
                ),
                "triage_campaign_id": campaign_id,
                "triage_label": "relevant" if index < 60 else "background",
                "triage_priority": (
                    "core_candidate" if index < 20 else "high" if index < 60 else "medium"
                ),
                "triage_confidence": "high" if index < 60 else "medium",
                "triage_stream_tags": [streams[index % len(streams)]],
            }
        )
    (state_root / "data" / "papers.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_refinement_requires_researcher_strategy_at_each_tier(tmp_path: Path) -> None:
    _write_fixture(tmp_path, 100)

    retained = refinement_next_step(tmp_path)
    assert retained["next_action"] == "retained_corpus_checkpoint"
    assert retained["human_checkpoint_required"] is True
    assert retained["records"] == 100

    record_decision(tmp_path, stage="retained", action="refine")
    assert refinement_next_step(tmp_path)["next_action"] == "rank_evidence_candidates"
    evidence = rank_corpus(tmp_path, to_tier="evidence")
    assert evidence["selected_records"] == 45
    assert refinement_next_step(tmp_path)["next_action"] == "evidence_candidate_checkpoint"

    record_decision(tmp_path, stage="evidence", action="refine")
    assert refinement_next_step(tmp_path)["next_action"] == "rank_core_papers"
    core = rank_corpus(tmp_path, to_tier="core")
    assert core["selected_records"] == 19
    assert refinement_next_step(tmp_path)["next_action"] == "core_paper_checkpoint"

    selected = set(selection_ids(tmp_path, "core"))
    source_rows = [
        json.loads(line)
        for line in (tmp_path / ".litreview" / "data" / "papers.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    selected_streams = {
        row["triage_stream_tags"][0] for row in source_rows if row["paper_id"] in selected
    }
    assert selected_streams == {"stream a", "stream b", "stream c", "stream d"}

    record_decision(tmp_path, stage="core", action="continue")
    done = refinement_next_step(tmp_path)
    assert done["next_action"] == "proceed_to_landscape"
    assert done["human_checkpoint_required"] is False


def test_acquire_choice_routes_to_local_python_runtime_pass(tmp_path: Path) -> None:
    _write_fixture(tmp_path, 20)
    record_decision(tmp_path, stage="retained", action="acquire")
    step = refinement_next_step(tmp_path)
    assert step["next_action"] == "acquire_retained_locally"
    assert step["ai_usage"] == "none inside the acquisition runtime"
    assert "--tier retained" in step["commands"][0]
    coverage = tier_coverage(tmp_path, "retained")
    assert coverage["automatic_resolution_pending"] == 20
