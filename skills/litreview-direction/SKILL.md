---
name: litreview-direction
description: Propose and refine candidate research directions from the saved Research Landscape and Evidence Map, then stop for an explicit researcher decision. Use when the researcher wants to identify, compare, select, modify, combine, reject, or replace a research direction.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: research-direction
---

# Lit Review Construct — Research Direction

Use this skill after a Research Landscape and Evidence Map have been saved.

## Product boundary

AI proposes research directions; the researcher decides. Never silently convert an AI suggestion into the project's accepted Research Direction.

A possible gap or novelty claim is provisional until the underlying literature has been verified sufficiently. If the Evidence Map flags abstract-only or missing full text, carry those verification limits into every candidate direction.

## Candidate workflow

1. Run `lrc evidence show . --json` and confirm an Evidence Map exists.
2. Run `lrc direction prepare . --json`.
3. Read `.litreview/packets/direction.json` rather than loading the full corpus indiscriminately.
4. Construct 2–5 genuinely distinct candidate directions using the packet schema.
5. For each candidate, include:
   - research idea;
   - rationale;
   - supporting paper IDs and evidence IDs where available;
   - what is currently supported by the evidence;
   - possible research gap, explicitly provisional;
   - potential novelty, explicitly provisional;
   - data feasibility;
   - methodological feasibility;
   - difficulty;
   - risks and limitations;
   - verification needs;
   - confidence.
6. Do not claim a definitive gap merely because a topic was absent from the bounded corpus.
7. Save the candidate JSON to a temporary project file and run `lrc direction save . --input <file>`.
8. Run `lrc direction show . --json` to obtain the generated `direction_id` values.
9. Present the candidates to the researcher in a compact comparative form.
10. **Stop. Ask the researcher to choose what to do.** Valid researcher actions are:
    - select one candidate;
    - modify one candidate;
    - combine two or more candidates;
    - reject all candidates;
    - ask for replacement candidates.

Do not run `lrc direction decide` before the researcher has explicitly expressed a decision.

## Applying the researcher decision

After the researcher explicitly decides, create a JSON decision file and run `lrc direction decide . --input <file>`.

Decision shapes:

- Select: `{"action":"select","direction_ids":["<id>"]}`
- Modify: `{"action":"modify","direction_ids":["<id>"],"final_direction":{...}}`
- Combine: `{"action":"combine","direction_ids":["<id1>","<id2>"],"final_direction":{...}}`
- Reject all: `{"action":"reject_all"}`

For `modify` and `combine`, the `final_direction` uses the same fields as a candidate direction. Preserve the researcher's intended changes rather than substituting your own preferred direction.

## Human-checkpoint rule

The Research Direction stage is accepted only after `lrc direction decide` records an explicit researcher selection/modification/combination. If all candidates are rejected, the stage returns to `in_progress` and new candidates may be developed.

## Evidence discipline

- Never transform `ai_inference` into `source_reported` evidence.
- Treat abstract-only evidence conservatively.
- Distinguish empirical feasibility from a speculative data idea.
- Distinguish methodological feasibility from methodological novelty.
- A literature gap, research contribution, or novelty proposition must remain qualified when source coverage is incomplete.

## Authorship boundary

The accepted Research Direction informs later Literature Review Blueprint construction. It does not authorize generation of a complete final literature review for direct submission.
