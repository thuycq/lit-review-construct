---
name: litreview-map
description: Construct a source-disciplined Evidence Map from a saved Lit Review Construct Research Landscape. Use when the researcher wants to map theories, methods, data, findings, contradictions, limitations, or evidence gaps while preserving epistemic provenance.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: evidence-mapping
---

# Lit Review Construct — Evidence Map

Use this skill after an initial Research Landscape has been saved.

## Product boundary

The Evidence Map is a structured research aid, not a finished literature review. Preserve traceability and uncertainty. Do not turn thin metadata into substantive findings.

## Runtime rules

- Use the globally installed `lrc` command. Do not create a project-local Python environment.
- Treat `.litreview/` as authoritative project state.
- Use `lrc evidence prepare . --json` to create the bounded Evidence Map packet.
- Do not run new literature searches unless the researcher asks or the current evidence is clearly insufficient and a new search materially affects the research direction.

## Evidence discipline

Every evidence item must preserve both its **epistemic provenance** and **source basis**.

Allowed provenance classes:

- `source_reported`: explicitly supported by the paper content;
- `tool_derived`: mechanically derived by the toolkit;
- `ai_synthesis`: cross-source synthesis performed by the model;
- `ai_inference`: model interpretation that goes beyond an explicit source statement;
- `methodological_interpretation`: methodological reading or classification;
- `researcher_judgment`: a decision or interpretation supplied by the researcher.

Allowed source bases:

- `full_text`;
- `abstract`;
- `metadata`;
- `researcher_note`.

Never label a claim `source_reported` when it comes only from title, citation count, journal metadata, or AI inference.

## Workflow

1. Run `lrc landscape show . --json` and confirm a saved landscape exists.
2. Run `lrc evidence prepare . --json`.
3. Read `.litreview/packets/evidence.json`.
4. Work only from the papers referenced by the saved landscape for this mapping pass.
5. For papers with local full text, inspect the PDF selectively when needed. Do not load every PDF automatically.
6. For metadata-only papers, use the abstract only for claims explicitly stated there. If the abstract does not support the needed detail, add the paper ID to `papers_requiring_full_text` instead of guessing.
7. Distinguish carefully among:
   - association;
   - prediction;
   - causal findings;
   - null findings;
   - heterogeneous findings.
8. Do not infer causality from regression language alone. Use `causal_finding` only when the study's design or explicit source statement supports a causal interpretation.
9. Capture theories, methods, data/context, limitations, contradictions, and gap claims only when supported at the stated provenance level.
10. Create a temporary JSON submission matching `expected_output_schema` in the packet.
11. Save it with `lrc evidence save . --input <submission.json>`.
12. Report the resulting Evidence Map status, evidence-item count, source limitations, and the path to `outputs/04_evidence_map.md`.

## Important limitation handling

An abstract-only Evidence Map is acceptable as an **initial map**, but it must say so. The correct behavior is to flag evidence requiring fuller verification, not to silently fill missing sample, method, theory, variable, or result details.

## Context discipline

Prefer the bounded packet and selectively opened full texts. Preserve paper IDs on all structured claims so later Research Direction and Blueprint stages can trace every substantive argument back to the evidence store.
