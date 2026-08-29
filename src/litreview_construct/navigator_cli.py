from __future__ import annotations

import json
from pathlib import Path

import typer

from .main_cli import discover_app
from .navigator import discovery_next_step


@discover_app.command("next")
def discover_next(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = discovery_next_step(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return

    typer.echo(f"Next discovery action: {result['next_action']}")
    typer.echo(f"Campaign status: {result['campaign_status']}")
    typer.echo(f"Researcher checkpoint required: {result['human_checkpoint_required']}")
    typer.echo(f"Reason: {result['reason']}")
    if result.get("selected_focuses"):
        typer.echo("Selected focuses: " + "; ".join(result["selected_focuses"]))
    if result.get("commands"):
        typer.echo("Runtime action(s):")
        for command in result["commands"]:
            typer.echo(f"  {command}")
