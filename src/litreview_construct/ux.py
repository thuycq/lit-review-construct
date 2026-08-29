from __future__ import annotations

from typing import Mapping


def suggested_user_message(result: Mapping[str, object]) -> str:
    """Return a short researcher-facing message that can advance the saved workflow.

    This is guidance only. It never substitutes for a required researcher decision.
    """
    action = str(result.get("next_action") or "")
    suggestions = {
        "complete_research_intent": "Help me complete the Research Intent using what I have already provided.",
        "review_seed_inventory": "Show me the seed-paper inventory and let me confirm it.",
        "ask_seed_literature": "Continue the setup and ask me about any existing related papers.",
        "start_discovery": "Start the literature discovery campaign and proceed with the recommended next step.",
        "prepare_broad_query_plan": "Prepare the broad discovery query plan and continue.",
        "run_saved_query_plan": "Run the saved discovery query plan and show me the results when the next researcher checkpoint is reached.",
        "prepare_early_review": "Build the initial discovery map and show me the research streams and focus options.",
        "researcher_decision_required": "Proceed with your recommended discovery option, but ask me before recording any researcher decision.",
        "revise_research_intent": "Help me revise the research scope based on the discovery results.",
        "prepare_focused_query_plan": "Prepare and run the focused discovery plan for my selected focus areas.",
        "continue_triage": "Filter another priority batch from the current corpus, without broadening the search.",
        "prepare_narrowing_review": "Build the updated narrowing map from the papers filtered so far and show me the next options.",
        "prepare_final_landscape": "Build the current Research Landscape from the retained literature.",
        "construct_current_research_landscape": "Build the current Research Landscape from the retained literature.",
        "construct_evidence_map": "Construct the Evidence Map using the current Research Landscape and verified source basis.",
        "propose_research_directions": "Propose candidate Research Directions from the current Landscape and Evidence Map, then stop for my choice.",
        "researcher_direction_decision": "Show me the candidate Research Directions and recommend which ones are most defensible, but let me decide.",
        "construct_literature_review_blueprint": "Construct the Literature Review Blueprint for the selected Research Direction.",
        "researcher_blueprint_review": "Show me the Literature Review Blueprint and the main decisions I should review before accepting it.",
        "researcher_handoff": "Show me the researcher handoff and the optional AI-use statement based only on recorded project activity.",
    }
    return suggestions.get(action, "Continue with the recommended next step from the saved project state.")
