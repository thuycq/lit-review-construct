from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .project import PROJECT_DIR, _atomic_write_text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    _atomic_write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _project_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root


def _file_references(row: dict[str, object]) -> list[dict[str, object]]:
    instances = row.get("file_instances")
    refs: list[dict[str, object]] = []
    if isinstance(instances, list):
        for item in instances:
            if isinstance(item, dict) and item.get("file_reference"):
                refs.append(dict(item))
    if row.get("file_reference") and not any(
        item.get("file_reference") == row.get("file_reference") for item in refs
    ):
        refs.append(
            {
                "file_reference": row.get("file_reference"),
                "location_type": row.get("location_type"),
            }
        )
    return refs


def _has_full_text(row: dict[str, object]) -> bool:
    return bool(_file_references(row))


def reconcile_full_text_links(root: Path) -> dict[str, object]:
    """Propagate local PDF references across high-confidence same-DOI work records.

    Records remain distinct for provenance/version safety. Only the verified local full-text
    reference is linked to the matching scholarly record; no record is deleted or merged.
    """
    root = _project_root(root)
    data_root = root / PROJECT_DIR / "data"
    papers_file = data_root / "papers.jsonl"
    relations_file = data_root / "paper_relations.jsonl"
    records = _load_jsonl(papers_file)
    relations = _load_jsonl(relations_file)
    by_id = {str(row.get("paper_id")): row for row in records if row.get("paper_id")}
    linked: list[dict[str, str]] = []

    for relation in relations:
        if relation.get("relation") != "same_work" or relation.get("confidence") != "high":
            continue
        if "same_doi" not in (relation.get("basis") or []):
            continue
        left_id = str(relation.get("left_paper_id") or "")
        right_id = str(relation.get("right_paper_id") or "")
        left = by_id.get(left_id)
        right = by_id.get(right_id)
        if not left or not right:
            continue

        for source, source_id, target, target_id in (
            (left, left_id, right, right_id),
            (right, right_id, left, left_id),
        ):
            source_refs = _file_references(source)
            if not source_refs or _has_full_text(target):
                continue
            target["file_instances"] = source_refs
            target["file_reference"] = source_refs[0].get("file_reference")
            target["location_type"] = source_refs[0].get("location_type") or source.get("location_type")
            target["file_hash"] = source.get("file_hash")
            target["page_count"] = source.get("page_count")
            target["parse_status"] = source.get("parse_status")
            target["parse_error"] = source.get("parse_error")
            target["full_text_linked_from_paper_id"] = source_id
            target["full_text_link_basis"] = "same_doi"
            target["full_text_linked_at"] = _now()
            target["updated_at"] = _now()
            linked.append(
                {
                    "source_paper_id": source_id,
                    "target_paper_id": target_id,
                    "basis": "same_doi",
                }
            )

    if linked:
        _write_jsonl(papers_file, records)

    return {
        "records": len(records),
        "same_work_relations": sum(
            row.get("relation") == "same_work" and row.get("confidence") == "high"
            for row in relations
        ),
        "full_text_links_added": len(linked),
        "links": linked,
    }


def full_text_status(root: Path) -> dict[str, object]:
    root = _project_root(root)
    records = _load_jsonl(root / PROJECT_DIR / "data" / "papers.jsonl")
    labels = Counter(str(row.get("triage_label") or "untriaged") for row in records)
    available = [row for row in records if _has_full_text(row)]
    relevant = [
        row
        for row in records
        if row.get("triage_label") in {"relevant", "background", "adjacent"}
    ]
    relevant_missing = [row for row in relevant if not _has_full_text(row)]
    priority_rank = {"core_candidate": 0, "high": 1, "medium": 2, "low": 3}
    relevant_missing.sort(
        key=lambda row: (
            priority_rank.get(str(row.get("triage_priority") or "medium"), 9),
            -(int(row.get("citation_count") or 0)),
            -(int(row.get("year") or 0)),
        )
    )
    needed = [
        {
            "paper_id": row.get("paper_id"),
            "title": row.get("title"),
            "doi": row.get("doi"),
            "year": row.get("year"),
            "triage_label": row.get("triage_label"),
            "triage_priority": row.get("triage_priority"),
        }
        for row in relevant_missing[:100]
    ]
    return {
        "indexed_records": len(records),
        "full_text_available": len(available),
        "retained_triaged_records": len(relevant),
        "retained_missing_full_text": len(relevant_missing),
        "triage_labels": dict(sorted(labels.items())),
        "priority_missing_full_text": needed,
    }
