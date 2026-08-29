---
name: litreview-direction
description: Propose and refine candidate research directions only after the iterative multi-source discovery campaign has been explicitly finished by the researcher and the current Research Landscape and Evidence Map have been refreshed. Then stop for an explicit researcher decision.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: research-direction
---

# Lit Review Construct — Research Direction

Use this skill only after a sufficiently broad discovery campaign, Research Landscape, and Evidence Map have been completed for the current scope.

## Mandatory discovery gate

Before proposing Research Directions:

1. Run `lrc discover status . --json`.
2. The campaign must exist and its status must be `complete`, meaning the **researcher explicitly chose to finish discovery for the current narrative-review purpose**.
3. If discovery is still `collecting`, `focused`, `awaiting_researcher`, or `scope_change_requested`, do not proceed to final Research Direction. Return to the discovery loop.
4. If the Landscape or Evidence Map predates the completed discovery campaign or is marked `needs_refresh`, refresh those artifacts first.

This gate exists because a research gap cannot be defended from a deliberately tiny or unreviewed literature sample.

## Product boundary

AI proposes research directions; the researcher decides. Never silently convert an AI suggestion into the project's accepted Research Direction.

A possible gap or novelty claim remains provisional until important underlying papers have been verified sufficiently. If the Evidence Map flags abstract-only or missing full text, carry those verification limits into every candidate direction.

## Candidate workflow

1. Confirm `lrc discover status . --json` reports a completed campaign.
2. Run `lrc evidence show . --json` and confirm the current Evidence Map exists.
3. Run `lrc direction prepare . --json`.
4. Read `.litreview/packets/direction.json` rather than loading the full corpus indiscriminately.
5. Construct 2–5 genuinely distinct candidate directions using the packet schema.
6. For each candidate, include:
   - research idea;
   - rationale;
   - supporting paper IDs and evidence IDs where available;
   - what is currently supported by the evidence;
   - possible research gap, explicitly qualified;
   - potential novelty, explicitly qualified;
   - data feasibility;
   - methodological feasibility;
   - difficulty;
   - risks and limitations;
   - verification needs;
   - confidence.
7. Do not claim a definitive gap merely because a topic was absent from a bounded AI packet. Use the discovery campaign and focused follow-up searches as coverage context.
8. Save the candidate JSON and run `lrc direction save . --input <file>`.
9. Run `lrc direction show . --json` to obtain generated `direction_id` values.
10. Present the candidates to the researcher in compact comparative form.
11. **Stop. Ask the researcher to choose.** Valid actions are select, modify, combine, reject all, or request replacement candidates.

Do not run `lrc direction decide` before the researcher explicitly decides.

## Applying the researcher decision

After the researcher explicitly decides, create a JSON decision file and run `lrc direction decide . --input <file>`.

Decision shapes:

- Select: `{"action":"select","direction_ids":["<id>"]}`
- Modify: `{"action":"modify","direction_ids":["<id>"],"final_direction":{...}}`
- Combine: `{"action":"combine","direction_ids":["<id1>","<id2>"],"final_direction":{...}}`
- Reject all: `{"action":"reject_all"}`

For `modify` and `combine`, `final_direction` uses the same fields as a candidate. Preserve the researcher's intended changes rather than substituting your own preference.

## Human-checkpoint rule

The Research Direction stage is accepted only after `lrc direction decide` records explicit researcher selection/modification/combination. If all candidates are rejected, the stage returns to `in_progress` and the researcher may request more discovery or replacement candidates.

## Evidence discipline

- Never transform `ai_inference` into `source_reported` evidence.
- Treat abstract-only evidence conservatively.
- Distinguish empirical feasibility from a speculative data idea.
- Distinguish methodological feasibility from methodological novelty.
- Gap and novelty statements should be supported by both discovery coverage and source-level evidence, not by paper count alone.

## Authorship boundary

The accepted Research Direction informs later Literature Review Blueprint construction. It does not authorize generation of a complete final literature review for direct submission.
