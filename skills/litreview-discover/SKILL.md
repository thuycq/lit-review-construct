---
name: litreview-discover
description: Discover additional literature and construct a Research Landscape for an accepted Lit Review Construct Research Intent. Use when the researcher wants to expand beyond seed papers, find recent or influential studies, explore search concepts, identify anchor papers, organize research streams, or synthesize the literature landscape.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Literature Discovery and Research Landscape

Use this skill after the Research Intent has been accepted.

## Product boundary

This is narrative-review discovery support. Do not claim exhaustive retrieval, systematic-review completeness, PRISMA compliance, or formal screening completeness. Do not write a complete final literature review.

## Runtime rules

- Use the globally installed `lrc` runtime.
- Project state is authoritative; do not rely on conversation memory for scope.
- Never store API keys inside the research workspace.
- If `OPENALEX_API_KEY` exists in the environment, the runtime may use it. A key is optional.
- Do not create a project-local Python environment.

## Discovery workflow

1. Run `lrc intent show . --json` and verify the Research Intent is accepted.
2. Inspect the seed inventory and paper metadata if seed literature exists.
3. Design several focused search concepts rather than one giant query. Search concepts should reflect the research topic/question, important constructs, common synonyms, theories, methods, contexts, or terminology visible in seed papers when useful.
4. Explain search concepts briefly only when they materially affect scope. Routine wording variations do not require a checkpoint.
5. Execute focused queries using `lrc search openalex . --query "<query>" --limit <n>`.
6. Search results are automatically constrained to the accepted Publication period. Paper-language scope is enforced before import.
7. The runtime records every search under `.litreview/searches/`, imports new metadata into `.litreview/data/papers.jsonl`, and rebuilds duplicate/version relation candidates.
8. Use `lrc search history . --json` when you need to understand what has already been searched.
9. Do not treat every imported result as relevant. Imported OpenAlex records begin as unresolved literature candidates.
10. Prefer multiple complementary searches that improve conceptual coverage while keeping each query interpretable.

## Research Landscape workflow

After the discovery pool is adequate for an initial narrative landscape:

1. Run `lrc landscape prepare . --json`.
2. Read the generated `.litreview/packets/landscape.json`. Treat this bounded packet as the primary context for landscape synthesis instead of loading the entire corpus.
3. Analyze the packet using multiple signals. Citation count is only one signal. Consider topical relevance to the accepted Research Intent, seed-paper importance, recency, theoretical or methodological role, publication context, and the available abstract/metadata evidence.
4. Select a **small and useful** set of anchor papers rather than labeling every plausible paper as an anchor.
5. Organize the literature into meaningful research streams. Streams should reflect substantive theories, mechanisms, debates, methodological traditions, contexts, or other research structures that help the researcher understand the field.
6. Surface major debates, contradictory positions, methodological clusters, recent developments, and unresolved questions.
7. Preserve `paper_id` values exactly so all synthesis remains traceable to project records.
8. Do not invent substantive findings from metadata alone. When an abstract supports only a broad topic or association, state only that level of certainty. Detailed findings will be verified in the Evidence Mapping stage.
9. Write the structured landscape submission as JSON following `expected_output_schema` from the packet. A convenient temporary location is `.litreview/packets/landscape_submission.json`.
10. Persist and validate it with:

   `lrc landscape save . --input .litreview/packets/landscape_submission.json`

11. Inspect `outputs/03_research_landscape.md` and present the researcher with the **landscape**, not a wall of individual search results.

The saved Research Landscape is marked `ready_for_review`. No artificial mandatory approval checkpoint is required here; the researcher may comment on or redirect the landscape before Evidence Mapping. The major mandatory human checkpoint remains Research Direction later in the workflow.

## Search strategy guidance

Useful query families may include:

- direct topic/construct combinations;
- theory terminology;
- established terminology found in anchor or seed papers;
- methodological terminology when methodology is central to the research question;
- context-specific combinations;
- recent-development terminology.

Avoid using citation count as the only definition of importance.

## Evidence discipline

OpenAlex metadata is discovery evidence, not proof of a paper's substantive finding. Keep discovery-level synthesis distinct from later source-verified Evidence Mapping. Important statements should preserve epistemic provenance: source-reported content, metadata/abstract-supported observation, AI synthesis, or AI inference.

## Context discipline

Use metadata and abstracts first. Do not automatically inject every discovered paper or full PDF into context. The `landscape prepare` command intentionally creates a bounded, diverse packet. Selectively load anchor papers and source evidence only when later stages require them.
