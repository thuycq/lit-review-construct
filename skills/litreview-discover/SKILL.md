---
name: litreview-discover
description: Discover additional literature for an accepted Lit Review Construct Research Intent using OpenAlex. Use when the researcher wants to expand beyond seed papers, find recent or influential studies, explore search concepts, or begin constructing the Research Landscape.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Literature Discovery

Use this skill after the Research Intent has been accepted.

## Product boundary

This is narrative-review discovery support. Do not claim exhaustive retrieval, systematic-review completeness, PRISMA compliance, or formal screening completeness.

## Runtime rules

- Use the globally installed `lrc` runtime.
- Project state is authoritative; do not rely on conversation memory for scope.
- Never store API keys inside the research workspace.
- If `OPENALEX_API_KEY` exists in the environment, the runtime may use it. A key is optional.

## Workflow

1. Run `lrc intent show . --json` and verify the Research Intent is accepted.
2. Inspect the seed inventory and paper metadata if seed literature exists.
3. Design several focused search concepts rather than one giant query. Search concepts should reflect the research topic/question, important constructs, common synonyms, theories, methods, contexts, or terminology visible in seed papers when useful.
4. Explain the search concepts briefly to the researcher when they materially affect scope. Routine wording variations do not require a checkpoint.
5. Execute focused queries using `lrc search openalex . --query "<query>" --limit <n>`.
6. Search results are automatically constrained to the accepted Publication period. Paper-language scope is enforced before import.
7. The runtime records every search under `.litreview/searches/`, imports new metadata into `.litreview/data/papers.jsonl`, and rebuilds duplicate/version relation candidates.
8. Use `lrc search history . --json` when you need to understand what has already been searched.
9. Do not treat every imported result as relevant. Imported OpenAlex records begin as `unresolved`; relevance assessment comes next.
10. Prefer multiple complementary searches that improve recall and conceptual coverage while keeping each query interpretable.

## Search strategy guidance

Useful query families may include:

- direct topic/construct combinations;
- theory terminology;
- established terminology found in anchor or seed papers;
- methodological terminology when methodology is central to the research question;
- context-specific combinations;
- recent-development terminology.

Avoid using citation count as the only definition of importance. Later Research Landscape work should consider relevance, influence, methodological/theoretical importance, recency, network position, and source information where available.

## Evidence discipline

OpenAlex metadata is discovery evidence, not proof of a paper's substantive finding. Do not report findings, limitations, or causal claims unless they are supported by the paper itself or another identified source.

## Context discipline

Use metadata and abstracts first. Do not automatically inject every discovered paper or full PDF into context. Selectively load anchor papers and evidence when later stages require them.
