---
name: litreview-discover
description: Run iterative multi-source literature discovery for an accepted Lit Review Construct Research Intent. Use when the researcher wants to build a broad literature universe, triage large result sets, inspect provisional research streams, expand through citation/reference networks, narrow to selected themes, or change the research scope before constructing a defensible Research Landscape.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Iterative Multi-Source Literature Discovery

Use this skill after the Research Intent has been accepted.

## Product boundary

The purpose of this stage is to build and progressively narrow a sufficiently broad literature universe for a narrative review before making strong research-gap claims. Do not claim exhaustive retrieval, systematic-review completeness, PRISMA compliance, or formal screening completeness. Do not write a complete final literature review.

## Runtime rules

- Use the globally installed `lrc` runtime.
- Project state is authoritative; do not rely on conversation memory for scope.
- Never store API credentials inside the research workspace.
- Supported first-version discovery providers are **OpenAlex, Crossref, and Semantic Scholar**.
- Optional provider configuration is global/environmental: `OPENALEX_API_KEY`, `CROSSREF_MAILTO`, and `SEMANTIC_SCHOLAR_API_KEY`.
- Do not create a project-local Python environment.

## Core discovery model

Discovery is an **iterative funnel**, not a one-shot search:

**Broad multi-source retrieval → normalization/deduplication → title/abstract relevance triage → exploratory synthesis → researcher checkpoint → focused retrieval and citation chaining → re-triage → repeated narrowing → researcher finishes discovery → Research Landscape → Evidence Map → Research Direction.**

A broad topic may legitimately produce hundreds or thousands of metadata records. Do not reduce the search universe to a few papers merely to fit model context. The runtime stores the large universe locally and prepares bounded packets for AI analysis.

## 1. Start a campaign and retrieve broadly

1. Run `lrc intent show . --json` and verify the Research Intent is accepted.
2. Inspect seed papers when available. Seed papers can supply terminology but are not automatically relevant.
3. Run `lrc discover start .`.
4. Design several interpretable **query families**, not one giant query. Cover direct constructs, synonyms, established terminology, theories/mechanisms, contexts, and methodological terms when appropriate.
5. For the first broad iteration, normally use all three providers. Example:

   `lrc discover run . -q "working capital firm performance" -q "working capital management profitability" -q "cash conversion cycle firm performance" --max-per-query-provider 300`

The runtime retrieves metadata from OpenAlex, Crossref, and Semantic Scholar, merges strong identifier matches, enriches existing records, preserves unresolved bibliographic relations, and records every provider/query run.

### Broad-retrieval principles

- Prefer recall early. A broad finance topic may produce hundreds or thousands of records.
- Do not treat retrieval rank, citation count, or provider presence as a relevance decision.
- Do not load the entire retrieved universe into model context.
- Keep newly discovered papers unresolved until relevance triage.
- Language metadata can be absent in some providers. Unknown-language records may be retained for later triage rather than silently discarded.
- Provider overlap is useful corroboration but not evidence of substantive relevance.

## 2. Triage a large corpus in bounded batches

After broad retrieval, progressively classify title/abstract relevance rather than jumping straight to a Research Landscape.

1. Run `lrc discover prepare-triage . --batch-size 100 --json`.
2. Read `.litreview/packets/triage.json`.
3. Classify **every paper in the packet** using only the supplied title/abstract/metadata:
   - `relevant` — directly useful to the current focal relationship/question;
   - `background` — useful framing/theory/context but not directly focal;
   - `adjacent` — nearby work that may reveal an alternative direction or mechanism;
   - `out_of_scope` — clearly outside the current intent/focus;
   - `unresolved` — insufficient title/abstract information to classify confidently.
4. Assign a priority: `core_candidate`, `high`, `medium`, or `low`.
5. Give a short auditable rationale and optional stream tags/key terms.
6. Save the batch with:

   `lrc discover save-triage . --input .litreview/packets/triage_submission.json`

7. Check progress with `lrc discover triage-status .`.
8. Repeat `prepare-triage → save-triage` until enough of the current corpus has been classified for a useful narrowing decision.

Triage is not full-text screening. Do not infer detailed findings, methods, causal claims, or definitive gaps from title/abstract triage. `unresolved` is a valid outcome and is preferable to guessing.

## 3. Analyze provisional streams and ask the researcher where to go

Once triage has started, prefer the triage-aware review packet:

`lrc discover prepare-review . --after-triage --json`

Read `.litreview/packets/discovery_review.json` and produce only an **exploratory map**:

- provisional research streams;
- indicative terminology;
- provisional questions;
- candidate focus areas;
- suggested next queries;
- coverage weaknesses/noise;
- whether broader search, focused search, citation expansion, or a scope change is useful.

Save it using:

`lrc discover save-review . --input .litreview/packets/discovery_review_submission.json`

Then **stop and ask the researcher** to choose:

- **continue** — keep broadening the literature universe;
- **focus** — continue discovery around one or more selected streams/focuses;
- **change_scope** — revise the topic/question/scope;
- **finish** — discovery is sufficient for the current narrative-review purpose.

Never choose this action for the researcher.

Examples:

- `lrc discover decide . --action continue`
- `lrc discover decide . --action focus --focus "Nonlinear working-capital optimization"`
- `lrc discover decide . --action change_scope --notes "Shift toward SMEs in emerging markets"`
- `lrc discover decide . --action finish`

## 4. Focused search after researcher selection

When the researcher selects one or more focuses:

1. Use the selected focus and previous `query_suggestions` to build new query families.
2. Run another iteration with `--phase focused`.
3. Continue using multiple providers unless there is a clear provider-specific reason not to.
4. Newly imported papers are untriaged for the current campaign and must enter the same bounded triage loop.
5. Rebuild the triage-aware discovery review and return to the researcher checkpoint.

This loop may repeat several times. The point is to let the literature itself expose plausible directions while the researcher controls narrowing.

## 5. Citation/reference/related-paper expansion

Keyword/concept search and graph expansion are complementary. Once good relevant/core candidates emerge, use them as seeds for snowballing.

Examples:

- References + citations around automatically selected relevant/core candidates:

  `lrc discover expand . --relation both --max-per-seed-provider 100`

- Expand around explicit project paper IDs:

  `lrc discover expand . --paper-id <id1> --paper-id <id2> --relation both`

- OpenAlex related-work expansion:

  `lrc discover expand . --paper-id <id> --relation related --provider openalex`

Graph expansion uses OpenAlex and Semantic Scholar for references/citations in v0.1. Crossref remains a multi-source metadata/search provider rather than the primary citation-graph backend.

Rules:

- Normally use a small seed set (up to 10 relevant/core candidates; hard cap 20 per iteration).
- Do not snowball from every retrieved paper.
- Graph-discovered papers return to the same deduplication and triage funnel.
- `paper_graph.jsonl` records source paper → target paper → relation → provider for traceability.
- Citation count is not relevance. Citation chaining is not a substitute for concept search.

## 6. Discovery sufficiency

There is **no universal paper-count threshold**. A niche topic and a broad topic require different corpus sizes. The final sufficiency decision belongs to the researcher.

For a defensible later gap claim, prefer evidence that discovery has:

- used multiple query families;
- used multiple scholarly providers;
- triaged a meaningful proportion of the retrieved universe;
- gone through researcher review checkpoints;
- explored important provisional streams;
- used focused follow-up searches where needed;
- used citation/reference expansion around strong candidate papers where useful;
- later verified important claims against fuller source evidence.

Use `lrc discover status .` and `lrc discover triage-status .` to inspect campaign and filtering progress.

Only after the researcher explicitly finishes the discovery campaign should downstream Research Landscape, Evidence Map, and Research Direction be treated as final-current rather than provisional/test artifacts.

## 7. Research Landscape after discovery

After discovery is finished, construct/refresh the Research Landscape from the retained corpus. The Landscape should identify anchors and meaningful streams without pretending that every retrieved record was deeply read.

The later Evidence Map should preferentially use papers that survived relevance triage and are important to the researcher-selected focus. Full-text verification is still required before strong gap/novelty claims.

## Evidence discipline

Provider metadata and abstracts are **discovery evidence**, not proof of detailed substantive findings. Do not infer causal results, precise methods, limitations, or research gaps from titles/metadata. Preserve provenance and defer detailed verification to Evidence Mapping/full text.

## Context discipline

The large discovery universe stays local in `.litreview/data/papers.jsonl`. AI receives bounded packets. Use title/abstract data for broad orientation and triage, then selectively load core/full-text papers when the task genuinely requires them.
