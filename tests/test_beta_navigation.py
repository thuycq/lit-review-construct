import json
from pathlib import Path

from litreview_construct.navigator import discovery_next_step
from litreview_construct.project import init_project
from litreview_construct.ux import suggested_user_message


def _setup(root: Path, graph_gains: list[int]) -> None:
    init_project(root)
    state_file = root / ".litreview" / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["research_intent"]["status"] = "accepted"
    state["stages"]["seed_literature"]["status"] = "accepted"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    (root / ".litreview" / "data" / "seed_decision.json").write_text(
        json.dumps({"decision": "skip"}), encoding="utf-8"
    )

    iterations = [
        {"phase": "broad", "new_records": 500, "timestamp": "2026-08-29T01:00:00+00:00"},
        {"phase": "focused", "new_records": 1, "timestamp": "2026-08-29T02:00:00+00:00"},
    ]
    for index, gain in enumerate(graph_gains, start=1):
        iterations.append(
            {
                "phase": "citation_expansion",
                "new_records": gain,
                "timestamp": f"2026-08-29T0{index + 2}:00:00+00:00",
            }
        )
    campaign = {
        "campaign_id": "c1",
        "status": "awaiting_researcher",
        "revision": 5,
        "selected_focuses": ["Ownership-governance heterogeneity"],
        "iterations": iterations,
        "review_checkpoints": [],
    }
    (root / ".litreview" / "data" / "discovery_campaign.json").write_text(
        json.dumps(campaign), encoding="utf-8"
    )

    paper_lines = []
    for i in range(10):
        paper_lines.append(
            json.dumps(
                {
                    "paper_id": f"core-{i}",
                    "triage_campaign_id": "c1",
                    "triage_label": "relevant",
                    "triage_priority": "core_candidate",
                }
            )
        )
    # These are relevant but are not core candidates; beta metric must not conflate them.
    for i in range(20):
        paper_lines.append(
            json.dumps(
                {
                    "paper_id": f"high-{i}",
                    "triage_campaign_id": "c1",
                    "triage_label": "relevant",
                    "triage_priority": "high",
                }
            )
        )
    paper_lines.append('{"paper_id":"broken","title":"unterminated')
    for i in range(200):
        paper_lines.append(json.dumps({"paper_id": f"u-{i}"}))
    (root / ".litreview" / "data" / "papers.jsonl").write_text(
        "\n".join(paper_lines) + "\n", encoding="utf-8"
    )


def test_saturated_focused_search_auto_refines_without_human_click(tmp_path: Path) -> None:
    _setup(tmp_path, [200])
    result = discovery_next_step(tmp_path)
    assert result["next_action"] == "refine"
    assert result["human_checkpoint_required"] is False
    assert result["core_candidates"] == 10
    assert result["relevant_records"] == 30
    assert result["citation_expansion_rounds"] == 1


def test_three_refinement_rounds_stop_and_recommend_finish(tmp_path: Path) -> None:
    _setup(tmp_path, [336, 388, 166])
    result = discovery_next_step(tmp_path)
    assert result["next_action"] == "researcher_decision_required"
    assert result["human_checkpoint_required"] is True
    assert result["discovery_saturated"] is True
    assert result["recommended_option"] == "finish"
    suggestion = suggested_user_message(result)
    assert "Finish discovery" in suggestion
    assert "lrc " not in suggestion


def test_low_graph_gain_stops_before_three_rounds(tmp_path: Path) -> None:
    _setup(tmp_path, [40])
    result = discovery_next_step(tmp_path)
    assert result["next_action"] == "researcher_decision_required"
    assert result["discovery_saturated"] is True
