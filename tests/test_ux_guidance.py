import json
from pathlib import Path

from typer.testing import CliRunner

from litreview_construct.entrypoint import app
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project
from litreview_construct.seed_state import skip_seed_literature
from litreview_construct.ux import suggested_user_message


runner = CliRunner()


def _accepted_project(root: Path) -> None:
    init_project(root, name="UX Guidance Test")
    set_intent(
        root,
        topic="working capital and firm performance",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    skip_seed_literature(root)


def test_suggested_message_has_safe_generic_fallback() -> None:
    message = suggested_user_message({"next_action": "unknown_future_action"})
    assert "recommended next step" in message.lower()


def test_project_next_json_includes_suggested_user_message(tmp_path: Path) -> None:
    _accepted_project(tmp_path)
    result = runner.invoke(app, ["next", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["next_action"] == "start_discovery"
    assert payload["suggested_user_message"]
    assert "discovery" in payload["suggested_user_message"].lower()


def test_discovery_next_json_includes_suggested_user_message(tmp_path: Path) -> None:
    _accepted_project(tmp_path)
    start = runner.invoke(app, ["discover", "start", str(tmp_path)])
    assert start.exit_code == 0
    result = runner.invoke(app, ["discover", "next", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["next_action"] == "prepare_broad_query_plan"
    assert payload["suggested_user_message"]
    assert "query plan" in payload["suggested_user_message"].lower()
