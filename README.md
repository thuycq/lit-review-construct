# Lit Review Construct

Lit Review Construct is a local-first, AI-assisted literature review construction toolkit for researchers.

It helps researchers discover, understand, organize, and construct the literature behind a research project while keeping the researcher responsible for scholarly judgment, source verification, research-direction decisions, authorship, and final prose.

The toolkit does **not** generate a complete final literature review for direct submission.

## Initial product scope

- Windows-first installation and runtime
- Codex Desktop and OpenCode
- Narrative literature-review construction
- Local authoritative project state in `.litreview/`
- Researcher-provided seed literature and external paper folders
- Multi-source scholarly discovery through OpenAlex, Crossref, and Semantic Scholar
- Progressive title/abstract relevance triage for large corpora
- Citation/reference/related-paper expansion around selected core candidates
- Researcher checkpoints for continuing, focusing, changing scope, or finishing discovery
- Source-disciplined Evidence Mapping with explicit epistemic provenance
- Literature Review Blueprint rather than a submission-ready final review
- AI-use statement derived from actual recorded project activity

## Core workflow

1. **Research Intent** — define the topic/question, publication period, and paper-language scope.
2. **Seed Literature** — index papers the researcher already has without assuming they are relevant.
3. **Broad Discovery Campaign** — retrieve a large metadata/abstract universe from multiple scholarly providers and normalize/deduplicate it locally.
4. **Early Exploratory Review** — analyze a bounded representative sample to expose provisional research streams and candidate focus areas before deep filtering.
5. **Researcher Checkpoint** — the researcher chooses to continue broadly, focus on one or more streams, change scope, or finish discovery.
6. **Progressive Relevance Triage** — classify bounded title/abstract batches as relevant, background, adjacent, out of scope, or unresolved; prioritize likely core papers without pretending triage is full-text evidence.
7. **Focused Discovery and Citation Chaining** — run more focused multi-source searches and expand references/citations/related works around strong candidate papers; return new records to the same triage funnel.
8. **Repeat Researcher Checkpoints** — continue narrowing until the researcher judges discovery sufficient for the current narrative-review purpose.
9. **Research Landscape** — after discovery is explicitly finished, construct the current landscape only from retained triaged literature while carrying forward coverage warnings.
10. **Full-Text Reconciliation and Evidence Map** — selectively obtain/attach important local PDFs, map theories/methods/data/findings/limitations/contradictions, and preserve source basis and provenance.
11. **Research Direction** — AI proposes candidate directions; the researcher must explicitly select, modify, combine, or reject them.
12. **Literature Review Blueprint** — construct the section/argument/evidence architecture the researcher can use to write the final review.
13. **Researcher Handoff and AI-Use Statement** — support verification and transparently describe only the AI activities actually recorded in the project.

## Discovery design principles

A broad research topic may produce hundreds or thousands of records. Lit Review Construct does not shrink that universe to a few papers just to fit model context. The large corpus remains in local structured state; the host model receives bounded task packets.

There is no universal paper-count threshold for a narrative review. Search coverage, triage coverage, researcher checkpoints, focused follow-up, citation chaining, and later source verification matter more than an arbitrary number. A missing topic in a small or bounded packet is never treated as proof of a research gap.

Provider failures are recorded rather than silently ignored. A temporary access/rate-limit problem at one scholarly provider should not discard successful results from the other providers.

## Local project model

A research workspace contains researcher-facing files such as `papers/` and `outputs/`, plus hidden machine state under `.litreview/`. Conversation history is not the project database.

Local PDFs are never silently merged or deleted. Exact duplicate files are detected by hash; bibliographic same-work/version relations remain traceable. When a researcher later supplies a PDF for a discovered paper, high-confidence same-DOI records can share the verified local full-text reference without destroying record provenance.

## Development status

Technical Design / implementation v0.1 is under active development. The current vertical slice includes Windows installation, project state, Research Intent, seed-paper indexing, multi-source discovery campaigns, progressive triage, citation graph expansion, post-discovery landscape preparation, full-text reconciliation, Evidence Mapping, and Research Direction checkpoints.
