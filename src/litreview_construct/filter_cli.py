from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import typer

from .activity import append_activity
from .main_cli import discover_app
from .project import PROJECT_DIR


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_filter_decision(root: Path, researcher_notes: str | None = None) -> dict[str, object]:
    root = root.expanduser().resolve()
    campaign_file = root / PROJECT_DIR / "data" / "discovery_campaign.json"
    state_file = root / PROJECT_DIR / "state.json"
    if not campaign_file.exists() or not state_file.exists():
        raise FileNotFoundError(f"No active Lit Review Construct discovery campaign found at {root}")

    campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
    checkpoints = campaign.get("review_checkpoints") or []
    if not checkpoints or campaign.get("status") != "awaiting_researcher":
        raise ValueError("A saved discovery review checkpoint is required before requesting more filtering.")

    selected_focuses = campaign.get("selected_focuses") or []
    event = {
        "timestamp": _now(),
        "action": "filter",
        "selected_focuses": [],
        "researcher_notes": researcher_notes,
    }
    checkpoints[-1]["decision"] = event
    campaign["review_checkpoints"] = checkpoints
    campaign["updated_at"] = event["timestamp"]
    # Filtering changes no scholarly scope and performs no retrieval. Preserve current focuses.
    campaign["status"] = "focused" if selected_focuses else "collecting"
    campaign["selected_focuses"] = selected_focuses
    campaign_file.write_text(json.dumps(campaign, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["literature_discovery"]["status"] = "in_progress"
    state["current_stage"] = "literature_discovery"
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_activity(
        root,
        category="discovery_scope_decision",
        actor="researcher",
        inputs={"action": "filter", "researcher_notes": researcher_notes},
        outputs=[".litreview/data/discovery_campaign.json"],
        notes="Researcher chose to continue filtering the existing corpus without additional retrieval.",
    )
    return {
        "action": "filter",
        "status": campaign["status"],
        "selected_focuses": selected_focuses,
        "campaign_file": str(campaign_file),
    }


@discover_app.command("filter")
def discover_filter(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    notes: str | None = typer.Option(None, "--notes", help="Optional researcher notes."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Continue progressive triage of the current corpus without running another search."""
    try:
        result = _record_filter_decision(path, researcher_notes=notes)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo("Discovery decision: filter")
    typer.echo(f"Campaign status: {result['status']}")
    if result["selected_focuses"]:
        typer.echo("Selected focuses preserved: " + "; ".join(result["selected_focuses"]))
