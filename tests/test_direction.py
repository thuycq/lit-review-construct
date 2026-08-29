import json
from pathlib import Path

from litreview_construct.direction import (
    apply_direction_decision,
    prepare_direction_packet,
    save_direction_candidates,
)
from litreview_construct.project import init_project


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _ready_project(tmp_path: Path) -> tuple[str, str]:
    init_project(tmp_path, name="Direction Test")
    state_root = tmp_path / ".litreview"
    paper_id = "paper-1"
    evidence_id = "evidence-1"
    _write_jsonl(
        state_root / "data" / "papers.jsonl",
        [{"paper_id": paper_id, "title": "Paper One", "source_origin": "openalex"}],
    )
    _write_json(
        state_root / "data" / "landscape.json",
        {
            "summary": "Landscape",
            "anchor_paper_ids": [paper_id],
            "streams": [{"name": "Stream", "paper_ids": [paper_id]}],
            "major_debates": [],
            "unresolved_questions": [],
            "limitations": [],
        },
    )
    _write_jsonl(
        state_root / "data" / "evidence.jsonl",
        [
            {
                "evidence_id": evidence_id,
                "paper_id": paper_id,
                "evidence_type": "association",
                "claim": "Working capital is associated with performance.",
                "provenance": "source_reported",
                "source_basis": "abstract",
                "certainty": "medium",
            }
        ],
    )
    _write_json(
        state_root / "data" / "evidence_map.json",
        {
            "summary": "Evidence",
            "cross_paper_patterns": [],
            "contradictions": [],
            "evidence_gaps": ["More verification needed."],
            "papers_requiring_full_text": [paper_id],
            "limitations": ["Abstract-only evidence."],
        },
    )
    state_path = state_root / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["stages"]["evidence_mapping"]["status"] = "ready_for_review"
    state["current_stage"] = "evidence_mapping"
    _write_json(state_path, state)
    return paper_id, evidence_id


def test_prepare_and_save_candidates_requires_human_decision(tmp_path: Path) -> None:
    paper_id, evidence_id = _ready_project(tmp_path)
    packet = prepare_direction_packet(tmp_path)
    assert packet["evidence_items"] == 1
    assert packet["full_text_verification_flags"] == 1

    submission = {
        "summary": "Two provisional directions.",
        "directions": [
            {
                "title": "Direction A",
                "research_idea": "Test nonlinear working-capital effects.",
                "rationale": "The current evidence suggests contingent effects.",
                "supporting_paper_ids": [paper_id],
                "supporting_evidence_ids": [evidence_id],
                "what_is_known": ["An association is reported."],
                "possible_gap": "The nonlinear form needs fuller verification.",
                "novelty": "Potentially tests an underexplored nonlinear specification.",
                "data_feasibility": "Potential firm-panel data could be used; availability is not yet verified.",
                "methodological_feasibility": "Panel models are plausible but not yet selected.",
                "difficulty": "medium",
                "verification_needs": ["Verify full text."],
                "confidence": "medium",
            },
            {
                "title": "Direction B",
                "research_idea": "Study crisis-state heterogeneity.",
                "rationale": "Contingency may matter across macro states.",
                "supporting_paper_ids": [paper_id],
                "supporting_evidence_ids": [evidence_id],
                "what_is_known": ["An association is reported."],
                "possible_gap": "Crisis-state evidence is not established in the current corpus.",
                "novelty": "Potential state-dependent extension.",
                "data_feasibility": "Requires firm and macro data; availability is not yet verified.",
                "methodological_feasibility": "Interaction or regime methods may be possible.",
                "difficulty": "high",
                "verification_needs": ["Expand and verify the literature."],
                "confidence": "low",
            },
        ],
    }
    submission_path = tmp_path / "direction_submission.json"
    _write_json(submission_path, submission)
    result = save_direction_candidates(tmp_path, submission_path)
    assert result["status"] == "ready_for_review"
    assert result["human_decision_required"] is True

    state = json.loads((tmp_path / ".litreview" / "state.json").read_text(encoding="utf-8"))
    assert state["stages"]["research_direction"]["status"] == "ready_for_review"


def test_explicit_researcher_selection_accepts_direction(tmp_path: Path) -> None:
    paper_id, evidence_id = _ready_project(tmp_path)
    submission = {
        "summary": "Candidates",
        "directions": [
            {
                "title": "Direction A",
                "research_idea": "Idea A",
                "rationale": "Rationale A",
                "supporting_paper_ids": [paper_id],
                "supporting_evidence_ids": [evidence_id],
                "possible_gap": "Possible gap A",
                "novelty": "Potential novelty A",
                "data_feasibility": "Needs verification.",
                "methodological_feasibility": "Plausible.",
            },
            {
                "title": "Direction B",
                "research_idea": "Idea B",
                "rationale": "Rationale B",
                "possible_gap": "Possible gap B",
                "novelty": "Potential novelty B",
                "data_feasibility": "Needs verification.",
                "methodological_feasibility": "Plausible.",
            },
        ],
    }
    submission_path = tmp_path / "direction_submission.json"
    _write_json(submission_path, submission)
    save_direction_candidates(tmp_path, submission_path)
    rows = [
        json.loads(line)
        for line in (tmp_path / ".litreview" / "data" / "directions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    chosen_id = rows[0]["direction_id"]
    decision_path = tmp_path / "direction_decision.json"
    _write_json(
        decision_path,
        {
            "action": "select",
            "direction_ids": [chosen_id],
            "researcher_notes": "Choose Direction A for the test.",
        },
    )
    result = apply_direction_decision(tmp_path, decision_path)
    assert result["status"] == "accepted"
    assert result["selected"] == "Direction A"
    state = json.loads((tmp_path / ".litreview" / "state.json").read_text(encoding="utf-8"))
    assert state["stages"]["research_direction"]["status"] == "accepted"
    decision = json.loads(
        (tmp_path / ".litreview" / "data" / "direction_decision.json").read_text(encoding="utf-8")
    )
    assert decision["provenance"] == "researcher_judgment"
