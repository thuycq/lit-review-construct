---
name: litreview-workflow
description: Resume and orchestrate an entire Lit Review Construct project from authoritative local state. Use when the researcher asks to continue, resume, proceed, or work on the literature review without naming a specific stage. Route to the correct specialized skill and stop at researcher checkpoints.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: orchestration
---

# Lit Review Construct — Workflow Orchestrator

This is the top-level routing skill for an existing Lit Review Construct research workspace.

## North-star objective

The toolkit exists to help a researcher **construct the literature behind a study**: define the literature scope, discover enough relevant scholarship, understand the research landscape, organize evidence, reason about defensible research directions/gaps, build a Literature Review Blueprint, and turn that accepted architecture into a researcher-editable Working Draft. It is not a generic academic search engine and it does not replace the researcher as author of the final literature review.

When deciding what to do next, prefer progress toward this objective over adding unrelated analysis, convenience features, or technical complexity.

## Resume rule

Always begin an unspecified continuation/resume request with:

`lrc next . --json`

Treat the returned project state as authoritative. Do not reconstruct workflow state from conversation history.

The response includes:
- `next_action`;
- `stage`;
- the specialized `skill` to use;
- whether a human checkpoint is required;
- the structural command(s) that move the project forward;
- `suggested_user_message`, a short message the researcher can send to advance the saved workflow without needing to know internal commands.

## Routing

Route to the specialized skill named by `lrc next`:
- `litreview-start` — Research Intent;
- `litreview-seeds` — existing/seed literature;
- `litreview-discover` — multi-source discovery, iterative narrowing, Research Landscape;
- `litreview-fulltext` — lawful OA full-text acquisition for priority papers;
- `litreview-map` — Evidence Map;
- `litreview-direction` — candidate Research Direction and researcher selection;
- `litreview-blueprint` — Literature Review Blueprint;
- `litreview-draft` — researcher-editable evidence-linked Working Draft;
- `litreview-ai-use` — optional activity-grounded disclosure at handoff.

Do not duplicate stage-specific logic here when the specialized skill already defines it.

## Human checkpoints

If `human_checkpoint_required` is true, stop and ask the researcher for the required scholarly/product decision. Never silently choose:
- whether seed literature exists;
- whether discovery should filter more, continue/broaden, focus/refocus, change scope, or finish;
- which Research Direction to select/modify/combine/reject;
- whether the Literature Review Blueprint is accepted.

Do not disguise an AI recommendation as a researcher decision.

## User-facing completion contract

Every researcher-facing response that completes a workflow action or reaches a checkpoint must end with clear guidance about what the researcher can do next.

1. Briefly state what was completed and the important project status.
2. If there is a human checkpoint, show the valid choices and give one reasoned recommendation when appropriate.
3. End with exactly one easy-to-copy line in this form:

   **Suggested next message:** <message>

4. Prefer the `suggested_user_message` returned by `lrc next . --json` or `lrc discover next . --json` when available.
5. The suggestion is never itself researcher approval. If the next action requires a human decision, phrase it so the researcher still makes or confirms that decision.
6. Do not expose internal `lrc` commands as the primary thing the researcher must type unless debugging is explicitly requested.

A generic non-checkpoint fallback is:

**Suggested next message:** Continue with the recommended next step.

## Researcher handoff

The accepted Blueprint is **not** the end of useful product assistance. Before handoff, construct the Researcher Working Draft when `lrc next` requests it. This draft provides section-level prose fragments, evidence anchors, transitions, verification flags, and researcher tasks. It remains explicitly non-final.

When `lrc next` finally returns `researcher_handoff`, the researcher has both an accepted Blueprint and a Working Draft. The researcher then verifies sources/citations, rewrites and approves prose, and authors the final review. The toolkit may continue to support targeted source verification, citation checks, evidence questions, revision against the Blueprint, and Word export.

Do **not** present the AI-assisted Working Draft as submission-ready final prose. An AI-use statement is optional and must be generated only from recorded project activity.

## Word export

When requested, export saved artifacts through the runtime rather than relying on host-specific Word features:

- `lrc export docx . --artifact working-draft`
- `lrc export docx . --artifact blueprint`
- `lrc export docx . --artifact handoff`

Markdown/JSON remains authoritative state; DOCX is an editable presentation/export format.

## Context discipline

Use bounded packets and structured project state. Do not load the entire discovery corpus into context merely because it exists locally. Load full text selectively when the current scholarly claim requires it.
