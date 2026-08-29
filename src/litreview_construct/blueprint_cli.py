from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import app
from .blueprint import accept_blueprint, prepare_blueprint_packet, save_blueprint, show_blueprint


blueprint_app = typer.Typer(help="Construct and review the evidence-linked Literature Review Blueprint.")
app.add_typer(blueprint_app, name="blueprint")


@blueprint_app.command("prepare")
def blueprint_prepare(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    max_evidence: int = typer.Option(120, "--max-evidence", min=20, max=250),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_blueprint_packet(path, max_evidence=max_evidence)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Blueprint packet papers: {result['papers']}")
    typer.echo(f"Evidence items: {result['evidence_items']}")
    typer.echo(f"Verification flags: {result['verification_flags']}")
    typer.echo(f"Packet: {result['packet_file']}")


@blueprint_app.command("save")
def blueprint_save(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    input_file: Path = typer.Option(..., "--input", help="Structured Blueprint JSON produced from the packet."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = save_blueprint(path, input_file)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Literature Review Blueprint: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Sections: {result['sections']}")
    typer.echo(f"Output: {result['output']}")


@blueprint_app.command("show")
def blueprint_show(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = show_blueprint(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Literature Review Blueprint: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Sections: {result['sections']}")
    typer.echo(f"Output: {result['output']}")


@blueprint_app.command("accept")
def blueprint_accept(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = accept_blueprint(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo("Literature Review Blueprint accepted for researcher handoff.")
