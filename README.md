# Literature Review Construct

**Build the literature behind your study — without handing authorship to AI.**

**Current beta:** `0.1.0b3`  
**Primary orientation:** narrative literature reviews  
**Design:** local-first, researcher-controlled, Windows-first

Literature Review Construct (LRC) is a local toolkit for researchers who want AI to help with **literature discovery, synthesis, evidence organization, research-landscape construction, and review planning** while keeping the final scholarly judgment and writing with the researcher.

LRC is not a one-click paper writer. It is a structured research workflow that helps turn a broad topic and a large literature set into a **defensible, source-linked foundation for a literature review**.

---

## Why LRC exists

A useful literature review requires more than finding papers. Researchers must decide:

- what literature actually belongs in scope;
- which papers are central rather than merely similar;
- what the main research streams and disagreements are;
- which findings are supported by full text and which remain provisional;
- what research direction is genuinely defensible;
- how the evidence should be organized into an argument.

LRC automates or assists the repetitive technical work around those decisions, but deliberately leaves the important academic decisions with the researcher.

> **The final literature review remains researcher-authored.**

---

## What LRC can do

LRC can help you:

- define and persist a Research Intent;
- search scholarly literature broadly before narrowing;
- ingest researcher-provided seed papers;
- deduplicate and prioritize literature;
- follow citations and references from important papers;
- identify major research streams, debates, methods, and recurring findings;
- build a Research Landscape and source-linked Evidence Map;
- suggest and compare possible Research Directions;
- build a Literature Review Blueprint;
- create bounded Working Draft fragments for researcher revision;
- collect lawful open-access full text when available;
- maintain a researcher-facing paper library;
- export working references, including EndNote-compatible output;
- prepare a Word Researcher Writing Pack;
- optionally prepare an AI-use statement from activities actually recorded in the project.

### What LRC does not do

LRC is not designed to:

- write a submission-ready literature review on the researcher's behalf;
- make final scholarly judgments automatically;
- guarantee exhaustive coverage of all published literature;
- treat an abstract as equivalent to checked full text;
- make unsupported claims that a research gap is globally novel;
- bypass paywalls, publisher logins, CAPTCHAs, or access controls;
- provide PRISMA/systematic-review completeness claims in the current beta.

---

# Quick start

## 1. Download the toolkit once

Clone the repository:

```powershell
git clone https://github.com/thuycq/literature-review-construct.git
cd literature-review-construct
```

Or download the repository ZIP and extract it to a permanent toolkit folder.

## 2. Install on Windows

Double-click:

```text
install.bat
```

or run it from PowerShell.

The installer provisions the LRC runtime and host integrations. You do **not** need to install Python manually.

Verify installation:

```powershell
lrc version
```

Expected current beta:

```text
0.1.0b3
```

## 3. Create a separate research folder

Do **not** use the LRC source-code repository itself as your research workspace.

For example:

```text
C:\Research\Working Capital\
```

or:

```text
C:\Research\Bank Efficiency\
```

One folder = one research project.

## 4. Open the research folder in your AI host

The current beta is best tested on **Windows with Codex Desktop and OpenCode**. LRC also includes adapters for several Agent-Skills-compatible hosts.

A universal start prompt is:

> **Start a new Literature Review Construct project in this folder. Help me define the Research Intent before you begin searching.**

To resume later:

> **Continue this Literature Review Construct project from its saved state. Do not repeat completed work. Continue technical steps automatically and stop only when you need a research decision from me.**

For OpenCode and compatible command adapters, `/lr` may also be available.

See [`QUICK_START.md`](QUICK_START.md) for Fast Start templates and more detailed usage.

---

# Toolkit folder and research folder are different things

LRC is installed once. Research projects live elsewhere.

```text
literature-review-construct/      ← toolkit source code
│
├── src/
├── skills/
├── commands/
├── tests/
├── install.bat
└── ...

C:\Research\Project A\           ← research workspace
├── AGENTS.md
├── papers/
├── references/
├── outputs/
└── .litreview/

C:\Research\Project B\           ← another research workspace
└── ...
```

The toolkit can be repaired, updated, or reinstalled without resetting a research workspace. The saved `.litreview` state inside each research folder is authoritative for that project.

---

# Two layers: local tools + AI reasoning

LRC intentionally separates work that does **not** need an AI model from work that does.

```text
Local LRC runtime / PowerShell
    ↓
search operations, full-text retrieval, file handling,
state persistence, deduplication, exports, packaging
    ↓
research workspace (.litreview + papers + outputs)
    ↓
Codex / OpenCode / other supported host
    ↓
research reasoning, synthesis, landscape construction,
direction comparison, blueprinting, researcher dialogue
```

This means long-running mechanical operations do not need to consume AI-model usage.

For example, lawful full-text retrieval can be run directly in **PowerShell**:

```powershell
lrc fulltext acquire .
```

and the remaining researcher-action queue can be inspected with:

```powershell
lrc fulltext queue .
```

The AI host can then resume the project from the updated local state.

For large acquisition batches, running the command directly in PowerShell is generally preferable to keeping a long AI-host turn open.

---

# Lawful full-text acquisition

LRC can resolve and download open/public full text reported by scholarly providers. The current resolver uses sources including OpenAlex and Semantic Scholar, with optional Unpaywall fallback.

To enable Unpaywall for the current PowerShell session:

```powershell
$env:UNPAYWALL_EMAIL="your-email@example.com"
```

Then run:

```powershell
lrc fulltext acquire .
```

LRC distinguishes between:

- successfully acquired local full text;
- lawful OA locations whose automatic download failed;
- temporary provider/network failures that should be retried automatically;
- papers that genuinely require researcher/library action.

The researcher-action queue is persisted at:

```text
.litreview/data/missing_fulltext.json
```

LRC never attempts to bypass access controls. If automatic lawful retrieval is not available, the researcher may supply a copy obtained through an institutional library, author-provided source, or another lawful route.

---

# Coverage is a diagnostic, not a target

LRC reports how much retained literature has been resolved, but **100% full-text coverage is not required**.

For a narrative review, a smaller set of high-value papers with good coverage of the important research streams may be more useful than collecting every technically retrievable paper.

The researcher decides when the evidence base is sufficiently strong for the purpose of the review.

LRC therefore treats:

```text
Coverage complete: True/False
```

as information about the corpus — not as a requirement that must be satisfied before the project can move forward.

---

# Core workflow

A typical LRC project moves through the following stages.

### 1. Research Intent

Clarify the topic, period, language, context, inclusion/exclusion boundaries, and any seed literature.

### 2. Discovery

Search broadly, deduplicate, triage, refine, and follow promising citation paths.

The researcher decides when the literature is sufficiently developed; routine technical refinement does not require repeated approval.

### 3. Research Landscape

Organize the retained literature into major streams, important papers, theories, methods, agreements, disagreements, and recent developments.

### 4. Evidence Map

Keep substantive claims linked to their source basis and make uncertainty visible.

### 5. Research Direction

Compare possible directions by contribution, evidence strength, feasibility, and risk. The toolkit can recommend; the researcher chooses.

### 6. Literature Review Blueprint

Build the structure and argument flow of the future literature review, including evidence anchors, contradictions, weaknesses, and unresolved decisions.

### 7. Working Draft fragments

Generate bounded, editable prose fragments for researcher review rather than a seamless submission-ready literature review.

### 8. Researcher handoff

Prepare the useful working materials: papers, references, source-verification tasks, EndNote export, and the Researcher Writing Pack.

---

# Human checkpoints

LRC tries not to interrupt the researcher for routine technical decisions.

The main human checkpoints are:

1. confirming the Research Intent when needed;
2. deciding whether to focus/change/finish discovery;
3. selecting the Research Direction;
4. accepting the Literature Review Blueprint;
5. verifying important sources and writing/approving the final literature review.

Deduplication, batching, OA resolution, file organization, evidence refresh, formatting, and packaging should normally proceed without unnecessary confirmation.

---

# Evidence and authorship safeguards

LRC keeps several distinctions explicit.

### Full text available ≠ full text checked

A PDF existing in the paper library does not automatically mean the AI has used it to verify a claim.

### AI checked ≠ researcher verified

Researcher verification is only recorded after explicit human verification.

### Abstract evidence ≠ full-text evidence

Claims based only on metadata or abstracts should remain appropriately provisional.

### Corpus gap ≠ global novelty

A gap observed in the current corpus is a candidate research opportunity, not automatic proof that no relevant study exists anywhere else.

These boundaries are central to the design of the toolkit.

---

# Research workspace structure

A typical project contains:

```text
Research_Project/
├── AGENTS.md
├── papers/
│   ├── full_text/
│   ├── abstract_only/
│   └── user_uploads/
├── references/
│   ├── references_used.enw
│   ├── references_used.csv
│   └── references_manifest.md
├── outputs/
│   ├── 01_research_intent.md
│   ├── 03_research_landscape.md
│   ├── 04_evidence_map.md
│   ├── 05_research_direction.md
│   ├── 06_literature_review_blueprint.md
│   ├── 06b_literature_review_working_draft.md
│   └── LitReview_Researcher_Writing_Pack.docx
└── .litreview/
```

Researchers normally interact with:

```text
papers/
references/
outputs/
```

`.litreview/` stores internal project state and normally does not need manual editing.

---

# Existing papers

If you already have relevant PDFs, place them in:

```text
papers/user_uploads/
```

Then tell the AI host:

> **I added papers to `papers/user_uploads`. Scan them as seed literature, preserve the original files, and do not assume they are all relevant.**

Researcher-provided papers are treated as seed material, not automatically as core evidence.

---

# Installation, repair, and uninstall

## Repair/update on Windows

After pulling a newer toolkit version, run:

```text
install.bat
```

The installer repairs/reinstalls the LRC runtime while preserving research workspaces and their `.litreview` state.

## Uninstall on Windows

Run:

```text
uninstall.bat
```

The uninstall workflow can remove the LRC runtime and host integrations without deleting research workspaces, PDFs, outputs, `uv`, or shared Python installations.

A fuller LRC-local cleanup option is also available.

---

# Supported hosts

The toolkit core is host-independent. Host adapters help compatible AI environments discover the same canonical workflow.

Current adapters include:

- **Codex** — primary beta target;
- **OpenCode** — primary beta target;
- Claude Code;
- Cursor;
- Windsurf;
- Gemini CLI;
- GitHub Copilot;
- Cline.

Support quality may vary across hosts and models. The current beta has received the most hands-on testing in the Windows + Codex/OpenCode workflow.

---

# Current beta limitations

- Narrative-review workflow only; no PRISMA/systematic-review completeness claims.
- Scholarly APIs may rate-limit, fail temporarily, or return incomplete metadata.
- Publisher/provider OA links are not always direct downloadable PDFs.
- Some full text will still require lawful researcher/library access.
- Bibliographic metadata can require researcher correction.
- Researcher source verification remains necessary.
- Output quality varies by AI host and model.
- The Blueprint and Working Draft are construction artifacts, not submission-ready prose.

---

# Project philosophy

LRC is built around a simple division of labor:

**Use software for repetitive research operations.**  
**Use AI for synthesis and reasoning.**  
**Use the researcher for scholarly judgment and authorship.**

The goal is not to maximize the number of papers collected or the amount of AI-generated prose. The goal is to help a researcher reach a **better-supported, more transparent, and more manageable understanding of the literature**.

---

## Documentation

- [`QUICK_START.md`](QUICK_START.md) — Fast Start prompts, maintenance, and practical usage
- [`BETA_READINESS.md`](BETA_READINESS.md) — beta behavior, safeguards, and testing notes

---

## License

MIT
