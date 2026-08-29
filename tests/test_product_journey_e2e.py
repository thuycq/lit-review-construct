import json
from pathlib import Path

from litreview_construct.ai_use import generate_ai_use_statement
from litreview_construct.blueprint import accept_blueprint, prepare_blueprint_packet, save_blueprint
from litreview_construct.direction import (
    apply_direction_decision,
    prepare_direction_packet,
    save_direction_candidates,
)
from litreview_construct.evidence import save_evidence_map
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.landscape import save_landscape
from litreview_construct.project import init_project
from litreview_construct.seed_state import skip_seed_literature
from litreview_construct.workflow import project_next_step


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_researcher_journey_reaches_blueprint_handoff_not_final_review(tmp_path: Path) -> None:
    # 1. Research Intent is a researcher checkpoint.
    init_project(tmp_path, name="Working Capital Product Journey")
    set_intent(
        tmp_path,
        topic="working capital management and firm performance",
        research_question="How does working capital management affect firm performance, and when might the relationship be nonlinear?",
        publication_from=2010,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(tmp_path)
    assert project_next_step(tmp_path)["next_action"] == "ask_seed_literature"

    # 2. Researcher explicitly says no seed papers are currently available.
    skip_seed_literature(tmp_path)
    assert project_next_step(tmp_path)["next_action"] == "start_discovery"

    # Discovery itself has a dedicated multi-source end-to-end test. Here we inject the durable
    # result of a researcher-finished campaign so this test can exercise the full post-discovery
    # product contract without external network access.
    state_root = tmp_path / ".litreview"
    paper_ids = ["paper-linear", "paper-nonlinear", "paper-context"]
    papers = [
        {
            "paper_id": paper_ids[0],
            "title": "Working Capital Management and Firm Performance",
            "authors": ["Author A"],
            "year": 2020,
            "journal": "Finance Journal",
            "abstract": "Working capital management is associated with firm performance.",
            "source_origin": "openalex",
            "discovery_sources": ["openalex", "crossref"],
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "status": "relevant",
            "file_reference": None,
            "file_hash": None,
        },
        {
            "paper_id": paper_ids[1],
            "title": "Nonlinear Working Capital and Firm Value",
            "authors": ["Author B"],
            "year": 2023,
            "journal": "Corporate Finance Review",
            "abstract": "The relationship between working capital and firm value may be nonlinear.",
            "source_origin": "semantic_scholar",
            "discovery_sources": ["semantic_scholar"],
            "triage_label": "relevant",
            "triage_priority": "core_candidate",
            "status": "relevant",
            "file_reference": None,
            "file_hash": None,
        },
        {
            "paper_id": paper_ids[2],
            "title": "Financing Constraints and Working Capital Policy",
            "authors": ["Author C"],
            "year": 2022,
            "journal": "Emerging Markets Journal",
            "abstract": "Financing constraints shape working capital policy in emerging markets.",
            "source_origin": "crossref",
            "discovery_sources": ["crossref"],
            "triage_label": "background",
            "triage_priority": "high",
            "status": "background",
            "file_reference": None,
            "file_hash": None,
        },
    ]
    _write_jsonl(state_root / "data" / "papers.jsonl", papers)
    _write_json(
        state_root / "data" / "discovery_campaign.json",
        {
            "campaign_id": "campaign-e2e",
            "status": "complete",
            "iterations": [
                {
                    "phase": "broad",
                    "queries": [
                        "working capital firm performance",
                        "cash conversion cycle profitability",
                    ],
                    "providers": ["openalex", "crossref", "semantic_scholar"],
                },
                {
                    "phase": "focused",
                    "queries": ["nonlinear working capital firm value"],
                    "providers": ["openalex", "semantic_scholar"],
                },
            ],
            "review_checkpoints": [
                {
                    "checkpoint_id": "review-1",
                    "decision": {"action": "focus"},
                },
                {
                    "checkpoint_id": "review-2",
                    "decision": {"action": "finish"},
                },
            ],
            "selected_focuses": ["Nonlinear working-capital optimization"],
            "researcher_completion": {"action": "finish"},
        },
    )
    state_file = state_root / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["literature_discovery"]["status"] = "accepted"
    state["current_stage"] = "literature_discovery"
    _write_json(state_file, state)

    step = project_next_step(tmp_path)
    assert step["next_action"] == "construct_current_research_landscape"
    assert step["human_checkpoint_required"] is False

    # 3. Current Research Landscape is synthesized from retained literature.
    landscape_submission = {
        "summary": "The retained literature separates a direct efficiency stream from a nonlinear optimization stream, with financing constraints providing context.",
        "anchor_paper_ids": [paper_ids[0], paper_ids[1]],
        "streams": [
            {
                "name": "Working-capital efficiency and performance",
                "description": "Studies linking working-capital policy to firm outcomes.",
                "paper_ids": [paper_ids[0], paper_ids[2]],
                "anchor_paper_ids": [paper_ids[0]],
                "main_theories": ["liquidity-profitability trade-off"],
                "main_methods": ["panel regression"],
                "major_findings": ["Working-capital choices are associated with firm performance."],
                "contradictions": [],
                "recent_developments": [],
                "confidence": "medium",
            },
            {
                "name": "Nonlinear working-capital optimization",
                "description": "Studies considering whether both too little and too much working capital can be costly.",
                "paper_ids": [paper_ids[1]],
                "anchor_paper_ids": [paper_ids[1]],
                "main_theories": ["optimal investment trade-off"],
                "main_methods": ["nonlinear panel specifications"],
                "major_findings": ["The relationship may be nonlinear."],
                "contradictions": [],
                "recent_developments": ["Greater attention to nonlinear specifications."],
                "confidence": "medium",
            },
        ],
        "major_debates": ["Whether the performance relationship is linear or nonlinear."],
        "methodological_clusters": ["Panel regressions", "Nonlinear specifications"],
        "recent_developments": ["Nonlinear working-capital optimization"],
        "unresolved_questions": ["How robust is the optimal range across firm contexts?"],
        "limitations": ["Several retained records are abstract-only and require fuller verification."],
    }
    landscape_file = tmp_path / "landscape_submission.json"
    _write_json(landscape_file, landscape_submission)
    saved_landscape = save_landscape(tmp_path, landscape_file)
    assert saved_landscape["status"] == "ready_for_review"
    assert project_next_step(tmp_path)["next_action"] == "construct_evidence_map"

    # 4. Evidence Map preserves source basis and uncertainty.
    evidence_submission = {
        "summary": "Preliminary evidence supports a working-capital/performance relationship and suggests nonlinear heterogeneity, but full-text verification remains necessary.",
        "evidence_items": [
            {
                "paper_id": paper_ids[0],
                "evidence_type": "association",
                "claim": "Working capital management is associated with firm performance.",
                "provenance": "source_reported",
                "source_basis": "abstract",
                "source_locator": "abstract",
                "variables": ["working capital management", "firm performance"],
                "theories": [],
                "methods": [],
                "data_context": [],
                "certainty": "medium",
            },
            {
                "paper_id": paper_ids[1],
                "evidence_type": "heterogeneous_finding",
                "claim": "The working-capital/performance relationship may be nonlinear.",
                "provenance": "source_reported",
                "source_basis": "abstract",
                "source_locator": "abstract",
                "variables": ["working capital", "firm value"],
                "theories": [],
                "methods": [],
                "data_context": [],
                "certainty": "medium",
            },
            {
                "paper_id": paper_ids[2],
                "evidence_type": "theory",
                "claim": "Financing constraints can shape working-capital policy.",
                "provenance": "source_reported",
                "source_basis": "abstract",
                "source_locator": "abstract",
                "variables": ["financing constraints", "working capital policy"],
                "theories": [],
                "methods": [],
                "data_context": ["emerging markets"],
                "certainty": "medium",
            },
        ],
        "cross_paper_patterns": ["The literature links working-capital choices with performance but varies in functional form and context."],
        "contradictions": [],
        "evidence_gaps": ["The stability of nonlinear thresholds across contexts requires verification."],
        "papers_requiring_full_text": paper_ids,
        "limitations": ["Current substantive records are based on abstracts."],
    }
    evidence_file = tmp_path / "evidence_submission.json"
    _write_json(evidence_file, evidence_submission)
    saved_evidence = save_evidence_map(tmp_path, evidence_file)
    assert saved_evidence["requires_full_text"] == 3
    assert project_next_step(tmp_path)["next_action"] == "propose_research_directions"

    evidence_rows = [
        json.loads(line)
        for line in (state_root / "data" / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    evidence_ids = [row["evidence_id"] for row in evidence_rows]

    # 5. AI proposes alternatives but does not select one.
    prepared_direction = prepare_direction_packet(tmp_path)
    assert prepared_direction["full_text_verification_flags"] == 3
    direction_submission = {
        "summary": "Two provisional directions emerge from the current landscape and evidence.",
        "directions": [
            {
                "title": "Nonlinear working-capital optimization",
                "research_idea": "Test whether firm performance is maximized within an intermediate working-capital range.",
                "rationale": "The retained literature suggests the relationship may be nonlinear.",
                "supporting_paper_ids": [paper_ids[0], paper_ids[1]],
                "supporting_evidence_ids": evidence_ids[:2],
                "what_is_known": ["Working-capital choices are associated with performance."],
                "possible_gap": "Threshold stability across contexts appears insufficiently verified in the current evidence set.",
                "novelty": "Estimate and compare nonlinear ranges under clearly defined contexts.",
                "data_feasibility": "Potentially feasible with firm-level accounting data; exact availability must be checked.",
                "methodological_feasibility": "Nonlinear panel specifications are plausible but require design verification.",
                "difficulty": "medium",
                "risks": ["Threshold results may be sample-specific."],
                "limitations": ["Key papers still require full-text verification."],
                "verification_needs": ["Verify prior nonlinear specifications and samples in full text."],
                "confidence": "medium",
            },
            {
                "title": "Financing constraints as a moderator",
                "research_idea": "Examine whether financing constraints alter the working-capital/performance relationship.",
                "rationale": "Context literature indicates financing constraints shape working-capital policy.",
                "supporting_paper_ids": [paper_ids[0], paper_ids[2]],
                "supporting_evidence_ids": [evidence_ids[0], evidence_ids[2]],
                "what_is_known": ["Financing constraints affect working-capital policy."],
                "possible_gap": "The moderating role is not established by the current bounded evidence set.",
                "novelty": "Integrate financing constraints into the focal performance relationship.",
                "data_feasibility": "Potentially feasible if financing-constraint proxies can be constructed.",
                "methodological_feasibility": "Interaction or subgroup specifications are plausible but require validation.",
                "difficulty": "medium",
                "risks": ["Proxy choice may drive results."],
                "limitations": ["Current evidence does not establish the moderator causally."],
                "verification_needs": ["Verify measurement approaches in core papers."],
                "confidence": "low",
            },
        ],
        "cross_direction_notes": ["Both directions require fuller source verification before strong novelty claims."],
        "limitations": ["The current evidence map is abstract-heavy."],
    }
    directions_file = tmp_path / "directions_submission.json"
    _write_json(directions_file, direction_submission)
    saved_directions = save_direction_candidates(tmp_path, directions_file)
    assert saved_directions["human_decision_required"] is True
    step = project_next_step(tmp_path)
    assert step["next_action"] == "researcher_direction_decision"
    assert step["human_checkpoint_required"] is True

    direction_rows = [
        json.loads(line)
        for line in (state_root / "data" / "directions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selected_id = direction_rows[0]["direction_id"]
    decision_file = tmp_path / "direction_decision.json"
    _write_json(
        decision_file,
        {
            "action": "select",
            "direction_ids": [selected_id],
            "researcher_notes": "Use the nonlinear optimization direction as the working research direction.",
        },
    )
    applied = apply_direction_decision(tmp_path, decision_file)
    assert applied["status"] == "accepted"
    assert project_next_step(tmp_path)["next_action"] == "construct_literature_review_blueprint"

    # 6. Blueprint is an evidence-linked architecture, not completed manuscript prose.
    prepared_blueprint = prepare_blueprint_packet(tmp_path)
    assert prepared_blueprint["verification_flags"] == 3
    blueprint_submission = {
        "title": "Literature Review Blueprint: Working Capital and Firm Performance",
        "organizing_logic": "Move from theory and established relationship evidence toward nonlinear evidence, contextual heterogeneity, and the verified motivation for the selected direction.",
        "opening_tasks": ["Define working-capital constructs and delimit the literature scope."],
        "sections": [
            {
                "title": "Theoretical foundations of working-capital decisions",
                "purpose": "Establish why liquidity and working-capital choices can affect firm outcomes.",
                "key_arguments": ["Explain the liquidity-profitability trade-off and financing-constraint context."],
                "anchor_paper_ids": [paper_ids[0]],
                "supporting_paper_ids": [paper_ids[2]],
                "conflicting_paper_ids": [],
                "evidence_ids": [evidence_ids[0], evidence_ids[2]],
                "theoretical_foundations": ["Liquidity-profitability trade-off", "Financing constraints"],
                "methodological_context": [],
                "hypothesis_or_proposition_links": [],
                "unresolved_questions": ["Which theoretical mechanism best explains nonlinear effects?"],
                "transition_logic": "Move from theoretical mechanisms to the empirical working-capital/performance relationship.",
            },
            {
                "title": "Empirical relationship between working capital and performance",
                "purpose": "Establish the empirical baseline and show why functional form matters.",
                "key_arguments": ["Synthesize direct association evidence before considering nonlinear specifications."],
                "anchor_paper_ids": [paper_ids[0]],
                "supporting_paper_ids": [],
                "conflicting_paper_ids": [],
                "evidence_ids": [evidence_ids[0]],
                "theoretical_foundations": [],
                "methodological_context": ["Panel regression evidence"],
                "hypothesis_or_proposition_links": ["Establishes the baseline relationship requiring refinement."],
                "unresolved_questions": [],
                "transition_logic": "Use limitations of a purely linear framing to motivate nonlinear evidence.",
            },
            {
                "title": "Nonlinear optimization and contextual heterogeneity",
                "purpose": "Evaluate the evidence motivating the selected nonlinear working-capital direction and identify what still requires verification.",
                "key_arguments": ["Compare nonlinear evidence with financing-constraint context without overstating a verified gap."],
                "anchor_paper_ids": [paper_ids[1]],
                "supporting_paper_ids": [paper_ids[2]],
                "conflicting_paper_ids": [],
                "evidence_ids": [evidence_ids[1], evidence_ids[2]],
                "theoretical_foundations": ["Optimal investment trade-off"],
                "methodological_context": ["Nonlinear panel specifications"],
                "hypothesis_or_proposition_links": ["Motivates testing an intermediate performance-maximizing working-capital range."],
                "unresolved_questions": ["Are estimated nonlinear thresholds stable across firm contexts?"],
                "transition_logic": None,
            },
        ],
        "cross_section_synthesis_tasks": ["Reconcile linear, nonlinear, and contextual evidence before stating the research motivation."],
        "closing_tasks": ["State only the gap/novelty that survives full-text verification."],
        "verification_priorities": ["Obtain and verify full text for all three current core/context papers."],
        "limitations": ["The present architecture is based partly on abstract-level evidence."],
    }
    blueprint_file = tmp_path / "blueprint_submission.json"
    _write_json(blueprint_file, blueprint_submission)
    saved_blueprint = save_blueprint(tmp_path, blueprint_file)
    assert saved_blueprint["status"] == "ready_for_review"
    step = project_next_step(tmp_path)
    assert step["next_action"] == "researcher_blueprint_review"
    assert step["human_checkpoint_required"] is True

    accept_blueprint(tmp_path)
    step = project_next_step(tmp_path)
    assert step["next_action"] == "researcher_handoff"
    assert step["human_checkpoint_required"] is True
    assert step["prohibited_next_step"] == "generate_complete_final_literature_review"

    # 7. Optional disclosure must reflect recorded assistance but not invent drafting.
    disclosure = generate_ai_use_statement(tmp_path, style="standard")
    statement = disclosure["statement"].lower()
    assert "research landscapes" in statement
    assert "organizing source evidence" in statement
    assert "candidate research directions" in statement
    assert "literature-review architecture" in statement
    assert "draft fragments" not in statement

    # Researcher-facing outputs exist through the Blueprint and disclosure, but there is deliberately
    # no output file representing a complete final literature review.
    assert (tmp_path / "outputs" / "03_research_landscape.md").exists()
    assert (tmp_path / "outputs" / "04_evidence_map.md").exists()
    assert (tmp_path / "outputs" / "05_research_direction.md").exists()
    assert (tmp_path / "outputs" / "06_literature_review_blueprint.md").exists()
    assert (tmp_path / "outputs" / "07_ai_use_statement.md").exists()
    assert not (tmp_path / "outputs" / "08_final_literature_review.md").exists()
