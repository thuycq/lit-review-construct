---
name: litreview-map
description: Construct a source-disciplined Evidence Map from the post-discovery Lit Review Construct Research Landscape. Use when the researcher wants to map theories, methods, data, findings, contradictions, limitations, or evidence gaps while preserving epistemic provenance and selectively obtaining fuller source evidence.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: evidence-mapping
---

# Lit Review Construct — Evidence Map

Use this skill after the researcher has finished discovery and the post-discovery Research Landscape has been saved.

## Product boundary

The Evidence Map is a structured research aid, not a finished literature review. Preserve traceability and uncertainty. Do not turn thin metadata into substantive findings.

## Runtime rules

- Use the globally installed `lrc` command. Do not create a project-local Python environment.
- Treat `.litreview/` as authoritative project state.
- Do not silently restart broad literature discovery from this stage. If evidence reveals a meaningful coverage problem, return to the discovery workflow and tell the researcher why.

## Full-text workflow

Discovery normally leaves many records as metadata/abstract only. Before deep Evidence Mapping:

1. Run `lrc fulltext status . --json` to see how many retained papers already have local full text and which high-priority papers are missing it.
2. If the researcher has downloaded PDFs into `papers/` or provided an external paper folder, run the normal seed scan for those files.
3. Run `lrc fulltext reconcile .` after scanning. High-confidence **same DOI** records may share the verified local PDF reference without deleting or merging the underlying scholarly records.
4. Do not auto-link merely similar titles or possible versions as if they were the same paper.
5. Do not retrieve or bypass access controls for paywalled copyrighted material. If full text is unavailable, keep the paper flagged for fuller verification and work conservatively from the available abstract.
6. Prioritize full-text acquisition for anchor/core-candidate/high-priority relevant papers and papers supporting important contradictions or candidate gaps. It is not necessary to obtain every PDF in the discovery universe.

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

1. Run `lrc discover status . --json`; the current campaign should be `complete` for a final-current Evidence Map.
2. Run `lrc landscape show . --json` and confirm the refreshed post-discovery landscape exists.
3. Check/reconcile local full text as described above.
4. Run `lrc evidence prepare . --json`.
5. Read `.litreview/packets/evidence.json`.
6. Work only from the papers referenced by the saved landscape for this mapping pass.
7. For papers with local full text, inspect the PDF selectively when needed. Do not load every PDF automatically.
8. For metadata-only papers, use the abstract only for claims explicitly stated there. If the abstract does not support the needed detail, add the paper ID to `papers_requiring_full_text` instead of guessing.
9. Distinguish carefully among association, prediction, causal findings, null findings, and heterogeneous findings.
10. Do not infer causality from regression language alone. Use `causal_finding` only when the study's design or explicit source statement supports a causal interpretation.
11. Capture theories, methods, data/context, limitations, contradictions, and gap claims only when supported at the stated provenance level.
12. Create a temporary JSON submission matching `expected_output_schema` in the packet.
13. Save it with `lrc evidence save . --input <submission.json>`.
14. Report the resulting Evidence Map status, evidence-item count, source limitations, and the path to `outputs/04_evidence_map.md`.

## Important limitation handling

An abstract-only Evidence Map is acceptable as an **initial/provisional map**, but it must say so. The correct behavior is to flag evidence requiring fuller verification, not to silently fill missing sample, method, theory, variable, or result details.

A candidate research gap should not become strong merely because many papers lack local PDFs. Missing full text is uncertainty, not evidence of absence.

## Context discipline

Prefer the bounded packet and selectively opened full texts. Preserve paper IDs on all structured claims so later Research Direction and Blueprint stages can trace every substantive argument back to the evidence store.
