---
name: litreview-discover
description: Run iterative multi-source literature discovery for an accepted Lit Review Construct Research Intent. Use when the researcher wants to build a broad literature universe, inspect provisional research streams, decide whether to continue collecting, narrow to selected themes, or change the research scope before constructing a defensible Research Landscape.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Iterative Multi-Source Literature Discovery

Use this skill after the Research Intent has been accepted.

## Product boundary

The purpose of this stage is to build a sufficiently broad literature universe for a narrative review before making strong research-gap claims. Do not claim exhaustive retrieval, systematic-review completeness, PRISMA compliance, or formal screening completeness. Do not write a complete final literature review.

## Runtime rules

- Use the globally installed `lrc` runtime.
- Project state is authoritative; do not rely on conversation memory for scope.
- Never store API credentials inside the research workspace.
- Supported first-version discovery providers are **OpenAlex, Crossref, and Semantic Scholar**.
- Optional provider configuration is global/environmental: `OPENALEX_API_KEY`, `CROSSREF_MAILTO`, and `SEMANTIC_SCHOLAR_API_KEY`.
- Do not create a project-local Python environment.

## Core discovery model

Discovery is an **iterative funnel**, not a one-shot search:

**Broad retrieval → normalization/deduplication → exploratory synthesis → researcher checkpoint → broader/focused retrieval → repeated filtering → final discovery acceptance → Research Landscape → Evidence Map → Research Direction.**

A broad topic may legitimately produce hundreds or thousands of metadata records. Do not reduce the search universe to a few papers merely to fit model context. The runtime stores the large universe locally and prepares bounded representative packets for AI analysis.

## Starting a campaign

1. Run `lrc intent show . --json` and verify the Research Intent is accepted.
2. Inspect seed papers when available. Seed papers can supply terminology but are not automatically relevant.
3. Run `lrc discover start .`.
4. Design several interpretable **query families**, not one giant query. Cover direct constructs, synonyms, established terminology, theories/mechanisms, contexts, and methodological terms when appropriate.
5. For the first broad iteration, normally use all three providers. Example:

   `lrc discover run . -q "working capital firm performance" -q "working capital management profitability" -q "cash conversion cycle firm performance" --max-per-query-provider 300`

The runtime retrieves metadata from OpenAlex, Crossref, and Semantic Scholar, merges strong identifier matches, enriches existing records, preserves unresolved bibliographic relations, and records every provider/query run.

## Broad retrieval principles

- Prefer recall early. A broad finance topic may produce hundreds or thousands of records.
- Do not treat retrieval rank, citation count, or provider presence as a relevance decision.
- Do not load the entire retrieved universe into model context.
- Keep papers `unresolved` until later relevance triage.
- Language metadata can be absent in some providers. Unknown-language records may be retained for later triage rather than silently discarded.
- Provider overlap is useful corroboration but not evidence of substantive relevance.

## Exploratory review checkpoint

After one or more broad iterations:

1. Run `lrc discover prepare-review . --json`.
2. Read `.litreview/packets/discovery_review.json`.
3. Analyze the bounded representative packet and the campaign-level coverage summary.
4. Produce only an **exploratory map**:
   - provisional research streams;
   - indicative terminology;
   - provisional questions;
   - candidate focus areas;
   - suggested next queries;
   - coverage weaknesses/noise;
   - whether another discovery iteration is useful.
5. Do **not** call these final research gaps or final novelty claims.
6. Save the structured review using the packet schema, for example:

   `lrc discover save-review . --input .litreview/packets/discovery_review_submission.json`

7. Stop and ask the researcher to choose one of four actions:
   - **continue** — keep broadening the literature universe;
   - **focus** — continue discovery around one or more selected streams/focuses;
   - **change_scope** — return to Research Intent and revise the topic/question/scope;
   - **finish** — the researcher judges discovery sufficient for the current narrative-review purpose.

Never choose this action for the researcher.

## Recording the researcher decision

Examples:

- Continue broadly:
  `lrc discover decide . --action continue`

- Focus subsequent discovery:
  `lrc discover decide . --action focus --focus "Nonlinear working-capital optimization"`

- Request a scope change:
  `lrc discover decide . --action change_scope --notes "Shift toward SMEs in emerging markets"`

- Finish discovery for the current narrative review:
  `lrc discover decide . --action finish`

Use `lrc discover status .` to inspect iterations, providers, query-family count, indexed corpus size, checkpoints, selected focuses, and coverage warnings.

## Focused iterations

When the researcher selects one or more focuses:

1. Use the selected focus and the previous review's `query_suggestions` to build new query families.
2. Run another iteration with `--phase focused`.
3. Continue using multiple providers unless there is a clear provider-specific reason not to.
4. Re-run `prepare-review` and present the updated provisional structure.
5. Repeat the researcher checkpoint.

Later focused iterations should add citation/reference/related-paper expansion around important papers. Do not treat citation chaining as a substitute for keyword/concept search; it is a complementary route into the literature network.

## When discovery is sufficient

There is **no universal paper-count threshold**. A niche topic and a broad topic require different corpus sizes. The runtime may warn when only one provider/query family has been used or when the corpus is very small, but the final sufficiency decision belongs to the researcher.

For a defensible gap claim, prefer evidence that discovery has:

- used multiple query families;
- used multiple scholarly providers;
- gone through at least one researcher review checkpoint;
- explored the most important provisional streams;
- used focused follow-up searches where needed;
- later verified important claims against fuller source evidence.

Only after the researcher explicitly finishes the discovery campaign should the toolkit treat downstream Research Landscape, Evidence Map, and Research Direction as final-current rather than provisional/test artifacts.

## Research Landscape after discovery

After discovery is finished, construct/refresh the Research Landscape from the selected and triaged corpus using `lrc landscape prepare`. The Landscape should identify a small set of anchors and meaningful streams without pretending that every retrieved record was deeply read.

## Evidence discipline

Provider metadata and abstracts are **discovery evidence**, not proof of detailed substantive findings. Do not infer causal results, methods, limitations, or research gaps from titles/metadata. Preserve provenance and defer detailed verification to Evidence Mapping/full text.

## Context discipline

The large discovery universe stays local in `.litreview/data/papers.jsonl`. AI receives bounded representative packets. Use metadata/abstracts for broad orientation, then selectively load core/full-text papers when the task genuinely requires them.
