from __future__ import annotations

import json
from pathlib import Path

from .activity import append_activity
from .project import PROJECT_DIR, _write_json


def _load(root: Path) -> tuple[Path, dict[str, object]]:
    root = root.expanduser().resolve()
    state_file = root / PROJECT_DIR / "state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root, json.loads(state_file.read_text(encoding="utf-8"))


def _user_seed_count(root: Path) -> int:
    papers_file = root / PROJECT_DIR / "data" / "papers.jsonl"
    if not papers_file.exists():
        return 0
    count = 0
    for line in papers_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("source_origin") == "user_seed":
            count += 1
    return count


def accept_seed_inventory(root: Path) -> dict[str, object]:
    root, state = _load(root)
    count = _user_seed_count(root)
    if count == 0:
        raise ValueError("No researcher-provided seed papers are indexed. Use 'lrc seed skip' if there are no seed papers.")
    record = {
        "schema_version": 1,
        "decision": "seed_inventory_acknowledged",
        "has_seed_literature": True,
        "indexed_seed_records": count,
        "provenance": "researcher_judgment",
        "relevance_assumption": "none",
    }
    _write_json(root / PROJECT_DIR / "data" / "seed_decision.json", record)
    state["stages"]["seed_literature"]["status"] = "accepted"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)
    append_activity(
        root,
        category="seed_literature_decision",
        actor="researcher",
        inputs={"has_seed_literature": True, "indexed_seed_records": count},
        outputs=[".litreview/data/seed_decision.json", ".litreview/state.json"],
        notes="Researcher acknowledged the seed inventory; seed status does not imply relevance.",
    )
    return {"status": "accepted", "has_seed_literature": True, "indexed_seed_records": count}


def skip_seed_literature(root: Path) -> dict[str, object]:
    root, state = _load(root)
    count = _user_seed_count(root)
    if count:
        raise ValueError(
            "Researcher-provided seed papers are already indexed. Acknowledge them with 'lrc seed accept'; this does not mark them relevant."
        )
    record = {
        "schema_version": 1,
        "decision": "no_seed_literature",
        "has_seed_literature": False,
        "indexed_seed_records": 0,
        "provenance": "researcher_judgment",
    }
    _write_json(root / PROJECT_DIR / "data" / "seed_decision.json", record)
    state["stages"]["seed_literature"]["status"] = "accepted"
    state["current_stage"] = "literature_discovery"
    _write_json(root / PROJECT_DIR / "state.json", state)
    append_activity(
        root,
        category="seed_literature_decision",
        actor="researcher",
        inputs={"has_seed_literature": False},
        outputs=[".litreview/data/seed_decision.json", ".litreview/state.json"],
        notes="Researcher indicated that no seed literature was available at this stage.",
    )
    return {"status": "accepted", "has_seed_literature": False, "indexed_seed_records": 0}
