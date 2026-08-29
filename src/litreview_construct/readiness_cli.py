from __future__ import annotations

import json
from pathlib import Path

import typer

from . import main_cli as discovery_cli
from .main_cli import discover_app
from .project import PROJECT_DIR, _write_json
from .readiness import assess_discovery_readiness


_previous_record_decision = discovery_cli.record_discovery_decision


def _record_decision_with_readiness(
    root: Path,
    *,
    action: str,
    selected_focuses: list[str] | None = None,
    researcher_notes: str | None = None,
) -> dict[str, object]:
    assessment = assess_discovery_readiness(root) if action == "finish" else None
    result = _previous_record_decision(
        root,
        action=action,  # type: ignore[arg-type]
        selected_focuses=selected_focuses,
        researcher_notes=researcher_notes,
    )
    if assessment is not None:
        campaign_file = root.expanduser().resolve() / PROJECT_DIR / "data" / "discovery_campaign.json"
        campaign = json.loads(campaign_file.read_text(encoding="utf-8"))
        campaign["completion_assessment"] = assessment
        completion = campaign.get("researcher_completion")
        if isinstance(completion, dict):
            completion["coverage_snapshot"] = assessment
        _write_json(campaign_file, campaign)
        result["coverage_snapshot"] = assessment
        result["coverage_warnings"] = assessment["warnings"]
    return result


# main_cli's command body resolves this module global at runtime. app_cli has already replaced it
# with the activity-logging wrapper; this layer adds the finish-time coverage snapshot without
# bypassing the activity log.
discovery_cli.record_discovery_decision = _record_decision_with_readiness


@discover_app.command("readiness")
def discover_readiness(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = assess_discovery_readiness(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return

    typer.echo("Discovery readiness (advisory; researcher decides sufficiency)")
    typer.echo(f"Indexed records: {result['indexed_records']}")
    typer.echo(
        f"Successful scholarly providers: {result['successful_provider_count']} "
        f"({', '.join(result['successful_providers']) or 'none'})"
    )
    typer.echo(f"Successful query families: {result['successful_query_family_count']}")
    typer.echo(f"Saved Query Plans: {result['saved_query_plans']}")
    typer.echo(f"Researcher review checkpoints: {result['review_checkpoints']}")
    typer.echo(
        f"Triaged records: {result['triaged_records']} / {result['indexed_records']} "
        f"({result['triage_ratio']:.1%})"
    )
    typer.echo(f"Retained records: {result['retained_records']}")
    typer.echo(f"Unresolved records: {result['unresolved_records']}")
    typer.echo(f"Citation graph edges: {result['graph_edges']}")
    if result["strengths"]:
        typer.echo("Coverage strengths:")
        for strength in result["strengths"]:
            typer.echo(f"  + {strength}")
    if result["warnings"]:
        typer.echo("Coverage warnings:")
        for warning in result["warnings"]:
            typer.echo(f"  - {warning}")
