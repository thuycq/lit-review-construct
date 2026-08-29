from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .bibliography import normalize_doi
from .project import PROJECT_DIR, _atomic_write_text


_WINDOWS_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _safe(value: str, limit: int = 150) -> str:
    return _WINDOWS_UNSAFE.sub("__", value.strip()).strip(" ._")[:limit] or "unknown"


def canonical_paper_stem(row: dict[str, object]) -> str:
    doi = normalize_doi(str(row.get("doi"))) if row.get("doi") else None
    if doi:
        prefix, _, suffix = doi.partition("/")
        return f"doi_{_safe(prefix)}__{_safe(suffix)}"
    openalex = str(row.get("openalex_id") or "").rstrip("/").rsplit("/", 1)[-1]
    if openalex:
        return "openalex_" + _safe(openalex)
    s2 = str(row.get("s2_paper_id") or "")
    if s2:
        return "s2_" + _safe(s2)
    return "paper_" + _safe(str(row.get("paper_id") or "unknown"))


def _existing_reference(root: Path, row: dict[str, object]) -> Path | None:
    refs: list[str] = []
    if row.get("file_reference"):
        refs.append(str(row["file_reference"]))
    instances = row.get("file_instances")
    if isinstance(instances, list):
        refs.extend(
            str(item.get("file_reference"))
            for item in instances
            if isinstance(item, dict) and item.get("file_reference")
        )
    for reference in refs:
        candidate = Path(reference)
        path = candidate if candidate.is_absolute() else root / candidate
        if path.is_file():
            return path
    return None


def sync_acquired_oa_library(root: Path) -> dict[str, object]:
    """Copy toolkit-acquired OA PDFs into papers/full_text with stable DOI-based names.

    Researcher-provided files are never renamed or moved. Legacy cache files remain available as
    provenance instances, while the canonical record points to the researcher-facing copy.
    """
    root = root.expanduser().resolve()
    papers_file = root / PROJECT_DIR / "data" / "papers.jsonl"
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    records = _load_jsonl(papers_file)
    target_dir = root / "papers" / "full_text"
    target_dir.mkdir(parents=True, exist_ok=True)
    (root / "papers" / "abstract_only").mkdir(parents=True, exist_ok=True)
    (root / "papers" / "user_uploads").mkdir(parents=True, exist_ok=True)

    copied = 0
    available = 0
    for row in records:
        provenance = row.get("full_text_provenance")
        if not isinstance(provenance, dict) or provenance.get("access") != "open_access":
            continue
        source = _existing_reference(root, row)
        if source is None:
            continue
        available += 1
        target = target_dir / f"{canonical_paper_stem(row)}.pdf"
        old_refs: list[str] = []
        if row.get("file_reference"):
            old_refs.append(str(row["file_reference"]))
        if source.resolve() != target.resolve() and not target.exists():
            shutil.copy2(source, target)
            copied += 1
        reference = str(target.relative_to(root))
        row["file_reference"] = reference
        row["location_type"] = "managed"
        instances = [{"file_reference": reference, "location_type": "managed"}]
        for old in old_refs:
            if old != reference:
                instances.append({"file_reference": old, "location_type": "legacy_cache"})
        row["file_instances"] = instances
        row["researcher_library_path"] = reference
        row["updated_at"] = _now()

    _atomic_write_text(
        papers_file,
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
    )
    return {
        "oa_full_text_available": available,
        "copied_to_researcher_library": copied,
        "library": "papers/full_text",
    }
