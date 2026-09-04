import json
import re
from pathlib import Path

import pytest

from litreview_construct import campaign, finalize, graph_resilient, resilient, triage
from litreview_construct.corpus import rank_corpus, record_decision
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:50]


def _provider_record(provider: str, query: str, index: int) -> dict:
    query_slug = _slug(query)
    suffix = f"{provider}-{query_slug}-{index}"
    if index == 7:
        title = f"Cryptocurrency sentiment and speculative returns {provider} {index}"
        abstract = "This study examines cryptocurrency sentiment and speculative asset returns."
    elif "nonlinear" in query.lower() or "optimal" in query.lower():
        title = f"Nonlinear working capital optimization and firm value {provider} {index}"
        abstract = (
            "This study examines nonlinear working capital policy, cash conversion cycle, "
            "profitability, and firm value."
        )
    elif "cash conversion" in query.lower():
        title = f"Cash conversion cycle and corporate profitability {provider} {index}"
        abstract = (
            "This paper studies cash conversion cycle, liquidity management, profitability, "
            "and firm performance."
        )
    elif "trade credit" in query.lower() or "financing constraints" in query.lower():
        title = f"Trade credit, financing constraints, and working capital {provider} {index}"
        abstract = (
            "This paper studies trade credit, financing constraints, working capital policy, "
            "and corporate investment."
        )
    else:
        title = f"Working capital policy and firm performance {provider} {index}"
        abstract = (
            "This paper studies working capital management, liquidity, profitability, and firm "
            "performance."
        )
    return {
        "title": title,
        "normalized_title": title.lower(),
        "authors": [f"Author {provider} {index}"],
        "year": 2020 + (index % 6),
        "doi": f"10.6000/{suffix}",
        "openalex_id": f"https://openalex.org/W{_slug(suffix).upper()}" if provider == "openalex" else None,
        "s2_paper_id": f"S2-{suffix}" if provider == "semantic_scholar" else None,
        "journal": "Finance Research Journal",
        "language": "en",
        "citation_count": 5 + index * 7,
        "publication_type": "article",
        "abstract": abstract,
        "provider": provider,
    }


def _rows(provider: str, query: str, max_results: int) -> tuple[list[dict], dict]:
    count = min(8, max_results)
    return ([_provider_record(provider, query, index) for index in range(count)], {"calls": 1})


def _review_submission(packet: dict, *, focused: bool) -> dict:
    ids = [row["paper_id"] for row in packet["representative_papers"]]
    assert len(ids) >= 6
    focus_name = "Nonlinear working-capital optimization"
    return {
        "summary": (
            "The literature universe contains several working-capital streams, with nonlinear "
            "optimization emerging as a promising focus."
        ),
        "provisional_streams": [
            {
                "name": "Working-capital efficiency and performance",
                "description": "Studies connecting working-capital policy, liquidity, and firm outcomes.",
                "representative_paper_ids": ids[:3],
                "indicative_terms": ["working capital", "profitability"],
                "provisional_questions": ["Is the relationship nonlinear?"],
                "confidence": "medium",
            },
            {
                "name": "Cash-conversion-cycle research",
                "description": "Studies using the cash conversion cycle as an operating-efficiency construct.",
                "representative_paper_ids": ids[3:6],
                "indicative_terms": ["cash conversion cycle", "liquidity"],
                "provisional_questions": ["Does an optimal cash conversion cycle exist?"],
                "confidence": "medium",
            },
        ],
        "candidate_focuses": [
            {
                "name": focus_name,
                "rationale": "A focused route linking efficiency, liquidity trade-offs, and firm value.",
                "representative_paper_ids": ids[:2],
                "query_suggestions": [
                    "nonlinear working capital firm value",
                    "optimal cash conversion cycle profitability",
                ],
                "why_promising": ["Can reconcile conflicting linear findings"],
                "risks": ["Requires later full-text verification of functional-form claims"],
            }
        ],
        "coverage_observations": [
            "The corpus was retrieved through multiple query families and scholarly providers.",
            "The current map is exploratory rather than a definitive gap assessment.",
        ],
        "recommended_next_actions": [
            "Finish discovery after citation expansion and complete triage."
            if focused
            else "Run focused retrieval around nonlinear working-capital optimization."
        ],
        "limitations": ["Title/abstract evidence is insufficient for a definitive research-gap claim."],
    }


def _save_review(root: Path, *, focused: bool) -> None:
    prepared = (
        triage.prepare_narrowing_review(root, max_papers=80)
        if focused
        else campaign.prepare_discovery_review(root, max_papers=40)
    )
    packet = json.loads(Path(prepared["packet_file"]).read_text(encoding="utf-8"))
    submission = root / ("focused_review.json" if focused else "broad_review.json")
    submission.write_text(json.dumps(_review_submission(packet, focused=focused)), encoding="utf-8")
    saved = campaign.save_discovery_review(root, submission)
    assert saved["status"] == "awaiting_researcher"


def _triage_all_current_records(root: Path) -> None:
    while True:
        status = triage.triage_status(root)
        if status["complete"]:
            return
        prepared = triage.prepare_triage_batch(root, batch_size=200)
        packet = json.loads(Path(prepared["packet_file"]).read_text(encoding="utf-8"))
        items = []
        for paper in packet["papers"]:
            title = str(paper["title"]).lower()
            if "cryptocurrency" in title:
                label, priority, tags = "out_of_scope", "low", []
            elif "nonlinear" in title or "optimal" in title:
                label, priority, tags = "relevant", "core_candidate", ["nonlinear working-capital optimization"]
            elif "cash conversion" in title:
                label, priority, tags = "relevant", "high", ["cash conversion cycle"]
            elif "trade credit" in title or "financing constraints" in title:
                label, priority, tags = "adjacent", "medium", ["financing constraints"]
            else:
                label, priority, tags = "background", "medium", ["working capital and performance"]
            items.append(
                {
                    "paper_id": paper["paper_id"],
                    "label": label,
                    "priority": priority,
                    "rationale": "Classified from supplied title and abstract for discovery narrowing.",
                    "stream_tags": tags,
                    "key_terms": tags,
                    "confidence": "high" if label != "background" else "medium",
                }
            )
        submission = root / "triage_submission.json"
        submission.write_text(
            json.dumps(
                {
                    "batch_summary": "Working-capital papers were retained and search noise was excluded.",
                    "items": items,
                    "emerging_terms": ["nonlinear working capital", "optimal cash conversion cycle"],
                    "emerging_streams": ["nonlinear working-capital optimization"],
                    "notes": [],
                }
            ),
            encoding="utf-8",
        )
        triage.save_triage_batch(root, submission)


def _graph_record(provider: str, seed: dict, relation: str) -> dict:
    seed_fragment = _slug(str(seed["paper_id"]))[:20]
    suffix = f"{provider}-{relation}-{seed_fragment}"
    title = f"Citation-network evidence on optimal working capital {provider} {seed_fragment}"
    return {
        "title": title,
        "normalized_title": title.lower(),
        "authors": ["Network Author"],
        "year": 2025,
        "doi": f"10.7000/{suffix}",
        "openalex_id": f"https://openalex.org/W{suffix.upper()}" if provider == "openalex" else None,
        "s2_paper_id": f"S2-{suffix}" if provider == "semantic_scholar" else None,
        "journal": "Corporate Finance Review",
        "language": "en",
        "citation_count": 15,
        "publication_type": "article",
        "abstract": "This paper studies optimal working capital, nonlinear effects, and firm value.",
        "provider": provider,
    }


def test_working_capital_discovery_funnel_end_to_end(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    init_project(root, name="Working Capital Discovery E2E")
    set_intent(
        root,
        topic="working capital management and firm performance",
        research_question="How does working capital management relate to firm performance, and what directions remain promising?",
        publication_from=2015,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(root)
    campaign.start_discovery_campaign(root)

    monkeypatch.setattr(
        resilient,
        "_search_openalex",
        lambda client, query, start, end, max_results: _rows("openalex", query, max_results),
    )
    monkeypatch.setattr(
        resilient,
        "_search_crossref",
        lambda client, query, start, end, max_results: _rows("crossref", query, max_results),
    )
    monkeypatch.setattr(
        resilient,
        "_search_semantic_scholar",
        lambda client, query, start, end, max_results: _rows("semantic_scholar", query, max_results),
    )

    broad = resilient.run_resilient_discovery_iteration(
        root,
        [
            "working capital firm performance",
            "cash conversion cycle profitability",
            "trade credit financing constraints working capital",
        ],
        max_per_query_provider=20,
    )
    assert broad["providers_succeeded"] == ["crossref", "openalex", "semantic_scholar"]
    assert broad["corpus_records"] >= 60

    _save_review(root, focused=False)
    decision = campaign.record_discovery_decision(
        root,
        action="focus",
        selected_focuses=["Nonlinear working-capital optimization"],
    )
    assert decision["status"] == "focused"

    focused = resilient.run_resilient_discovery_iteration(
        root,
        [
            "nonlinear working capital firm value",
            "optimal cash conversion cycle profitability",
        ],
        phase="focused",
        max_per_query_provider=20,
    )
    assert focused["corpus_records"] > broad["corpus_records"]

    _triage_all_current_records(root)
    triage_state = triage.triage_status(root)
    assert triage_state["complete"] is True
    assert triage_state["labels"]["relevant"] > 0
    assert triage_state["labels"]["out_of_scope"] > 0

    with pytest.raises(ValueError, match="not complete"):
        finalize.prepare_final_landscape_packet(root)

    records = [
        json.loads(line)
        for line in (root / ".litreview" / "data" / "papers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    core_ids = [
        str(row["paper_id"])
        for row in records
        if row.get("triage_priority") == "core_candidate"
    ][:2]
    assert len(core_ids) == 2

    monkeypatch.setattr(
        graph_resilient,
        "_expand_openalex_seed",
        lambda client, seed, relation, start, end, max_results: (
            [("references", _graph_record("openalex", seed, "reference"))],
            {"calls": 1, "resolved": True, "seed_provider_id": seed.get("openalex_id") or seed.get("doi")},
        ),
    )
    monkeypatch.setattr(
        graph_resilient,
        "_expand_s2_seed",
        lambda client, seed, relation, start, end, max_results: (
            [("citations", _graph_record("semantic_scholar", seed, "citation"))],
            {"calls": 1, "resolved": True, "seed_provider_id": seed.get("s2_paper_id") or seed.get("doi")},
        ),
    )
    expanded = graph_resilient.expand_resilient_citation_graph(
        root,
        paper_ids=core_ids,
        relation="both",
        max_per_seed_provider=20,
    )
    assert expanded["new_records"] == 4
    assert expanded["new_graph_edges"] == 4

    _triage_all_current_records(root)
    assert triage.triage_status(root)["complete"] is True

    _save_review(root, focused=True)
    finished = campaign.record_discovery_decision(root, action="finish")
    assert finished["status"] == "complete"

    # New post-triage corpus funnel before deep landscape/evidence work.
    record_decision(root, stage="retained", action="refine")
    evidence = rank_corpus(root, to_tier="evidence")
    assert evidence["selected_records"] > 0
    record_decision(root, stage="evidence", action="refine")
    core = rank_corpus(root, to_tier="core")
    assert core["selected_records"] > 0
    record_decision(root, stage="core", action="continue")

    final = finalize.prepare_final_landscape_packet(root, max_papers=80)
    packet = json.loads(Path(final["packet_file"]).read_text(encoding="utf-8"))
    context = packet["discovery_context"]
    assert context["campaign_status"] == "complete"
    assert context["review_checkpoints"] == 2
    assert context["selected_focuses"] == ["Nonlinear working-capital optimization"]
    assert context["untriaged_records"] == 0
    assert context["graph_edges_total"] == 4
    assert final["retained_records"] > 0
    assert all(
        paper["triage_label"] in {"relevant", "background", "adjacent"}
        for paper in packet["papers"]
    )
    assert all(paper["triage_label"] != "out_of_scope" for paper in packet["papers"])
