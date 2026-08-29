from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml

from .project import PROJECT_DIR, STAGES, _atomic_write_text, _now, _write_json, _write_yaml


def _paths(root: Path) -> tuple[Path, Path, Path]:
    root = root.expanduser().resolve()
    state_root = root / PROJECT_DIR
    project_file = state_root / "project.yaml"
    state_file = state_root / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root, project_file, state_file


def _load(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    root, project_file, state_file = _paths(root)
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    state = json.loads(state_file.read_text(encoding="utf-8"))
    return root, project, state


def _missing_fields(project: dict[str, object]) -> list[str]:
    research = project.get("research") or {}
    if not isinstance(research, dict):
        return ["research_question_or_topic", "publication_period", "languages"]
    missing: list[str] = []
    if not (research.get("research_question") or research.get("topic")):
        missing.append("research_question_or_topic")
    period = research.get("publication_period") or {}
    if not isinstance(period, dict) or period.get("from") is None or period.get("to") is None:
        missing.append("publication_period")
    languages = research.get("languages") or []
    if not isinstance(languages, list) or not languages:
        missing.append("languages")
    return missing


def _render(root: Path, project: dict[str, object], status: str) -> Path:
    research = project["research"]
    assert isinstance(research, dict)
    period = research.get("publication_period") or {}
    if not isinstance(period, dict):
        period = {}
    languages = research.get("languages") or []
    lines = [
        "# Research Intent",
        "",
        f"**Status:** {status}",
        "",
        "## Topic",
        "",
        str(research.get("topic") or "Not yet specified."),
        "",
        "## Research question",
        "",
        str(research.get("research_question") or "Not yet specified."),
        "",
        "## Literature scope",
        "",
        f"- Publication period: {period.get('from') or 'Not set'}–{period.get('to') or 'Not set'}",
        f"- Paper language(s): {', '.join(str(x) for x in languages) if languages else 'Not set'}",
        "",
        "> Publication period refers to the literature search scope, not the sample/data period inside individual studies.",
        "",
    ]
    output = root / "outputs" / "01_research_intent.md"
    _atomic_write_text(output, "\n".join(lines))
    return output


def _log(root: Path, category: str, inputs: dict[str, object], outputs: list[str]) -> None:
    activity_file = root / PROJECT_DIR / "activity" / "activity.jsonl"
    event = {
        "event_id": str(uuid4()),
        "timestamp": _now(),
        "category": category,
        "actor": "toolkit",
        "host": None,
        "model": None,
        "inputs": inputs,
        "outputs": outputs,
        "source_ids": [],
        "notes": None,
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def set_intent(
    root: Path,
    *,
    topic: str | None = None,
    research_question: str | None = None,
    publication_from: int | None = None,
    publication_to: int | None = None,
    languages: list[str] | None = None,
) -> dict[str, object]:
    root, project, state = _load(root)
    research = project.setdefault("research", {})
    assert isinstance(research, dict)
    period = research.setdefault("publication_period", {"from": None, "to": None})
    assert isinstance(period, dict)

    before = json.dumps(research, ensure_ascii=False, sort_keys=True)
    if topic is not None:
        research["topic"] = topic.strip() or None
    if research_question is not None:
        research["research_question"] = research_question.strip() or None
    if publication_from is not None:
        period["from"] = publication_from
    if publication_to is not None:
        period["to"] = publication_to
    if languages is not None:
        cleaned = [item.strip() for item in languages if item.strip()]
        research["languages"] = list(dict.fromkeys(cleaned))

    start = period.get("from")
    end = period.get("to")
    if start is not None and end is not None and int(start) > int(end):
        raise ValueError("Publication period start year cannot be after end year.")

    after = json.dumps(research, ensure_ascii=False, sort_keys=True)
    changed = before != after
    intent_state = state["stages"]["research_intent"]
    was_accepted = intent_state["status"] == "accepted"
    missing = _missing_fields(project)

    if changed:
        intent_state["revision"] += 1
        intent_state["status"] = "in_progress" if missing else "ready_for_review"
        state["current_stage"] = "research_intent"
        if was_accepted:
            for stage_name in STAGES[1:]:
                downstream = state["stages"][stage_name]
                if downstream["status"] not in {"not_started", "blocked"}:
                    downstream["status"] = "needs_refresh"

    project["updated_at"] = _now()
    _write_yaml(root / PROJECT_DIR / "project.yaml", project)
    _write_json(root / PROJECT_DIR / "state.json", state)
    output = _render(root, project, intent_state["status"])
    if changed:
        _log(
            root,
            "research_intent_assistance",
            {"fields_updated": True},
            [".litreview/project.yaml", ".litreview/state.json", "outputs/01_research_intent.md"],
        )
    return {
        "changed": changed,
        "status": intent_state["status"],
        "revision": intent_state["revision"],
        "missing": missing,
        "research": research,
        "output": str(output),
    }


def show_intent(root: Path) -> dict[str, object]:
    root, project, state = _load(root)
    intent_state = state["stages"]["research_intent"]
    output = _render(root, project, intent_state["status"])
    return {
        "status": intent_state["status"],
        "revision": intent_state["revision"],
        "missing": _missing_fields(project),
        "research": project["research"],
        "output": str(output),
    }


def accept_intent(root: Path) -> dict[str, object]:
    root, project, state = _load(root)
    missing = _missing_fields(project)
    if missing:
        raise ValueError("Research Intent is incomplete: " + ", ".join(missing))

    intent_state = state["stages"]["research_intent"]
    intent_state["status"] = "accepted"
    if state["stages"]["seed_literature"]["status"] == "in_progress":
        state["current_stage"] = "seed_literature"
    else:
        state["current_stage"] = "seed_literature"

    _write_json(root / PROJECT_DIR / "state.json", state)
    output = _render(root, project, "accepted")
    _log(
        root,
        "research_intent_acceptance",
        {},
        [".litreview/state.json", "outputs/01_research_intent.md"],
    )
    return {
        "status": "accepted",
        "revision": intent_state["revision"],
        "research": project["research"],
        "output": str(output),
    }
