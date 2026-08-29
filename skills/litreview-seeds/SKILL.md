---
name: litreview-seeds
description: Inspect researcher-provided seed literature in an active Lit Review Construct workspace or record that none is available. Default researcher drop zone is `papers/user_uploads/`; user files remain unchanged and seed status never implies relevance.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: seed-literature
---

# Lit Review Construct — Beta Seed Literature

Ask once: **Do you already have papers related to this research?** Local state preserves the answer.

## Researcher drop zone

For project-managed uploads, ask the researcher to place PDFs in:

`papers/user_uploads/`

Then scan with the seed workflow. Do not ask the researcher to browse `.litreview/`. If an external folder is explicitly supplied, reference it in place/read-only.

Never move or rename researcher-provided files. Toolkit-acquired OA PDFs belong separately in `papers/full_text/`.

## Meaning of seed status

Researcher-provided papers are starting literature only. Acknowledging the inventory does **not** mark them relevant, anchor, evidence, or final citations. Preserve duplicates/version relations conservatively; do not delete files.

If no seed papers exist, record the decision once and continue. Do not repeat the same checkpoint later.

## Researcher-facing mode

Present a readable inventory summary and material anomalies only. Hide file hashes/internal IDs/CLI details unless debug is requested. Continue to the next structural workflow step after the seed decision.
