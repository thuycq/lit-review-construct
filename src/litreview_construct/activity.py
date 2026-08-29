from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .project import PROJECT_DIR


def append_activity(
    root: Path,
    *,
    category: str,
    actor: str,
    inputs: object | None = None,
    outputs: list[str] | None = None,
    source_ids: list[str] | None = None,
    notes: str | None = None,
    host: str | None = None,
    model: str | None = None,
) -> dict[str, object]:
    """Append one meaningful project activity event for later AI-use reporting."""
    root = root.expanduser().resolve()
    activity_file = root / PROJECT_DIR / "activity" / "activity.jsonl"
    activity_file.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "actor": actor,
        "host": host,
        "model": model,
        "inputs": inputs if inputs is not None else {},
        "outputs": outputs or [],
        "source_ids": sorted(set(source_ids or [])),
        "notes": notes,
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event
