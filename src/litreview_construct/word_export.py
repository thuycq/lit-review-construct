from __future__ import annotations

import re
from pathlib import Path

import yaml
from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Inches, Pt

from .activity import append_activity
from .project import PROJECT_DIR


ARTIFACTS = {
    "intent": ("outputs/01_research_intent.md", "01_research_intent.docx"),
    "seed-inventory": ("outputs/02_seed_inventory.md", "02_seed_inventory.docx"),
    "landscape": ("outputs/03_research_landscape.md", "03_research_landscape.docx"),
    "evidence": ("outputs/04_evidence_map.md", "04_evidence_map.docx"),
    "direction": ("outputs/05_research_direction.md", "05_research_direction.docx"),
    "blueprint": ("outputs/06_literature_review_blueprint.md", "06_literature_review_blueprint.docx"),
    "working-draft": ("outputs/06b_literature_review_working_draft.md", "06b_literature_review_working_draft.docx"),
    "ai-use": ("outputs/07_ai_use_statement.md", "07_ai_use_statement.docx"),
}

HANDOFF_ORDER = ["intent", "landscape", "evidence", "direction", "blueprint", "working-draft", "ai-use"]


def _project_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root


def _configure(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    normal.paragraph_format.line_spacing = 1.15
    for name, size in [("Title", 18), ("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 11)]:
        style = document.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True


def _split_inline(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))")
    parts: list[tuple[str, str]] = []
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            parts.append(("text", text[pos:match.start()]))
        token = match.group(0)
        if token.startswith("**"):
            parts.append(("bold", token[2:-2]))
        elif token.startswith("`"):
            parts.append(("code", token[1:-1]))
        else:
            label, url = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", token).groups()  # type: ignore[union-attr]
            parts.append(("link", f"{label} ({url})"))
        pos = match.end()
    if pos < len(text):
        parts.append(("text", text[pos:]))
    return parts


def _add_inline(paragraph, text: str) -> None:
    for kind, value in _split_inline(text):
        run = paragraph.add_run(value)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        if kind == "bold":
            run.bold = True
        elif kind == "code":
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
        elif kind == "link":
            run.underline = True


def _table_cells(line: str) -> list[str]:
    text = line.strip().strip("|")
    return [cell.strip().replace("\\|", "|") for cell in text.split("|")]


def _is_separator(line: str) -> bool:
    cells = _table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _add_table(document: Document, lines: list[str]) -> None:
    rows = [_table_cells(line) for line in lines if line.strip()]
    if len(rows) >= 2 and _is_separator(lines[1]):
        rows = [rows[0], *rows[2:]]
    if not rows:
        return
    width = max(len(row) for row in rows)
    table = document.add_table(rows=len(rows), cols=width)
    table.style = "Table Grid"
    for r_index, row in enumerate(rows):
        for c_index in range(width):
            text = row[c_index] if c_index < len(row) else ""
            paragraph = table.cell(r_index, c_index).paragraphs[0]
            _add_inline(paragraph, text)
            if r_index == 0:
                for run in paragraph.runs:
                    run.bold = True


def _append_markdown(document: Document, markdown: str, *, suppress_first_title: bool = False) -> None:
    lines = markdown.splitlines()
    i = 0
    first_heading_seen = False
    while i < len(lines):
        raw = lines[i].rstrip()
        if raw.startswith("|") and i + 1 < len(lines) and lines[i + 1].lstrip().startswith("|") and _is_separator(lines[i + 1]):
            table_lines = [raw, lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                table_lines.append(lines[i].rstrip())
                i += 1
            _add_table(document, table_lines)
            continue
        if not raw.strip():
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", raw)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if suppress_first_title and not first_heading_seen and level == 1:
                first_heading_seen = True
                i += 1
                continue
            first_heading_seen = True
            document.add_heading(text, level=min(level, 3))
            i += 1
            continue
        if raw.startswith(">"):
            paragraph = document.add_paragraph()
            run = paragraph.add_run(raw.lstrip("> "))
            run.italic = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
            i += 1
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", raw)
        if numbered:
            paragraph = document.add_paragraph(style="List Number")
            _add_inline(paragraph, numbered.group(2))
            i += 1
            continue
        if raw.startswith("- "):
            paragraph = document.add_paragraph(style="List Bullet")
            _add_inline(paragraph, raw[2:])
            i += 1
            continue
        paragraph = document.add_paragraph()
        _add_inline(paragraph, raw)
        i += 1


def _project_name(root: Path) -> str:
    payload = yaml.safe_load((root / PROJECT_DIR / "project.yaml").read_text(encoding="utf-8")) or {}
    return str(payload.get("name") or payload.get("project_name") or root.name)


def export_artifact_docx(root: Path, *, artifact: str, output: Path | None = None) -> dict[str, object]:
    root = _project_root(root)
    if artifact == "handoff":
        return export_handoff_docx(root, output=output)
    if artifact not in ARTIFACTS:
        raise ValueError("Unknown Word artifact. Choose: " + ", ".join([*ARTIFACTS, "handoff"]))
    source_rel, default_name = ARTIFACTS[artifact]
    source = root / source_rel
    if not source.exists():
        raise ValueError(f"Artifact is not available yet: {source_rel}")
    target = output.expanduser().resolve() if output else root / "outputs" / default_name
    target.parent.mkdir(parents=True, exist_ok=True)

    document = Document()
    _configure(document)
    _append_markdown(document, source.read_text(encoding="utf-8"))
    document.core_properties.title = f"{_project_name(root)} — {artifact}"
    document.core_properties.subject = "Lit Review Construct researcher artifact"
    document.save(target)
    append_activity(
        root,
        category="document_export",
        actor="toolkit",
        inputs={"format": "docx", "artifact": artifact},
        outputs=[str(target.relative_to(root)) if target.is_relative_to(root) else str(target)],
        notes="Exported a project artifact to Word. Structured Markdown/JSON remains authoritative project state.",
    )
    return {"artifact": artifact, "source": str(source), "output": str(target)}


def export_handoff_docx(root: Path, *, output: Path | None = None) -> dict[str, object]:
    root = _project_root(root)
    available: list[tuple[str, Path]] = []
    for artifact in HANDOFF_ORDER:
        source_rel, _ = ARTIFACTS[artifact]
        source = root / source_rel
        if source.exists():
            available.append((artifact, source))
    if not available:
        raise ValueError("No researcher-handoff artifacts are available to export.")
    target = output.expanduser().resolve() if output else root / "outputs" / "LitReview_Researcher_Handoff.docx"
    target.parent.mkdir(parents=True, exist_ok=True)

    document = Document()
    _configure(document)
    document.add_heading("Lit Review Construct — Researcher Handoff", 0)
    p = document.add_paragraph()
    _add_inline(p, _project_name(root))
    document.add_paragraph("Generated from the project's saved Lit Review Construct artifacts. Markdown/JSON remains the authoritative workflow state.")

    for index, (artifact, source) in enumerate(available):
        if index:
            document.add_page_break()
        label = artifact.replace("-", " ").title()
        document.add_heading(label, level=1)
        _append_markdown(document, source.read_text(encoding="utf-8"), suppress_first_title=True)

    document.core_properties.title = f"{_project_name(root)} — Researcher Handoff"
    document.core_properties.subject = "Lit Review Construct researcher handoff package"
    document.save(target)
    append_activity(
        root,
        category="document_export",
        actor="toolkit",
        inputs={"format": "docx", "artifact": "handoff", "included": [name for name, _ in available]},
        outputs=[str(target.relative_to(root)) if target.is_relative_to(root) else str(target)],
        notes="Exported the researcher handoff package to Word. Structured Markdown/JSON remains authoritative project state.",
    )
    return {"artifact": "handoff", "included": [name for name, _ in available], "output": str(target)}
