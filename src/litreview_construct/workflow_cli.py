from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import app
from .workflow import project_next_step


@app.command("next")
def project_next(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = project_next_step(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Next action: {result['next_action']}")
    typer.echo(f"Stage: {result['stage']}")
    typer.echo(f"Skill: {result['skill']}")
    typer.echo(f"Human checkpoint required: {result['human_checkpoint_required']}")
    typer.echo(f"Reason: {result['reason']}")
    for command in result.get("commands") or []:
        typer.echo(f"  {command}")
    for command in result.get("optional_commands") or []:
        typer.echo(f"  optional: {command}")
