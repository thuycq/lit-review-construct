---
name: litreview-discover
description: Run iterative multi-source literature discovery for an accepted Lit Review Construct Research Intent. Use when the researcher wants to build a broad literature universe, inspect provisional research streams early, narrow toward selected themes, expand through citation/reference networks, or change scope before constructing a defensible Research Landscape.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Iterative Multi-Source Literature Discovery

Use this skill after the Research Intent has been accepted.

## Product boundary

The purpose of discovery is to build and progressively narrow a sufficiently broad literature universe for a narrative review before making strong research-gap claims. Do not claim exhaustive retrieval, systematic-review completeness, PRISMA compliance, or formal screening completeness. Do not write a complete final literature review.

## Runtime rules

- Use the globally installed `lrc` runtime.
- Treat `.litreview/` as authoritative project state; do not rely on conversation history as the project database.
- Supported first-version discovery providers are **OpenAlex, Crossref, and Semantic Scholar**.
- Provider configuration is global/environmental: `OPENALEX_API_KEY`, `CROSSREF_MAILTO`, and `SEMANTIC_SCHOLAR_API_KEY`.
- If one provider fails or is rate-limited, keep successful provider results and record the failure rather than discarding the whole iteration.
- Never store API credentials inside the research workspace.
- Do not create a project-local Python environment.

## Core discovery model

Discovery is an **iterative researcher-guided funnel**, not a one-shot search:

**Research Intent → structured Query Plan → broad multi-source retrieval → early exploratory synthesis → researcher checkpoint → continue/focus/change scope → bounded triage → focused Query Plan → focused retrieval + citation chaining → re-triage → repeated researcher checkpoints → researcher finishes discovery → Research Landscape → Evidence Map → Research Direction.**

A broad topic may legitimately produce hundreds or thousands of metadata records. Do not reduce the search universe to a few papers merely to fit model context. The runtime stores the large universe locally and prepares bounded packets for AI analysis.

## 1. Start discovery and create a broad Query Plan

1. Run `lrc intent show . --json` and verify the Research Intent is accepted.
2. Inspect seed papers when available. Seed papers can contribute terminology and known anchors, but are not automatically relevant.
3. Run `lrc discover start .`.
4. Run:

   `lrc discover prepare-plan . --phase broad --json`

5. Read `.litreview/packets/query_plan.json`.
6. Produce a structured plan with several interpretable query families rather than one giant opaque query. Normally include:
   - at least one direct-construct query;
   - at least one terminology/synonym query;
   - mechanism, theory, context, or method families when they materially improve coverage.
7. Give each family a name, role, rationale, concepts, and priority. Do not design queries around citation count.
8. Save the plan:

   `lrc discover save-plan . --input .litreview/packets/query_plan_submission.json`

9. Execute it:

   `lrc discover run-plan . --max-per-query-provider 300`

`run-plan` normally requests all three scholarly providers. It records the plan, provider results, provider failures, and the discovery iteration. The saved plan makes search decisions auditable and reproducible.

### Broad-retrieval principles

- Prefer recall early. A broad finance topic may produce hundreds or thousands of records.
- Do not treat retrieval rank, citation count, or provider presence as a relevance decision.
- Do not load the entire retrieved universe into model context.
- Keep newly discovered papers unresolved until relevance triage.
- Unknown provider language metadata may be retained for later triage rather than silently discarded.
- Provider overlap is useful corroboration but not evidence of substantive relevance.
- A query plan does not imply exhaustive retrieval.

## 2. Show the researcher an early provisional map before deep filtering

The researcher should not have to wait for hundreds of papers to be triaged before seeing what the broad literature appears to contain.

After the first substantial broad iteration:

1. Run `lrc discover prepare-review . --json` **without** `--after-triage`.
2. Read `.litreview/packets/discovery_review.json`. It contains a bounded representative sample plus campaign-level coverage information; it is not the whole corpus.
3. Produce only an exploratory map:
   - provisional research streams;
   - indicative terminology;
   - provisional questions;
   - candidate focus areas;
   - suggested next queries;
   - obvious coverage weaknesses/noise;
   - whether more broad retrieval, focused retrieval, or triage appears useful.
4. Do not call any stream a final gap or novelty claim.
5. Save the review:

   `lrc discover save-review . --input .litreview/packets/discovery_review_submission.json`

6. **Stop and ask the researcher** to choose:
   - **continue** — broaden the literature universe further;
   - **focus** — prioritize one or more promising streams/focuses;
   - **change_scope** — revise the topic/question/scope based on what the literature revealed;
   - **finish** — only when the researcher judges discovery genuinely sufficient for the current narrative-review purpose.

The AI may recommend an action but must not record the decision until the researcher explicitly chooses.

Examples:

- `lrc discover decide . --action continue`
- `lrc discover decide . --action focus --focus "Nonlinear working-capital optimization"`
- `lrc discover decide . --action change_scope --notes "Shift toward SMEs in emerging markets"`
- `lrc discover decide . --action finish`

For a broad topic, an early `finish` after one small iteration should be discouraged with coverage warnings rather than treated as evidence of a definitive gap.

## 3. If the researcher continues broadly

When the researcher chooses **continue**:

1. Prepare another broad Query Plan with `lrc discover prepare-plan . --phase broad --json`.
2. Inspect `previous_query_families` in the packet.
3. Design complementary queries that improve terminology, theory/mechanism, context, or method coverage instead of mechanically repeating the first plan.
4. Save and run the plan.
5. Rebuild the early discovery review.
6. Stop for another researcher checkpoint.

Several broad iterations are acceptable when the topic is large or terminology is fragmented.

## 4. If the researcher selects a focus

When the researcher chooses **focus**:

1. Run:

   `lrc discover prepare-plan . --phase focused --json`

2. The packet must contain the researcher-selected focus and previous query history.
3. Build focused follow-up queries around the chosen stream(s), but include adjacent terminology where useful to test whether the apparent focus is too narrow.
4. Save the focused plan and run it with `lrc discover run-plan .`.
5. Newly discovered papers return to the same corpus and must later enter the triage loop.

The researcher may later broaden again, combine streams, choose a different focus, or request a scope change. Do not force a one-way funnel.

## 5. Progressively triage the corpus in bounded batches

After the researcher has seen the initial broad map—and especially after a focus has been selected—classify title/abstract relevance progressively rather than loading the entire corpus into context.

1. Run `lrc discover prepare-triage . --batch-size 100 --json`.
2. Read `.litreview/packets/triage.json`.
3. Classify **every paper in that packet** using only supplied title/abstract/metadata:
   - `relevant` — directly useful to the current focal relationship/question;
   - `background` — useful framing/theory/context but not directly focal;
   - `adjacent` — nearby work that may reveal an alternative direction or mechanism;
   - `out_of_scope` — clearly outside the current intent/focus;
   - `unresolved` — insufficient title/abstract information to classify confidently.
4. Assign priority: `core_candidate`, `high`, `medium`, or `low`.
5. Give a short auditable rationale plus optional stream tags/key terms.
6. Save the batch:

   `lrc discover save-triage . --input .litreview/packets/triage_submission.json`

7. Check progress with `lrc discover triage-status .`.
8. Repeat in bounded batches. It is not necessary to classify every paper before every checkpoint; classify enough of the current universe to make the next narrowing decision responsibly.

Triage is not full-text screening. Do not infer detailed findings, methods, causal claims, or definitive gaps from title/abstract triage. `unresolved` is a valid outcome and is preferable to guessing.

## 6. Re-analyze after triage and return to the researcher

Once meaningful triage has occurred, use:

`lrc discover prepare-review . --after-triage --json`

The triage-aware review should emphasize retained papers while still reporting how much of the corpus remains untriaged or unresolved. Produce:

- updated provisional streams;
- what appears central vs background vs adjacent;
- candidate focus areas;
- concrete next-query suggestions;
- whether graph expansion is now useful;
- coverage weaknesses and uncertainty;
- recommended next action.

Save with `lrc discover save-review ...`, then stop for the same researcher decision: **continue / focus / change_scope / finish**.

This checkpoint can recur many times. The literature should expose possible directions while the researcher controls where the funnel narrows.

## 7. Citation/reference/related-paper expansion

Keyword/concept search and graph expansion are complementary. Once strong relevant/core candidates emerge, use them as seeds for snowballing.

Examples:

- References + citations around automatically selected relevant/core candidates:

  `lrc discover expand . --relation both --max-per-seed-provider 100`

- Expand around explicit paper IDs:

  `lrc discover expand . --paper-id <id1> --paper-id <id2> --relation both`

- OpenAlex related-work expansion:

  `lrc discover expand . --paper-id <id> --relation related --provider openalex`

Rules:

- Normally use a small seed set; hard cap is 20 seeds per graph-expansion iteration.
- Do not snowball from every retrieved paper.
- Graph-discovered papers return to the same deduplication and triage funnel.
- `.litreview/data/paper_graph.jsonl` records source paper → target paper → relation → provider.
- Citation count is not relevance.
- Citation chaining is not a substitute for concept search.
- In v0.1, OpenAlex and Semantic Scholar are graph backends; Crossref remains a metadata/search source.

## 8. Discovery sufficiency

There is **no universal paper-count threshold**. A niche topic and a broad topic require different corpus sizes. The final sufficiency decision belongs to the researcher.

For a defensible later gap claim, prefer evidence that discovery has:

- used multiple structured query families;
- used multiple scholarly providers or explicitly recorded provider-access failures;
- shown the researcher an early broad map before narrowing;
- triaged a meaningful proportion of the retrieved universe;
- gone through multiple researcher checkpoints when the topic is broad;
- explored important provisional streams;
- used focused follow-up searches where needed;
- used citation/reference expansion around strong candidate papers where useful;
- later verified important claims against fuller source evidence.

Use `lrc discover status .` and `lrc discover triage-status .` to inspect campaign and filtering progress.

Only after the researcher explicitly chooses **finish** should downstream Research Landscape, Evidence Map, and Research Direction be treated as final-current.

## 9. Build the current Research Landscape only after discovery is finished

After the researcher explicitly finishes discovery:

1. Verify `lrc discover status . --json` reports `complete`.
2. Run:

   `lrc discover prepare-landscape . --json`

3. Read `.litreview/packets/landscape.json`.
4. The packet contains only the bounded retained triaged corpus (`relevant`, `background`, `adjacent`). `out_of_scope` papers are excluded. Unresolved/untriaged records remain visible as coverage warnings rather than silently becoming evidence.
5. Synthesize anchors, streams, debates, methodological clusters, recent developments, and unresolved questions.
6. Preserve `paper_id` references and discovery limitations.
7. Save:

   `lrc landscape save . --input .litreview/packets/landscape_submission.json`

The final Research Landscape is a structured map of retained literature, not proof that every retrieved record was deeply read. It still must not assert a definitive research gap solely because something is absent from the bounded packet.

The legacy `lrc landscape prepare` path is not valid once an iterative discovery campaign exists because it does not apply campaign triage/narrowing state.

## 10. Continue to Evidence Mapping

After the post-discovery Research Landscape is saved, construct or refresh the Evidence Map. Prefer core/anchor/relevant papers and selectively obtain fuller source text where detailed claims, contradictions, theories, methods, limitations, or candidate gaps require verification.

Use `lrc fulltext reconcile .` after adding local PDFs so metadata-only discovered records can be linked to their local full text without destroying provenance. Use `lrc fulltext status .` to identify priority retained papers still lacking full text.

Research Direction remains downstream of both the **researcher-finished discovery campaign** and a refreshed Evidence Map. Do not bypass these gates.

## Evidence discipline

Provider metadata and abstracts are **discovery evidence**, not proof of detailed substantive findings. Do not infer causal results, precise methods, limitations, or research gaps from titles/metadata. Preserve provenance and defer detailed verification to Evidence Mapping/full text.

## Context discipline

The large discovery universe stays local in `.litreview/data/papers.jsonl`. AI receives bounded packets. Use title/abstract data for broad orientation and triage, then selectively load core/full-text papers only when the task genuinely requires them.
