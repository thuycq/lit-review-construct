from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from pypdf import PdfReader

from .project import PROJECT_DIR, _atomic_write_text, _write_json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_pdf_metadata(path: Path) -> dict[str, object]:
    title = None
    authors: list[str] = []
    page_count = None
    parse_status = "ok"
    error = None
    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        metadata = reader.metadata or {}
        raw_title = getattr(metadata, "title", None)
        raw_author = getattr(metadata, "author", None)
        if raw_title:
            title = str(raw_title).strip() or None
        if raw_author:
            authors = [part.strip() for part in str(raw_author).replace(";", ",").split(",") if part.strip()]
    except Exception as exc:  # parser failures are recorded, not fatal to the scan
        parse_status = "metadata_error"
        error = str(exc)

    return {
        "title": title or path.stem,
        "authors": authors,
        "page_count": page_count,
        "parse_status": parse_status,
        "parse_error": error,
    }


def _load_project(root: Path) -> dict[str, object]:
    project_file = root / PROJECT_DIR / "project.yaml"
    if not project_file.exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return yaml.safe_load(project_file.read_text(encoding="utf-8"))


def _load_existing_records(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        file_hash = record.get("file_hash")
        if file_hash:
            records[str(file_hash)] = record
    return records


def scan_seed_papers(root: Path, source: Path | None = None) -> dict[str, object]:
    root = root.expanduser().resolve()
    _load_project(root)
    state_root = root / PROJECT_DIR
    source_dir = (source.expanduser().resolve() if source else root / "papers")
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Paper folder not found: {source_dir}")

    records_file = state_root / "data" / "papers.jsonl"
    existing = _load_existing_records(records_file)
    scanned: list[dict[str, object]] = []
    duplicate_count = 0

    pdfs = sorted(p for p in source_dir.rglob("*.pdf") if p.is_file())
    for pdf in pdfs:
        file_hash = _sha256(pdf)
        if file_hash in existing:
            record = existing[file_hash]
            duplicate_count += 1
        else:
            metadata = _extract_pdf_metadata(pdf)
            try:
                relative_path = str(pdf.relative_to(root))
                location_type = "managed"
            except ValueError:
                relative_path = str(pdf)
                location_type = "external"

            record = {
                "paper_id": str(uuid4()),
                "title": metadata["title"],
                "authors": metadata["authors"],
                "year": None,
                "doi": None,
                "openalex_id": None,
                "journal": None,
                "language": None,
                "source_origin": "user_seed",
                "location_type": location_type,
                "file_reference": relative_path,
                "file_hash": file_hash,
                "page_count": metadata["page_count"],
                "parse_status": metadata["parse_status"],
                "parse_error": metadata["parse_error"],
                "status": "user_seed",
                "created_at": _now(),
                "updated_at": _now(),
            }
            existing[file_hash] = record
        scanned.append(record)

    all_records = sorted(existing.values(), key=lambda item: str(item.get("title") or "").lower())
    payload = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in all_records)
    _atomic_write_text(records_file, payload)

    inventory_lines = [
        "# Existing Literature Inventory",
        "",
        f"Seed source: `{source_dir}`",
        f"PDF files detected: **{len(pdfs)}**",
        f"Unique indexed papers: **{len(all_records)}**",
        "",
        "| Title | Location | Parse status | Status |",
        "|---|---|---|---|",
    ]
    for record in scanned:
        title = str(record.get("title") or "Untitled").replace("|", "\\|")
        inventory_lines.append(
            f"| {title} | {record['location_type']} | {record['parse_status']} | {record['status']} |"
        )
    inventory_lines.extend([
        "",
        "> User-provided papers are seed literature. They are not automatically treated as final relevant literature.",
        "",
    ])
    _atomic_write_text(root / "outputs" / "02_seed_inventory.md", "\n".join(inventory_lines))

    state_file = state_root / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["current_stage"] = "seed_literature"
    state["stages"]["research_intent"]["status"] = "ready_for_review"
    state["stages"]["seed_literature"]["status"] = "in_progress"
    state["stages"]["seed_literature"]["revision"] += 1
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
        "outputs": [".litreview/data/papers.jsonl", "outputs/02_seed_inventory.md"],
        "source_ids": [record["paper_id"] for record in scanned],
        "notes": None,
    }
    with activity_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "source": str(source_dir),
        "pdfs_detected": len(pdfs),
        "records_total": len(all_records),
        "duplicates_seen": duplicate_count,
        "inventory": str(root / "outputs" / "02_seed_inventory.md"),
    }
