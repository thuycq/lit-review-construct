import json
from pathlib import Path

from litreview_construct.project import init_project
from litreview_construct.workflow import project_next_step


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_legacy_abstract_evidence_is_not_forced_backward_but_refreshes_after_new_oa(
    tmp_path: Path,
) -> None:
    init_project(tmp_path, name="Legacy OA Migration")
    root = tmp_path / ".litreview"
    state_path = root / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    for stage in (
        "research_intent",
        "seed_literature",
        "research_direction",
        "literature_review_blueprint",
    ):
        state["stages"][stage]["status"] = "accepted"
    state["stages"]["literature_discovery"]["status"] = "ready_for_review"
    state["stages"]["evidence_mapping"]["status"] = "ready_for_review"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    _write_json(root / "data" / "seed_decision.json", {"decision": "none"})
    _write_json(root / "data" / "discovery_campaign.json", {"status": "complete"})
    _write_json(root / "data" / "landscape.json", {"summary": "Landscape", "streams": []})
    _write_json(
        root / "data" / "evidence_map.json",
        {
            "summary": "Abstract-only evidence",
            "saved_at": "2026-08-29T01:00:00+00:00",
            "papers_requiring_full_text": ["p1"],
        },
    )
    _write_json(root / "data" / "selected_direction.json", {"title": "Direction"})
    _write_json(root / "data" / "blueprint.json", {"title": "Blueprint", "sections": []})

    # Existing beta projects that already progressed beyond corpus refinement are preserved.
    first = project_next_step(tmp_path)
    assert first["next_action"] == "construct_working_draft"

    # If the researcher/toolkit later acquires newer full text, the evidence is refreshed.
    _write_json(
        root / "data" / "fulltext_resolution.json",
        {
            "selected_papers": 1,
            "downloaded": 1,
            "toolkit_oa_full_text_records": 1,
            "latest_toolkit_oa_acquired_at": "2026-08-29T02:00:00+00:00",
        },
    )
    second = project_next_step(tmp_path)
    assert second["next_action"] == "refresh_evidence_after_fulltext"
    assert second["toolkit_oa_full_text_records"] == 1

    _write_json(
        root / "data" / "evidence_map.json",
        {
            "summary": "Full-text refreshed evidence",
            "saved_at": "2026-08-29T03:00:00+00:00",
            "papers_requiring_full_text": [],
        },
    )
    third = project_next_step(tmp_path)
    assert third["next_action"] == "construct_working_draft"
