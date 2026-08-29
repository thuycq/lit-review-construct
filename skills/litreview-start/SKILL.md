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

## Workflow

1. Treat the currently opened research folder as the workspace.
2. Check whether `.litreview/project.yaml` exists.
3. If the project is not initialized, run `lrc init .`.
4. If it is initialized, run `lrc status . --json` and continue from the recorded project state rather than relying on conversation history.
5. Begin the research interaction conversationally with: **What are you planning to research?**
6. Ensure the Research Intent eventually contains at minimum:
   - research question or topic;
   - publication period;
   - paper language(s).
7. Ask targeted follow-up questions only when they materially improve the research scope. Relevant examples include geography, unit of analysis, variables, data constraints, methods, known theories/papers, or whether the researcher is exploring broadly versus refining an existing idea.
8. Early in the workflow, ask whether the researcher already has related papers. Treat those papers as seed literature, not automatically as final relevant literature.
9. Preserve important decisions in project state or project outputs. Do not treat the conversation as the project database.

## Context discipline

Keep context bounded. Prefer project state, structured metadata, evidence records, and task-specific packets over repeatedly loading the full literature corpus.

## Current bootstrap limitation

In Technical Design v0.1 Milestone 0–1, `lrc init`, `lrc status`, and `lrc doctor` are available. Structured Research Intent persistence is added in the next implementation slice; until then, do not invent a persistence command that does not exist.
