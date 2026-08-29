import json
from pathlib import Path

from litreview_construct.campaign import start_discovery_campaign
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.navigator import discovery_next_step
from litreview_construct.project import init_project


def _accepted(root: Path) -> Path:
    init_project(root, name="Navigator Test")
    set_intent(
        root,
        topic="working capital management and firm performance",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    return root


def _campaign(root: Path) -> tuple[Path, dict]:
    path = root / ".litreview" / "data" / "discovery_campaign.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def _save_campaign(path: Path, campaign: dict) -> None:
    path.write_text(json.dumps(campaign), encoding="utf-8")


def _write_papers(root: Path, rows: list[dict]) -> None:
    path = root / ".litreview" / "data" / "papers.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_navigator_starts_discovery_after_accepted_intent(tmp_path: Path) -> None:
    root = _accepted(tmp_path)
    result = discovery_next_step(root)
    assert result["next_action"] == "start_discovery"
    assert result["human_checkpoint_required"] is False


def test_navigator_moves_from_query_plan_to_early_review(tmp_path: Path) -> None:
    root = _accepted(tmp_path)
    start_discovery_campaign(root)

    assert discovery_next_step(root)["next_action"] == "prepare_broad_query_plan"

    plan = {
        "plan_id": "plan-1",
        "phase": "broad",
        "saved_at": "2026-08-29T01:00:00+00:00",
        "query_families": [{"query": "working capital firm performance"}],
    }
    (root / ".litreview" / "data" / "discovery_query_plan.json").write_text(
        json.dumps(plan), encoding="utf-8"
    )
    assert discovery_next_step(root)["next_action"] == "run_saved_query_plan"

    campaign_path, campaign = _campaign(root)
    campaign["revision"] = 1
    campaign["iterations"] = [
        {
            "iteration_id": "broad-1",
            "phase": "broad",
            "queries": ["working capital firm performance"],
            "providers": ["openalex", "crossref"],
        }
    ]
    _save_campaign(campaign_path, campaign)
    _write_papers(root, [{"paper_id": "p1", "title": "Working capital and performance"}])

    result = discovery_next_step(root)
    assert result["next_action"] == "prepare_early_review"
    assert result["human_checkpoint_required"] is False


def test_navigator_stops_for_researcher_and_then_runs_new_focused_plan(tmp_path: Path) -> None:
    root = _accepted(tmp_path)
    start_discovery_campaign(root)
    campaign_path, campaign = _campaign(root)
    campaign["revision"] = 1
    campaign["iterations"] = [
        {
            "iteration_id": "broad-1",
            "phase": "broad",
            "queries": ["working capital firm performance"],
            "providers": ["openalex", "crossref"],
        }
    ]
    campaign["status"] = "awaiting_researcher"
    campaign["review_checkpoints"] = [
        {
            "checkpoint_id": "c1",
            "iteration_revision": 1,
            "decision": None,
        }
    ]
    _save_campaign(campaign_path, campaign)

    waiting = discovery_next_step(root)
    assert waiting["next_action"] == "researcher_decision_required"
    assert waiting["human_checkpoint_required"] is True

    campaign["status"] = "focused"
    campaign["selected_focuses"] = ["Nonlinear working-capital optimization"]
    campaign["review_checkpoints"][0]["decision"] = {
        "action": "focus",
        "timestamp": "2026-08-29T02:00:00+00:00",
        "selected_focuses": ["Nonlinear working-capital optimization"],
    }
    _save_campaign(campaign_path, campaign)

    assert discovery_next_step(root)["next_action"] == "prepare_focused_query_plan"

    focused_plan = {
        "plan_id": "plan-focused",
        "phase": "focused",
        "saved_at": "2026-08-29T02:05:00+00:00",
        "query_families": [{"query": "nonlinear working capital firm value"}],
    }
    (root / ".litreview" / "data" / "discovery_query_plan.json").write_text(
        json.dumps(focused_plan), encoding="utf-8"
    )
    result = discovery_next_step(root)
    assert result["next_action"] == "run_saved_query_plan"
    assert result["selected_focuses"] == ["Nonlinear working-capital optimization"]


def test_navigator_routes_new_focused_results_through_triage_and_review(tmp_path: Path) -> None:
    root = _accepted(tmp_path)
    start_discovery_campaign(root)
    campaign_path, campaign = _campaign(root)
    campaign_id = campaign["campaign_id"]
    campaign["revision"] = 2
    campaign["status"] = "focused"
    campaign["selected_focuses"] = ["Nonlinear working-capital optimization"]
    campaign["iterations"] = [
        {"iteration_id": "broad-1", "phase": "broad", "queries": ["working capital"]},
        {"iteration_id": "focused-1", "phase": "focused", "queries": ["nonlinear working capital"]},
    ]
    campaign["review_checkpoints"] = [
        {
            "checkpoint_id": "c1",
            "iteration_revision": 1,
            "decision": {
                "action": "focus",
                "timestamp": "2026-08-29T02:00:00+00:00",
                "selected_focuses": ["Nonlinear working-capital optimization"],
            },
        }
    ]
    _save_campaign(campaign_path, campaign)
    _write_papers(
        root,
        [
            {
                "paper_id": "p1",
                "title": "Working capital and performance",
                "triage_campaign_id": campaign_id,
                "triage_label": "relevant",
            },
            {"paper_id": "p2", "title": "New focused paper"},
        ],
    )

    triage = discovery_next_step(root)
    assert triage["next_action"] == "continue_triage"
    assert triage["untriaged_records"] == 1

    _write_papers(
        root,
        [
            {
                "paper_id": "p1",
                "title": "Working capital and performance",
                "triage_campaign_id": campaign_id,
                "triage_label": "relevant",
            },
            {
                "paper_id": "p2",
                "title": "New focused paper",
                "triage_campaign_id": campaign_id,
                "triage_label": "adjacent",
            },
        ],
    )
    review = discovery_next_step(root)
    assert review["next_action"] == "prepare_narrowing_review"
    assert review["untriaged_records"] == 0


def test_navigator_routes_completed_campaign_to_final_landscape(tmp_path: Path) -> None:
    root = _accepted(tmp_path)
    start_discovery_campaign(root)
    campaign_path, campaign = _campaign(root)
    campaign["status"] = "complete"
    _save_campaign(campaign_path, campaign)

    result = discovery_next_step(root)
    assert result["next_action"] == "prepare_final_landscape"
    assert result["human_checkpoint_required"] is False
