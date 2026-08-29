import json
from pathlib import Path

from typer.testing import CliRunner

from litreview_construct.entrypoint import app
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


runner = CliRunner()


def test_extended_discovery_commands_are_exposed() -> None:
    result = runner.invoke(app, ["discover", "--help"])
    assert result.exit_code == 0
    for command in (
        "prepare-plan",
        "save-plan",
        "run-plan",
        "prepare-triage",
        "save-triage",
        "triage-status",
        "filter",
        "expand",
        "prepare-review",
        "readiness",
        "prepare-landscape",
    ):
        assert command in result.stdout


def test_beta_handoff_commands_are_exposed() -> None:
    assert runner.invoke(app, ["fulltext", "--help"]).exit_code == 0
    assert "acquire" in runner.invoke(app, ["fulltext", "--help"]).stdout
    assert runner.invoke(app, ["draft", "--help"]).exit_code == 0
    assert "prepare" in runner.invoke(app, ["draft", "--help"]).stdout
    assert runner.invoke(app, ["export", "--help"]).exit_code == 0
    assert "docx" in runner.invoke(app, ["export", "--help"]).stdout
    assert runner.invoke(app, ["package", "--help"]).exit_code == 0
    assert "prepare" in runner.invoke(app, ["package", "--help"]).stdout


def test_runtime_reports_beta_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0b1" in result.stdout


def _accepted_project(root: Path) -> None:
    init_project(root, name="Gate Test")
    set_intent(
        root,
        topic="working capital and firm performance",
        publication_from=2020,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)


def test_direction_prepare_is_blocked_without_completed_discovery(tmp_path: Path) -> None:
    _accepted_project(tmp_path)
    result = runner.invoke(app, ["direction", "prepare", str(tmp_path)])
    assert result.exit_code == 1
    assert "completed multi-source discovery campaign" in result.stderr


def test_legacy_landscape_prepare_is_blocked_when_campaign_exists(tmp_path: Path) -> None:
    _accepted_project(tmp_path)
    campaign = {
        "campaign_id": "campaign-1",
        "status": "collecting",
        "iterations": [],
        "review_checkpoints": [],
    }
    path = tmp_path / ".litreview" / "data" / "discovery_campaign.json"
    path.write_text(json.dumps(campaign), encoding="utf-8")
    result = runner.invoke(app, ["landscape", "prepare", str(tmp_path)])
    assert result.exit_code == 1
    assert "lrc discover prepare-landscape" in result.stderr
