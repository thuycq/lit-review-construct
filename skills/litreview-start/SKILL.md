---
name: litreview-start
description: Start a Lit Review Construct research project or handle Research Intent. Use for a new project, Research Intent definition/revision, a prefilled Fast Start Research Brief, or when the whole-project navigator routes back to the intent stage. For an already initialized project with an unspecified request to continue, use litreview-workflow and `lrc next` rather than rebuilding state from conversation history.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: research-intent
---

# Lit Review Construct — Start / Research Intent

## Product boundary

Lit Review Construct helps the researcher find, understand, organize, synthesize, and construct the literature behind a study. It does not write a complete final literature review for direct submission. The researcher remains responsible for scholarly judgment, source verification, interpretation, authorship, final prose, citation selection, accuracy, and research integrity.

## Runtime rule

Use the globally installed `lrc` command. Do not create a project-local Python environment or install toolkit dependencies inside the research workspace.

## New versus resumed project

1. Treat the currently opened research folder as the workspace.
2. If `.litreview/project.yaml` does not exist, run `lrc init .` and begin Research Intent.
3. If the project already exists and the researcher merely says to continue/resume/proceed, route through `litreview-workflow` and run `lrc next . --json`. Do not restart Research Intent or repeat already recorded checkpoints.
4. Use this skill directly when the project is new, when `lrc next` returns the Research Intent stage, when the researcher pastes a Fast Start Research Brief, or when the researcher explicitly wants to revise the intent.

## Two onboarding modes

### Conversational Start

Use this when the researcher provides only a topic, an early idea, or wants help clarifying scope.

1. Run `lrc intent show . --json`.
2. For a new project begin conversationally with: **What are you planning to research?**
3. Ensure the Research Intent eventually contains at minimum:
   - research question or topic;
   - **publication period** for literature retrieval;
   - paper language(s).
4. Ask targeted follow-up questions only when they materially improve the literature scope. Examples include geography, unit of analysis, variables, data constraints, methods, known theories/papers, or whether the researcher is exploring broadly versus refining an existing idea.

### Fast Start Research Brief

Use this when the researcher pastes a structured or semi-structured brief, including the templates in `QUICK_START.md`.

1. Parse all information already supplied. Do **not** ask the researcher to repeat it in conversational form.
2. Persist all supported Research Intent fields with `lrc intent set .`. Treat optional context/preferences as starting constraints or notes, not claims that the literature must confirm.
3. Ask follow-up questions only if a minimum field is missing, two supplied constraints conflict, or a clarification would materially alter literature retrieval.
4. If the brief explicitly states that the researcher **confirms the supplied information as the initial Research Intent**, that statement counts as researcher approval of the supplied scope; after validating the minimum fields, run `lrc intent accept .` without asking for a redundant confirmation.
5. If the brief explicitly states **No seed papers**, after Intent acceptance persist that researcher decision with `lrc seed skip .` when the workflow reaches the seed checkpoint.
6. If the brief explicitly instructs the toolkit to use a specified project or external paper folder as seed literature, scan that source. If the brief also explicitly authorizes acknowledging those papers as seed literature while preserving provenance and not assuming relevance, that authorization may satisfy the seed-inventory acknowledgement after the scan. Still surface material anomalies such as unreadable files, duplicates, or a clearly mismatched corpus; do not silently mark seed papers relevant.
7. A Fast Start brief bypasses repetitive onboarding only. It does not bypass later scholarly checkpoints for discovery focus, discovery completion, Research Direction selection, or Blueprint acceptance.

## Research Intent persistence

1. Persist agreed scope with `lrc intent set .` using the relevant options. Incremental updates are allowed.
2. When using Conversational Start, summarize the interpreted scope and only after researcher agreement run `lrc intent accept .`.
3. When using Fast Start, follow the explicit-confirmation rule above rather than asking the researcher to reconfirm information they already confirmed in the pasted brief.
4. Do not silently interpret sample/data years inside empirical studies as the literature **publication period**.

## After Intent acceptance

Do not independently invent the next workflow step. Run:

`lrc next . --json`

The normal next checkpoint asks whether the researcher already has related papers. If a Fast Start brief has already supplied and explicitly confirmed that seed decision, persist it rather than asking again. Otherwise ask the checkpoint normally.

Seed papers are starting literature only and are never automatically final relevant literature.

## Revision behavior

If an accepted Research Intent is materially changed, downstream artifacts may be marked `needs_refresh`. Follow project state and regenerate affected discovery/evidence/direction/blueprint work instead of silently using stale outputs.

## Context discipline

Keep context bounded. Prefer project state, structured metadata, evidence records, and task-specific packets over repeatedly loading the full literature corpus.
