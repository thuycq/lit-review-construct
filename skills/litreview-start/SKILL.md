---
name: litreview-start
description: Start or resume a Lit Review Construct research project. Use when the researcher wants to begin a literature-review project, define research intent, inspect project status, or continue from an existing local research workspace.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: research-intent
---

# Lit Review Construct — Start

Use this skill to start or resume a Lit Review Construct project.

## Product boundary

Lit Review Construct helps the researcher find, understand, organize, synthesize, and construct the literature behind a study. It does not write a complete final literature review for direct submission. The researcher remains responsible for scholarly judgment, source verification, interpretation, authorship, final prose, citation selection, accuracy, and research integrity.

## Runtime rule

Use the globally installed `lrc` command. Do **not** create a project-local Python environment or install dependencies inside the research workspace.

## Workflow

1. Treat the currently opened research folder as the workspace.
2. Check whether `.litreview/project.yaml` exists.
3. If the project is not initialized, run `lrc init .`.
4. Run `lrc status . --json` and `lrc intent show . --json`. Continue from recorded project state rather than relying on conversation history.
5. Begin a new Research Intent conversation with: **What are you planning to research?**
6. Ensure the Research Intent eventually contains at minimum:
   - research question or topic;
   - publication period;
   - paper language(s).
7. Ask targeted follow-up questions only when they materially improve the research scope. Relevant examples include geography, unit of analysis, variables, data constraints, methods, known theories/papers, or whether the researcher is exploring broadly versus refining an existing idea.
8. Persist agreed scope using `lrc intent set .` with the relevant options. Multiple incremental updates are allowed.
9. When all minimum fields are present, summarize the interpreted scope for the researcher. Only after the researcher agrees, run `lrc intent accept .`.
10. Early in the workflow, ask whether the researcher already has related papers. Treat those papers as seed literature, not automatically as final relevant literature.
11. Preserve important decisions in project state or project outputs. Do not treat the conversation as the project database.

## Command pattern

Example only; use the researcher's actual values:

`lrc intent set . --topic "Working capital and firm performance" --from-year 2015 --to-year 2026 --language en`

Research question can be stored with `--question`. `--language` may be repeated.

## Revision behavior

If an already accepted Research Intent is materially changed, the runtime marks downstream work as needing refresh where applicable. Do not silently continue using stale discovery, evidence, direction, or blueprint outputs.

## Context discipline

Keep context bounded. Prefer project state, structured metadata, evidence records, and task-specific packets over repeatedly loading the full literature corpus.
