---
name: litreview-ai-use
description: Generate an AI-use disclosure from the activities actually recorded in a Lit Review Construct project. Use near researcher handoff or whenever the researcher wants to inspect what AI assistance was recorded. Never claim AI uses that are not present in project activity/artifact provenance.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: researcher-handoff
---

# Lit Review Construct — AI Use Statement

Use this skill to produce an auditable disclosure of AI assistance from the current project.

## Grounding rule

The statement must be based on **actual project records**, not on toolkit capabilities and not on conversation memory.

Run:

`lrc ai-use summary . --json`

Inspect the recorded activity types. Do not add activities that are absent. Older project artifacts may provide explicit `ai_synthesis` provenance where activity logging was not yet wired; the runtime may use that provenance conservatively.

## Generate statement

The runtime provides three variants:

- `short`
- `standard`
- `detailed`

Generate with:

`lrc ai-use generate . --style standard`

The generated `outputs/07_ai_use_statement.md` contains all three variants and identifies the selected one.

## Disclosure boundary

The statement should distinguish AI-assisted reasoning/synthesis from deterministic toolkit operations where useful. Examples of deterministic operations include metadata retrieval, indexing, deduplication, and local file reconciliation; these should not be described as generative AI reasoning unless the project record says otherwise.

Always preserve researcher responsibility for:
- relevance and scope decisions;
- source and citation verification;
- interpretation;
- research-direction selection;
- final prose and authorship;
- research integrity.

Do not claim a specific host/model unless it was actually recorded. Do not claim that AI drafted text unless a drafting/draft-fragment activity was recorded.

## Journal/institution adaptation

The generated wording is a project-grounded draft disclosure, not a guarantee of compliance with every journal, university, funder, or course policy. If the researcher asks for a policy-specific version, verify the applicable external policy separately and adapt the recorded statement without expanding the underlying list of AI activities.
