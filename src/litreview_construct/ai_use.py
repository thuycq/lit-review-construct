from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from .activity import append_activity
from .project import PROJECT_DIR, _atomic_write_text, _write_json

StatementStyle = Literal["short", "standard", "detailed"]

AI_EVENT_LABELS = {
    "research_intent_assistance": "refining the research intent and literature scope",
    "search_assistance": "designing or refining scholarly search queries",
    "paper_prioritization": "title/abstract relevance triage and paper prioritization",
    "research_landscape_synthesis": "synthesizing provisional or final research landscapes",
    "evidence_mapping": "organizing source evidence, methods, theories, findings, and limitations",
    "gap_suggestion": "suggesting provisional research gaps",
    "direction_suggestion": "proposing candidate research directions and provisional novelty claims",
    "blueprint_generation": "constructing the literature-review architecture and evidence-linked blueprint",
    "draft_fragment": "producing limited argument-level draft fragments or wording suggestions",
    "citation_check": "checking citation-to-claim alignment",
    "source_verification": "assisting with source verification",
}

TOOL_EVENT_LABELS = {
    "seed_indexing": "indexing researcher-provided seed papers",
    "literature_discovery": "retrieving and recording scholarly metadata from configured providers",
    "deduplication": "detecting duplicate or version relationships",
    "metadata_extraction": "extracting bibliographic metadata",
    "source_verification": "linking, resolving, or acquiring lawful source files",
    "document_export": "exporting saved researcher artifacts to editable Word documents",
}


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _human_join(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def _artifact_inferences(root: Path) -> list[tuple[str, str]]:
    """Infer only from durable project artifacts that explicitly record AI provenance."""
    state_root = root / PROJECT_DIR
    inferred: list[tuple[str, str]] = []

    plans = _load_jsonl(state_root / "data" / "discovery_query_plans.jsonl")
    if any(row.get("provenance") == "ai_synthesis" for row in plans):
        inferred.append(("search_assistance", AI_EVENT_LABELS["search_assistance"]))

    artifact_checks = [
        ("landscape.json", "research_landscape_synthesis"),
        ("evidence_map.json", "evidence_mapping"),
        ("direction_set.json", "direction_suggestion"),
        ("blueprint.json", "blueprint_generation"),
        ("working_draft.json", "draft_fragment"),
    ]
    for filename, category in artifact_checks:
        artifact = _load_json(state_root / "data" / filename)
        if artifact and artifact.get("provenance") == "ai_synthesis":
            inferred.append((category, AI_EVENT_LABELS[category]))

    return inferred


def summarize_ai_use(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    activity_file = root / PROJECT_DIR / "activity" / "activity.jsonl"
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")

    events = _load_jsonl(activity_file)
    ai_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    hosts: set[str] = set()
    models: set[str] = set()

    for event in events:
        category = str(event.get("category") or "")
        actor = str(event.get("actor") or "")
        if event.get("host"):
            hosts.add(str(event["host"]))
        if event.get("model"):
            models.add(str(event["model"]))
        if actor == "ai_assisted" and category in AI_EVENT_LABELS:
            ai_counts[category] += 1
        elif actor == "toolkit" and category in TOOL_EVENT_LABELS:
            tool_counts[category] += 1

    # Older/dev projects may contain AI-provenance artifacts before activity logging was wired in.
    for category, _ in _artifact_inferences(root):
        if not ai_counts[category]:
            ai_counts[category] = 1

    ai_activities = [
        {
            "category": category,
            "label": AI_EVENT_LABELS[category],
            "events": count,
        }
        for category, count in AI_EVENT_LABELS.items()
        if ai_counts.get(category)
    ]
    tool_activities = [
        {
            "category": category,
            "label": TOOL_EVENT_LABELS[category],
            "events": count,
        }
        for category, count in TOOL_EVENT_LABELS.items()
        if tool_counts.get(category)
    ]
    return {
        "activity_events": len(events),
        "ai_activities": ai_activities,
        "tool_activities": tool_activities,
        "hosts_recorded": sorted(hosts),
        "models_recorded": sorted(models),
        "scope_note": "This summary reflects only activities recorded inside this Lit Review Construct project.",
    }


def _short_statement(summary: dict[str, object]) -> str:
    activities = [str(row["label"]) for row in summary["ai_activities"]]
    if not activities:
        return (
            "No AI-assisted research activities are recorded in this Lit Review Construct project. "
            "This statement reflects the project activity log only."
        )
    return (
        "AI-assisted tools were used to support "
        + _human_join(activities)
        + ". The researcher retained responsibility for source verification, scholarly judgment, "
        "research decisions, citation selection, and the final written literature review."
    )


def _standard_statement(summary: dict[str, object]) -> str:
    activities = [str(row["label"]) for row in summary["ai_activities"]]
    tool_activities = [str(row["label"]) for row in summary["tool_activities"]]
    if not activities:
        return _short_statement(summary)
    text = (
        "AI-assisted functionality within Lit Review Construct was used to support "
        + _human_join(activities)
        + ". These activities were used as research support rather than as a substitute for scholarly judgment or authorship. "
    )
    if tool_activities:
        text += "The workflow also used deterministic tooling for " + _human_join(tool_activities) + ". "
    text += (
        "The researcher remained responsible for evaluating relevance, verifying source content and citations, "
        "selecting the research direction, interpreting the literature, rewriting and approving any AI-assisted draft fragments, "
        "and authoring the final manuscript text. This disclosure is generated from the activities recorded in this project and "
        "does not claim uses that were not logged."
    )
    return text


def _detailed_statement(summary: dict[str, object]) -> str:
    activities = [str(row["label"]) for row in summary["ai_activities"]]
    tool_activities = [str(row["label"]) for row in summary["tool_activities"]]
    if not activities:
        return _short_statement(summary)
    details = []
    for row in summary["ai_activities"]:
        details.append(f"{row['label']} ({row['events']} recorded event{'s' if row['events'] != 1 else ''})")
    text = (
        "Lit Review Construct was used as an AI-assisted research support environment. Recorded AI-assisted activities included "
        + _human_join(details)
        + ". "
    )
    if tool_activities:
        text += "Non-generative toolkit operations additionally included " + _human_join(tool_activities) + ". "
    hosts = summary.get("hosts_recorded") or []
    models = summary.get("models_recorded") or []
    if hosts:
        text += "Recorded host environment(s): " + ", ".join(str(value) for value in hosts) + ". "
    if models:
        text += "Recorded model identifier(s): " + ", ".join(str(value) for value in models) + ". "
    text += (
        "AI outputs were treated as suggestions or working material requiring researcher review. "
        "The researcher retained responsibility for relevance decisions, source and citation verification, interpretation, "
        "the final research direction, rewriting and approving draft fragments, the final prose, and research integrity. "
        "This statement is limited to the auditable activities recorded inside this project."
    )
    return text


def generate_ai_use_statement(root: Path, *, style: StatementStyle = "standard") -> dict[str, object]:
    if style not in {"short", "standard", "detailed"}:
        raise ValueError("AI-use statement style must be short, standard, or detailed.")
    root = root.expanduser().resolve()
    summary = summarize_ai_use(root)
    variants = {
        "short": _short_statement(summary),
        "standard": _standard_statement(summary),
        "detailed": _detailed_statement(summary),
    }
    selected = variants[style]
    payload = {
        "schema_version": 1,
        "selected_style": style,
        "statement": selected,
        "variants": variants,
        "activity_summary": summary,
    }
    state_root = root / PROJECT_DIR
    _write_json(state_root / "data" / "ai_use_statement.json", payload)

    lines = [
        "# AI Use Statement",
        "",
        "## Selected statement",
        "",
        selected,
        "",
        "## Short variant",
        "",
        variants["short"],
        "",
        "## Standard variant",
        "",
        variants["standard"],
        "",
        "## Detailed variant",
        "",
        variants["detailed"],
        "",
        "> This statement is generated only from recorded project activity and should be adapted to the applicable journal, institution, course, or funder policy without adding unrecorded AI uses.",
        "",
    ]
    output = root / "outputs" / "07_ai_use_statement.md"
    _atomic_write_text(output, "\n".join(lines))
    append_activity(
        root,
        category="ai_use_disclosure",
        actor="toolkit",
        inputs={"style": style},
        outputs=[".litreview/data/ai_use_statement.json", "outputs/07_ai_use_statement.md"],
        notes="Generated an AI-use statement strictly from the project's recorded activity.",
    )
    return {
        "style": style,
        "statement": selected,
        "output": str(output),
        "activity_events": summary["activity_events"],
        "ai_activity_categories": len(summary["ai_activities"]),
    }
