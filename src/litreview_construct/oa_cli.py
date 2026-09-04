from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import fulltext_app
from .corpus import pending_acquisition_ids, tier_coverage
from .oa_coverage import (
    finalize_oa_report,
    missing_fulltext_queue,
    next_oa_batch,
    oa_coverage_status,
)
from .oa_fulltext import acquire_open_access_full_text
from .paper_library import sync_acquired_oa_library


@fulltext_app.command("acquire")
def fulltext_acquire(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    paper_id: list[str] | None = typer.Option(
        None,
        "--paper-id",
        help=(
            "Priority paper_id; repeatable. Without explicit IDs or --tier, continue the retained-"
            "literature OA coverage pass, including retryable resolver failures."
        ),
    ),
    tier: str | None = typer.Option(
        None,
        "--tier",
        help=(
            "Acquire the selected corpus tier: retained, evidence, or core. This is the preferred "
            "mode after a corpus-refinement checkpoint."
        ),
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
    if paper_id and tier:
        typer.echo("Use either --paper-id or --tier, not both.", err=True)
        raise typer.Exit(code=1)

    try:
        if tier:
            selected = pending_acquisition_ids(path, tier, max_papers=max_papers)
        elif paper_id:
            selected = paper_id
        else:
            selected = next_oa_batch(path, max_papers=max_papers)

        if not selected:
            result = finalize_oa_report(
                path,
                {
                    "selected_papers": 0,
                    "download_requested": not resolve_only,
                    "already_local": 0,
                    "resolved_pdf": 0,
                    "downloaded": 0,
                    "resolved_landing": 0,
                    "unresolved_or_closed": 0,
                    "retryable_errors": 0,
                    "provider_error_exhausted": 0,
                    "unpaywall_enabled": False,
                    "provider_failures": [],
                    "outcomes": [],
                },
            )
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
            else {
                "oa_full_text_available": 0,
                "copied_to_researcher_library": 0,
                "library": "papers/full_text",
            }
        )
        result["researcher_library"] = library
        if tier:
            result["corpus_tier"] = tier
            result["tier_coverage"] = tier_coverage(path, tier)
            result["local_runtime"] = "python"
            result["ai_model_calls_inside_acquisition"] = 0
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return

    typer.echo(f"Priority papers checked this batch: {result['selected_papers']}")
    typer.echo(f"OA PDFs downloaded this batch: {result['downloaded']}")
    if tier:
        coverage = result["tier_coverage"]
        typer.echo(f"Corpus tier: {coverage['tier']}")
        typer.echo(
            f"Current-tier full text: {coverage['local_full_text']} / "
            f"{coverage['selected_records']}"
        )
        typer.echo(
            f"Automatic resolution remaining in tier: "
            f"{coverage['automatic_resolution_pending']}"
        )
        typer.echo("Local runtime: Python; no AI model call is made per paper by this command.")
    else:
        typer.echo(
            f"Remaining retained records to resolve: "
            f"{result.get('remaining_resolution_candidates', 0)}"
        )
        if result.get("retryable_resolution_candidates", 0):
            typer.echo(
                f"Automatic resolver retries pending: "
                f"{result.get('retryable_resolution_candidates', 0)}"
            )
        typer.echo(
            f"Missing full text requiring researcher action: "
            f"{result.get('missing_fulltext_records', 0)}"
        )
        typer.echo(f"Coverage complete: {result.get('coverage_complete', False)}")
    typer.echo("Researcher paper library: papers/full_text (DOI-based filenames where available)")
    typer.echo("Missing-full-text queue: .litreview/data/missing_fulltext.json")
    if not result.get("unpaywall_enabled"):
        typer.echo("Note: set UNPAYWALL_EMAIL to enable DOI fallback through Unpaywall.")
    if result.get("provider_failures"):
        typer.echo(f"Provider warnings recorded: {len(result['provider_failures'])}")
    typer.echo("Policy: no paywall, login, CAPTCHA, or access-control bypassing.")


@fulltext_app.command("queue")
def fulltext_queue(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Show retained papers that still need full text from the researcher/library."""
    try:
        queue = missing_fulltext_queue(path)
        coverage = oa_coverage_status(path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "count": len(queue),
                    "remaining_resolution_candidates": coverage.get(
                        "remaining_resolution_candidates", 0
                    ),
                    "retryable_resolution_candidates": coverage.get(
                        "retryable_resolution_candidates", 0
                    ),
                    "papers": queue,
                },
                ensure_ascii=False,
            )
        )
        return

    typer.echo(f"Missing full-text papers requiring researcher action: {len(queue)}")
    typer.echo(
        f"Papers still awaiting automatic OA resolution: "
        f"{coverage.get('remaining_resolution_candidates', 0)}"
    )
    if coverage.get("retryable_resolution_candidates", 0):
        typer.echo(
            f"  of which retryable network/provider failures: "
            f"{coverage.get('retryable_resolution_candidates', 0)}"
        )

    if not queue:
        if coverage.get("remaining_resolution_candidates", 0):
            typer.echo(
                "No researcher action is needed yet; run 'lrc fulltext acquire .' to continue "
                "automatic resolution."
            )
        else:
            typer.echo("No retained papers currently require researcher-supplied full text.")
        return

    for item in queue:
        doi = f" | DOI: {item['doi']}" if item.get("doi") else ""
        typer.echo(
            f"- {item.get('paper_id')}: {item.get('title')} "
            f"({item.get('year') or 'n.d.'}){doi}"
        )
        if item.get("best_landing_url"):
            typer.echo(f"  Lawful landing page: {item['best_landing_url']}")
        elif item.get("best_location_url"):
            typer.echo(f"  Resolved OA location: {item['best_location_url']}")
        if item.get("best_provider"):
            typer.echo(
                f"  Resolver: {item['best_provider']} | Status: {item.get('oa_resolution_status')}"
            )
        attempts = item.get("download_attempts")
        if isinstance(attempts, list) and len(attempts) > 1:
            typer.echo(f"  Automatic download candidates tried: {len(attempts)}")
        if item.get("download_error"):
            typer.echo(f"  Automatic download note: {item['download_error']}")
        typer.echo(f"  Action: {item['researcher_action']}")

    typer.echo(
        "Policy: use open-access, institutional/library, author-provided, or "
        "researcher-supplied copies only."
    )
