from __future__ import annotations

import json
from pathlib import Path

import typer

from . import __version__
from .papers import resolve_bibliography, scan_seed_papers
from .project import doctor as run_doctor
from .project import init_project, read_status

app = typer.Typer(
    name="lrc",
    help="Lit Review Construct local research toolkit.",
    no_args_is_help=True,
)
seed_app = typer.Typer(help="Manage researcher-provided seed literature.")
app.add_typer(seed_app, name="seed")


@app.command()
def version() -> None:
    """Show the installed Lit Review Construct version."""
    typer.echo(__version__)


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    name: str | None = typer.Option(None, "--name", help="Optional project display name."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Initialize a local Lit Review Construct research workspace."""
    result = init_project(path, name=name)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    if result["created"]:
        typer.echo(f"Initialized Lit Review Construct project at {result['root']}")
    else:
        typer.echo(result["message"])


@app.command()
def status(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Show current project workflow status."""
    try:
        result = read_status(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return

    typer.echo(f"Project: {result['name']}")
    typer.echo(f"Stage: {result['current_stage']} ({result['stage_status']})")
    typer.echo(f"Schema: v{result['schema_version']}")


@seed_app.command("scan")
def seed_scan(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    source: Path | None = typer.Option(None, "--source", help="Optional local folder containing PDFs."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Index PDF seed literature from the project papers folder or an external folder."""
    try:
        result = scan_seed_papers(path, source=source)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return

    typer.echo(f"PDFs detected: {result['pdfs_detected']}")
    typer.echo(f"Indexed records: {result['records_total']}")
    typer.echo(f"Duplicate files: {result['duplicate_files']}")
    typer.echo(f"Bibliographic candidates: {result['relation_candidates']}")
    typer.echo(f"  Same work: {result['same_work']}")
    typer.echo(f"  Probable duplicates: {result['probable_duplicates']}")
    typer.echo(f"  Possible versions: {result['possible_versions']}")
    typer.echo(f"Inventory: {result['inventory']}")


@app.command()
def dedupe(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Rebuild bibliographic duplicate/version candidates without merging records."""
    try:
        result = resolve_bibliography(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return

    typer.echo(f"Indexed records: {result['records_total']}")
    typer.echo(f"Bibliographic candidates: {result['relation_candidates']}")
    typer.echo(f"  Same work: {result['same_work']}")
    typer.echo(f"  Probable duplicates: {result['probable_duplicates']}")
    typer.echo(f"  Possible versions: {result['possible_versions']}")
    typer.echo(f"Relations: {result['relations_file']}")


@app.command()
def doctor(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Run basic installation/project checks."""
    checks = run_doctor(path)
    if json_output:
        typer.echo(json.dumps(checks, ensure_ascii=False))
        return

    for check in checks:
        typer.echo(f"[{check['status']}] {check['check']}: {check['detail']}")


if __name__ == "__main__":
    app()
