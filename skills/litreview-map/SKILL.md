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

1. If `lrc next . --json` routes to `resolve_priority_full_text`, run:

   `lrc fulltext acquire . --max-papers 30 --json`

   This proactively checks lawful OA locations through configured scholarly services and downloads direct public PDFs into `.litreview/cache/fulltext/` when available.
2. Run `lrc fulltext status . --json` to see how many retained papers have full text and which high-priority papers are still missing it.
3. If the researcher has additional PDFs in `papers/` or an external folder, scan them and then run `lrc fulltext reconcile .` so high-confidence same-DOI records can share the verified local file reference without merging records.
4. Never auto-link merely similar titles or possible versions as if they were the same paper.
5. Never bypass paywalls, logins, CAPTCHAs, institutional access controls, or other restrictions. If no lawful OA copy exists, retain the paper and flag it for researcher verification.
6. Prioritize full text for anchors, core candidates, high-priority relevant papers, contradictions, and papers carrying important direction/gap claims. Do not try to download the entire discovery universe.
7. OA availability is an access property, not a relevance or quality score.

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
3. Resolve/reconcile priority full text as described above.
4. Run `lrc evidence prepare . --json`.
5. Read `.litreview/packets/evidence.json`.
6. Work only from the papers referenced by the saved landscape for this mapping pass.
7. **When a local/OA PDF is available and the current evidence task needs detailed methods, findings, sample, theory, limitations, or construct definitions, inspect that full text and prefer it over the abstract.** Do not leave a claim marked `abstract` merely because the abstract is easier to access when the relevant full text has already been acquired.
8. Load PDFs selectively around the current claim; do not dump every PDF into model context.
9. For papers without full text, use the abstract only for claims explicitly stated there. If the abstract does not support the needed detail, add the paper ID to `papers_requiring_full_text` instead of guessing.
10. Distinguish carefully among association, prediction, causal findings, null findings, and heterogeneous findings.
11. Do not infer causality from regression language alone. Use `causal_finding` only when the study's design or explicit source statement supports a causal interpretation.
12. Capture theories, methods, data/context, limitations, contradictions, and gap claims only when supported at the stated provenance level.
13. Create a temporary JSON submission matching `expected_output_schema` in the packet.
14. Save it with `lrc evidence save . --input <submission.json>`.
15. Report the Evidence Map status, evidence-item count, full-text versus abstract basis, unresolved verification needs, and the path to `outputs/04_evidence_map.md`.

## Refresh rule after later full-text acquisition

If important full text is acquired **after** an Evidence Map was already created, do not silently pretend existing abstract-grounded records have become full-text evidence. Revisit the affected paper/evidence items, verify them against the PDF, and refresh downstream interpretations when the verified source materially changes the claim, method, limitation, contradiction, or proposed gap.

## Important limitation handling

An abstract-only Evidence Map is acceptable as an **initial/provisional map**, but it must say so. The correct behavior is to flag evidence requiring fuller verification, not to silently fill missing sample, method, theory, variable, or result details.

A candidate research gap should not become strong merely because many papers lack local PDFs. Missing full text is uncertainty, not evidence of absence.

## Context discipline

Prefer the bounded packet and selectively opened full texts. Preserve paper IDs on all structured claims so later Research Direction, Blueprint, and Working Draft stages can trace every substantive argument back to the evidence store.
