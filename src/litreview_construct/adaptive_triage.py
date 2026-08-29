from __future__ import annotations

import json
from pathlib import Path

from . import main_cli
from .project import PROJECT_DIR


_original_prepare_narrowing_review = main_cli.prepare_narrowing_review


def _prepare_adaptive_narrowing_review(
    root: Path,
    *,
    max_papers: int = 150,
    abstract_chars: int = 1800,
) -> dict[str, object]:
    result = _original_prepare_narrowing_review(
        root,
        max_papers=max_papers,
        abstract_chars=abstract_chars,
    )
    root = root.expanduser().resolve()
    packet_file = root / PROJECT_DIR / "packets" / "discovery_review.json"
    if not packet_file.exists():
        return result

    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    contract = packet.get("analysis_contract")
    if isinstance(contract, dict):
        contract["purpose"] = (
            "Analyze the progressively filtered discovery corpus and return to researcher-guided "
            "narrowing after bounded priority triage; do not require exhaustive title/abstract screening."
        )
        required = list(contract.get("required") or [])
        guidance = (
            "treat remaining untriaged records as a coverage limitation, not an obligation to screen "
            "the entire corpus before the next researcher checkpoint"
        )
        if guidance not in required:
            required.append(guidance)
        contract["required"] = required
        contract["human_checkpoint"] = (
            "Stop after the review and ask the researcher whether to filter more of the current corpus, "
            "broaden/search more, focus or change the selected areas, change scope, or finish discovery. "
            "Use filter when the researcher wants more triage without another literature search."
        )
    packet["triage_policy"] = {
        "mode": "progressive",
        "exhaustive_screening_required": False,
        "rationale": (
            "This toolkit supports narrative-review construction. Bounded priority batches and repeated "
            "researcher checkpoints are preferred over mechanically screening every retrieved record."
        ),
    }
    packet_file.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


main_cli.prepare_narrowing_review = _prepare_adaptive_narrowing_review
