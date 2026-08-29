from __future__ import annotations

import csv
import io
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .activity import append_activity
from .bibliography import normalize_doi
from .project import PROJECT_DIR, _atomic_write_text, _write_json
from .word_export import export_artifact_docx


_WINDOWS_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_SPACE = re.compile(r"\s+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root


def _load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    _atomic_write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _safe_identifier(value: str, *, limit: int = 150) -> str:
    text = _WINDOWS_UNSAFE.sub("__", value.strip())
    text = _SPACE.sub("_", text)
    text = text.strip(" ._")
    return (text or "unknown")[:limit].rstrip(" ._")


def canonical_paper_stem(row: dict[str, object]) -> str:
    """Return a stable, Windows-safe researcher-facing filename stem.

    DOI is preferred because it is the most portable scholarly identifier. The DOI slash is
    intentionally rendered as a double underscore so the identifier remains visually reversible.
    """
    doi = normalize_doi(str(row.get("doi"))) if row.get("doi") else None
    if doi:
        prefix, _, suffix = doi.partition("/")
        return "doi_" + _safe_identifier(prefix) + "__" + _safe_identifier(suffix)
    openalex = str(row.get("openalex_id") or "").rstrip("/").rsplit("/", 1)[-1]
    if openalex:
        return "openalex_" + _safe_identifier(openalex)
    s2 = str(row.get("s2_paper_id") or "")
    if s2:
        return "s2_" + _safe_identifier(s2)
    return "paper_" + _safe_identifier(str(row.get("paper_id") or "unknown"))


def _file_references(row: dict[str, object]) -> list[str]:
    refs: list[str] = []
    instances = row.get("file_instances")
    if isinstance(instances, list):
        for item in instances:
            if isinstance(item, dict) and item.get("file_reference"):
                value = str(item["file_reference"])
                if value not in refs:
                    refs.append(value)
    if row.get("file_reference"):
        value = str(row["file_reference"])
        if value not in refs:
            refs.append(value)
    return refs


def _existing_file(root: Path, row: dict[str, object]) -> Path | None:
    for reference in _file_references(row):
        candidate = Path(reference)
        path = candidate if candidate.is_absolute() else root / candidate
        if path.is_file():
            return path
    return None


def _working_paper_ids(root: Path) -> list[str]:
    """Return papers actually used by the current working artifact, not the whole discovery corpus."""
    state_root = root / PROJECT_DIR / "data"
    ordered: list[str] = []
    seen: set[str] = set()

    def add(values: object) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            paper_id = str(value or "")
            if paper_id and paper_id not in seen:
                seen.add(paper_id)
                ordered.append(paper_id)

    working = _load_json(state_root / "working_draft.json")
    if working:
        for section in working.get("sections") or []:
            if not isinstance(section, dict):
                continue
            for fragment in section.get("fragments") or []:
                if isinstance(fragment, dict):
                    add(fragment.get("paper_ids"))
    if ordered:
        return ordered

    blueprint = _load_json(state_root / "blueprint.json")
    if blueprint:
        for section in blueprint.get("sections") or []:
            if not isinstance(section, dict):
                continue
            add(section.get("anchor_paper_ids"))
            add(section.get("supporting_paper_ids"))
            add(section.get("conflicting_paper_ids"))
    if ordered:
        return ordered

    evidence = _load_jsonl(state_root / "evidence.jsonl")
    add([row.get("paper_id") for row in evidence if row.get("paper_id")])
    return ordered


def _ensure_library_dirs(root: Path) -> dict[str, Path]:
    paths = {
        "papers": root / "papers",
        "full_text": root / "papers" / "full_text",
        "abstract_only": root / "papers" / "abstract_only",
        "user_uploads": root / "papers" / "user_uploads",
        "references": root / "references",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _migrate_managed_oa(root: Path, records: list[dict[str, object]], full_text_dir: Path) -> int:
    """Expose toolkit-acquired OA PDFs in papers/full_text and update canonical file references."""
    migrated = 0
    for row in records:
        provenance = row.get("full_text_provenance")
        if not isinstance(provenance, dict) or provenance.get("access") != "open_access":
            continue
        source = _existing_file(root, row)
        if source is None:
            continue
        target = full_text_dir / f"{canonical_paper_stem(row)}.pdf"
        if source.resolve() != target.resolve():
            if not target.exists():
                shutil.copy2(source, target)
            migrated += 1
        reference = str(target.relative_to(root))
        old_refs = _file_references(row)
        row["file_reference"] = reference
        row["location_type"] = "managed"
        instances = [{"file_reference": reference, "location_type": "managed"}]
        for old in old_refs:
            if old != reference:
                instances.append({"file_reference": old, "location_type": "legacy_cache"})
        row["file_instances"] = instances
        row["researcher_library_path"] = reference
        row["updated_at"] = _now()
    return migrated


def _abstract_note(row: dict[str, object]) -> str:
    authors = row.get("authors") if isinstance(row.get("authors"), list) else []
    roles = row.get("landscape_roles") if isinstance(row.get("landscape_roles"), list) else []
    lines = [
        f"# {row.get('title') or 'Untitled'}",
        "",
        f"- Authors: {', '.join(str(v) for v in authors) or 'Unknown'}",
        f"- Year: {row.get('year') or 'Unknown'}",
        f"- Journal/source: {row.get('journal') or row.get('venue') or 'Unknown'}",
        f"- DOI: {normalize_doi(str(row.get('doi'))) if row.get('doi') else 'Not available'}",
        f"- Current role: {', '.join(str(v) for v in roles) or row.get('triage_priority') or row.get('triage_label') or 'working literature'}",
        "- Full-text status: not locally available; abstract-level use remains provisional",
        "",
        "## Abstract",
        "",
        str(row.get("abstract") or "Abstract not available in the canonical record."),
        "",
        "> This file is a researcher-facing access note, not a substitute for the full paper. Verify the full text before treating detailed claims as established evidence.",
        "",
    ]
    return "\n".join(lines)


def _render_enw(records: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for row in records:
        lines = ["%0 Journal Article"]
        authors = row.get("authors") if isinstance(row.get("authors"), list) else []
        for author in authors:
            if str(author).strip():
                lines.append(f"%A {str(author).strip()}")
        if row.get("year"):
            lines.append(f"%D {row['year']}")
        if row.get("title"):
            lines.append(f"%T {row['title']}")
        journal = row.get("journal") or row.get("venue") or row.get("source")
        if journal:
            lines.append(f"%J {journal}")
        if row.get("volume"):
            lines.append(f"%V {row['volume']}")
        if row.get("issue"):
            lines.append(f"%N {row['issue']}")
        pages = row.get("pages") or row.get("page")
        if pages:
            lines.append(f"%P {pages}")
        doi = normalize_doi(str(row.get("doi"))) if row.get("doi") else None
        if doi:
            lines.append(f"%R {doi}")
            lines.append(f"%U https://doi.org/{doi}")
        else:
            url = row.get("url")
            if not url and isinstance(row.get("oa_best_location"), dict):
                url = row["oa_best_location"].get("landing_url") or row["oa_best_location"].get("pdf_url")
            if url:
                lines.append(f"%U {url}")
        if row.get("abstract"):
            lines.append("%X " + str(row["abstract"]).replace("\r", " ").replace("\n", " "))
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks) + ("\n" if chunks else "")


def _render_csv(records: list[dict[str, object]], section_map: dict[str, list[str]]) -> str:
    output = io.StringIO(newline="")
    fieldnames = [
        "paper_id",
        "used_in_sections",
        "authors",
        "year",
        "title",
        "journal",
        "doi",
        "full_text_status",
        "researcher_verification_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in records:
        paper_id = str(row.get("paper_id") or "")
        writer.writerow(
            {
                "paper_id": paper_id,
                "used_in_sections": "; ".join(section_map.get(paper_id) or []),
                "authors": "; ".join(str(v) for v in row.get("authors") or []),
                "year": row.get("year") or "",
                "title": row.get("title") or "",
                "journal": row.get("journal") or row.get("venue") or "",
                "doi": normalize_doi(str(row.get("doi"))) if row.get("doi") else "",
                "full_text_status": "available" if row.get("file_reference") or row.get("file_hash") else "abstract_only",
                "researcher_verification_status": "pending",
            }
        )
    return output.getvalue()


def _section_map(root: Path) -> dict[str, list[str]]:
    working = _load_json(root / PROJECT_DIR / "data" / "working_draft.json") or {}
    mapping: dict[str, list[str]] = {}
    for section in working.get("sections") or []:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title") or section.get("section_id") or "Working Draft")
        for fragment in section.get("fragments") or []:
            if not isinstance(fragment, dict):
                continue
            for paper_id in fragment.get("paper_ids") or []:
                value = str(paper_id)
                mapping.setdefault(value, [])
                if title not in mapping[value]:
                    mapping[value].append(title)
    return mapping


def prepare_researcher_package(root: Path, *, export_word: bool = True) -> dict[str, object]:
    root = _project_root(root)
    dirs = _ensure_library_dirs(root)
    papers_file = root / PROJECT_DIR / "data" / "papers.jsonl"
    records = _load_jsonl(papers_file)
    by_id = {str(row.get("paper_id")): row for row in records if row.get("paper_id")}

    migrated = _migrate_managed_oa(root, records, dirs["full_text"])
    _write_jsonl(papers_file, records)

    used_ids = _working_paper_ids(root)
    used_records = [by_id[paper_id] for paper_id in used_ids if paper_id in by_id]

    # abstract_only is toolkit-managed: keep it synchronized with the current working literature.
    for existing in dirs["abstract_only"].glob("*.md"):
        existing.unlink()
    abstract_only = 0
    for row in used_records:
        if _existing_file(root, row) is not None:
            continue
        note = dirs["abstract_only"] / f"{canonical_paper_stem(row)}.md"
        _atomic_write_text(note, _abstract_note(row))
        abstract_only += 1

    section_map = _section_map(root)
    enw = dirs["references"] / "references_used.enw"
    csv_file = dirs["references"] / "references_used.csv"
    manifest_md = dirs["references"] / "references_manifest.md"
    _atomic_write_text(enw, _render_enw(used_records))
    _atomic_write_text(csv_file, _render_csv(used_records, section_map))

    full_text_used = sum(_existing_file(root, row) is not None for row in used_records)
    manifest_lines = [
        "# Researcher Reference Manifest",
        "",
        f"Generated: {_now()}",
        f"References used in the current Working Draft/Blueprint: **{len(used_records)}**",
        f"Used references with local full text: **{full_text_used}**",
        f"Used references currently abstract-only: **{abstract_only}**",
        "",
        "- `references_used.enw` — EndNote tagged import file generated from canonical scholarly records.",
        "- `references_used.csv` — quick audit table with section usage and verification status.",
        "- `papers/full_text/` — toolkit-acquired lawful OA PDFs, named by DOI where available.",
        "- `papers/abstract_only/` — working references without local full text; these remain provisional.",
        "- `papers/user_uploads/` — researcher drop zone; user files are not renamed or moved automatically.",
        "",
        "> Reference files are generated from canonical records, not from AI-written citation strings. Researcher verification remains pending unless explicitly recorded elsewhere.",
        "",
    ]
    _atomic_write_text(manifest_md, "\n".join(manifest_lines))

    word_output = None
    if export_word:
        try:
            word_output = export_artifact_docx(root, artifact="handoff")["output"]
        except ValueError:
            word_output = None

    report = {
        "schema_version": 1,
        "generated_at": _now(),
        "working_reference_count": len(used_records),
        "working_full_text_count": full_text_used,
        "working_abstract_only_count": abstract_only,
        "managed_oa_migrated": migrated,
        "paper_library": {
            "full_text": "papers/full_text",
            "abstract_only": "papers/abstract_only",
            "user_uploads": "papers/user_uploads",
        },
        "references": {
            "endnote": "references/references_used.enw",
            "csv": "references/references_used.csv",
            "manifest": "references/references_manifest.md",
        },
        "word_handoff": str(Path(word_output).relative_to(root)) if word_output and Path(word_output).is_relative_to(root) else word_output,
        "researcher_verification_status": "pending",
    }
    _write_json(root / PROJECT_DIR / "data" / "researcher_package.json", report)
    append_activity(
        root,
        category="researcher_handoff",
        actor="toolkit",
        inputs={"action": "prepare_researcher_package", "working_paper_ids": used_ids},
        outputs=[
            "papers/full_text/",
            "papers/abstract_only/",
            "papers/user_uploads/",
            "references/references_used.enw",
            "references/references_used.csv",
            "references/references_manifest.md",
            ".litreview/data/researcher_package.json",
            *([str(Path(word_output).relative_to(root))] if word_output and Path(word_output).is_relative_to(root) else []),
        ],
        source_ids=used_ids,
        notes="Prepared the researcher-facing literature library, canonical EndNote export, audit CSV, and Word handoff without changing researcher-authored files.",
    )
    return report


def researcher_package_status(root: Path) -> dict[str, object]:
    root = _project_root(root)
    report = _load_json(root / PROJECT_DIR / "data" / "researcher_package.json")
    return report or {"status": "not_prepared"}
