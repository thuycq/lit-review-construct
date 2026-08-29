# Lit Review Construct

Lit Review Construct is a local-first, AI-assisted toolkit for **constructing the literature behind a research study**.

It helps a researcher move from an initial idea to a broad literature universe, understand the field before narrowing, organize source-disciplined evidence, choose a defensible research direction, and build a Literature Review Blueprint plus bounded Working Draft fragments.

It does **not** generate a complete final literature review for direct submission. The researcher remains responsible for scholarly judgment, source/citation verification, interpretation, citation selection, authorship, and final prose.

## Beta build

**`0.1.0b1`**

This beta incorporates findings from the first full end-to-end benchmark, especially repeated technical checkpoints, refine loops, developer-oriented chat output, full-text status ambiguity, hidden PDF storage, missing EndNote handoff, and stale next-step suggestions.

## Researcher experience

The toolkit is installed globally but **activates only in an LRC workspace** (`.litreview/project.yaml`) or when the researcher explicitly starts/invokes Lit Review Construct. Generic literature questions in unrelated folders should not create a project.

After installation, open a dedicated research folder in **Codex Desktop** or **OpenCode** and work conversationally. The local project state is authoritative, so the project can be closed/reopened or moved between supported hosts without relying on old chat history.

The researcher should not need to memorize CLI commands. Internal commands, JSON, IDs, provider logs, and tests are implementation details hidden in normal researcher-facing responses.

## Beta workflow

The production-facing journey is organized around a small number of genuine scholarly checkpoints:

1. **Research Intent** — researcher confirms the topic/question, literature publication period, language(s), and material scope constraints.
2. **Discovery Focus** — broad retrieval + early map are built; researcher chooses/adjusts the scholarly focus or scope.
3. **Research Direction** — after technical narrowing, Research Landscape, lawful OA coverage, and Evidence Mapping, researcher selects/modifies/combines/rejects candidate directions.
4. **Literature Review Blueprint** — AI constructs and quality-checks the argument/evidence architecture; researcher accepts or revises it.
5. **Researcher Handoff** — bounded Working Draft fragments and the researcher-facing paper/reference/Word package are prepared; researcher verifies sources and authors the final review.

Technical work such as deduplication, batching, progressive triage, citation chaining, OA resolution, evidence refresh, consistency checks, claim-strength checks, file packaging, and formatting should proceed automatically between these checkpoints.

### Discovery narrowing

Discovery is for a **narrative review**, not PRISMA/systematic screening. Large corpora remain local and are triaged progressively rather than exhaustively.

After the researcher selects a focus, focused retrieval may be followed by bounded automatic refinement:

**priority triage → citation/reference chaining from strong core seeds → triage graph additions → rebuild narrowing map → reassess saturation**

The beta allows up to three automatic citation-refinement rounds and can stop earlier when marginal graph gain becomes low or drops sharply. A high percentage of untriaged records alone is **not** a reason to refine indefinitely.

The researcher still explicitly decides when discovery is sufficient.

## Researcher-facing project structure

```text
Research_Project/
├── AGENTS.md
├── papers/
│   ├── full_text/       # lawful OA PDFs acquired by the toolkit
│   ├── abstract_only/   # working references without local full text
│   └── user_uploads/    # researcher drop zone; user files are not renamed/moved
├── references/
│   ├── references_used.enw
│   ├── references_used.csv
│   └── references_manifest.md
├── outputs/
│   ├── 01_research_intent.md
│   ├── 02_seed_inventory.md
│   ├── 03_research_landscape.md
│   ├── 04_evidence_map.md
│   ├── 05_research_direction.md
│   ├── 06_literature_review_blueprint.md
│   ├── 06b_literature_review_working_draft.md
│   └── LitReview_Researcher_Handoff.docx
└── .litreview/          # authoritative machine state/cache
```

Researchers should normally work with `papers/`, `references/`, and `outputs/` rather than browsing `.litreview/`.

### Paper naming

Toolkit-acquired PDFs use a stable identifier, preferring DOI. DOI `/` is rendered safely for Windows, for example:

```text
doi_10.1016__j.jbankfin.2024.107123.pdf
```

Fallback identity: OpenAlex ID → Semantic Scholar ID → internal stable paper ID.

Researcher-provided files in `papers/user_uploads/` are not silently renamed, moved, or deleted.

### EndNote handoff

`references/references_used.enw` is generated from **canonical bibliographic records**, not AI-written citation strings. It contains the current working references used by the Blueprint/Working Draft set, not the entire discovery universe. A CSV audit and manifest are generated alongside it.

## Full-text and evidence states

The beta deliberately separates three states:

1. **Full text available** — a local PDF exists.
2. **AI checked against full text** — an evidence record uses `source_basis=full_text`.
3. **Researcher verified** — only after explicit researcher verification.

These are not interchangeable. Downloading a PDF does not verify a claim, and AI checking a PDF does not constitute researcher verification.

OA resolution uses only lawful provider-reported open/public locations (OpenAlex, Semantic Scholar, and optional Unpaywall). It never bypasses paywalls, logins, CAPTCHAs, or institutional access controls.

OA acquisition is a **coverage pass in bounded batches**. A batch size such as 100 is not a product-level cap; the runtime advances past already-resolved records until the retained-literature coverage pass is complete.

## Evidence and Working Draft safety

Titles, abstracts, citation counts, and metadata are discovery evidence, not proof of detailed findings.

Working Draft claim language follows evidence status:

- abstract-only support uses provisional wording such as “suggests” or “reports”;
- `source_basis=full_text` may describe what the checked study reports/finds, subject to study design;
- narrative-review gap claims are bounded to the reviewed corpus unless independently verified;
- researcher verification is never invented.

The runtime performs mechanical claim-strength QA before a Working Draft is shown. Working Draft sections remain bounded fragments with researcher tasks/decisions; proposed empirical design is kept distinct from literature synthesis.

## Installation (Windows-first)

1. Download or clone this repository once.
2. Double-click **`install.bat`**.
3. The installer provisions Python 3.12 through `uv`, installs the global `lrc` runtime, copies canonical skills for Codex/OpenCode, and installs OpenCode wrappers.
4. Open a **dedicated research folder** in Codex Desktop or OpenCode.
5. Explicitly start Lit Review Construct for that folder. Global installation alone does not activate it in unrelated workspaces.

Provider credentials are environmental/global and are never written into a research workspace.

## OpenCode

The installed wrappers include:

```text
/lr
/lr-status
```

`/lr` resumes from authoritative local state. Normal responses are researcher-facing; low-level technical diagnostics are shown only when debugging is explicitly requested.

## Optional AI-use statement

The toolkit can generate an optional AI-use statement from activities actually recorded in the project. It must not claim AI performed tasks that are absent from the activity log. Deterministic metadata/indexing operations remain distinguishable from AI-assisted synthesis/draft fragments.

## Development and beta testing

Automated tests run on Windows and Ubuntu. Beta-specific regressions cover researcher workspace structure, DOI-safe naming, EndNote export, OA coverage cursoring, bounded discovery refinement/saturation, tolerant JSONL loading, natural-language next-step guidance, and Working Draft claim-strength rules.

See **`BETA_READINESS.md`** for beta scope, known limitations, and tester expectations.
