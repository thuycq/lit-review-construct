# Lit Review Construct

Lit Review Construct is a local-first, AI-assisted toolkit for **constructing the literature behind a research study**.

Its purpose is not merely to search for papers. It helps a researcher move from an initial research idea to a broad literature universe, understand the field before narrowing, organize source-disciplined evidence, reason about defensible research directions, and build a Literature Review Blueprint that the researcher can use to write the final literature review.

The toolkit does **not** generate a complete final literature review for direct submission. The researcher remains responsible for scholarly judgment, relevance decisions, source and citation verification, research-direction selection, interpretation, authorship, and final prose.

## Current development build

`0.1.0.dev10`

Dev10 completes the first end-to-end workflow architecture:

**Research Intent → Seed Literature checkpoint → broad multi-source Discovery → early provisional map → researcher-guided narrowing → Evidence Map → researcher-selected Research Direction → Literature Review Blueprint → researcher handoff → optional activity-grounded AI-use statement.**

## Researcher experience

The researcher should not need to memorize the internal CLI.

After installation, open a research folder in **Codex Desktop** or **OpenCode** and work conversationally. The local `.litreview/` state is authoritative, so a project can be closed, reopened, or moved between the two hosts without relying on the previous chat context.

For an existing project, the host can ask the runtime for the next structural step with:

```text
lrc next . --json
```

The navigator returns the current stage, the specialized skill to use, and whether the workflow must stop for a researcher decision.

Human decisions are deliberately preserved at the important scholarly checkpoints:

- whether existing/seed literature is available;
- whether discovery should continue, focus, change scope, or finish;
- which candidate Research Direction should be selected, modified, combined, or rejected;
- whether the Literature Review Blueprint is accepted.

The runtime must not make those decisions silently.

### Codex Desktop

Use natural language such as:

> Continue my literature review project.

The installed `litreview-workflow` skill resumes from local project state and routes to the appropriate stage-specific skill.

### OpenCode

Dev10 installs thin global wrappers:

```text
/lr
/lr-status
```

`/lr` resumes the project through the same `lrc next` state machine. `/lr-status` reports current status and next action without advancing the workflow.

Both hosts use the same canonical skills and the same local project data. The host adapter does not contain separate research logic.

## Why discovery starts broad

A literature review cannot support a credible gap discussion if the search universe was intentionally reduced to a handful of papers just to fit model context.

Lit Review Construct therefore separates **corpus size** from **AI context size**. A broad topic can produce hundreds or thousands of scholarly records. Those records remain locally indexed while the host model receives bounded task packets.

The first synthesis is deliberately provisional. It shows the researcher what research streams, terminology families, mechanisms, theories, contexts, or methodological clusters appear to exist. The researcher then decides where to broaden or narrow. Stronger gap/direction reasoning is delayed until discovery and evidence organization are substantially developed.

## End-to-end workflow

1. **Research Intent** — define the topic/question, literature publication period, and paper-language scope. Researcher explicitly accepts the interpreted intent.
2. **Seed Literature checkpoint** — ask whether the researcher already has related papers. Existing papers may be indexed from `papers/` or an external read-only folder. `lrc seed accept` acknowledges an inventory without marking those papers relevant; `lrc seed skip` records that none are currently available.
3. **Structured Query Plan** — AI creates interpretable query families such as direct constructs, synonyms, mechanisms, theories, contexts, and methods.
4. **Broad Multi-Source Discovery** — run saved plans across available **OpenAlex, Crossref, and Semantic Scholar** sources and retain normalized local records.
5. **Early Exploratory Map** — analyze a bounded representative sample before deep filtering so the researcher can see provisional streams and candidate focuses.
6. **Researcher checkpoint** — choose `continue`, `focus`, `change_scope`, or eventually `finish` discovery.
7. **Progressive Relevance Triage** — classify bounded title/abstract batches as `relevant`, `background`, `adjacent`, `out_of_scope`, or `unresolved`, with auditable rationale and priority.
8. **Focused Discovery + Citation Chaining** — search chosen streams more deeply and expand references/citations/related works around strong candidates. New records return to the same corpus and triage loop.
9. **Discovery Readiness** — report successful providers/query families, triage coverage, unresolved/untriaged records, checkpoints, focused iterations, and citation graph coverage. Readiness is advisory rather than a fake numeric sufficiency score.
10. **Researcher finishes Discovery** — completion and a coverage snapshot are persisted.
11. **Research Landscape** — construct the current field map from retained triaged literature while carrying forward coverage warnings.
12. **Full-Text Reconciliation + Evidence Map** — selectively attach/inspect important PDFs and organize theories, variables, data, methods, findings, null/heterogeneous evidence, contradictions, limitations, and evidence gaps with explicit provenance.
13. **Research Direction** — AI proposes 2–5 provisional directions with supporting literature, possible gap/novelty, feasibility, difficulty, risks, and verification needs. The researcher must explicitly select/modify/combine/reject.
14. **Literature Review Blueprint** — construct the section/argument/evidence architecture around the researcher-selected direction. Each section states what it must establish, which papers/evidence support or conflict with it, its theoretical/methodological role, unresolved questions, and transition logic.
15. **Researcher Handoff** — the researcher writes the final literature-review prose. The toolkit may continue source verification, citation checks, evidence questions, limited argument-level wording, or checking a researcher draft against the Blueprint.
16. **Optional AI-use statement** — generate short/standard/detailed disclosure variants from activities actually recorded in the project. Unrecorded AI uses are not added.

## The Literature Review Blueprint

The Blueprint is the main construction output, not a disguised final manuscript.

A Blueprint section answers:

> **What must this section establish, using which evidence, and why is it necessary for the selected research direction?**

It can include concise argument notes, anchor/supporting/conflicting paper IDs, evidence IDs, theoretical foundations, methodological context, hypothesis/proposition links, verification priorities, unresolved questions, and transition logic.

It must not become continuous publication-ready prose that can simply be concatenated into a final review.

## AI-use disclosure

The optional disclosure is derived from `.litreview/activity/activity.jsonl` and explicit artifact provenance.

For example, if a project used AI-assisted search planning, relevance triage, landscape synthesis, Evidence Mapping, and Blueprint construction—but never used AI for draft fragments—the statement must not claim AI drafting.

Deterministic operations such as indexing, metadata retrieval, deduplication, and file reconciliation are distinguished from AI-assisted synthesis where the project record supports that distinction.

```text
lrc ai-use summary . --json
lrc ai-use generate . --style short
lrc ai-use generate . --style standard
lrc ai-use generate . --style detailed
```

Policy-specific disclosure wording should be adapted separately to the relevant journal, institution, funder, or course requirements without expanding the underlying recorded AI-use history.

## Context and provenance discipline

A large corpus stays local in structured state. AI receives bounded packets tailored to the current task.

Titles, abstracts, citation counts, and provider metadata are **discovery evidence**, not proof of detailed methods/findings/gaps. Evidence records distinguish source basis and epistemic provenance such as `source_reported`, `ai_synthesis`, `ai_inference`, `methodological_interpretation`, and `researcher_judgment`.

The toolkit must not silently convert association into causality, infer substantive findings from metadata, or declare a definitive research gap merely because a concept is absent from a bounded packet.

## Local project model

Typical research workspace:

```text
Research_Project/
  AGENTS.md
  papers/
  outputs/
    01_research_intent.md
    02_seed_inventory.md
    03_research_landscape.md
    04_evidence_map.md
    05_research_direction.md
    06_literature_review_blueprint.md
    07_ai_use_statement.md
  .litreview/
    project.yaml
    state.json
    data/
      seed_decision.json
      papers.jsonl
      paper_relations.jsonl
      paper_graph.jsonl
      discovery_campaign.json
      discovery_query_plan.json
      discovery_query_plans.jsonl
      triage_runs.jsonl
      landscape.json
      evidence.jsonl
      evidence_map.json
      directions.jsonl
      selected_direction.json
      blueprint.json
      ai_use_statement.json
    searches/
    activity/
      activity.jsonl
    packets/
    cache/
    locks/
```

Conversation history is not the project database.

Local PDFs are never silently moved, renamed, merged, or deleted. Exact duplicate files are hash-detected; scholarly same-work/version relations remain traceable. External paper folders are referenced in place by default.

## Installation

Windows-first workflow:

1. Download or clone this repository once.
2. Double-click `install.bat`.
3. The installer provisions Python 3.12 through `uv`, installs the global `lrc` runtime, copies canonical skills to Codex and OpenCode locations, and installs the OpenCode command wrappers.
4. Open an independent research folder in Codex Desktop or OpenCode.
5. Initialize once with `lrc init .` when creating a new project.

Provider credentials, when needed, are global/environmental and are never stored in the research workspace.

## Useful runtime commands

The host agent normally runs these on behalf of the researcher.

```text
lrc next . --json
lrc status .
lrc intent show .
lrc seed scan .
lrc discover readiness .
lrc fulltext status .
lrc evidence show .
lrc direction show .
lrc blueprint show .
lrc ai-use summary .
```

## Development status

Dev10 includes the first complete workflow architecture from Research Intent through researcher handoff, with a broad multi-source discovery funnel, structured Query Plans, provider resilience, scalable bibliographic candidate blocking, progressive triage, citation graph expansion, per-paper discovery provenance, coverage/readiness snapshots, Research Landscape, full-text reconciliation, provenance-aware Evidence Mapping, researcher-controlled Research Direction, Literature Review Blueprint, whole-project `lrc next` navigation, Codex/OpenCode host adapters, and activity-derived AI-use disclosure.

Automated tests run on Windows and Ubuntu. The discovery funnel includes a synthetic working-capital scenario and large-corpus bibliographic blocking tests; post-discovery Blueprint/handoff behavior is also covered.
