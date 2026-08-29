from pathlib import Path

import pytest

from litreview_construct.intent import accept_intent, set_intent, show_intent
from litreview_construct.project import init_project, read_status


def test_intent_requires_minimum_scope_before_acceptance(tmp_path: Path) -> None:
    init_project(tmp_path, name="Intent Test")
    set_intent(tmp_path, topic="Green finance")

    with pytest.raises(ValueError):
        accept_intent(tmp_path)


def test_complete_intent_can_be_accepted(tmp_path: Path) -> None:
    init_project(tmp_path, name="Intent Test")
    result = set_intent(
        tmp_path,
        topic="Green finance and firm performance",
        research_question="How does green finance relate to firm performance?",
        publication_from=2015,
        publication_to=2026,
        languages=["en", "vi"],
    )
    assert result["status"] == "ready_for_review"
    assert result["missing"] == []

    accepted = accept_intent(tmp_path)
    assert accepted["status"] == "accepted"
    assert read_status(tmp_path)["current_stage"] == "seed_literature"

    shown = show_intent(tmp_path)
    assert shown["status"] == "accepted"
    output = (tmp_path / "outputs" / "01_research_intent.md").read_text(encoding="utf-8")
    assert "Green finance and firm performance" in output
    assert "2015–2026" in output


def test_revising_accepted_intent_requires_review_again(tmp_path: Path) -> None:
    init_project(tmp_path)
    set_intent(
        tmp_path,
        topic="Green finance",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(tmp_path)

    revised = set_intent(tmp_path, publication_from=2018)
    assert revised["status"] == "ready_for_review"
    assert read_status(tmp_path)["current_stage"] == "research_intent"
