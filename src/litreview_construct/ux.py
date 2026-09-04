from __future__ import annotations

from typing import Mapping


def suggested_user_message(result: Mapping[str, object]) -> str:
    """Return a short researcher-facing message that can advance the saved workflow.

    Guidance is natural language only. It never substitutes for a required researcher decision,
    never exposes an `lrc` command as the primary instruction, and should move forward rather than
    asking the researcher to re-open an artifact they just received.
    """
    action = str(result.get("next_action") or "")

    if action == "researcher_decision_required":
        if bool(result.get("discovery_saturated")) or result.get("recommended_option") == "finish":
            return (
                "Finish discovery and proceed if the current focus is sufficient, or show me what "
                "would materially change if I broadened it."
            )
        return (
            "Show me the discovery choices in researcher-friendly language, recommend the most "
            "defensible option, and let me decide."
        )

    suggestions = {
        "complete_research_intent": "Help me complete the Research Intent using what I have already provided.",
        "review_seed_inventory": "Show me the seed-paper inventory and let me confirm it.",
        "ask_seed_literature": "Ask me whether I have any existing papers to add before discovery starts.",
        "start_discovery": "Start the literature discovery campaign and continue through the technical setup automatically.",
        "prepare_broad_query_plan": "Prepare the broad discovery query plan and continue.",
        "run_saved_query_plan": "Run the saved discovery plan and return when a genuine researcher decision is needed.",
        "prepare_early_review": "Build the initial discovery map and show me the research streams and focus options.",
        "revise_research_intent": "Help me revise the research scope based on the discovery results.",
        "prepare_focused_query_plan": "Prepare and run focused discovery for my selected focus areas.",
        "continue_triage": "Continue priority triage of the current corpus without broadening the search.",
        "prepare_narrowing_review": "Rebuild the narrowing map from the evidence filtered so far and continue automatically if no researcher decision is needed.",
        "refine": "Refine the current corpus using priority triage and citation chaining, then reassess saturation before asking me to decide.",
        "retained_corpus_checkpoint": "Show me the retained-paper count and full-text coverage, then let me choose between local acquisition now or narrowing to Evidence Candidates first.",
        "acquire_retained_locally": "Run the local full-text acquisition pass for the retained papers and continue automatically when it finishes.",
        "rank_evidence_candidates": "Rank the retained papers into a smaller, coverage-aware Evidence Candidate corpus and show me the result.",
        "evidence_candidate_checkpoint": "Show me the Evidence Candidate count and full-text coverage, then let me choose between local acquisition now or narrowing to Core Papers first.",
        "acquire_evidence_candidates_locally": "Run the local full-text acquisition pass for the Evidence Candidates and continue automatically when it finishes.",
        "rank_core_papers": "Rank the Evidence Candidates into the Core Paper set for deep evidence work and show me the result.",
        "core_paper_checkpoint": "Show me the Core Paper count and full-text coverage, then let me choose whether to run local acquisition before evidence work or continue with current coverage.",
        "acquire_core_papers_locally": "Run the local full-text acquisition pass for the Core Papers and continue automatically when it finishes.",
        "prepare_final_landscape": "Build the Research Landscape from the refined Core Paper corpus.",
        "construct_current_research_landscape": "Build the Research Landscape from the refined Core Paper corpus.",
        "resolve_priority_full_text": "Resolve lawful open-access full text for the selected priority corpus and continue in local batches.",
        "refresh_evidence_after_fulltext": "Refresh affected Evidence Map items against newly available full text and continue.",
        "construct_evidence_map": "Construct the Evidence Map using the strongest source basis currently available.",
        "propose_research_directions": "Propose candidate Research Directions from the Landscape and Evidence Map, then stop for my choice.",
        "researcher_direction_decision": "Show me the candidate Research Directions, recommend the most defensible options, and let me decide.",
        "construct_literature_review_blueprint": "Construct and quality-check the Literature Review Blueprint for the selected Research Direction.",
        "researcher_blueprint_review": "Show me the Literature Review Blueprint in researcher-friendly form and the few substantive decisions I should review before accepting it.",
        "construct_working_draft": "Construct the bounded researcher Working Draft, keeping verification states and substantive researcher decisions visible.",
        "prepare_researcher_package": "Prepare the final researcher package with the paper library, EndNote references, audit files, and Word handoff.",
        "researcher_handoff": "Help me review the remaining source-verification tasks before I continue writing the final literature review.",
    }
    return suggestions.get(action, "Continue with the recommended next step.")
