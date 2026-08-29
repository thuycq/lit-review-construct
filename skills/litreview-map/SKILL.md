---
name: litreview-map
description: Construct and refresh a source-disciplined Evidence Map in an active Lit Review Construct workspace after Research Landscape/OA coverage. Preserve epistemic provenance and distinguish full-text availability, AI full-text checking, and researcher verification.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: evidence-mapping
---

# Lit Review Construct — Beta Evidence Map

## Boundary

The Evidence Map organizes theories, methods, data, reported findings, contradictions, limitations and provisional gaps. It is not final prose. Metadata/title/citation counts are not substantive evidence.

## Full-text sequence

Follow `lrc next . --json`. OA coverage is a resumable technical pass across retained/priority literature; `--max-papers 100` is a batch size, not a total cap. Continue batches automatically until runtime reports coverage complete, unless a genuine access/researcher issue requires attention.

Toolkit OA PDFs are researcher-visible in `papers/full_text/`. Researcher PDFs can be placed in `papers/user_uploads/` or an explicitly supplied folder and reconciled conservatively.

Never bypass paywalls/access controls.

## Evidence-state contract

Every Evidence item has epistemic provenance plus source basis.

Source basis:
- `full_text` = **AI checked against full text** for that evidence item;
- `abstract` = abstract-supported only;
- `metadata` = metadata only, not substantive source-reported finding;
- `researcher_note` = supplied researcher material/judgment basis.

Separately:
- **Full text available** means a local PDF exists, even if AI has not checked the relevant claim;
- **Researcher verified** is only recorded after explicit researcher verification.

Never render `full_text_available=true` as “full-text verified”. Never render `source_basis=full_text` as researcher-verified.

## Evidence construction

Use the bounded Evidence packet and selectively inspect local full texts when detailed findings/methods/limitations/construct definitions are needed. If a PDF is available and the claim requires detail, prefer the full text over the abstract. If evidence remains abstract-only, keep detailed claims provisional and add important papers to verification needs rather than guessing.

Preserve provenance categories such as `source_reported`, `tool_derived`, `ai_synthesis`, `ai_inference`, `methodological_interpretation`, and `researcher_judgment`. `source_reported` requires actual paper content (abstract or full text), never title/metadata alone.

Distinguish association, prediction, causal, null and heterogeneous findings. Do not upgrade regression association to causality without source/design support.

## Refresh behavior

A newly downloaded PDF does **not** automatically upgrade an older abstract Evidence item. If OA acquisition occurs after a saved Evidence Map, rebuild/re-check affected items. Then downstream Direction/Blueprint/Draft should use the refreshed evidence state.

## Gaps and contradictions

Surface contradictions without manufacturing consensus. Gap claims must be bounded to the reviewed corpus/coverage when discovery is narrative/progressive. Missing full text is uncertainty, not evidence of absence.

## Researcher-facing response

Present meaningful paper/claim descriptions and concise status labels; hide internal IDs/JSON/line numbers unless debug is requested. Report paper-level access counts separately from evidence-item-level source-basis counts so numbers cannot be mistaken as additive categories.
