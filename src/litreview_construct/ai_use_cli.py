from __future__ import annotations

import json
from pathlib import Path

import typer

from .ai_use import generate_ai_use_statement, summarize_ai_use
from .app_cli import app


ai_use_app = typer.Typer(help="Summarize recorded AI assistance and generate an auditable AI-use statement.")
app.add_typer(ai_use_app, name="ai-use")


@ai_use_app.command("summary")
def ai_use_summary(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = summarize_ai_use(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Recorded activity events: {result['activity_events']}")
    typer.echo("AI-assisted activities:")
    if result["ai_activities"]:
        for row in result["ai_activities"]:
            typer.echo(f"  - {row['label']} ({row['events']})")
    else:
        typer.echo("  - none recorded")
    if result["tool_activities"]:
        typer.echo("Deterministic toolkit activities:")
        for row in result["tool_activities"]:
            typer.echo(f"  - {row['label']} ({row['events']})")


@ai_use_app.command("generate")
def ai_use_generate(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    style: str = typer.Option("standard", "--style", help="short, standard, or detailed"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = generate_ai_use_statement(path, style=style)  # type: ignore[arg-type]
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"AI-use statement style: {result['style']}")
    typer.echo(result["statement"])
    typer.echo(f"Output: {result['output']}")
