import json
from pathlib import Path

from typer.testing import CliRunner

from litreview_construct.campaign import start_discovery_campaign
from litreview_construct.entrypoint import app
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project
from litreview_construct.readiness import assess_discovery_readiness


runner = CliRunner()


def _init(root: Path) -> tuple[Path, str]:
    init_project(root, name="Discovery Readiness Test")
    set_intent(
        root,
        topic="working capital management and firm performance",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    start_discovery_campaign(root)
    campaign_file = root / ".litreview" / "data" / "discovery_campaign.json"
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    return root, campaign["campaign_id"]


def _write_fixture_state(root: Path, campaign_id: str) -> None:
    campaign_file = root / ".litreview" / "data" / "discovery_campaign.json"
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    campaign["status"] = "awaiting_researcher"
    campaign["selected_focuses"] = ["Nonlinear working-capital optimization"]
    campaign["iterations"] = [
        {
            "iteration_id": "broad-1",
            "phase": "broad",
            "queries": ["working capital firm performance", "cash conversion cycle profitability"],
            "providers": ["openalex", "crossref", "semantic_scholar"],
            "provider_runs": [
                {
                    "provider": "openalex",
                    "query": "working capital firm performance",
                    "status": "success",
                },
                {
                    "provider": "crossref",
                    "query": "working capital firm performance",
                    "status": "success",
                },
                {
                    "provider": "semantic_scholar",
                    "query": "cash conversion cycle profitability",
                    "status": "success",
                },
            ],
        },
        {
            "iteration_id": "focused-1",
            "phase": "focused",
            "queries": ["nonlinear working capital firm value"],
            "providers": ["openalex", "crossref"],
            "provider_runs": [
                {
                    "provider": "openalex",
                    "query": "nonlinear working capital firm value",
                    "status": "success",
                },
                {
                    "provider": "crossref",
                    "query": "nonlinear working capital firm value",
                    "status": "failed",
                },
            ],
        },
    ]
    campaign["review_checkpoints"] = [
        {
            "checkpoint_id": "checkpoint-1",
            "timestamp": "2026-08-29T00:00:00+00:00",
            "iteration_revision": 2,
            "review_file": ".litreview/data/discovery_review.json",
            "decision": None,
        }
    ]
    campaign_file.write_text(json.dumps(campaign), encoding="utf-8")

    papers = [
        {
            "paper_id": "p1",
            "title": "Working capital and firm performance",
            "triage_campaign_id": campaign_id,
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
        },
        {
            "paper_id": "p2",
            "title": "Cash conversion cycle and profitability",
            "triage_campaign_id": campaign_id,
            "triage_label": "background",
            "triage_priority": "medium",
        },
        {
            "paper_id": "p3",
            "title": "Unclear liquidity paper",
            "triage_campaign_id": campaign_id,
            "triage_label": "unresolved",
            "triage_priority": "low",
        },
        {
            "paper_id": "p4",
            "title": "Newly retrieved paper not yet triaged",
        },
    ]
    papers_file = root / ".litreview" / "data" / "papers.jsonl"
    papers_file.write_text(
        "".join(json.dumps(row) + "\n" for row in papers),
        encoding="utf-8",
    )

    plans = root / ".litreview" / "data" / "discovery_query_plans.jsonl"
    plans.write_text(
        json.dumps({"plan_id": "plan-1", "phase": "broad"}) + "\n",
        encoding="utf-8",
    )


def test_readiness_is_diagnostic_not_numeric_sufficiency(tmp_path: Path) -> None:
    root, campaign_id = _init(tmp_path)
    _write_fixture_state(root, campaign_id)

    readiness = assess_discovery_readiness(root)

    assert readiness["successful_provider_count"] == 3
    assert readiness["successful_query_family_count"] == 3
    assert readiness["saved_query_plans"] == 1
    assert readiness["review_checkpoints"] == 1
    assert readiness["focused_iterations"] == 1
    assert readiness["triaged_records"] == 3
    assert readiness["untriaged_records"] == 1
    assert readiness["unresolved_records"] == 1
    assert readiness["retained_records"] == 2
    assert readiness["advisory_only"] is True
    assert readiness["warnings"]
    assert "score" not in readiness


def test_finish_via_cli_persists_coverage_snapshot(tmp_path: Path) -> None:
    root, campaign_id = _init(tmp_path)
    _write_fixture_state(root, campaign_id)

    ready = runner.invoke(app, ["discover", "readiness", str(root), "--json"])
    assert ready.exit_code == 0
    payload = json.loads(ready.stdout)
    assert payload["untriaged_records"] == 1

    result = runner.invoke(
        app,
        ["discover", "decide", str(root), "--action", "finish", "--json"],
    )
    assert result.exit_code == 0
    decision = json.loads(result.stdout)
    assert decision["status"] == "complete"
    assert decision["coverage_snapshot"]["untriaged_records"] == 1

    campaign = json.loads(
        (root / ".litreview" / "data" / "discovery_campaign.json").read_text(encoding="utf-8")
    )
    assert campaign["completion_assessment"]["advisory_only"] is True
    assert campaign["researcher_completion"]["coverage_snapshot"]["unresolved_records"] == 1
