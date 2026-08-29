from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml

PROJECT_DIR = ".litreview"
SCHEMA_VERSION = 1
STAGES = [
    "research_intent",
    "seed_literature",
    "literature_discovery",
    "evidence_mapping",
    "research_direction",
    "literature_review_blueprint",
    "researcher_handoff",
]

AGENTS_TEXT = """# Lit Review Construct Project\n\nThis folder is a Lit Review Construct research workspace.\n\n## North-star objective\n\nHelp the researcher construct the literature behind a study: define the literature scope, discover sufficiently broad scholarship before narrowing, understand the research landscape, organize source-disciplined evidence, reason about defensible research directions, and construct a Literature Review Blueprint that the researcher can use to write the final review. Do not turn the project into a generic academic search exercise or replace the researcher as author.\n\n## Project rules\n\n- Treat `.litreview/` as the authoritative project state. Conversation history is not the project database.\n- For an unspecified request to continue/resume/proceed, run `lrc next . --json` and follow the routed Lit Review Construct skill rather than guessing the next stage.\n- Stop whenever `lrc next` says `human_checkpoint_required: true`; do not make researcher decisions silently.\n- Use the globally installed `lrc` runtime for structured project operations when available.\n- Do not create a project-local Python environment (`.venv`, `venv`) just to run Lit Review Construct. If `lrc` is missing or outdated, update/reinstall the toolkit from its installation repository instead.\n- Preserve source, search, evidence, AI-synthesis, and researcher-judgment provenance.\n- Persist important research decisions and outputs locally rather than relying on conversation history.\n- Keep large literature corpora local and use bounded packets for model context.\n- AI may assist with search planning, literature discovery, triage, synthesis, evidence organization, research-direction reasoning, and literature-review architecture.\n- Treat gap and novelty suggestions as provisional until supported by adequate discovery coverage and source verification.\n- The principal construction output is the Literature Review Blueprint.\n- Do not generate a complete final literature review intended for direct submission. The researcher remains responsible for scholarly judgment, verification, authorship, final prose, citation selection, accuracy, and research integrity.\n"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temp.write_text(content, encoding="utf-8")
    os.replace(temp, path)


def _write_json(path: Path, value: object) -> None:
    _atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _write_yaml(path: Path, value: object) -> None:
    _atomic_write_text(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def init_project(root: Path, name: str | None = None) -> dict[str, object]:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    state_root = root / PROJECT_DIR
    project_file = state_root / "project.yaml"

    if project_file.exists():
        return {"created": False, "root": str(root), "message": "Project already initialized."}

    now = _now()
    project_id = str(uuid4())

    for relative in [
        "data",
        "searches",
        "activity",
        "packets",
        "cache",
        "locks",
    ]:
        (state_root / relative).mkdir(parents=True, exist_ok=True)

    (root / "papers").mkdir(exist_ok=True)
    (root / "outputs").mkdir(exist_ok=True)

    project = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "name": name or root.name,
        "created_at": now,
        "updated_at": now,
        "review_type": "narrative",
        "research": {
            "topic": None,
            "research_question": None,
            "publication_period": {"from": None, "to": None},
            "languages": [],
        },
        "paper_sources": [{"type": "project_folder", "path": "papers"}],
        "external_paper_folders": [],
        "hosts_seen": [],
    }

    state = {
        "schema_version": SCHEMA_VERSION,
        "current_stage": "research_intent",
        "stages": {
            stage: {
                "status": "not_started" if stage != "research_intent" else "in_progress",
                "revision": 0,
            }
            for stage in STAGES
        },
    }

    event = {
        "event_id": str(uuid4()),
        "timestamp": now,
        "category": "project_initialization",
        "actor": "toolkit",
        "host": None,
        "model": None,
        "inputs": [],
        "outputs": [
            ".litreview/project.yaml",
            ".litreview/state.json",
            "AGENTS.md",
        ],
        "source_ids": [],
        "notes": None,
    }

    _write_yaml(project_file, project)
    _write_json(state_root / "state.json", state)
    _write_json(state_root / "data" / "blueprint.json", {})
    _atomic_write_text(state_root / "activity" / "activity.jsonl", json.dumps(event) + "\n")

    agents_file = root / "AGENTS.md"
    if not agents_file.exists():
        _atomic_write_text(agents_file, AGENTS_TEXT)

    return {
        "created": True,
        "root": str(root),
        "project_id": project_id,
        "project_file": str(project_file),
    }


def read_status(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    state_root = root / PROJECT_DIR
    project_file = state_root / "project.yaml"
    state_file = state_root / "state.json"
    if not project_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")

    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    state = json.loads(state_file.read_text(encoding="utf-8"))
    current_stage = state["current_stage"]
    return {
        "root": str(root),
        "name": project["name"],
        "review_type": project["review_type"],
        "current_stage": current_stage,
        "stage_status": state["stages"][current_stage]["status"],
        "schema_version": state["schema_version"],
    }


def doctor(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    checks: list[dict[str, object]] = []

    state_root = root / PROJECT_DIR
    project_file = state_root / "project.yaml"
    state_file = state_root / "state.json"
    checks.append({"name": "project.yaml", "ok": project_file.exists()})
    checks.append({"name": "state.json", "ok": state_file.exists()})
    checks.append({"name": "outputs directory", "ok": (root / "outputs").is_dir()})

    if project_file.exists():
        try:
            project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
            checks.append({"name": "project schema", "ok": project.get("schema_version") == SCHEMA_VERSION})
        except Exception as exc:
            checks.append({"name": "project parse", "ok": False, "detail": str(exc)})

    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            checks.append({"name": "state schema", "ok": state.get("schema_version") == SCHEMA_VERSION})
        except Exception as exc:
            checks.append({"name": "state parse", "ok": False, "detail": str(exc)})

    return {
        "ok": all(check["ok"] for check in checks),
        "root": str(root),
        "checks": checks,
    }
