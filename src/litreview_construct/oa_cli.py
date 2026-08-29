from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import fulltext_app
from .oa_coverage import finalize_oa_report, next_oa_batch, oa_coverage_status
from .oa_fulltext import acquire_open_access_full_text
from .paper_library import sync_acquired_oa_library


@fulltext_app.command("acquire")
def fulltext_acquire(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    paper_id: list[str] | None = typer.Option(
        None,
        "--paper-id",
        help="Priority paper_id; repeatable. Without explicit IDs, continue the retained-literature OA coverage pass.",
    ),
    max_papers: int = typer.Option(100, "--max-papers", min=1, max=100),
    resolve_only: bool = typer.Option(
        False,
        "--resolve-only",
        help="Resolve lawful OA locations without downloading PDFs.",
    ),
    max_pdf_mb: int = typer.Option(50, "--max-pdf-mb", min=1, max=200),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        selected = paper_id if paper_id else next_oa_batch(path, max_papers=max_papers)
        if not selected:
            result = {
                "selected_papers": 0,
                "download_requested": not resolve_only,
                "already_local": 0,
                "resolved_pdf": 0,
                "downloaded": 0,
                "resolved_landing": 0,
                "unresolved_or_closed": 0,
                "unpaywall_enabled": False,
                "provider_failures": [],
                "outcomes": [],
            }
            result.update(oa_coverage_status(path))
        else:
            result = acquire_open_access_full_text(
                path,
                paper_ids=selected,
                max_papers=max_papers,
                download=not resolve_only,
                max_pdf_mb=max_pdf_mb,
            )
            result = finalize_oa_report(path, result)
        library = (
            sync_acquired_oa_library(path)
            if not resolve_only
            else {"oa_full_text_available": 0, "copied_to_researcher_library": 0, "library": "papers/full_text"}
        )
        result["researcher_library"] = library
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Priority papers checked this batch: {result['selected_papers']}")
    typer.echo(f"OA PDFs downloaded this batch: {result['downloaded']}")
    typer.echo(f"Remaining retained records to resolve: {result.get('remaining_resolution_candidates', 0)}")
    typer.echo(f"Coverage complete: {result.get('coverage_complete', False)}")
    typer.echo("Researcher paper library: papers/full_text (DOI-based filenames where available)")
    if not result.get("unpaywall_enabled"):
        typer.echo("Note: set UNPAYWALL_EMAIL to enable DOI fallback through Unpaywall.")
    if result.get("provider_failures"):
        typer.echo(f"Provider warnings recorded: {len(result['provider_failures'])}")
    typer.echo("Policy: no paywall, login, CAPTCHA, or access-control bypassing.")
