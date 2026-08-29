---
name: litreview-blueprint
description: Construct the Literature Review Blueprint after the researcher has accepted a Research Direction. Use when the researcher wants to organize the retained literature into section logic, arguments, theoretical foundations, evidence, contradictions, hypothesis/proposition support, verification priorities, and transitions without generating a complete submission-ready literature review.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-review-blueprint
---

# Lit Review Construct — Literature Review Blueprint

Use this skill only after a Research Direction has been explicitly accepted by the researcher.

## Core product boundary

The primary output is a **Literature Review Blueprint**, not the final literature review. The toolkit helps the researcher determine what each section must establish, which evidence and papers support it, how streams and contradictions relate, and how sections connect. The researcher remains responsible for final prose, source verification, citation selection, interpretation, and authorship.

Do not produce a continuous, submission-ready literature review or a set of complete paragraphs that can simply be concatenated into one.

## Workflow

1. Read authoritative project state, not conversation memory.
2. Verify `research_direction` is `accepted` and `.litreview/data/selected_direction.json` exists.
3. Run:

   `lrc blueprint prepare . --json`

4. Read `.litreview/packets/blueprint.json`.
5. Construct a coherent literature-review architecture around the selected research direction. Avoid paper-by-paper chronology unless the evidence genuinely requires it.
6. For each proposed section, specify:
   - **purpose** — what this section must establish and why it is necessary;
   - concise **key arguments**, not finished paragraphs;
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

## Allowed assistance after Blueprint creation

You may help with:
- evidence summaries for a particular section;
- argument-level draft fragments;
- alternative phrasing for one argument;
- transition options;
- citation/source verification;
- checking whether the researcher's own draft follows the Blueprint;
- identifying missing evidence for a section.

When such assistance occurs, ensure the relevant activity is recorded if the runtime supports that event category.

## Prohibited output

Do not:
- write the full final literature review;
- generate all sections as polished publication-ready prose;
- conceal uncertain or abstract-only evidence;
- invent citations, theories, methods, findings, or gaps;
- turn an AI-suggested gap into an established fact;
- overwrite the researcher-selected direction with a different AI preference.

## Context discipline

Use the bounded Blueprint packet and referenced evidence/papers. Load fuller source text selectively only when a specific argument or verification task requires it. The entire discovery corpus should not be loaded into context merely to construct the Blueprint.
