from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import app
from .word_export import ARTIFACTS, export_artifact_docx


export_app = typer.Typer(help="Export saved Lit Review Construct artifacts to presentation formats.")
app.add_typer(export_app, name="export")


@export_app.command("docx")
def export_docx(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    artifact: str = typer.Option(
        "handoff",
        "--artifact",
        help=(
            "Artifact to export: " + ", ".join([*ARTIFACTS, "handoff"])
        ),
    ),
    output: Path | None = typer.Option(None, "--output", help="Optional destination .docx path."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = export_artifact_docx(path, artifact=artifact, output=output)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Word export: {result['artifact']}")
    if result.get("included"):
        typer.echo("Included: " + ", ".join(result["included"]))
    typer.echo(f"Output: {result['output']}")
