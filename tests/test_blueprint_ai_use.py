import json
from pathlib import Path

from typer.testing import CliRunner

from litreview_construct.activity import append_activity
from litreview_construct.ai_use import generate_ai_use_statement
from litreview_construct.blueprint import accept_blueprint, prepare_blueprint_packet, save_blueprint
from litreview_construct.entrypoint import app
from litreview_construct.project import init_project


runner = CliRunner()


def _setup_blueprint_project(root: Path) -> tuple[str, str]:
    init_project(root, name="Blueprint Test")
    state_root = root / ".litreview"
    paper_id = "paper-1"
    evidence_id = "evidence-1"

    papers = [
        {
            "paper_id": paper_id,
            "title": "Working Capital Management and Firm Performance",
            "authors": ["Researcher"],
            "year": 2024,
            "journal": "Journal",
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "file_reference": None,
            "file_hash": None,
        }
    ]
    (state_root / "data" / "papers.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in papers), encoding="utf-8"
    )
    evidence = [
        {
            "evidence_id": evidence_id,
            "paper_id": paper_id,
            "evidence_type": "association",
            "claim": "Working capital policy is associated with firm performance.",
            "provenance": "source_reported",
            "source_basis": "abstract",
            "certainty": "medium",
            "theories": [],
            "variables": ["working capital", "firm performance"],
            "methods": ["panel regression"],
            "data_context": ["listed firms"],
        }
    ]
    (state_root / "data" / "evidence.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in evidence), encoding="utf-8"
    )
    (state_root / "data" / "landscape.json").write_text(
        json.dumps(
            {
                "summary": "Working-capital literature landscape.",
                "anchor_paper_ids": [paper_id],
                "streams": [
                    {
                        "name": "Working-capital efficiency",
                        "description": "Direct relationship literature.",
                        "paper_ids": [paper_id],
                        "anchor_paper_ids": [paper_id],
                    }
                ],
                "major_debates": [],
                "methodological_clusters": [],
                "recent_developments": [],
                "unresolved_questions": [],
                "limitations": [],
                "provenance": "ai_synthesis",
            }
        ),
        encoding="utf-8",
    )
    (state_root / "data" / "evidence_map.json").write_text(
        json.dumps(
            {
                "summary": "Evidence map.",
                "cross_paper_patterns": [],
                "contradictions": [],
                "evidence_gaps": [],
                "papers_requiring_full_text": [paper_id],
                "limitations": ["Full text is not yet available."],
                "provenance": "ai_synthesis",
            }
        ),
        encoding="utf-8",
    )
    (state_root / "data" / "selected_direction.json").write_text(
        json.dumps(
            {
                "direction_id": "direction-1",
                "title": "Nonlinear working-capital optimization",
                "research_idea": "Examine nonlinear working-capital effects on firm performance.",
                "supporting_paper_ids": [paper_id],
                "supporting_evidence_ids": [evidence_id],
                "status": "selected",
                "provenance": "researcher_judgment",
            }
        ),
        encoding="utf-8",
    )
    state_file = state_root / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["research_intent"]["status"] = "accepted"
    state["stages"]["literature_discovery"]["status"] = "accepted"
    state["stages"]["evidence_mapping"]["status"] = "ready_for_review"
    state["stages"]["research_direction"]["status"] = "accepted"
    state["current_stage"] = "research_direction"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return paper_id, evidence_id


def test_blueprint_requires_accepted_direction(tmp_path: Path) -> None:
    init_project(tmp_path, name="Blocked Blueprint")
    try:
        prepare_blueprint_packet(tmp_path)
    except ValueError as exc:
        assert "researcher-accepted Research Direction" in str(exc)
    else:
        raise AssertionError("Blueprint preparation should be blocked before direction acceptance")


def test_blueprint_prepare_save_accept(tmp_path: Path) -> None:
    paper_id, evidence_id = _setup_blueprint_project(tmp_path)
    prepared = prepare_blueprint_packet(tmp_path)
    packet = json.loads(Path(prepared["packet_file"]).read_text(encoding="utf-8"))
    assert packet["analysis_contract"]["authorship_boundary"]
    assert packet["selected_research_direction"]["provenance"] == "researcher_judgment"

    submission = {
        "title": "Working-capital literature review architecture",
        "organizing_logic": "Move from theoretical rationale to empirical patterns and unresolved nonlinear effects.",
        "opening_tasks": ["Define the focal working-capital constructs."],
        "sections": [
            {
                "title": "Theoretical foundations",
                "purpose": "Establish why working-capital decisions can affect firm outcomes.",
                "key_arguments": ["Explain the liquidity-profitability trade-off."],
                "anchor_paper_ids": [paper_id],
                "supporting_paper_ids": [],
                "conflicting_paper_ids": [],
                "evidence_ids": [evidence_id],
                "theoretical_foundations": ["Liquidity-profitability trade-off"],
                "methodological_context": [],
                "hypothesis_or_proposition_links": [],
                "unresolved_questions": [],
                "transition_logic": "Move from theory to the empirical working-capital/performance relationship.",
            },
            {
                "title": "Empirical relationship and nonlinear direction",
                "purpose": "Synthesize the empirical relationship and motivate the selected nonlinear direction.",
                "key_arguments": ["Compare linear evidence with the need to test nonlinear effects."],
                "anchor_paper_ids": [paper_id],
                "supporting_paper_ids": [],
                "conflicting_paper_ids": [],
                "evidence_ids": [evidence_id],
                "theoretical_foundations": [],
                "methodological_context": ["Panel regression evidence"],
                "hypothesis_or_proposition_links": ["Motivates a nonlinear working-capital hypothesis."],
                "unresolved_questions": ["Where is the performance-maximizing working-capital range?"],
                "transition_logic": None,
            },
        ],
        "cross_section_synthesis_tasks": ["Reconcile theory with empirical heterogeneity."],
        "closing_tasks": ["State the verified gap conservatively."],
        "verification_priorities": ["Obtain full text for the anchor paper."],
        "limitations": ["Current evidence includes abstract-only support."],
    }
    submission_file = tmp_path / "blueprint_submission.json"
    submission_file.write_text(json.dumps(submission), encoding="utf-8")
    saved = save_blueprint(tmp_path, submission_file)
    assert saved["status"] == "ready_for_review"
    assert saved["sections"] == 2
    blueprint = json.loads(
        (tmp_path / ".litreview" / "data" / "blueprint.json").read_text(encoding="utf-8")
    )
    assert blueprint["authorship_boundary"] == "researcher_writes_final_prose"
    assert all(section.get("section_id") for section in blueprint["sections"])
    accepted = accept_blueprint(tmp_path)
    assert accepted["status"] == "accepted"


def test_ai_use_statement_only_reports_recorded_ai_activity(tmp_path: Path) -> None:
    init_project(tmp_path, name="AI Use Test")
    append_activity(
        tmp_path,
        category="paper_prioritization",
        actor="ai_assisted",
        inputs={},
        outputs=[],
    )
    append_activity(
        tmp_path,
        category="literature_discovery",
        actor="toolkit",
        inputs={},
        outputs=[],
    )
    result = generate_ai_use_statement(tmp_path, style="standard")
    assert "relevance triage" in result["statement"]
    assert "retrieving and recording scholarly metadata" in result["statement"]
    assert "draft" not in result["statement"].lower()


def test_cli_exposes_blueprint_and_ai_use() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "blueprint" in result.stdout
    assert "ai-use" in result.stdout
