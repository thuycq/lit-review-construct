from typer.testing import CliRunner

from litreview_construct.app_cli import app


runner = CliRunner()


def test_extended_discovery_commands_are_exposed() -> None:
    result = runner.invoke(app, ["discover", "--help"])
    assert result.exit_code == 0
    for command in (
        "prepare-triage",
        "save-triage",
        "triage-status",
        "expand",
        "prepare-review",
        "prepare-landscape",
    ):
        assert command in result.stdout


def test_runtime_reports_dev8() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0.dev8" in result.stdout
