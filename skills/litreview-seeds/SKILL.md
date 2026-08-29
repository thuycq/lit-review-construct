---
name: litreview-seeds
description: Inspect and organize researcher-provided seed literature in a Lit Review Construct project, or record that no seed literature is currently available. Use when the researcher already has papers, wants to scan the project papers folder, reference an external local paper folder, inspect the seed inventory, or answer the early seed-literature checkpoint.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: seed-literature
---

# Lit Review Construct — Seed Literature

Use this skill for the early question: **Do you already have papers related to this research?**

## Product rule

User-provided papers are **seed literature**. Acknowledging the seed inventory does **not** mark those papers relevant, anchor, or evidence for the eventual research direction.

## Runtime rule

Use the globally installed `lrc` command. Do not create a project-local Python environment merely to run the toolkit.

## If the researcher has papers

1. If PDFs are in project `papers/`, run `lrc seed scan .`.
2. If the researcher identifies another local folder, run `lrc seed scan . --source "<folder>"`. External files are referenced in place and treated as read-only.
3. Inspect `outputs/02_seed_inventory.md` and report notable parsing/duplicate/version issues conservatively.
4. Ask the researcher only for genuinely ambiguous scholarly decisions when needed.
5. Once the inventory is acknowledged, run:

   `lrc seed accept .`

This records the checkpoint while explicitly preserving the rule that seed status does not imply relevance.

## If the researcher has no papers

Record the answer once with:

`lrc seed skip .`

Do not keep asking the same seed-literature question on later resumes; the local project decision is authoritative.

## Duplicate/version discipline

- Exact duplicate files are identified by SHA-256.
- Bibliographic `same_work`, `probable_duplicate`, and `possible_version` relations are reviewable links, not permission to delete source files.
- Same DOI is a strong same-work signal.
- Title/author similarity remains conservative.
- Preserve source/version provenance.

## Interaction guidance

Seed Literature may be handled while Research Intent is being refined, but broad discovery should not repeatedly bypass the seed checkpoint once Research Intent has been accepted.

Do not construct the final Research Landscape from seed papers alone. Seed papers are starting points for terminology, known scholarship, and later discovery/triage.

## Context discipline

Prefer metadata and selective full-text loading. Do not load every PDF into model context automatically.
