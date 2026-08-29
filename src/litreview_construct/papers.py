from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from pypdf import PdfReader

from .bibliography import detect_relations, extract_doi, normalize_doi, normalize_title
from .project import PROJECT_DIR, _atomic_write_text, _write_json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_location(root: Path, path: Path) -> tuple[str, str]:
    try:
        return str(path.relative_to(root)), "managed"
    except ValueError:
        return str(path), "external"


def _extract_pdf_metadata(path: Path) -> dict[str, object]:
    title = None
    authors: list[str] = []
    doi = None
    page_count = None
    parse_status = "ok"
    error = None
    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        metadata = reader.metadata or {}
        raw_title = getattr(metadata, "title", None)
        raw_author = getattr(metadata, "author", None)
        raw_subject = getattr(metadata, "subject", None)
        if raw_title:
            title = str(raw_title).strip() or None
        if raw_author:
            authors = [
                part.strip()
                for part in str(raw_author).replace(";", ",").split(",")
                if part.strip()
            ]

        # DOI extraction is deliberately bounded to document metadata and the
        # first two pages. Full-text extraction belongs to later evidence stages.
        doi = extract_doi(str(raw_subject) if raw_subject else None)
        if doi is None:
            first_pages: list[str] = []
            for page in reader.pages[:2]:
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                if text:
                    first_pages.append(text)
            doi = extract_doi("\n".join(first_pages))
    except Exception as exc:  # parser failures are recorded, not fatal to the scan
        parse_status = "metadata_error"
        error = str(exc)

    display_title = title or path.stem
    return {
        "title": display_title,
        "normalized_title": normalize_title(display_title),
        "authors": authors,
        "doi": normalize_doi(doi),
        "page_count": page_count,
        "parse_status": parse_status,
        "parse_error": error,
    }


def _load_project(root: Path) -> dict[str, object]:
    project_file = root / PROJECT_DIR / "project.yaml"
    if not project_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return yaml.safe_load(project_file.read_text(encoding="utf-8"))


def _load_records(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _records_by_hash(records: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        str(record["file_hash"]): record
        for record in records
        if record.get("file_hash")
    }


def _ensure_file_instance(
    record: dict[str, object], root: Path, pdf: Path
) -> tuple[str, str, bool]:
    reference, location_type = _file_location(root, pdf)
    instances = record.get("file_instances")
    if not isinstance(instances, list):
        instances = []
        old_reference = record.get("file_reference")
        old_location = record.get("location_type")
        if old_reference:
            instances.append(
                {
                    "file_reference": str(old_reference),
                    "location_type": str(old_location or "managed"),
                }
            )
    candidate = {"file_reference": reference, "location_type": location_type}
    added = candidate not in instances
    if added:
        instances.append(candidate)
        record["updated_at"] = _now()
    record["file_instances"] = instances
    return reference, location_type, added


def resolve_bibliography(root: Path) -> dict[str, object]:
    """Rebuild bibliographic relation candidates from indexed paper records."""
    root = root.expanduser().resolve()
    _load_project(root)
    state_root = root / PROJECT_DIR
    records_file = state_root / "data" / "papers.jsonl"
    records = _load_records(records_file)
    relations = detect_relations(records)
    relations_file = state_root / "data" / "paper_relations.jsonl"
    payload = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in relations)
    _atomic_write_text(relations_file, payload)
    return {
        "records_total": len(records),
        "relation_candidates": len(relations),
        "same_work": sum(item["relation"] == "same_work" for item in relations),
        "probable_duplicates": sum(
            item["relation"] == "probable_duplicate" for item in relations
        ),
        "possible_versions": sum(item["relation"] == "possible_version" for item in relations),
        "relations_file": str(relations_file),
    }


def _render_inventory(
    root: Path,
    source_dir: Path,
    pdf_count: int,
    all_records: list[dict[str, object]],
    scanned_ids: list[str],
    relation_summary: dict[str, object],
) -> Path:
    scanned_set = set(scanned_ids)
    inventory_lines = [
        "# Existing Literature Inventory",
        "",
        f"Seed source: `{source_dir}`",
        f"PDF files detected: **{pdf_count}**",
        f"Unique indexed paper records: **{len(all_records)}**",
        f"Bibliographic relation candidates: **{relation_summary['relation_candidates']}**",
        "",
        "| Title | DOI | Location | Parse status | Status |",
        "|---|---|---|---|---|",
    ]
    for record in all_records:
        if str(record.get("paper_id")) not in scanned_set:
            continue
        title = str(record.get("title") or "Untitled").replace("|", "\\|")
        doi = str(record.get("doi") or "")
        locations = record.get("file_instances")
        if isinstance(locations, list) and locations:
            location_label = ", ".join(
                sorted({str(item.get("location_type", "unknown")) for item in locations})
            )
        else:
            location_label = str(record.get("location_type") or "unknown")
        inventory_lines.append(
            f"| {title} | {doi} | {location_label} | {record['parse_status']} | {record['status']} |"
        )

    inventory_lines.extend(
        [
            "",
            "## Bibliographic relation candidates",
            "",
            f"- Same scholarly work (high-confidence DOI match): **{relation_summary['same_work']}**",
            f"- Probable duplicate records: **{relation_summary['probable_duplicates']}**",
            f"- Possible related versions: **{relation_summary['possible_versions']}**",
            "",
            "> Relation candidates are linked for review and are not silently merged. User-provided papers remain seed literature until relevance is assessed.",
            "",
        ]
    )
    output = root / "outputs" / "02_seed_inventory.md"
    _atomic_write_text(output, "\n".join(inventory_lines))
    return output


def scan_seed_papers(root: Path, source: Path | None = None) -> dict[str, object]:
    root = root.expanduser().resolve()
    _load_project(root)
    state_root = root / PROJECT_DIR
    source_dir = source.expanduser().resolve() if source else root / "papers"
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Paper folder not found: {source_dir}")

    records_file = state_root / "data" / "papers.jsonl"
    records = _load_records(records_file)
    by_hash = _records_by_hash(records)
    scanned_ids: list[str] = []
    duplicate_file_count = 0

    pdfs = sorted(p for p in source_dir.rglob("*.pdf") if p.is_file())
    for pdf in pdfs:
        file_hash = _sha256(pdf)
        if file_hash in by_hash:
            record = by_hash[file_hash]
            _, _, added_instance = _ensure_file_instance(record, root, pdf)
            if added_instance:
                duplicate_file_count += 1
        else:
            metadata = _extract_pdf_metadata(pdf)
            relative_path, location_type = _file_location(root, pdf)
            record = {
                "paper_id": str(uuid4()),
                "title": metadata["title"],
                "normalized_title": metadata["normalized_title"],
                "authors": metadata["authors"],
                "year": None,
                "doi": metadata["doi"],
                "openalex_id": None,
                "journal": None,
                "language": None,
                "source_origin": "user_seed",
                "location_type": location_type,
                "file_reference": relative_path,
                "file_instances": [
                    {"file_reference": relative_path, "location_type": location_type}
                ],
                "file_hash": file_hash,
                "page_count": metadata["page_count"],
                "parse_status": metadata["parse_status"],
                "parse_error": metadata["parse_error"],
                "status": "user_seed",
                "created_at": _now(),
                "updated_at": _now(),
            }
            records.append(record)
            by_hash[file_hash] = record
        scanned_ids.append(str(record["paper_id"]))

    # Backfill normalized fields for records created by earlier runtime versions.
    for record in records:
        record["normalized_title"] = normalize_title(str(record.get("title") or ""))
        if isinstance(record.get("doi"), str):
            record["doi"] = normalize_doi(str(record["doi"]))
        instances = record.get("file_instances")
        if not isinstance(instances, list):
            old_reference = record.get("file_reference")
            if old_reference:
                record["file_instances"] = [
                    {
                        "file_reference": str(old_reference),
                        "location_type": str(record.get("location_type") or "managed"),
                    }
                ]

    all_records = sorted(records, key=lambda item: str(item.get("title") or "").lower())
    payload = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in all_records)
    _atomic_write_text(records_file, payload)

    relation_summary = resolve_bibliography(root)
    inventory = _render_inventory(
        root,
        source_dir,
        len(pdfs),
        all_records,
        scanned_ids,
        relation_summary,
    )

    state_file = state_root / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["seed_literature"]["status"] = "in_progress"
    state["stages"]["seed_literature"]["revision"] += 1
    # Seed papers may be supplied while Research Intent is still being refined.
    # Do not implicitly complete or replace the current stage here.
    if state["stages"]["research_intent"]["status"] in {"accepted", "ready_for_review"}:
        state["current_stage"] = "seed_literature"
    _write_json(state_file, state)

    activity_file = state_root / "activity" / "activity.jsonl"
    event = {
        "event_id": str(uuid4()),
        "timestamp": _now(),
        "category": "seed_indexing",
        "actor": "toolkit",
        "host": None,
        "model": None,
        "inputs": {"source": str(source_dir)},
        "outputs": [
            ".litreview/data/papers.jsonl",
            ".litreview/data/paper_relations.jsonl",
            "outputs/02_seed_inventory.md",
        ],
        "source_ids": sorted(set(scanned_ids)),
        "notes": None,
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "source": str(source_dir),
        "pdfs_detected": len(pdfs),
        "records_total": len(all_records),
        "duplicate_files": duplicate_file_count,
        "relation_candidates": relation_summary["relation_candidates"],
        "same_work": relation_summary["same_work"],
        "probable_duplicates": relation_summary["probable_duplicates"],
        "possible_versions": relation_summary["possible_versions"],
        "inventory": str(inventory),
    }
