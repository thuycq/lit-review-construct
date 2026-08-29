from __future__ import annotations

import json
from pathlib import Path

import typer

from . import cli as core_cli
from . import main_cli as discovery_cli
from .activity import append_activity
from .campaign import (
    record_discovery_decision as _record_discovery_decision,
    save_discovery_review as _save_discovery_review,
    start_discovery_campaign as _start_discovery_campaign,
)
from .direction import prepare_direction_packet as _prepare_direction_packet
from .finalize import prepare_final_landscape_packet
from .fulltext import full_text_status, reconcile_full_text_links
from .graph_resilient import expand_resilient_citation_graph as _expand_citation_graph
from .landscape import prepare_landscape_packet as _prepare_legacy_landscape_packet
from .main_cli import app, discover_app
from .project import PROJECT_DIR
from .resilient import run_resilient_discovery_iteration as _run_discovery_iteration
from .triage import save_triage_batch as _save_triage_batch


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


def _logged_discovery_start(root: Path, *, reset: bool = False) -> dict[str, object]:
    result = _start_discovery_campaign(root, reset=reset)
    if result.get("created") or reset:
        append_activity(
            root,
            category="literature_discovery",
            actor="toolkit",
            inputs={"action": "start_campaign", "reset": reset},
            outputs=[".litreview/data/discovery_campaign.json"],
            notes="Started an iterative multi-source literature discovery campaign.",
        )
    return result


def _logged_discovery_run(
    root: Path,
    queries: list[str],
    *,
    providers: list[str] | None = None,
    phase: str = "broad",
    max_per_query_provider: int = 300,
    timeout: float = 45.0,
) -> dict[str, object]:
    result = _run_discovery_iteration(
        root,
        queries,
        providers=providers,
        phase=phase,
        max_per_query_provider=max_per_query_provider,
        timeout=timeout,
    )
    append_activity(
        root,
        category="literature_discovery",
        actor="toolkit",
        inputs={
            "phase": phase,
            "queries": queries,
            "providers_requested": providers or ["openalex", "crossref", "semantic_scholar"],
            "max_per_query_provider": max_per_query_provider,
        },
        outputs=[
            ".litreview/data/papers.jsonl",
            ".litreview/data/discovery_campaign.json",
            f".litreview/searches/campaign-{result['iteration_id']}.json",
        ],
        notes=(
            f"Retrieved {result['raw_results']} provider records; "
            f"indexed {result['new_records']} new records; "
            f"successful providers: {', '.join(result['providers_succeeded'])}."
            + (
                " Provider failures were recorded and successful sources were retained."
                if result.get("provider_failures")
                else ""
            )
        ),
    )
    return result


def _logged_triage_save(root: Path, input_file: Path) -> dict[str, object]:
    result = _save_triage_batch(root, input_file)
    append_activity(
        root,
        category="paper_prioritization",
        actor="ai_assisted",
        inputs={"submission": str(input_file), "batch_records": result["batch_records"]},
        outputs=[
            ".litreview/data/papers.jsonl",
            ".litreview/data/triage_runs.jsonl",
        ],
        notes=(
            f"AI-assisted title/abstract triage classified {result['batch_records']} papers. "
            "Triage is a relevance aid, not full-text evidence screening."
        ),
    )
    return result


def _logged_review_save(root: Path, input_file: Path) -> dict[str, object]:
    result = _save_discovery_review(root, input_file)
    append_activity(
        root,
        category="research_landscape_synthesis",
        actor="ai_assisted",
        inputs={"stage": "exploratory_discovery_review", "submission": str(input_file)},
        outputs=[
            ".litreview/data/discovery_review.json",
            "outputs/03_discovery_review.md",
        ],
        notes=(
            "Produced an exploratory synthesis of provisional streams/focuses during discovery; "
            "this is not a definitive research-gap assessment."
        ),
    )
    return result


def _logged_discovery_decision(
    root: Path,
    *,
    action: str,
    selected_focuses: list[str] | None = None,
    researcher_notes: str | None = None,
) -> dict[str, object]:
    result = _record_discovery_decision(
        root,
        action=action,  # type: ignore[arg-type]
        selected_focuses=selected_focuses,
        researcher_notes=researcher_notes,
    )
    append_activity(
        root,
        category="discovery_scope_decision",
        actor="researcher",
        inputs={
            "action": action,
            "selected_focuses": selected_focuses or [],
            "researcher_notes": researcher_notes,
        },
        outputs=[".litreview/data/discovery_campaign.json"],
        notes="Recorded an explicit researcher decision at a discovery checkpoint.",
    )
    return result


def _logged_graph_expand(
    root: Path,
    *,
    paper_ids: list[str] | None = None,
    relation: str = "both",
    providers: list[str] | None = None,
    max_per_seed_provider: int = 100,
    timeout: float = 45.0,
) -> dict[str, object]:
    result = _expand_citation_graph(
        root,
        paper_ids=paper_ids,
        relation=relation,
        providers=providers,
        max_per_seed_provider=max_per_seed_provider,
        timeout=timeout,
    )
    append_activity(
        root,
        category="literature_discovery",
        actor="toolkit",
        inputs={
            "action": "citation_graph_expansion",
            "seed_paper_ids": paper_ids or [],
            "relation": relation,
            "providers_requested": providers or ["openalex", "semantic_scholar"],
        },
        outputs=[
            ".litreview/data/papers.jsonl",
            ".litreview/data/paper_graph.jsonl",
            ".litreview/data/discovery_campaign.json",
        ],
        source_ids=paper_ids or [],
        notes=(
            f"Citation/reference expansion added {result['new_records']} records and "
            f"{result['new_graph_edges']} graph edges."
            + (
                " Provider failures were recorded and successful graph sources were retained."
                if result.get("provider_failures")
                else ""
            )
        ),
    )
    return result


# Existing command functions resolve these module globals at call time. Wrapping them here keeps
# one user-facing CLI while enforcing gates, provider resilience, and project activity logging.
core_cli.prepare_direction_packet = _guarded_direction_prepare
core_cli.prepare_landscape_packet = _guarded_legacy_landscape_prepare
discovery_cli.start_discovery_campaign = _logged_discovery_start
discovery_cli.run_resilient_discovery_iteration = _logged_discovery_run
discovery_cli.save_triage_batch = _logged_triage_save
discovery_cli.save_discovery_review = _logged_review_save
discovery_cli.record_discovery_decision = _logged_discovery_decision
discovery_cli.expand_citation_graph = _logged_graph_expand


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


fulltext_app = typer.Typer(
    help="Inspect and reconcile local full text with discovered scholarly records."
)
app.add_typer(fulltext_app, name="fulltext")


@fulltext_app.command("reconcile")
def fulltext_reconcile(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = reconcile_full_text_links(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if result["full_text_links_added"]:
        append_activity(
            path,
            category="source_verification",
            actor="toolkit",
            inputs={"action": "full_text_reconciliation"},
            outputs=[".litreview/data/papers.jsonl"],
            source_ids=[row["target_paper_id"] for row in result["links"]],
            notes=(
                f"Linked local full text to {result['full_text_links_added']} scholarly records "
                "using high-confidence same-DOI relations without merging/deleting records."
            ),
        )
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"High-confidence same-work relations: {result['same_work_relations']}")
    typer.echo(f"Full-text links added: {result['full_text_links_added']}")


@fulltext_app.command("status")
def fulltext_status_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = full_text_status(path)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Indexed records: {result['indexed_records']}")
    typer.echo(f"Local full text available: {result['full_text_available']}")
    typer.echo(f"Retained triaged records: {result['retained_triaged_records']}")
    typer.echo(f"Retained papers missing full text: {result['retained_missing_full_text']}")
    if result["priority_missing_full_text"]:
        typer.echo("Priority papers needing full text:")
        for row in result["priority_missing_full_text"][:20]:
            typer.echo(
                f"  - {row['title']} | id={row['paper_id']} | "
                f"label={row['triage_label']} | priority={row['triage_priority']}"
            )
