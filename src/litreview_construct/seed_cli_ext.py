from __future__ import annotations

import json
from pathlib import Path

import typer

from .cli import seed_app
from .seed_state import accept_seed_inventory, skip_seed_literature


@seed_app.command("accept")
def seed_accept(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = accept_seed_inventory(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(
        f"Seed inventory acknowledged ({result['indexed_seed_records']} indexed records). "
        "This does not mark them relevant."
    )


@seed_app.command("skip")
def seed_skip(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = skip_seed_literature(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo("Recorded that no seed literature is currently available.")
