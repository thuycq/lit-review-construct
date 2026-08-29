---
name: litreview-draft
description: Build bounded researcher-editable Working Draft fragments after an accepted Literature Review Blueprint in an active LRC workspace. Preserve evidence states and run draft-safety QA before showing the artifact. Never create a seamless submission-ready final review.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: researcher-handoff
---

# Lit Review Construct — Beta Researcher Working Draft

## Purpose and boundary

Turn the accepted Blueprint into a researcher-editable scaffold, not a final literature review. Cover every accepted Blueprint section, normally with a small bounded number of fragments, visible evidence status, unresolved decisions/tasks, and provisional transitions. The researcher verifies, selects final citations, rewrites, interprets, and authors final prose.

Do not expand each section into a seamless multi-paragraph manuscript merely to make it polished.

## Workflow

1. Prepare the bounded packet with `lrc draft prepare . --json`.
2. Use only accepted Blueprint paper/evidence anchors unless the researcher explicitly revises the Blueprint.
3. Construct short section-level fragments and structured researcher tasks/decisions.
4. Keep proposed empirical design/specification clearly labeled as a **proposal**, separate from literature synthesis.
5. Save through `lrc draft save ...`. Runtime claim-strength QA must pass before the artifact is presented.
6. If QA rejects strong wording, revise automatically and save again; do not make the researcher perform conversational QA on mechanical wording errors.
7. After save, follow `lrc next . --json` so final package preparation can proceed automatically.

## Evidence wording

Claim language must follow source basis:
- abstract/metadata/provisional evidence → natural cautious wording such as “available evidence suggests”, “the abstract reports”, “one study reports”; do not use “established”, “proves”, “confirms”, or equivalent certainty;
- `source_basis=full_text` → AI checked the claim against full text and may describe what the study reports/finds, subject to study design;
- researcher verification is a separate state and must never be invented.

A PDF merely existing locally means **Full text available**, not “verified”.

Gap/absence language must be corpus-bounded for narrative/progressive discovery, e.g. “within the reviewed corpus, direct evidence appears limited”. Never write “no study exists” unless that universal claim has actually been verified.

Do not combine contradictory phrases such as “provisionally established”. Keep verification status in concise labels/notes rather than stuffing repeated disclaimers into every sentence.

## Researcher-facing artifact

When asked to show the Working Draft, show the **actual fragments section by section**, then concise evidence status and researcher decisions/tasks. Do not show only a technical summary of JSON/file lines/internal IDs.

Hide internal paper/evidence IDs in normal presentation even though structured state retains them for provenance.

## Authorship boundary

Allowed: bounded provisional prose, synthesis scaffolding, transitions, evidence anchors, verification tasks, unresolved interpretation decisions.

Prohibited: invented citations/findings; upgrading association to causality; hiding uncertainty; treating abstract claims as full-text findings; removing researcher decisions to create smooth final prose; presenting the artifact as submission-ready.

The activity log may record AI draft-fragment assistance for the optional activity-grounded AI-use statement.
