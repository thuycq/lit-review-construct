from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import fulltext_app
from .oa_fulltext import acquire_open_access_full_text


@fulltext_app.command("acquire")
def fulltext_acquire(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    paper_id: list[str] | None = typer.Option(
        None,
        "--paper-id",
        help="Priority paper_id; repeatable. Defaults to Blueprint/Direction/Landscape priorities.",
    ),
    max_papers: int = typer.Option(30, "--max-papers", min=1, max=100),
    resolve_only: bool = typer.Option(
        False,
        "--resolve-only",
        help="Resolve lawful OA locations without downloading PDFs.",
    ),
    max_pdf_mb: int = typer.Option(50, "--max-pdf-mb", min=1, max=200),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = acquire_open_access_full_text(
            path,
            paper_ids=paper_id,
            max_papers=max_papers,
            download=not resolve_only,
            max_pdf_mb=max_pdf_mb,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Priority papers checked: {result['selected_papers']}")
    typer.echo(f"Already local: {result['already_local']}")
    typer.echo(f"OA PDF locations resolved: {result['resolved_pdf']}")
    typer.echo(f"OA PDFs downloaded: {result['downloaded']}")
    typer.echo(f"OA landing pages only: {result['resolved_landing']}")
    typer.echo(f"Unresolved/closed: {result['unresolved_or_closed']}")
    if not result["unpaywall_enabled"]:
        typer.echo("Note: set UNPAYWALL_EMAIL to enable DOI fallback through Unpaywall.")
    if result["provider_failures"]:
        typer.echo(f"Provider warnings recorded: {len(result['provider_failures'])}")
    typer.echo("Policy: no paywall, login, CAPTCHA, or access-control bypassing.")
