from __future__ import annotations

import json
from pathlib import Path

import typer

from .finalize import prepare_final_landscape_packet
from .main_cli import app, discover_app


@discover_app.command("prepare-landscape")
def discover_prepare_landscape(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    max_papers: int = typer.Option(
        80,
        "--max-papers",
        min=20,
        max=150,
        help="Maximum retained papers in the final Research Landscape packet.",
    ),
    abstract_chars: int = typer.Option(
        2200,
        "--abstract-chars",
        min=300,
        max=5000,
        help="Maximum abstract characters per retained paper.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_final_landscape_packet(
            path,
            max_papers=max_papers,
            abstract_chars=abstract_chars,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Indexed records: {result['indexed_records']}")
    typer.echo(f"Triaged records: {result['triaged_records']}")
    typer.echo(f"Retained records: {result['retained_records']}")
    typer.echo(f"Landscape packet records: {result['packet_records']}")
    if result["warnings"]:
        typer.echo("Coverage warnings:")
        for warning in result["warnings"]:
            typer.echo(f"  - {warning}")
    typer.echo(f"Landscape packet: {result['packet_file']}")
