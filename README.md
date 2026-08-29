# Lit Review Construct

Lit Review Construct is a local-first, AI-assisted literature review construction toolkit for researchers.

It helps researchers **find enough literature before narrowing**, understand how a research field is structured, organize source-disciplined evidence, explore defensible research directions, and construct a Literature Review Blueprint. The researcher remains responsible for scholarly judgment, source verification, research-direction decisions, authorship, and final prose.

The toolkit does **not** generate a complete final literature review for direct submission.

## Current development build

`0.1.0.dev9`

The dev9 discovery architecture is built around a researcher-guided funnel rather than a small one-shot search:

**Research Intent → Query Plan → broad multi-source retrieval → early provisional map → researcher choice → progressive triage → focused retrieval/citation chaining → repeated researcher checkpoints → discovery completion → Research Landscape → Evidence Map → Research Direction → Literature Review Blueprint.**

## Initial product scope

- Windows-first installation and runtime
- Codex Desktop and OpenCode
- Narrative literature-review construction
- Local authoritative project state in `.litreview/`
- Researcher-provided seed literature and external paper folders
- Multi-source scholarly discovery through **OpenAlex, Crossref, and Semantic Scholar**
- Structured, auditable Query Plans before broad and focused retrieval
- Large local discovery corpora with bounded AI context packets
- Progressive title/abstract relevance triage
- Citation/reference/related-paper expansion around selected core candidates
- Researcher checkpoints for continuing, focusing, changing scope, or finishing discovery
- Per-paper query/provider discovery provenance
- Advisory Discovery Readiness diagnostics rather than arbitrary sufficiency scores
- Source-disciplined Evidence Mapping with explicit epistemic provenance
- Human-reviewed Research Direction selection
- Literature Review Blueprint rather than a submission-ready final review
- AI-use statement derived only from actual recorded project activity

## Why discovery starts broad

A literature review cannot support a credible research-gap discussion if the search universe was deliberately reduced to a handful of papers simply to fit model context.

Lit Review Construct therefore separates **corpus size** from **AI context size**. A broad topic may produce hundreds or thousands of scholarly records. Those records remain in local structured state, while the host model receives bounded packets containing only what is needed for the current task.

The first AI synthesis is deliberately provisional. It shows the researcher what research streams, terminology families, mechanisms, theories, contexts, or methodological clusters appear to exist. The researcher then decides whether to broaden, focus, or change scope. Only later does the toolkit support stronger gap/direction reasoning.

## Core workflow

1. **Research Intent** — define the topic/question, publication period, and paper-language scope.
2. **Seed Literature** — index papers the researcher already has without assuming they are relevant.
3. **Broad Query Plan** — AI proposes several interpretable search families (direct constructs, synonyms, mechanisms, theories, contexts, methods where useful). The plan is saved locally.
4. **Broad Multi-Source Discovery** — execute the saved plan across available scholarly providers and retain a large normalized corpus.
5. **Early Exploratory Review** — analyze a bounded, diverse sample to expose provisional research streams and candidate focus areas before deep filtering.
6. **Researcher Checkpoint** — the researcher chooses to continue broadly, focus on one or more streams, change scope, or eventually finish discovery.
7. **Progressive Relevance Triage** — classify bounded title/abstract batches as `relevant`, `background`, `adjacent`, `out_of_scope`, or `unresolved`; assign priorities without pretending triage is full-text evidence.
8. **Focused Query Plans and Discovery** — after the researcher selects a direction, create focused follow-up queries and search again.
9. **Citation/Reference Expansion** — expand references, citations, and related works around strong candidates; new papers return to the same corpus and triage loop.
10. **Repeated Researcher Checkpoints** — re-map the evolving literature and let the researcher broaden, narrow, combine, or change direction.
11. **Discovery Readiness** — report successful provider/query coverage, saved plans, triage coverage, unresolved papers, checkpoints, focused follow-up, and citation expansion. This is advisory; it is not a numeric sufficiency score.
12. **Researcher Finishes Discovery** — the completion decision and its coverage snapshot are persisted.
13. **Research Landscape** — construct the current landscape only from retained triaged literature while carrying forward coverage limitations.
14. **Full-Text Reconciliation and Evidence Map** — selectively attach/inspect important PDFs and map theories, methods, data, findings, limitations, contradictions, and evidence gaps.
15. **Research Direction** — AI proposes candidate directions; the researcher must explicitly select, modify, combine, or reject them.
16. **Literature Review Blueprint** — construct the section/argument/evidence architecture the researcher can use to write the final review.
17. **Researcher Handoff and AI-Use Statement** — support verification and transparently describe only the AI activities actually recorded in the project.

## Discovery commands

The host agent normally runs these commands on behalf of the researcher; the researcher should not need to memorize them.

```text
lrc discover start .
lrc discover prepare-plan . --phase broad --json
lrc discover save-plan . --input <query-plan.json>
lrc discover run-plan .
lrc discover prepare-review . --json
lrc discover decide . --action continue|focus|change_scope|finish
lrc discover prepare-triage . --batch-size 100 --json
lrc discover save-triage . --input <triage.json>
lrc discover triage-status .
lrc discover expand . --relation both
lrc discover readiness .
lrc discover prepare-landscape . --json
```

A focused researcher choice enables a focused Query Plan:

```text
lrc discover prepare-plan . --phase focused --json
lrc discover run-plan .
```

## Discovery design principles

### No arbitrary paper-count threshold

There is no universal number of papers that makes a narrative review “complete.” A niche topic and a broad finance topic require different coverage. The toolkit therefore records coverage signals and warnings rather than declaring sufficiency from paper count alone.

### Search provenance is part of the paper record

Each discovered paper can retain the query family, provider, phase, iteration, and retrieval time that brought it into the corpus. A paper appearing through several queries or providers may be useful audit information, but **retrieval frequency is not a relevance score**.

### Multi-source retrieval is resilient

A temporary API-key, access, server, or rate-limit problem at one provider should not erase successful results from other providers. Provider failures are recorded alongside successful runs.

### Large-corpus deduplication must scale

Exact duplicate files are detected by hash. Bibliographic duplicate/version detection uses strong identifiers plus conservative candidate blocking instead of all-pairs comparison across the entire corpus. Same-work/version relations remain traceable and are not silently deleted.

### Discovery is not evidence verification

Titles, abstracts, citation counts, and provider metadata are discovery evidence. They are not sufficient grounds for detailed claims about methods, causal findings, limitations, or definitive research gaps. Stronger claims move downstream to Evidence Mapping and selective full-text verification.

## Local project model

A research workspace contains researcher-facing files such as `papers/` and `outputs/`, plus hidden machine state under `.litreview/`. Conversation history is not the project database.

Typical state includes:

```text
.litreview/
  project.yaml
  state.json
  data/
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
  searches/
  activity/
  packets/
  cache/
```

Local PDFs are never silently merged or deleted. When a researcher later supplies a PDF for a metadata-only discovered paper, high-confidence same-work relations can link the verified local full text to the scholarly record without destroying provenance.

## Installation model

The intended Windows workflow is:

1. Download or clone the toolkit repository once.
2. Double-click `install.bat`.
3. The installer provisions the runtime and installs the canonical Lit Review Construct skills for Codex and OpenCode.
4. For each research project, open only that research folder in Codex Desktop or OpenCode.
5. The same `.litreview/` project can be continued in either host without conversion.

The runtime uses Python 3.12 and `uv`. API credentials, when needed by scholarly providers, are global/environmental and must not be stored inside a research project.

## Authorship boundary

Lit Review Construct may provide:

- search assistance;
- research-landscape synthesis;
- evidence organization;
- gap/direction suggestions with explicit uncertainty;
- argument-level notes or limited draft fragments;
- citation/source verification assistance;
- a Literature Review Blueprint.

It must not silently turn those materials into a complete final literature review for direct submission. The researcher writes and approves the final scholarly prose.

## Development status

Technical Design / implementation v0.1 is under active development. Dev9 includes the end-to-end discovery funnel, structured Query Plans, multi-source provider resilience, scalable bibliographic candidate blocking, progressive triage, citation graph expansion, per-paper discovery provenance, Discovery Readiness snapshots, post-discovery Landscape preparation, full-text reconciliation, Evidence Mapping, Research Direction checkpoints, and activity logging for later AI-use disclosure.

The discovery funnel is covered by automated tests on both Windows and Ubuntu, including a synthetic end-to-end working-capital research scenario and large-corpus bibliographic blocking tests.
