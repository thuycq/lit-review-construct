from __future__ import annotations

import json
from pathlib import Path

import typer

from .activity import append_activity
from .campaign import start_discovery_campaign
from .main_cli import discover_app
from .planner import load_current_query_plan, prepare_query_plan, save_query_plan
from .resilient import run_resilient_discovery_iteration


@discover_app.command("prepare-plan")
def discover_prepare_plan(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    phase: str = typer.Option("broad", "--phase", help="broad or focused."),
    max_seed_papers: int = typer.Option(20, "--max-seed-papers", min=0, max=50),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if phase not in {"broad", "focused"}:
        typer.echo("phase must be broad or focused", err=True)
        raise typer.Exit(code=1)
    try:
        result = prepare_query_plan(
            path,
            phase=phase,  # type: ignore[arg-type]
            max_seed_papers=max_seed_papers,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Query-plan phase: {result['phase']}")
    typer.echo(f"Seed papers in packet: {result['seed_papers']}")
    typer.echo(f"Previous queries: {result['previous_queries']}")
    if result["selected_focuses"]:
        typer.echo("Selected focuses: " + "; ".join(result["selected_focuses"]))
    typer.echo(f"Query-plan packet: {result['packet_file']}")


@discover_app.command("save-plan")
def discover_save_plan(
    input_file: Path = typer.Option(..., "--input", help="JSON file containing the AI query plan."),
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = save_query_plan(path, input_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    append_activity(
        path,
        category="search_assistance",
        actor="ai_assisted",
        inputs={
            "phase": result["phase"],
            "query_count": result["query_count"],
            "submission": str(input_file),
        },
        outputs=[
            ".litreview/data/discovery_query_plan.json",
            ".litreview/data/discovery_query_plans.jsonl",
        ],
        notes=(
            "AI-assisted query planning created interpretable query families for scholarly "
            "discovery; the plan does not imply exhaustive retrieval."
        ),
    )
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Saved query plan: {result['plan_id']}")
    typer.echo(f"Phase: {result['phase']}")
    typer.echo(f"Query families: {result['query_count']}")


@discover_app.command("run-plan")
def discover_run_plan(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    provider: list[str] | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider to use; repeatable. Defaults to OpenAlex, Crossref, and Semantic Scholar.",
    ),
    max_per_query_provider: int = typer.Option(
        300,
        "--max-per-query-provider",
        min=10,
        max=2000,
        help="Maximum metadata records retrieved from each provider for each saved query family.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        plan = load_current_query_plan(path)
        phase = str(plan.get("phase") or "broad")
        queries = [
            str(row.get("query"))
            for row in plan.get("query_families") or []
            if isinstance(row, dict) and row.get("query")
        ]
        campaign_file = path.expanduser().resolve() / ".litreview" / "data" / "discovery_campaign.json"
        if not campaign_file.exists():
            start_discovery_campaign(path)
            append_activity(
                path,
                category="literature_discovery",
                actor="toolkit",
                inputs={"action": "start_campaign", "source": "run_plan"},
                outputs=[".litreview/data/discovery_campaign.json"],
                notes="Started discovery campaign before executing the saved query plan.",
            )
        result = run_resilient_discovery_iteration(
            path,
            queries,
            providers=provider,
            phase=phase,
            max_per_query_provider=max_per_query_provider,
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    append_activity(
        path,
        category="literature_discovery",
        actor="toolkit",
        inputs={
            "action": "run_saved_query_plan",
            "plan_id": plan.get("plan_id"),
            "phase": phase,
            "queries": queries,
            "providers_requested": provider or ["openalex", "crossref", "semantic_scholar"],
        },
        outputs=[
            ".litreview/data/papers.jsonl",
            ".litreview/data/discovery_campaign.json",
            f".litreview/searches/campaign-{result['iteration_id']}.json",
        ],
        notes=(
            f"Executed {len(queries)} saved query families; retrieved {result['raw_results']} "
            f"provider records and indexed {result['new_records']} new records."
        ),
    )
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Executed query plan: {plan.get('plan_id')}")
    typer.echo(f"Discovery iteration: {result['iteration_id']}")
    typer.echo(f"Phase: {result['phase']}")
    typer.echo(f"Query families: {result['queries']}")
    typer.echo("Successful providers: " + ", ".join(result["providers_succeeded"]))
    typer.echo(f"New indexed records: {result['new_records']}")
    if result.get("provider_failures"):
        typer.echo(f"Provider failures recorded: {len(result['provider_failures'])}")
