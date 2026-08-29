---
name: litreview-discover
description: Run iterative multi-source literature discovery for an accepted Lit Review Construct Research Intent. Use when the researcher wants to build a broad literature universe, inspect provisional research streams early, narrow toward selected themes, expand through citation/reference networks, resume a prior discovery campaign, or change scope before constructing a defensible Research Landscape.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Iterative Multi-Source Literature Discovery

Use this skill after the Research Intent has been accepted.

## Product boundary

Discovery exists to build and progressively narrow a sufficiently broad literature universe for a **narrative review** before strong research-gap claims are considered. Do not claim exhaustive retrieval, systematic-review completeness, PRISMA compliance, or formal screening completeness. Do not write a complete final literature review.

The researcher controls scope and narrowing. AI may recommend actions, streams, and search directions, but it must not silently choose a research focus or decide that discovery is sufficient.

## Runtime and resume rules

- Use the globally installed `lrc` runtime.
- Treat `.litreview/` as authoritative project state; conversation history is not the project database.
- At the beginning of a discovery turn, especially after reopening a project or switching hosts, run:

  `lrc discover next . --json`

  Follow the returned structural action. If `human_checkpoint_required` is true, stop and ask the researcher rather than continuing automatically.
- Use `lrc discover status . --json` for campaign status and successful provider/query coverage.
- Supported first-version discovery providers are **OpenAlex, Crossref, and Semantic Scholar**.
- Provider configuration is global/environmental: `OPENALEX_API_KEY`, `CROSSREF_MAILTO`, and `SEMANTIC_SCHOLAR_API_KEY`.
- If one provider fails or is rate-limited, preserve successful results from other providers and record the failure.
- Never store API credentials inside the research workspace.
- Do not create a project-local Python environment.

## Core discovery model

Discovery is an **iterative researcher-guided funnel**:

**Research Intent → structured Query Plan → broad multi-source retrieval → early provisional map → researcher checkpoint → continue/focus/change scope → bounded triage → focused Query Plan → focused retrieval + citation chaining → re-triage → repeated researcher checkpoints → Discovery Readiness → researcher finishes discovery → Research Landscape → Evidence Map → Research Direction.**

A broad topic may legitimately produce hundreds or thousands of records. Do not shrink the literature universe merely to fit model context. The large corpus remains local; the host model receives bounded packets.

## 1. Start discovery and plan broad retrieval

If `lrc discover next . --json` indicates discovery has not started:

1. Run `lrc discover start .`.
2. Run `lrc discover prepare-plan . --phase broad --json`.
3. Read `.litreview/packets/query_plan.json`.
4. Construct several interpretable query families rather than one opaque giant query. Normally cover:
   - the direct focal constructs/relationship;
   - terminology or synonym variants;
   - mechanisms, theories, contexts, or methods when they materially improve recall.
5. Give every query family a name, role, query, rationale, concepts, and priority.
6. Save the structured plan:

   `lrc discover save-plan . --input .litreview/packets/query_plan_submission.json`

7. Execute the saved plan:

   `lrc discover run-plan . --max-per-query-provider 300`

The saved Query Plan makes search logic auditable. It does **not** imply exhaustive retrieval.

### Broad-retrieval principles

- Prefer recall early.
- Do not use citation count as a relevance decision.
- Do not load the whole corpus into model context.
- Keep newly discovered papers unresolved until relevance triage.
- Unknown provider-language metadata may remain for later triage rather than being silently discarded.
- Provider overlap is useful audit information, not proof of substantive relevance.
- Each paper may retain `discovery_hits` identifying query, provider, phase, iteration, and retrieval time. Multiple hits are not a relevance score.

## 2. Show an early provisional map before deep filtering

After a substantial broad retrieval, the researcher should see what the field appears to contain **before** being forced through hundreds of triage decisions.

When `lrc discover next . --json` returns `prepare_early_review`:

1. Run `lrc discover prepare-review . --json` without `--after-triage`.
2. Read `.litreview/packets/discovery_review.json`.
3. Produce only an exploratory map:
   - provisional research streams;
   - indicative terminology;
   - provisional questions;
   - candidate focus areas;
   - suggested next queries;
   - visible noise/coverage weaknesses;
   - a recommendation to continue broadly, focus, change scope, or begin deeper filtering.
4. Do not call provisional streams final gaps or novelty claims.
5. Save the review:

   `lrc discover save-review . --input .litreview/packets/discovery_review_submission.json`

The campaign then becomes `awaiting_researcher`.

## 3. Human checkpoint: never bypass it

When `lrc discover next . --json` returns `researcher_decision_required`, stop and present the literature map plus relevant coverage warnings. Ask the researcher to choose:

- **continue** — broaden the literature universe;
- **focus** — prioritize one or more selected streams/focuses;
- **change_scope** — revise the topic/question/scope;
- **finish** — only if the researcher judges discovery sufficient for the current narrative-review purpose.

Record only the researcher's explicit choice:

- `lrc discover decide . --action continue`
- `lrc discover decide . --action focus --focus "<researcher-selected focus>"`
- `lrc discover decide . --action change_scope --notes "<researcher request>"`
- `lrc discover decide . --action finish`

Before presenting `finish` as a sensible option, run `lrc discover readiness . --json` and explain material warnings. Readiness is advisory; it is not a numeric sufficiency score and does not replace researcher judgment.

## 4. Continue broad discovery

If the researcher chooses `continue`, `lrc discover next . --json` will route the project back to a broad Query Plan. Use previous query history in the planning packet to build **complementary** terminology, theory/mechanism, context, or method families rather than mechanically repeating prior searches.

Save and execute the new plan, rebuild the early map, and return to another researcher checkpoint. Several broad rounds are valid for large or fragmented topics.

## 5. Focused discovery after researcher selection

If the researcher chooses `focus`:

1. Run `lrc discover prepare-plan . --phase focused --json` when the navigator requests it.
2. The packet contains researcher-selected focus areas and previous query history.
3. Build focused follow-up queries around those areas while retaining useful adjacent terminology that could challenge an overly narrow interpretation.
4. Save and run the focused plan.
5. Newly retrieved papers enter the same corpus and triage funnel.

A focus decision is revisable. The researcher may later broaden again, combine streams, choose another focus, or change scope.

## 6. Progressive relevance triage

When `lrc discover next . --json` returns `continue_triage`, work in bounded batches:

1. Run `lrc discover prepare-triage . --batch-size 100 --json`.
2. Read `.litreview/packets/triage.json`.
3. Classify every supplied paper using title/abstract/metadata only:
   - `relevant` — directly useful to the focal question/relationship;
   - `background` — useful framing/theory/context;
   - `adjacent` — nearby work that may expose an alternative mechanism/direction;
   - `out_of_scope` — clearly outside current intent/focus;
   - `unresolved` — information is insufficient for a confident classification.
4. Assign priority: `core_candidate`, `high`, `medium`, or `low`.
5. Give a short auditable rationale and optional stream/key-term tags.
6. Save the batch:

   `lrc discover save-triage . --input .litreview/packets/triage_submission.json`

7. Continue according to `lrc discover next . --json`.

Triage is **not** full-text screening. Do not infer detailed methods, causal findings, limitations, or definitive gaps from title/abstract triage. `unresolved` is preferable to guessing.

## 7. Re-map after filtering

When the navigator returns `prepare_narrowing_review`:

1. Run `lrc discover prepare-review . --after-triage --json`.
2. Emphasize retained papers while reporting remaining untriaged/unresolved coverage.
3. Update provisional streams, central/background/adjacent distinctions, candidate focus areas, query suggestions, graph-expansion needs, and uncertainty.
4. Save the review and return to the researcher checkpoint.

This cycle may repeat many times.

## 8. Citation/reference/related-paper expansion

Keyword/concept search and scholarly-network expansion are complementary. Once strong relevant/core candidates emerge, use a **small** seed set for snowballing.

Examples:

- `lrc discover expand . --relation both --max-per-seed-provider 100`
- `lrc discover expand . --paper-id <id1> --paper-id <id2> --relation both`
- `lrc discover expand . --paper-id <id> --relation related --provider openalex`

Rules:

- Do not snowball from every retrieved paper; the hard seed cap is 20 per iteration.
- Graph-discovered papers return to deduplication and triage.
- `.litreview/data/paper_graph.jsonl` preserves source paper → target paper → relation → provider.
- Citation count is not relevance.
- Citation chaining does not replace concept/keyword search.
- OpenAlex and Semantic Scholar are graph backends in v0.1; Crossref is primarily a metadata/search source.

## 9. Discovery Readiness before finish

Run:

`lrc discover readiness . --json`

The diagnostic reports, among other things:

- providers that actually returned usable results;
- successful query-family count;
- saved Query Plans;
- researcher review checkpoints;
- focused follow-up retrieval;
- triage coverage;
- retained, unresolved, and untriaged records;
- citation graph expansion;
- provider failures;
- coverage strengths and warnings.

Do not convert this into a numeric score or universal sufficiency rule. A niche topic and a broad topic require different coverage. If the researcher chooses `finish`, the toolkit persists the readiness snapshot with the completion decision so downstream gap reasoning cannot silently forget known coverage limitations.

## 10. Final Research Landscape gate

Only after the researcher explicitly finishes discovery should the current Research Landscape be constructed.

When the navigator returns `prepare_final_landscape`:

1. Run `lrc discover prepare-landscape . --json`.
2. Read `.litreview/packets/landscape.json`.
3. Use only the retained triaged corpus (`relevant`, `background`, `adjacent`) represented in the packet.
4. `out_of_scope` papers are excluded; unresolved/untriaged records remain coverage warnings.
5. Identify anchors, meaningful streams, debates, methodological clusters, recent developments, and unresolved questions.
6. Preserve paper IDs, discovery provenance, and limitations.
7. Save the landscape:

   `lrc landscape save . --input .litreview/packets/landscape_submission.json`

Do not infer a definitive research gap solely from absence within the bounded landscape packet. The legacy `lrc landscape prepare` route is invalid once an iterative campaign exists because it does not apply campaign narrowing state.

## 11. Full text and Evidence Mapping

After the post-discovery Research Landscape is saved, continue to Evidence Mapping.

- Prefer core/anchor/relevant papers for deeper verification.
- Use `lrc fulltext reconcile .` after the researcher adds PDFs so metadata-only discovered records can be linked to verified local full text without destroying provenance.
- Use `lrc fulltext status .` to identify priority retained papers still lacking full text.
- Do not upload, move, rename, or delete external local PDFs without explicit authorization.

Research Direction remains downstream of both the researcher-finished discovery campaign and a refreshed Evidence Map.

## Evidence discipline

Provider metadata and abstracts are **discovery evidence**, not proof of detailed substantive findings. Preserve provenance. Do not infer causal results, precise methods, limitations, or research gaps from titles/metadata. Detailed claims belong in Evidence Mapping and selective source verification.

## Context discipline

The large corpus remains local in `.litreview/data/papers.jsonl`. AI receives bounded packets. Use title/abstract data for broad orientation and triage, then selectively load full texts only where the current evidence task requires them.
