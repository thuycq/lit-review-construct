---
name: litreview-fulltext
description: Resolve and acquire lawful open-access full text for priority papers in a Lit Review Construct project. Use after the Research Landscape identifies important papers, before Evidence Mapping when possible, or later when the researcher wants to verify abstract-based evidence.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: evidence-mapping
---

# Lit Review Construct — Open-Access Full-Text Verification

Use this skill when the workflow requests `resolve_priority_full_text` or when the researcher asks to verify important papers beyond abstracts.

## Objective

Improve evidence quality by obtaining lawful open/public copies of papers that are already important to the current research direction. Full-text acquisition is **selective**, not a reason to restrict discovery to OA-only literature.

## Sources

The runtime may resolve open/public locations through:
- OpenAlex OA locations;
- Semantic Scholar `openAccessPdf`;
- Unpaywall DOI lookups when `UNPAYWALL_EMAIL` (or `CROSSREF_MAILTO`) is configured.

Provider credentials/configuration are environmental and must never be written into the project.

## Rules

- Never bypass a paywall, login, CAPTCHA, institutional access control, or robots/access restriction.
- Do not discard a substantively important paper merely because no OA copy is found.
- Preserve version information when available (`publishedVersion`, `acceptedVersion`, `submittedVersion`).
- Preserve provider, URL, license, and acquisition timestamp.
- Prefer an existing researcher-provided/local PDF over downloading another copy.
- Download only direct URLs that actually return a PDF. Failed or non-PDF responses remain unresolved rather than being forced through scraping.
- Treat OA availability as an access property, not a relevance or quality score.

## Standard workflow

Run:

`lrc fulltext acquire . --max-papers 30 --json`

By default the runtime prioritizes papers referenced by the accepted Blueprint when one exists, then selected Research Direction, then Research Landscape anchors/core retained papers.

For specific papers:

`lrc fulltext acquire . --paper-id <id1> --paper-id <id2> --json`

To resolve links without downloading:

`lrc fulltext acquire . --resolve-only --max-papers 30 --json`

Then inspect:

`lrc fulltext status . --json`

Downloaded files are stored under `.litreview/cache/fulltext/` and linked back to the existing scholarly record. Do not duplicate/replace researcher files outside the project.

## Evidence consequences

When full text becomes available, subsequent Evidence Mapping should prefer the full text for detailed findings, methods, limitations, constructs, and source-reported claims. Previously abstract-based evidence is not magically upgraded; rebuild or verify the relevant Evidence Map items against the acquired source.

If no OA copy is available, keep the paper in the project and surface it in the researcher verification list.
