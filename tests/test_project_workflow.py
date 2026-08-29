import json
from pathlib import Path

from typer.testing import CliRunner

from litreview_construct.entrypoint import app
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project
from litreview_construct.seed_state import skip_seed_literature
from litreview_construct.workflow import project_next_step


runner = CliRunner()


def _accepted_intent(root: Path) -> None:
    init_project(root, name="Workflow Test")
    set_intent(
        root,
        topic="working capital and firm performance",
        publication_from=2010,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)


def test_project_next_requires_seed_checkpoint_after_intent(tmp_path: Path) -> None:
    _accepted_intent(tmp_path)
    step = project_next_step(tmp_path)
    assert step["next_action"] == "ask_seed_literature"
    assert step["human_checkpoint_required"] is True
    assert step["skill"] == "litreview-seeds"


def test_seed_skip_persists_and_routes_to_discovery(tmp_path: Path) -> None:
    _accepted_intent(tmp_path)
    skip_seed_literature(tmp_path)
    step = project_next_step(tmp_path)
    assert step["stage"] == "literature_discovery"
    assert step["skill"] == "litreview-discover"
    assert step["next_action"] == "start_discovery"


def test_project_next_routes_accepted_direction_to_blueprint(tmp_path: Path) -> None:
    _accepted_intent(tmp_path)
    skip_seed_literature(tmp_path)
    state_root = tmp_path / ".litreview"
    campaign = {
        "campaign_id": "campaign-1",
        "status": "complete",
        "iterations": [],
        "review_checkpoints": [],
    }
    (state_root / "data" / "discovery_campaign.json").write_text(json.dumps(campaign), encoding="utf-8")
    (state_root / "data" / "landscape.json").write_text(json.dumps({"provenance": "ai_synthesis"}), encoding="utf-8")
    (state_root / "data" / "evidence_map.json").write_text(json.dumps({"provenance": "ai_synthesis"}), encoding="utf-8")
    (state_root / "data" / "selected_direction.json").write_text(
        json.dumps({"direction_id": "d1", "status": "selected", "provenance": "researcher_judgment"}),
        encoding="utf-8",
    )
    state_file = state_root / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["literature_discovery"]["status"] = "ready_for_review"
    state["stages"]["evidence_mapping"]["status"] = "ready_for_review"
    state["stages"]["research_direction"]["status"] = "accepted"
    state["current_stage"] = "research_direction"
    state_file.write_text(json.dumps(state), encoding="utf-8")

    step = project_next_step(tmp_path)
    assert step["next_action"] == "construct_literature_review_blueprint"
    assert step["skill"] == "litreview-blueprint"
    assert step["human_checkpoint_required"] is False


def test_project_next_never_generates_final_review_after_blueprint_acceptance(tmp_path: Path) -> None:
    _accepted_intent(tmp_path)
    skip_seed_literature(tmp_path)
    state_root = tmp_path / ".litreview"
    (state_root / "data" / "discovery_campaign.json").write_text(
        json.dumps({"campaign_id": "campaign-1", "status": "complete"}), encoding="utf-8"
    )
    for filename in ("landscape.json", "evidence_map.json", "selected_direction.json", "blueprint.json"):
        (state_root / "data" / filename).write_text(json.dumps({"exists": True}), encoding="utf-8")
    state_file = state_root / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["literature_discovery"]["status"] = "ready_for_review"
    state["stages"]["evidence_mapping"]["status"] = "ready_for_review"
    state["stages"]["research_direction"]["status"] = "accepted"
    state["stages"]["literature_review_blueprint"]["status"] = "accepted"
    state["stages"]["researcher_handoff"]["status"] = "in_progress"
    state_file.write_text(json.dumps(state), encoding="utf-8")

    step = project_next_step(tmp_path)
    assert step["next_action"] == "researcher_handoff"
    assert step["prohibited_next_step"] == "generate_complete_final_literature_review"
    assert "ai-use" in " ".join(step["optional_commands"])


def test_cli_exposes_project_next_and_seed_decisions() -> None:
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "next" in help_result.stdout
    seed_help = runner.invoke(app, ["seed", "--help"])
    assert seed_help.exit_code == 0
    assert "accept" in seed_help.stdout
    assert "skip" in seed_help.stdout
