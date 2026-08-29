from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import app
from .researcher_package import prepare_researcher_package, researcher_package_status


package_app = typer.Typer(help="Prepare researcher-facing papers, references, and handoff files.")
app.add_typer(package_app, name="package")


@package_app.command("prepare")
def package_prepare(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    no_word: bool = typer.Option(False, "--no-word", help="Do not generate the combined Word handoff."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_researcher_package(path, export_word=not no_word)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Working references: {result['working_reference_count']}")
    typer.echo(f"Full text: {result['working_full_text_count']}")
    typer.echo(f"Abstract only: {result['working_abstract_only_count']}")
    typer.echo("Paper library: papers/full_text, papers/abstract_only, papers/user_uploads")
    typer.echo("EndNote: references/references_used.enw")
    if result.get("word_handoff"):
        typer.echo(f"Word handoff: {result['word_handoff']}")


@package_app.command("status")
def package_status(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = researcher_package_status(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    if result.get("status") == "not_prepared":
        typer.echo("Researcher package: not prepared")
        return
    typer.echo(f"Researcher package generated: {result.get('generated_at')}")
    typer.echo(f"Working references: {result.get('working_reference_count', 0)}")
    typer.echo("EndNote: references/references_used.enw")
