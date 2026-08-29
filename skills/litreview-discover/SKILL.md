---
name: litreview-discover
description: Run iterative multi-source literature discovery for an accepted Lit Review Construct Research Intent. Use when the researcher wants to build a broad literature universe, inspect provisional research streams early, triage large result sets, expand through citation/reference networks, narrow to selected themes, or change the research scope before constructing a defensible Research Landscape.
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
- Provider configuration is global/environmental: `OPENALEX_API_KEY`, `CROSSREF_MAILTO`, and `SEMANTIC_SCHOLAR_API_KEY`. OpenAlex access policy may require its free API key; if a provider fails, record the warning and continue with successful providers rather than discarding the whole iteration.
- Do not create a project-local Python environment.

## Core discovery model

Discovery is an **iterative researcher-guided funnel**, not a one-shot search:

**Broad multi-source retrieval → early exploratory synthesis → researcher checkpoint → broad/focused choice → bounded relevance triage → focused retrieval and citation chaining → re-triage → repeated researcher checkpoints → researcher finishes discovery → Research Landscape → Evidence Map → Research Direction.**

A broad topic may legitimately produce hundreds or thousands of metadata records. Do not reduce the search universe to a few papers merely to fit model context. The runtime stores the large universe locally and prepares bounded representative packets for AI analysis.

## 1. Start a campaign and retrieve broadly

1. Run `lrc intent show . --json` and verify the Research Intent is accepted.
2. Inspect seed papers when available. Seed papers can supply terminology but are not automatically relevant.
3. Run `lrc discover start .`.
4. Design several interpretable **query families**, not one giant query. Cover direct constructs, synonyms, established terminology, theories/mechanisms, contexts, and methodological terms when appropriate.
5. For the first broad iteration, normally request all three providers. Example:

   `lrc discover run . -q "working capital firm performance" -q "working capital management profitability" -q "cash conversion cycle firm performance" --max-per-query-provider 300`

The runtime retrieves metadata from available providers, merges strong identifier matches, enriches existing records, preserves unresolved bibliographic relations, and records every provider/query run. One provider failure must not erase successful results from the others.

### Broad-retrieval principles

- Prefer recall early. A broad finance topic may produce hundreds or thousands of records.
- Do not treat retrieval rank, citation count, or provider presence as a relevance decision.
- Do not load the entire retrieved universe into model context.
- Keep newly discovered papers unresolved until relevance triage.
- Language metadata can be absent in some providers. Unknown-language records may be retained for later triage rather than silently discarded.
- Provider overlap is useful corroboration but not evidence of substantive relevance.

## 2. Show the researcher an early provisional map before deep filtering

The researcher should not have to wait for hundreds of papers to be triaged before seeing what the broad literature appears to contain.

After the first substantial broad iteration:

1. Run `lrc discover prepare-review . --json` **without** `--after-triage`.
2. Read `.litreview/packets/discovery_review.json`. This is a bounded, diverse representative sample plus campaign-level coverage information; it is not the whole corpus.
3. Produce an early exploratory map containing:
   - provisional research streams;
   - indicative terminology;
   - provisional questions;
   - candidate focus areas;
   - suggested next queries;
   - obvious coverage weaknesses/noise;
   - whether more broad retrieval, focused retrieval, or early triage would be useful.
4. Do not call any stream a final gap or novelty claim.
5. Save the structured review:

   `lrc discover save-review . --input .litreview/packets/discovery_review_submission.json`

6. **Stop and ask the researcher** to choose:
   - **continue** — broaden the universe further before narrowing;
   - **focus** — prioritize one or more promising streams/focuses for the next search and triage rounds;
   - **change_scope** — revise the topic/question/scope based on what the literature revealed;
   - **finish** — only when the researcher judges discovery genuinely sufficient for this narrative-review purpose.

The AI may recommend an action, but never records the decision until the researcher explicitly chooses.

Examples:

- `lrc discover decide . --action continue`
- `lrc discover decide . --action focus --focus "Nonlinear working-capital optimization"`
- `lrc discover decide . --action change_scope --notes "Shift toward SMEs in emerging markets"`
- `lrc discover decide . --action finish`

For broad topics, an early `finish` after one small iteration should be discouraged with a coverage warning, not silently accepted as evidence of a definitive gap.

## 3. Progressively triage the corpus in bounded batches

After the initial map—and especially after the researcher chooses a focus—classify title/abstract relevance progressively instead of loading the whole corpus into model context.

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
6. Save the batch:

   `lrc discover save-triage . --input .litreview/packets/triage_submission.json`

7. Check progress with `lrc discover triage-status .`.
8. Repeat in bounded batches. It is not necessary to classify every paper before every researcher checkpoint; classify enough of the current universe to make the next narrowing decision responsibly.

Triage is not full-text screening. Do not infer detailed findings, methods, causal claims, or definitive gaps from title/abstract triage. `unresolved` is a valid outcome and is preferable to guessing.

## 4. Re-analyze after triage and return to the researcher

Once meaningful triage has occurred, use the triage-aware review packet:

`lrc discover prepare-review . --after-triage --json`

The review should emphasize retained papers while still reporting how much of the corpus remains untriaged or unresolved. Produce:

- updated provisional streams;
- what appears central vs background vs adjacent;
- candidate focus areas;
- concrete next-query suggestions;
- whether graph expansion is now useful;
- coverage weaknesses and uncertainty;
- recommended next action.

Save with `lrc discover save-review ...`, then stop for the same researcher decision: **continue / focus / change_scope / finish**.

This checkpoint can recur many times. The purpose is for the literature to reveal possible directions while the researcher controls where the funnel narrows.

## 5. Focused search after researcher selection

When the researcher selects one or more focuses:

1. Use the selected focus and previous `query_suggestions` to build new query families.
2. Run another iteration with `--phase focused`.
3. Continue requesting multiple providers unless there is a clear provider-specific reason not to.
4. Newly imported papers are untriaged for the current campaign and must enter the same bounded triage loop.
5. Rebuild the triage-aware discovery review and return to the researcher checkpoint.

The researcher may later broaden again, change focus, combine streams, or request a scope change. Do not force a one-way funnel.

## 6. Citation/reference/related-paper expansion

Keyword/concept search and graph expansion are complementary. Once strong relevant/core candidates emerge, use them as seeds for snowballing.

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
- `.litreview/data/paper_graph.jsonl` records source paper → target paper → relation → provider for traceability.
- Citation count is not relevance. Citation chaining is not a substitute for concept search.

## 7. Discovery sufficiency

There is **no universal paper-count threshold**. A niche topic and a broad topic require different corpus sizes. The final sufficiency decision belongs to the researcher.

For a defensible later gap claim, prefer evidence that discovery has:

- used multiple query families;
- used multiple scholarly providers or explicitly recorded provider-access failures;
- triaged a meaningful proportion of the retrieved universe;
- gone through multiple researcher checkpoints when the topic is broad;
- explored important provisional streams;
- used focused follow-up searches where needed;
- used citation/reference expansion around strong candidate papers where useful;
- later verified important claims against fuller source evidence.

Use `lrc discover status .` and `lrc discover triage-status .` to inspect campaign and filtering progress.

Only after the researcher explicitly finishes the discovery campaign should downstream Research Landscape, Evidence Map, and Research Direction be treated as final-current rather than provisional/test artifacts.

## 8. Build the current Research Landscape only after discovery is finished

After the researcher explicitly chooses **finish**:

1. Run `lrc discover status . --json` and verify `status` is `complete`.
2. Run:

   `lrc discover prepare-landscape . --json`

   This is the required post-discovery landscape packet. Do **not** fall back to an old pre-campaign packet merely because one exists.
3. Read `.litreview/packets/landscape.json`.
4. The packet contains only the bounded **retained triaged corpus** (`relevant`, `background`, `adjacent`) selected from the completed campaign. `out_of_scope` papers are excluded; unresolved/untriaged records are reported as coverage warnings rather than silently treated as evidence.
5. Synthesize anchors, research streams, debates, methodological clusters, recent developments, and unresolved questions using the packet schema.
6. Preserve all `paper_id` references and carry discovery coverage warnings into `limitations`.
7. Save the structured submission:

   `lrc landscape save . --input .litreview/packets/landscape_submission.json`

The Research Landscape is a structured map of retained literature, not a claim that every retrieved record was deeply read. It still must not assert a definitive research gap solely because something is absent from the bounded packet.

The legacy `lrc landscape prepare` path is not valid once an iterative discovery campaign exists because it does not apply the campaign's triage/narrowing state.

## 9. Continue to Evidence Mapping

After the post-discovery Research Landscape is saved, construct/refresh the Evidence Map. Prefer core/anchor/relevant papers and selectively obtain fuller source text where detailed claims, contradictions, theories, methods, limitations, or candidate gaps require verification.

Research Direction remains downstream of both the **researcher-finished discovery campaign** and a refreshed Evidence Map. Do not bypass these gates.

## Evidence discipline

Provider metadata and abstracts are **discovery evidence**, not proof of detailed substantive findings. Do not infer causal results, precise methods, limitations, or research gaps from titles/metadata. Preserve provenance and defer detailed verification to Evidence Mapping/full text.

## Context discipline

The large discovery universe stays local in `.litreview/data/papers.jsonl`. AI receives bounded packets. Use title/abstract data for broad orientation and triage, then selectively load core/full-text papers when the task genuinely requires them.
