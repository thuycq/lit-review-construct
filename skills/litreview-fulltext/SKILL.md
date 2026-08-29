---
name: litreview-fulltext
description: Resolve and acquire lawful open-access full text for retained/priority papers in an active Lit Review Construct workspace. Use after Research Landscape and before Evidence Mapping, or later to improve abstract-based evidence. Never equate PDF availability with researcher verification.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: evidence-mapping
---

# Lit Review Construct — Beta Lawful Full-Text Acquisition

## Objective

Improve the source basis for literature construction by resolving lawful open/public copies of important retained papers. OA availability is an access property, not a relevance/quality score, and non-OA papers remain in the project.

## Allowed resolvers

Runtime may use provider-reported public locations from OpenAlex, Semantic Scholar `openAccessPdf`, and Unpaywall when configured. Never bypass paywalls, logins, CAPTCHAs, institutional access controls, robots restrictions, or other access restrictions.

## Coverage behavior

`lrc fulltext acquire . --max-papers 100 --json` uses `100` as a **technical batch size**, not a product-level cap. Without explicit paper IDs, the runtime advances through retained literature and skips records already locally available or already OA-resolved. Follow with `lrc next . --json`; if OA coverage is incomplete, continue the next batch automatically rather than asking the researcher to approve each batch.

Do not keep selecting the same first 100 records. `oa_resolved_at`/coverage state is the cursor. Coverage may legitimately finish with many papers unresolved/closed.

## Researcher-facing paper library

Toolkit-acquired lawful OA PDFs are exposed in:

`papers/full_text/`

Use stable DOI-based Windows-safe filenames when DOI exists, for example:

`doi_10.1016__j.jbankfin.2024.107123.pdf`

Fallback: OpenAlex ID → Semantic Scholar ID → internal stable paper ID. Preserve legacy cache references/provenance internally. Do not rename or move researcher-provided files.

Researcher uploads belong in `papers/user_uploads/`.

## Evidence-state contract

Keep these distinct:
- **Full text available** — a PDF exists locally.
- **AI checked against full text** — an Evidence item was rebuilt/read with `source_basis=full_text`.
- **Researcher verified** — only after explicit researcher verification.

Downloading a PDF does not upgrade existing abstract-based evidence. If new PDFs were acquired after the current Evidence Map, refresh the affected Evidence Map first. Do not call a downloaded paper “full-text verified” unless the researcher actually verified it.

## Failed/unresolved access

If only a landing page is available, or no lawful OA copy resolves, keep the scholarly record, preserve the access status, and include it in later verification needs when relevant. Do not force scraping.

## Researcher-facing response

Do not dump provider diagnostics by default. Summarize coverage in plain language: how many retained/priority records were checked, how many local PDFs are available, how many remain unresolved, and whether the coverage pass is complete. Continue automatically while coverage remains and no scholarly decision is required.
