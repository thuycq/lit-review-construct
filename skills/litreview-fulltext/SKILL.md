---
name: litreview-fulltext
description: Resolve and acquire lawful open-access full text for the researcher-selected Retained, Evidence Candidate, or Core Paper tier in an active Lit Review Construct workspace. Never equate PDF availability with researcher verification.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: evidence-mapping
---

# Lit Review Construct — Local Lawful Full-Text Acquisition

## Objective

Improve the source basis for literature construction by resolving lawful open/public copies of the corpus tier the researcher chose to acquire.

OA availability is an access property, not a relevance/quality score. Non-OA papers remain in the project.

## Local-runtime rule

Acquisition is a deterministic local task. Prefer:

`lrc fulltext acquire . --tier retained --max-papers 100 --json`

or the corresponding `evidence` / `core` tier returned by `lrc next`.

The command runs in LRC's local Python runtime and does not call an AI model once per paper. Codex/OpenCode should orchestrate the command, not perform a browser/search/download loop for every record.

`--max-papers` is a technical batch size, not a product-level cap. After the researcher has chosen acquisition for a tier, continue batches automatically until that tier's automatic pass is complete.

Do not start a whole-tier acquisition pass unless the researcher selected that option at the relevant corpus checkpoint.

## Allowed resolvers

Runtime may use provider-reported public locations from OpenAlex, Semantic Scholar `openAccessPdf`, and Unpaywall when configured. Never bypass paywalls, logins, CAPTCHAs, institutional access controls, robots restrictions, or other access restrictions.

## Researcher-facing paper library

Toolkit-acquired lawful OA PDFs are exposed in:

`papers/full_text/`

Use stable DOI-based filenames where possible. Preserve legacy cache references/provenance internally. Do not rename or move researcher-provided files.

Researcher uploads belong in `papers/user_uploads/`.

## Evidence-state contract

Keep these distinct:

1. **Full text available** — a PDF exists locally.
2. **AI checked against full text** — an Evidence item was rebuilt/read with `source_basis=full_text`.
3. **Researcher verified** — only after explicit researcher verification.

Downloading a PDF does not upgrade existing abstract-based evidence by itself.

## Failed/unresolved access

If only a landing page is available, or no lawful OA copy resolves, keep the scholarly record, preserve the access status, and include it in later verification needs when relevant. Do not force scraping.

## Researcher-facing response

Do not dump provider diagnostics by default. Summarize the current tier: selected papers, local PDFs available, automatic resolution still pending, and unresolved items. State clearly that the download pass used the local Python runtime rather than one AI interaction per paper.

On macOS, if `lrc` is not visible to a GUI AI host after installation, use `$HOME/.local/bin/lrc`.
