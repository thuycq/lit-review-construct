from __future__ import annotations

import json
import re
from pathlib import Path

from .project import PROJECT_DIR


_STRONG_ABSTRACT_PATTERNS = [
    re.compile(r"\bestablished\b", re.IGNORECASE),
    re.compile(r"\bproves?\b", re.IGNORECASE),
    re.compile(r"\bdemonstrates?\b", re.IGNORECASE),
    re.compile(r"\bconfirms?\b", re.IGNORECASE),
    re.compile(r"\bconclusively\b", re.IGNORECASE),
]
_UNBOUNDED_GAP = re.compile(
    r"\b(no|none)\s+(direct\s+)?(study|studies|research|evidence|paper|papers)\b",
    re.IGNORECASE,
)
_BOUNDED_GAP_MARKERS = (
    "within the reviewed",
    "within this reviewed",
    "in the reviewed corpus",
    "in the retained literature",
    "the reviewed evidence did not identify",
)


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def validate_working_draft_claim_language(root: Path, input_file: Path) -> dict[str, object]:
    """Reject common claim-strength regressions before a Working Draft is saved.

    This is intentionally conservative and mechanical. It does not judge scholarly truth; it only
    prevents abstract-only support from being rendered as established fact and prevents universal
    absence claims when discovery is narrative/progressive rather than exhaustive.
    """
    root = root.expanduser().resolve()
    payload = json.loads(input_file.expanduser().resolve().read_text(encoding="utf-8"))
    evidence_rows = _load_jsonl(root / PROJECT_DIR / "data" / "evidence.jsonl")
    evidence_by_id = {
        str(row.get("evidence_id")): row for row in evidence_rows if row.get("evidence_id")
    }
    errors: list[str] = []
    checked = 0

    for section in payload.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("section_id") or section.get("title") or "unknown")
        for index, fragment in enumerate(section.get("fragments") or [], start=1):
            if not isinstance(fragment, dict):
                continue
            text = str(fragment.get("draft_text") or "")
            evidence_ids = [str(value) for value in fragment.get("evidence_ids") or []]
            bases = {
                str(evidence_by_id[value].get("source_basis") or "unknown")
                for value in evidence_ids
                if value in evidence_by_id
            }
            checked += 1
            abstract_heavy = not bases or any(base != "full_text" for base in bases)
            if abstract_heavy:
                for pattern in _STRONG_ABSTRACT_PATTERNS:
                    if pattern.search(text):
                        errors.append(
                            f"{section_id} fragment {index}: abstract/provisional support uses strong phrase '{pattern.pattern}'. Use bounded wording such as 'suggests', 'reports', or 'available evidence indicates'."
                        )
                        break
            lower = text.lower()
            if _UNBOUNDED_GAP.search(text) and not any(marker in lower for marker in _BOUNDED_GAP_MARKERS):
                errors.append(
                    f"{section_id} fragment {index}: universal absence/gap claim is not bounded to the reviewed corpus."
                )
            if "provision" in lower and "established" in lower:
                errors.append(
                    f"{section_id} fragment {index}: do not combine provisional language with 'established'."
                )

    if errors:
        raise ValueError(
            "Working Draft claim-strength QA failed. Revise automatically before researcher review:\n- "
            + "\n- ".join(errors)
        )
    return {"status": "pass", "fragments_checked": checked, "errors": []}
