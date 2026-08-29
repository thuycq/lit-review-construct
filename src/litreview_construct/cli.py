from __future__ import annotations

import json
from pathlib import Path

import httpx
import typer

from . import __version__
from .discovery import search_history, search_openalex
from .evidence import prepare_evidence_packet, save_evidence_map, show_evidence_map
from .intent import accept_intent, set_intent, show_intent
from .landscape import prepare_landscape_packet, save_landscape, show_landscape
from .papers import resolve_bibliography, scan_seed_papers
from .project import doctor as run_doctor
from .project import init_project, read_status

app = typer.Typer(name="lrc", help="Lit Review Construct local research toolkit.", no_args_is_help=True)
intent_app = typer.Typer(help="Manage the project's Research Intent.")
seed_app = typer.Typer(help="Manage researcher-provided seed literature.")
search_app = typer.Typer(help="Discover literature from scholarly providers.")
landscape_app = typer.Typer(help="Prepare and persist the Research Landscape.")
evidence_app = typer.Typer(help="Prepare and persist the provenance-aware Evidence Map.")
app.add_typer(intent_app, name="intent")
app.add_typer(seed_app, name="seed")
app.add_typer(search_app, name="search")
app.add_typer(landscape_app, name="landscape")
app.add_typer(evidence_app, name="evidence")


@app.command()
def version() -> None:
    typer.echo(__version__)


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    name: str | None = typer.Option(None, "--name", help="Optional project display name."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    result = init_project(path, name=name)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(
        f"Initialized Lit Review Construct project at {result['root']}"
        if result["created"]
        else result["message"]
    )


@app.command()
def status(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
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


@intent_app.command("set")
def intent_set(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    topic: str | None = typer.Option(None, "--topic", help="Research topic."),
    question: str | None = typer.Option(None, "--question", help="Research question."),
    publication_from: int | None = typer.Option(None, "--from-year", help="Publication start year."),
    publication_to: int | None = typer.Option(None, "--to-year", help="Publication end year."),
    language: list[str] | None = typer.Option(
        None, "--language", "-l", help="Paper language; repeatable."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = set_intent(
            path,
            topic=topic,
            research_question=question,
            publication_from=publication_from,
            publication_to=publication_to,
            languages=language,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Research Intent: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    if result["missing"]:
        typer.echo("Missing: " + ", ".join(result["missing"]))
    typer.echo(f"Output: {result['output']}")


@intent_app.command("show")
def intent_show(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = show_intent(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Research Intent: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    if result["missing"]:
        typer.echo("Missing: " + ", ".join(result["missing"]))
    typer.echo(f"Output: {result['output']}")


@intent_app.command("accept")
def intent_accept(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = accept_intent(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo("Research Intent accepted.")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Output: {result['output']}")


@seed_app.command("scan")
def seed_scan(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    source: Path | None = typer.Option(None, "--source", help="Optional local folder containing PDFs."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
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


@search_app.command("openalex")
def search_openalex_command(
    query: str = typer.Option(..., "--query", "-q", help="Focused scholarly search query."),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    limit: int = typer.Option(25, "--limit", min=1, max=100, help="Maximum provider results."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = search_openalex(path, query, limit=limit)
    except (FileNotFoundError, ValueError, httpx.HTTPError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"OpenAlex query: {result['query']}")
    typer.echo(f"Provider results: {result['provider_results']}")
    typer.echo(f"Within language scope: {result['scope_results']}")
    typer.echo(f"Imported: {result['imported']}")
    typer.echo(f"Already known: {result['already_known']}")
    typer.echo(f"API key used: {result['api_key_used']}")
    if result["cost_usd"] is not None:
        typer.echo(f"Provider-reported cost: ${result['cost_usd']}")
    typer.echo(f"Search run: {result['search_run_file']}")


@search_app.command("history")
def search_history_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        runs = search_history(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(runs, ensure_ascii=False))
        return
    if not runs:
        typer.echo("No search runs recorded.")
        return
    for run in runs:
        typer.echo(
            f"{run['timestamp']} | {run['provider']} | {run['query']} | imported={run['imported_records']}"
        )


@landscape_app.command("prepare")
def landscape_prepare(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    max_papers: int = typer.Option(
        40, "--max-papers", min=1, max=100, help="Maximum papers in the bounded packet."
    ),
    abstract_chars: int = typer.Option(
        1600,
        "--abstract-chars",
        min=200,
        max=5000,
        help="Maximum abstract characters per paper.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_landscape_packet(
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
    typer.echo(f"Packet records: {result['packet_records']}")
    typer.echo(f"Landscape packet: {result['packet_file']}")


@landscape_app.command("save")
def landscape_save(
    input_file: Path = typer.Option(
        ..., "--input", help="JSON file containing the host-model landscape submission."
    ),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = save_landscape(path, input_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Research Landscape: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Anchor papers: {result['anchors']}")
    typer.echo(f"Research streams: {result['streams']}")
    typer.echo(f"Output: {result['output']}")


@landscape_app.command("show")
def landscape_show(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = show_landscape(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Research Landscape: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Anchor papers: {result['anchors']}")
    typer.echo(f"Research streams: {result['streams']}")
    typer.echo(f"Output: {result['output']}")


@evidence_app.command("prepare")
def evidence_prepare(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    max_papers: int = typer.Option(
        30, "--max-papers", min=1, max=60, help="Maximum landscape papers in the bounded packet."
    ),
    abstract_chars: int = typer.Option(
        2200,
        "--abstract-chars",
        min=300,
        max=5000,
        help="Maximum abstract characters per paper.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_evidence_packet(
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
    typer.echo(f"Landscape papers: {result['landscape_papers']}")
    typer.echo(f"Packet papers: {result['packet_papers']}")
    typer.echo(f"Local full text available: {result['full_text_available']}")
    typer.echo(f"Evidence packet: {result['packet_file']}")


@evidence_app.command("save")
def evidence_save(
    input_file: Path = typer.Option(
        ..., "--input", help="JSON file containing the host-model Evidence Map submission."
    ),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = save_evidence_map(path, input_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Evidence Map: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Evidence items: {result['evidence_items']}")
    typer.echo(f"Papers represented: {result['papers']}")
    typer.echo(f"Require fuller text: {result['requires_full_text']}")
    typer.echo(f"Output: {result['output']}")


@evidence_app.command("show")
def evidence_show(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = show_evidence_map(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Evidence Map: {result['status']}")
    typer.echo(f"Revision: {result['revision']}")
    typer.echo(f"Evidence items: {result['evidence_items']}")
    typer.echo(f"Papers represented: {result['papers']}")
    typer.echo(f"Require fuller text: {result['requires_full_text']}")
    if result["evidence_types"]:
        typer.echo("Evidence types:")
        for name, count in result["evidence_types"].items():
            typer.echo(f"  {name}: {count}")
    typer.echo(f"Output: {result['output']}")


@app.command()
def dedupe(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
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
    checks = run_doctor(path)
    if json_output:
        typer.echo(json.dumps(checks, ensure_ascii=False))
        return
    for check in checks:
        typer.echo(f"[{check['status']}] {check['check']}: {check['detail']}")


if __name__ == "__main__":
    app()
