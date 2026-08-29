from pathlib import Path

from litreview_construct.project import init_project, read_status


def test_init_project_creates_expected_structure(tmp_path: Path) -> None:
    result = init_project(tmp_path, name="Test Project")

    assert result["created"] is True
    assert (tmp_path / ".litreview" / "project.yaml").is_file()
    assert (tmp_path / ".litreview" / "state.json").is_file()
    assert (tmp_path / ".litreview" / "activity" / "activity.jsonl").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "papers").is_dir()
    assert (tmp_path / "outputs").is_dir()

    status = read_status(tmp_path)
    assert status["name"] == "Test Project"
    assert status["current_stage"] == "research_intent"
    assert status["stage_status"] == "in_progress"


def test_init_project_is_non_destructive(tmp_path: Path) -> None:
    first = init_project(tmp_path)
    second = init_project(tmp_path)

    assert first["created"] is True
    assert second["created"] is False
