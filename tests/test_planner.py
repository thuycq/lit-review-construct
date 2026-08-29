import json
from pathlib import Path

import pytest

from litreview_construct.campaign import start_discovery_campaign
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.planner import prepare_query_plan, save_query_plan
from litreview_construct.project import init_project


def _accepted_project(root: Path) -> Path:
    init_project(root, name="Query Planner Test")
    set_intent(
        root,
        topic="working capital management and firm performance",
        research_question="How does working capital management relate to firm performance?",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    return root


def _valid_plan(phase: str = "broad") -> dict:
    return {
        "phase": phase,
        "summary": "Use interpretable query families covering the focal relationship and terminology variants.",
        "query_families": [
            {
                "name": "Direct relationship",
                "role": "direct_construct" if phase == "broad" else "focused_followup",
                "query": (
                    "working capital firm performance"
                    if phase == "broad"
                    else "nonlinear working capital firm value"
                ),
                "rationale": "Captures the focal relationship directly.",
                "concepts": ["working capital", "firm performance"],
                "priority": "high",
            },
            {
                "name": "Cash conversion terminology",
                "role": "synonym" if phase == "broad" else "focused_followup",
                "query": (
                    "cash conversion cycle profitability"
                    if phase == "broad"
                    else "optimal cash conversion cycle profitability"
                ),
                "rationale": "Captures a common operationalization used in the literature.",
                "concepts": ["cash conversion cycle", "profitability"],
                "priority": "high",
            },
            {
                "name": "Financing mechanism",
                "role": "mechanism" if phase == "broad" else "focused_followup",
                "query": (
                    "working capital financing constraints trade credit"
                    if phase == "broad"
                    else "working capital optimum financing constraints"
                ),
                "rationale": "Adds a mechanism-oriented route into the literature.",
                "concepts": ["financing constraints", "trade credit"],
                "priority": "medium",
            },
        ],
        "coverage_notes": ["The plan intentionally uses several complementary terminology families."],
        "limitations": ["The plan does not guarantee exhaustive retrieval."],
    }


def test_broad_query_plan_is_structured_and_persisted(tmp_path: Path) -> None:
    root = _accepted_project(tmp_path)
    prepared = prepare_query_plan(root, phase="broad")
    packet = json.loads(Path(prepared["packet_file"]).read_text(encoding="utf-8"))
    assert packet["phase"] == "broad"
    assert packet["research_intent"]["topic"] == "working capital management and firm performance"
    assert packet["analysis_contract"]["prohibited"]

    submission = root / "query_plan_submission.json"
    submission.write_text(json.dumps(_valid_plan()), encoding="utf-8")
    saved = save_query_plan(root, submission)
    assert saved["query_count"] == 3
    assert len(saved["queries"]) == 3

    current = json.loads(
        (root / ".litreview" / "data" / "discovery_query_plan.json").read_text(encoding="utf-8")
    )
    assert current["plan_id"] == saved["plan_id"]
    assert current["provenance"] == "ai_synthesis"
    history = [
        json.loads(line)
        for line in (root / ".litreview" / "data" / "discovery_query_plans.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(history) == 1


def test_query_plan_rejects_duplicate_queries(tmp_path: Path) -> None:
    root = _accepted_project(tmp_path)
    prepare_query_plan(root, phase="broad")
    plan = _valid_plan()
    plan["query_families"][1]["query"] = plan["query_families"][0]["query"].upper()
    submission = root / "duplicate_plan.json"
    submission.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="unique query strings"):
        save_query_plan(root, submission)


def test_focused_query_plan_requires_researcher_selected_focus(tmp_path: Path) -> None:
    root = _accepted_project(tmp_path)
    start_discovery_campaign(root)
    with pytest.raises(ValueError, match="researcher-selected discovery focus"):
        prepare_query_plan(root, phase="focused")

    campaign_file = root / ".litreview" / "data" / "discovery_campaign.json"
    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    campaign["status"] = "focused"
    campaign["selected_focuses"] = ["Nonlinear working-capital optimization"]
    campaign["iterations"] = [
        {
            "iteration_id": "broad-1",
            "queries": ["working capital firm performance", "cash conversion cycle profitability"],
            "providers": ["openalex", "crossref", "semantic_scholar"],
        }
    ]
    campaign_file.write_text(json.dumps(campaign), encoding="utf-8")

    prepared = prepare_query_plan(root, phase="focused")
    packet = json.loads(Path(prepared["packet_file"]).read_text(encoding="utf-8"))
    assert packet["selected_focuses"] == ["Nonlinear working-capital optimization"]
    assert len(packet["previous_query_families"]) == 2

    submission = root / "focused_plan.json"
    submission.write_text(json.dumps(_valid_plan("focused")), encoding="utf-8")
    saved = save_query_plan(root, submission)
    assert saved["phase"] == "focused"
