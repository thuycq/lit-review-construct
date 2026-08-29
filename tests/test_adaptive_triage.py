import json
from pathlib import Path

from typer.testing import CliRunner

from litreview_construct.campaign import start_discovery_campaign
from litreview_construct.entrypoint import app
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.navigator import discovery_next_step
from litreview_construct.project import init_project


runner = CliRunner()


def _accepted(root: Path) -> tuple[Path, str]:
    init_project(root, name="Adaptive Triage Test")
    set_intent(
        root,
        topic="working capital management and firm performance",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    start_discovery_campaign(root)
    campaign_path = root / ".litreview" / "data" / "discovery_campaign.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    return campaign_path, str(campaign["campaign_id"])


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_one_priority_batch_after_retrieval_returns_to_narrowing_review(tmp_path: Path) -> None:
    campaign_path, campaign_id = _accepted(tmp_path)
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    campaign["revision"] = 2
    campaign["status"] = "focused"
    campaign["selected_focuses"] = ["Dynamic nonlinear working-capital optimization"]
    campaign["iterations"] = [
        {
            "iteration_id": "broad-1",
            "timestamp": "2026-08-29T01:00:00+00:00",
            "phase": "broad",
            "queries": ["working capital firm performance"],
        },
        {
            "iteration_id": "focused-1",
            "timestamp": "2026-08-29T02:10:00+00:00",
            "phase": "focused",
            "queries": ["nonlinear working capital optimization"],
        },
    ]
    campaign["review_checkpoints"] = [
        {
            "checkpoint_id": "c1",
            "iteration_revision": 1,
            "decision": {
                "action": "focus",
                "timestamp": "2026-08-29T02:00:00+00:00",
                "selected_focuses": ["Dynamic nonlinear working-capital optimization"],
            },
        }
    ]
    campaign_path.write_text(json.dumps(campaign), encoding="utf-8")

    papers = [
        {
            "paper_id": "p1",
            "title": "Top focused candidate",
            "triage_campaign_id": campaign_id,
            "triage_label": "relevant",
        },
        {"paper_id": "p2", "title": "Still untriaged"},
        {"paper_id": "p3", "title": "Also untriaged"},
    ]
    _write_jsonl(tmp_path / ".litreview" / "data" / "papers.jsonl", papers)
    _write_jsonl(
        tmp_path / ".litreview" / "data" / "triage_runs.jsonl",
        [
            {
                "triage_run_id": "t1",
                "campaign_id": campaign_id,
                "timestamp": "2026-08-29T02:20:00+00:00",
                "paper_ids": ["p1"],
            }
        ],
    )

    step = discovery_next_step(tmp_path)
    assert step["next_action"] == "prepare_narrowing_review"
    assert step["triaged_records"] == 1
    assert step["untriaged_records"] == 2
    assert "exhaustive triage is not required" in step["reason"]


def test_filter_decision_requests_one_more_batch_then_returns_to_checkpoint(tmp_path: Path) -> None:
    campaign_path, campaign_id = _accepted(tmp_path)
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    campaign["revision"] = 1
    campaign["status"] = "awaiting_researcher"
    campaign["selected_focuses"] = ["Governance and managerial drivers"]
    campaign["iterations"] = [
        {
            "iteration_id": "broad-1",
            "timestamp": "2026-08-29T01:00:00+00:00",
            "phase": "broad",
            "queries": ["working capital governance"],
        }
    ]
    campaign["review_checkpoints"] = [
        {
            "checkpoint_id": "c1",
            "timestamp": "2026-08-29T02:00:00+00:00",
            "iteration_revision": 1,
            "decision": None,
        }
    ]
    campaign_path.write_text(json.dumps(campaign), encoding="utf-8")
    _write_jsonl(
        tmp_path / ".litreview" / "data" / "papers.jsonl",
        [
            {
                "paper_id": "p1",
                "title": "Already triaged",
                "triage_campaign_id": campaign_id,
                "triage_label": "relevant",
            },
            {"paper_id": "p2", "title": "Next batch"},
            {"paper_id": "p3", "title": "Later batch"},
        ],
    )

    result = runner.invoke(app, ["discover", "filter", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "filter"
    assert payload["selected_focuses"] == ["Governance and managerial drivers"]

    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    decision_at = campaign["review_checkpoints"][-1]["decision"]["timestamp"]
    step = discovery_next_step(tmp_path)
    assert step["next_action"] == "continue_triage"

    _write_jsonl(
        tmp_path / ".litreview" / "data" / "triage_runs.jsonl",
        [
            {
                "triage_run_id": "t2",
                "campaign_id": campaign_id,
                "timestamp": decision_at.replace("+00:00", "+00:00") + "1",
                "paper_ids": ["p2"],
            }
        ],
    )
    papers_path = tmp_path / ".litreview" / "data" / "papers.jsonl"
    papers = [json.loads(line) for line in papers_path.read_text(encoding="utf-8").splitlines() if line]
    papers[1]["triage_campaign_id"] = campaign_id
    papers[1]["triage_label"] = "adjacent"
    _write_jsonl(papers_path, papers)

    step = discovery_next_step(tmp_path)
    assert step["next_action"] == "prepare_narrowing_review"
    assert step["untriaged_records"] == 1
