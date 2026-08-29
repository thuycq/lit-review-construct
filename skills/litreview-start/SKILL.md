---
name: litreview-start
description: Start a Lit Review Construct research project or handle Research Intent. Use for a new project, Research Intent definition/revision, or when the whole-project navigator routes back to the intent stage. For an already initialized project with an unspecified request to continue, use litreview-workflow and `lrc next` rather than rebuilding state from conversation history.
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
4. Use this skill directly when the project is new, when `lrc next` returns the Research Intent stage, or when the researcher explicitly wants to revise the intent.

## Research Intent workflow

1. Run `lrc intent show . --json`.
2. For a new project begin conversationally with: **What are you planning to research?**
3. Ensure the Research Intent eventually contains at minimum:
   - research question or topic;
   - **publication period** for literature retrieval;
   - paper language(s).
4. Ask targeted follow-up questions only when they materially improve the literature scope. Examples include geography, unit of analysis, variables, data constraints, methods, known theories/papers, or whether the researcher is exploring broadly versus refining an existing idea.
5. Persist agreed scope with `lrc intent set .` using the relevant options. Incremental updates are allowed.
6. When the minimum fields are complete, summarize the interpreted scope. Only after researcher agreement run `lrc intent accept .`.
7. Do not silently interpret sample/data years inside empirical studies as the literature **publication period**.

## After Intent acceptance

Do not independently invent the next workflow step. Run:

`lrc next . --json`

The normal next checkpoint asks whether the researcher already has related papers. That answer is persisted by the Seed Literature stage, so it should not be repeatedly asked on later resumes.

Seed papers are starting literature only and are never automatically final relevant literature.

## Revision behavior

If an accepted Research Intent is materially changed, downstream artifacts may be marked `needs_refresh`. Follow project state and regenerate affected discovery/evidence/direction/blueprint work instead of silently using stale outputs.

## Context discipline

Keep context bounded. Prefer project state, structured metadata, evidence records, and task-specific packets over repeatedly loading the full literature corpus.
