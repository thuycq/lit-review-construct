---
name: litreview-seeds
description: Inspect and organize researcher-provided seed literature in a Lit Review Construct project. Use when the researcher already has papers, wants to scan the project papers folder, reference an external local paper folder, inspect the seed inventory, or identify exact duplicate files.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: seed-literature
---

# Lit Review Construct — Seed Literature

Use this skill for papers the researcher already possesses before or during literature discovery.

## Product rule

User-provided papers are **seed literature**. Do not automatically treat them as final relevant literature, anchor literature, or evidence supporting the eventual research direction.

## Workflow

1. Confirm the current folder is a Lit Review Construct project using `lrc status . --json`.
2. If PDFs are stored in the project `papers/` folder, run `lrc seed scan .`.
3. If the researcher identifies another local folder, run `lrc seed scan . --source "<folder>"`. External files are referenced in place and must be treated as read-only.
4. Inspect `outputs/02_seed_inventory.md` and `.litreview/data/papers.jsonl` as needed.
5. Explain metadata or parsing problems without inventing missing bibliographic information.
6. Exact duplicate file detection is based on SHA-256. More advanced bibliographic/version deduplication will be added in a later implementation slice.
7. Preserve seed-paper status until relevance is evaluated against the Research Intent and newly discovered literature.

## Interaction guidance

The Seed Literature step may happen while Research Intent is still being refined. Do not force the researcher through an artificial strictly linear sequence.

When useful, summarize the seed corpus at a high level, but do not construct a full Research Landscape until discovery and relevance assessment are available.

## Context discipline

Prefer metadata and selectively loaded papers. Do not automatically load every full PDF into model context.
