---
name: litreview-blueprint
description: Construct the Literature Review Blueprint after the researcher has accepted a Research Direction. Use when the researcher wants to organize the retained literature into section logic, arguments, theoretical foundations, evidence, contradictions, hypothesis/proposition support, verification priorities, and transitions before a researcher-editable Working Draft is produced.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-review-blueprint
---

# Lit Review Construct — Literature Review Blueprint

Use this skill only after a Research Direction has been explicitly accepted by the researcher.

## Core product boundary

The Blueprint is the **accepted argument architecture** for the literature review. It determines what each section must establish, which evidence and papers support it, how streams and contradictions relate, and how sections connect. It is not yet the prose artifact.

After researcher acceptance, the workflow proceeds to the separate `litreview-draft` stage, which creates an evidence-linked researcher Working Draft. This separation keeps the architecture auditable before prose is generated.

## Workflow

1. Read authoritative project state, not conversation memory.
2. Verify `research_direction` is `accepted` and `.litreview/data/selected_direction.json` exists.
3. Run:

   `lrc blueprint prepare . --json`

4. Read `.litreview/packets/blueprint.json`.
5. Construct a coherent literature-review architecture around the selected research direction. Avoid paper-by-paper chronology unless the evidence genuinely requires it.
6. For each proposed section, specify:
   - **purpose** — what this section must establish and why it is necessary;
   - concise **key arguments**;
   - anchor papers;
   - supporting papers;
   - conflicting papers where relevant;
   - evidence IDs supporting substantive claims;
   - theoretical foundations;
   - methodological context where it matters to interpretation;
   - links to hypotheses/propositions/research logic where relevant;
   - unresolved questions;
   - transition logic to the next section.
7. Carry forward full-text verification needs, abstract-only limitations, unresolved contradictions, and provisional gap/novelty language.
8. Save structured JSON to `.litreview/packets/blueprint_submission.json`, then run:

   `lrc blueprint save . --input .litreview/packets/blueprint_submission.json`

9. Present the Blueprint to the researcher. Explain the architecture and any verification priorities. Do not silently accept it on the researcher's behalf.
10. If the researcher approves it, run:

   `lrc blueprint accept .`

11. Resume with `lrc next . --json`. The normal next action is `construct_working_draft`, not immediate handoff.

## Prohibited output at Blueprint stage

Do not:
- hide uncertain or abstract-only evidence;
- invent citations, theories, methods, findings, or gaps;
- turn an AI-suggested gap into an established fact;
- overwrite the researcher-selected direction with a different AI preference;
- silently skip Blueprint review and move into prose generation.

## Context discipline

Use the bounded Blueprint packet and referenced evidence/papers. Load fuller source text selectively only when a specific argument or verification task requires it. The entire discovery corpus should not be loaded into context merely to construct the Blueprint.
