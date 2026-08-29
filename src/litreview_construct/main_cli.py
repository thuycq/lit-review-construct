from __future__ import annotations

import json
from pathlib import Path

import httpx
import typer

from .campaign import (
    discovery_status,
    prepare_discovery_review,
    record_discovery_decision,
    run_discovery_iteration,
    save_discovery_review,
    start_discovery_campaign,
)
from .cli import app


discover_app = typer.Typer(
    help="Run iterative multi-source literature discovery with researcher checkpoints."
)
app.add_typer(discover_app, name="discover")


@discover_app.command("start")
def discover_start(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    reset: bool = typer.Option(False, "--reset", help="Start a fresh campaign and invalidate downstream artifacts."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = start_discovery_campaign(path, reset=reset)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Discovery campaign: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Campaign: {result['campaign_file']}")


@discover_app.command("run")
def discover_run(
    query: list[str] = typer.Option(..., "--query", "-q", help="Discovery query family; repeat for multiple queries."),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    provider: list[str] | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider to use; repeatable. Defaults to OpenAlex, Crossref, and Semantic Scholar.",
    ),
    phase: str = typer.Option("broad", "--phase", help="broad, focused, or citation_expansion."),
    max_per_query_provider: int = typer.Option(
        300,
        "--max-per-query-provider",
        min=10,
        max=2000,
        help="Maximum metadata records retrieved from each provider for each query family.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if phase not in {"broad", "focused", "citation_expansion"}:
        typer.echo("phase must be broad, focused, or citation_expansion", err=True)
        raise typer.Exit(code=1)
    try:
        result = run_discovery_iteration(
            path,
            query,
            providers=provider,
            phase=phase,  # type: ignore[arg-type]
            max_per_query_provider=max_per_query_provider,
        )
    except (FileNotFoundError, ValueError, httpx.HTTPError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Discovery iteration: {result['iteration_id']}")
    typer.echo(f"Phase: {result['phase']}")
    typer.echo(f"Query families: {result['queries']}")
    typer.echo(f"Providers: {result['providers']}")
    typer.echo(f"Raw provider records: {result['raw_results']}")
    typer.echo(f"New indexed records: {result['new_records']}")
    typer.echo(f"Existing records enriched: {result['existing_records_enriched']}")
    typer.echo(f"Corpus records: {result['corpus_records']}")
    typer.echo(f"Bibliographic relation candidates: {result['relation_candidates']}")
    if result["language_unknown"]:
        typer.echo(f"Records with unknown provider language metadata: {result['language_unknown']}")


@discover_app.command("prepare-review")
def discover_prepare_review(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    max_papers: int = typer.Option(120, "--max-papers", min=20, max=250),
    abstract_chars: int = typer.Option(1800, "--abstract-chars", min=300, max=5000),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_discovery_review(path, max_papers=max_papers, abstract_chars=abstract_chars)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Indexed records: {result['indexed_records']}")
    typer.echo(f"Representative papers in packet: {result['representative_papers']}")
    typer.echo(f"Discovery iterations: {result['iterations']}")
    typer.echo(f"Review packet: {result['packet_file']}")


@discover_app.command("save-review")
def discover_save_review(
    input_file: Path = typer.Option(..., "--input", help="JSON file containing the AI discovery-review synthesis."),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = save_discovery_review(path, input_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Discovery review: {result['status']}")
    typer.echo(f"Provisional streams: {result['streams']}")
    typer.echo(f"Candidate focus areas: {result['candidate_focuses']}")
    typer.echo(f"Output: {result['output']}")
    typer.echo("Researcher decision required: True")


@discover_app.command("decide")
def discover_decide(
    action: str = typer.Option(..., "--action", help="continue, focus, change_scope, or finish."),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    focus: list[str] | None = typer.Option(None, "--focus", help="Selected focus name; repeatable for action=focus."),
    notes: str | None = typer.Option(None, "--notes", help="Optional researcher notes."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if action not in {"continue", "focus", "change_scope", "finish"}:
        typer.echo("action must be continue, focus, change_scope, or finish", err=True)
        raise typer.Exit(code=1)
    try:
        result = record_discovery_decision(
            path,
            action=action,  # type: ignore[arg-type]
            selected_focuses=focus,
            researcher_notes=notes,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Discovery decision: {result['action']}")
    typer.echo(f"Campaign status: {result['status']}")
    if result["selected_focuses"]:
        typer.echo("Selected focuses: " + "; ".join(result["selected_focuses"]))


@discover_app.command("status")
def discover_status_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = discovery_status(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Discovery campaign: {result['status']}")
    if not result["exists"]:
        typer.echo(f"Campaign: {result['campaign_file']}")
        return
    typer.echo(f"Iterations: {result['iterations']}")
    typer.echo(f"Query families: {result['query_families']}")
    typer.echo("Providers used: " + ", ".join(result["providers_used"]))
    typer.echo(f"Indexed records: {result['indexed_records']}")
    typer.echo(f"Review checkpoints: {result['review_checkpoints']}")
    if result["selected_focuses"]:
        typer.echo("Selected focuses: " + "; ".join(result["selected_focuses"]))
    if result["warnings"]:
        typer.echo("Coverage warnings:")
        for warning in result["warnings"]:
            typer.echo(f"  - {warning}")
