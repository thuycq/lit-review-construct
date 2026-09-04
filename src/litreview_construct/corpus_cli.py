from __future__ import annotations

import json
from pathlib import Path

import typer

from .app_cli import app
from .corpus import corpus_status, rank_corpus, record_decision, refinement_next_step

corpus_app = typer.Typer(
    help=(
        "Refine retained literature into Evidence Candidates and Core Papers with "
        "researcher-controlled acquisition checkpoints."
    )
)
app.add_typer(corpus_app, name="corpus")


@corpus_app.command("status")
def corpus_status_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = corpus_status(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Retained Papers: {result['retained_records']}")
    typer.echo(f"Evidence Candidates: {result['evidence_candidate_records']}")
    typer.echo(f"Core Papers: {result['core_paper_records']}")
    next_step = result["next"]
    typer.echo(f"Next corpus action: {next_step['next_action']}")
    typer.echo(f"Researcher checkpoint required: {next_step['human_checkpoint_required']}")
    if next_step.get("coverage"):
        coverage = next_step["coverage"]
        typer.echo(
            f"Current-tier full text: {coverage['local_full_text']} / "
            f"{coverage['selected_records']}"
        )


@corpus_app.command("next")
def corpus_next_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    try:
        result = refinement_next_step(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    typer.echo(f"Next corpus action: {result['next_action']}")
    typer.echo(f"Researcher checkpoint required: {result['human_checkpoint_required']}")
    typer.echo(f"Reason: {result['reason']}")
    if result.get("records") is not None:
        typer.echo(f"Papers in current tier: {result['records']}")
    if result.get("coverage"):
        coverage = result["coverage"]
        typer.echo(
            f"Local full text: {coverage['local_full_text']} / {coverage['selected_records']}"
        )
    if result.get("options"):
        typer.echo("Choices:")
        for option in result["options"]:
            typer.echo(f"  - {option['action']}: {option['meaning']}")
            if option.get("ai_usage"):
                typer.echo(f"    AI usage: {option['ai_usage']}")
    if result.get("commands"):
        typer.echo("Runtime action(s):")
        for command in result["commands"]:
            typer.echo(f"  {command}")


@corpus_app.command("rank")
def corpus_rank_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    to_tier: str = typer.Option(..., "--to", help="Target tier: evidence or core."),
    max_papers: int | None = typer.Option(
        None,
        "--max-papers",
        min=1,
        max=200,
        help="Optional researcher override; otherwise use the adaptive recommended size.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    normalized = to_tier.strip().lower().replace("_", "-")
    if normalized in {"evidence", "evidence-candidates", "candidates"}:
        target = "evidence"
    elif normalized in {"core", "core-papers"}:
        target = "core"
    else:
        typer.echo("--to must be evidence or core", err=True)
        raise typer.Exit(code=1)
    try:
        result = rank_corpus(path, to_tier=target, max_papers=max_papers)  # type: ignore[arg-type]
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    label = "Evidence Candidates" if target == "evidence" else "Core Papers"
    typer.echo(f"{label}: {result['selected_records']} / {result['source_records']}")
    typer.echo(f"Adaptive recommendation: {result['recommended_count']}")
    typer.echo(
        "Ranking: relevance + evidence potential + quality/provenance + capped anchor value "
        "+ recency + focus alignment + stream coverage"
    )
    typer.echo("Citation count is not used as a sole ranking criterion.")
    typer.echo(f"Ranking basis: {result['ranking_basis']}")


@corpus_app.command("decide")
def corpus_decide_command(
    path: Path = typer.Argument(Path("."), help="Research workspace folder."),
    stage: str = typer.Option(..., "--stage", help="retained, evidence, or core."),
    action: str = typer.Option(
        ..., "--action", help="acquire/refine, or acquire/continue for core."
    ),
    note: str | None = typer.Option(None, "--note", help="Optional researcher note."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    stage_norm = stage.strip().lower().replace("_", "-")
    stage_alias = {
        "retained": "retained",
        "evidence": "evidence",
        "evidence-candidates": "evidence",
        "core": "core",
        "core-papers": "core",
    }
    stage_value = stage_alias.get(stage_norm)
    action_value = action.strip().lower()
    if stage_value is None or action_value not in {"acquire", "refine", "continue"}:
        typer.echo(
            "Invalid corpus decision. Use --stage retained|evidence|core and the allowed action.",
            err=True,
        )
        raise typer.Exit(code=1)
    try:
        result = record_decision(
            path,
            stage=stage_value,  # type: ignore[arg-type]
            action=action_value,  # type: ignore[arg-type]
            note=note,
        )
        next_step = refinement_next_step(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    payload = {"decision": result, "next": next_step}
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
        return
    typer.echo(f"Corpus decision recorded: {result['stage']} -> {result['action']}")
    if action_value == "acquire":
        typer.echo(
            "Acquisition will run in the local Python runtime; the runtime itself does not "
            "call an AI model per paper."
        )
    typer.echo(f"Next action: {next_step['next_action']}")
