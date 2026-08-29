---
name: litreview-start
description: Explicitly start a new Lit Review Construct project or handle Research Intent in an existing active LRC workspace. Do not auto-initialize merely because a generic literature question was asked in a folder without `.litreview/project.yaml`.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: research-intent
---

# Lit Review Construct — Beta Start / Research Intent

## Activation gate

Global installation means **available globally, not activated globally**.

- If `.litreview/project.yaml` exists, this is an active LRC workspace.
- If it does not exist, run `lrc init .` **only when the researcher explicitly asked to start/use Lit Review Construct, invoked `/lr` to start a project, or provided an LRC Fast Start brief**.
- A generic request about literature, citations, papers, or writing in another workspace must not silently create an LRC project.

For an existing project and a generic “continue/resume/proceed”, use `litreview-workflow` + `lrc next . --json` rather than reconstructing state.

## Product boundary

Help construct literature scope, discovery, evidence, research direction, Blueprint and bounded Working Draft support. Do not write a complete final literature review for direct submission. The researcher retains verification, scholarly judgment, citation selection, interpretation, authorship and final prose.

## Research Intent

Support two modes:

**Conversational Start** — researcher provides an early topic. Ask only questions that materially affect retrieval. Minimum intent: topic/question, publication period, language(s). Geography/unit/constructs/data/method/theory preferences are optional context when useful.

**Fast Start Brief** — parse all supplied information without asking the researcher to repeat it. Explicit confirmation in the brief can count as Intent approval. Explicit “No seed papers” can be persisted when the seed checkpoint is reached. Do not use Fast Start to bypass later scholarly decisions.

Persist agreed fields through runtime. Do not infer the literature publication period from sample/data years inside studies.

## After acceptance

Immediately follow `lrc next . --json`. Do not invent extra onboarding checkpoints.

The researcher paper drop zone is:

`papers/user_uploads/`

If the researcher says they already have papers, direct them there (or accept an explicit external folder), index them conservatively, preserve their filenames/locations, and never assume they are relevant merely because the researcher supplied them.

## Researcher-facing mode

Do not expose CLI/JSON/internal IDs unless debugging is requested. Summarize the interpreted Intent in ordinary research language and end completions/checkpoints with one natural-language **Suggested next message**.
