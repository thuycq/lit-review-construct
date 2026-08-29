from __future__ import annotations

import json
from pathlib import Path

import typer

from . import cli as core_cli
from .direction import prepare_direction_packet as _prepare_direction_packet
from .finalize import prepare_final_landscape_packet
from .landscape import prepare_landscape_packet as _prepare_legacy_landscape_packet
from .main_cli import app, discover_app
from .project import PROJECT_DIR


def _read_campaign(root: Path) -> dict[str, object] | None:
    path = root.expanduser().resolve() / PROJECT_DIR / "data" / "discovery_campaign.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _guarded_direction_prepare(root: Path, *, max_evidence: int = 80) -> dict[str, object]:
    campaign = _read_campaign(root)
    if campaign is None:
        raise ValueError(
            "A completed multi-source discovery campaign is required before Research Direction. "
            "Run lrc discover start and complete the discovery/narrowing workflow first."
        )
    if campaign.get("status") != "complete":
        raise ValueError(
            "Research Direction is blocked while discovery is still active. "
            "The researcher must explicitly finish the discovery campaign first."
        )
    return _prepare_direction_packet(root, max_evidence=max_evidence)


def _guarded_legacy_landscape_prepare(
    root: Path,
    *,
    max_papers: int = 40,
    abstract_chars: int = 1600,
) -> dict[str, object]:
    campaign = _read_campaign(root)
    if campaign is not None:
        raise ValueError(
            "This project uses the iterative discovery workflow. "
            "Use 'lrc discover prepare-landscape' after the researcher finishes discovery; "
            "the legacy landscape packet does not apply campaign triage/narrowing."
        )
    return _prepare_legacy_landscape_packet(
        root,
        max_papers=max_papers,
        abstract_chars=abstract_chars,
    )


# The original commands live in cli.py. Their function bodies resolve these module globals at
# call time, so replacing the references here enforces current product gates without duplicating
# the legacy command implementations.
core_cli.prepare_direction_packet = _guarded_direction_prepare
core_cli.prepare_landscape_packet = _guarded_legacy_landscape_prepare


@discover_app.command("prepare-landscape")
def discover_prepare_landscape(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    max_papers: int = typer.Option(
        80,
        "--max-papers",
        min=20,
        max=150,
        help="Maximum retained papers in the final Research Landscape packet.",
    ),
    abstract_chars: int = typer.Option(
        2200,
        "--abstract-chars",
        min=300,
        max=5000,
        help="Maximum abstract characters per retained paper.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = prepare_final_landscape_packet(
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
    typer.echo(f"Triaged records: {result['triaged_records']}")
    typer.echo(f"Retained records: {result['retained_records']}")
    typer.echo(f"Landscape packet records: {result['packet_records']}")
    if result["warnings"]:
        typer.echo("Coverage warnings:")
        for warning in result["warnings"]:
            typer.echo(f"  - {warning}")
    typer.echo(f"Landscape packet: {result['packet_file']}")
