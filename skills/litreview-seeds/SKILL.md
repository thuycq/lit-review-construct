---
name: litreview-seeds
description: Inspect and organize researcher-provided seed literature in a Lit Review Construct project. Use when the researcher already has papers, wants to scan the project papers folder, reference an external local paper folder, inspect the seed inventory, or identify duplicate and related-version candidates.
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

## Runtime rule

Use the globally installed `lrc` command. Do **not** create `.venv`, `venv`, install Python packages, or bootstrap a separate runtime inside the research workspace. If the installed `lrc` command is missing or does not expose the expected command, tell the researcher the toolkit installation needs updating instead of modifying the research folder environment.

## Workflow

1. Confirm the current folder is a Lit Review Construct project using `lrc status . --json`.
2. If PDFs are stored in the project `papers/` folder, run `lrc seed scan .`.
3. If the researcher identifies another local folder, run `lrc seed scan . --source "<folder>"`. External files are referenced in place and must be treated as read-only.
4. Inspect `outputs/02_seed_inventory.md`, `.litreview/data/papers.jsonl`, and `.litreview/data/paper_relations.jsonl` as needed.
5. Explain metadata or parsing problems without inventing missing bibliographic information.
6. Exact duplicate files are identified by SHA-256 and stored as multiple file instances of the same paper record rather than creating redundant scholarly records.
7. Bibliographic relation candidates are rebuilt with `lrc dedupe .` when needed. Treat `same_work`, `probable_duplicate`, and `possible_version` as relation candidates, not permission to delete or merge source files.
8. Same DOI is a high-confidence `same_work` signal. Title/author similarity is intentionally more conservative and remains unresolved until sufficient evidence exists.
9. Preserve seed-paper status until relevance is evaluated against the Research Intent and newly discovered literature.

## Interaction guidance

The Seed Literature step may happen while Research Intent is still being refined. Do not force the researcher through an artificial strictly linear sequence.

When a duplicate/version candidate matters, summarize the evidence for the relation and ask the researcher only if scholarly judgment is actually required. Do not silently discard working papers, preprints, conference papers, or alternative versions.

When useful, summarize the seed corpus at a high level, but do not construct a full Research Landscape until discovery and relevance assessment are available.

## Context discipline

Prefer metadata and selectively loaded papers. Do not automatically load every full PDF into model context. DOI extraction during seed scanning is bounded to PDF metadata and the first two pages.
