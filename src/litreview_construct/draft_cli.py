from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import app
from .draft_quality import validate_working_draft_claim_language
from .draft_support import prepare_working_draft_packet, save_working_draft, show_working_draft


draft_app = typer.Typer(help="Create a researcher-editable literature-review working draft from an accepted Blueprint.")
app.add_typer(draft_app, name="draft")


@draft_app.command("prepare")
def draft_prepare(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_working_draft_packet(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Working-draft sections: {result['sections']}")
    typer.echo(f"Paper anchors: {result['papers']}")
    typer.echo(f"Evidence items: {result['evidence_items']}")
    typer.echo(f"Abstract-only evidence items: {result['abstract_only_evidence']}")
    typer.echo(f"Packet: {result['packet_file']}")


@draft_app.command("save")
def draft_save(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    input_file: Path = typer.Option(..., "--input", help="Structured working-draft JSON produced from the packet."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        qa = validate_working_draft_claim_language(path, input_file)
        result = save_working_draft(path, input_file)
        result["claim_strength_qa"] = qa
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Researcher working draft: {result['status']}")
    typer.echo(f"Sections: {result['sections']}")
    typer.echo(f"Fragments requiring verification: {result['verification_fragments']}")
    typer.echo("Claim-strength QA: pass")
    typer.echo(f"Output: {result['output']}")


@draft_app.command("show")
def draft_show(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = show_working_draft(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Working-draft status: {result['status']}")
    typer.echo(f"Sections: {result['sections']}")
    typer.echo(f"Output: {result['output']}")
