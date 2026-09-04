---
name: litreview-corpus
description: Refine completed narrative-review triage from Retained Papers to Evidence Candidates and Core Papers, with researcher-controlled local full-text acquisition checkpoints.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Corpus Refinement

## Objective

Bridge discovery/triage and deep evidence work without treating every retained record as equally important.

The required funnel is:

`Retained Papers -> Evidence Candidates -> Core Papers`

Keep these meanings distinct:

- **Retained Paper**: relevant/background/adjacent enough that it should not be discarded after title/abstract triage.
- **Evidence Candidate**: a retained paper prioritized as likely to contribute useful evidence to the review.
- **Core Paper**: a smaller paper set prioritized for deep reading, evidence construction, and synthesis.

Core selection is prioritization, not proof that non-core retained papers are unimportant.

## Researcher acquisition checkpoints

Corpus strategy is a genuine researcher choice because it affects coverage, time, and paid-AI workflow cost.

At the Retained and Evidence Candidate checkpoints, present two choices:

1. **Acquire the whole current tier locally**, then continue refinement.
2. **Continue narrowing first**, then acquire a smaller higher-priority corpus later.

At the Core Paper checkpoint, present:

1. **Acquire all Core Papers locally before evidence work**.
2. **Continue with current full-text coverage**, preserving missing papers as explicit limitations/verification tasks.

Record the choice with the runtime. Once the researcher chooses, do not ask again for every technical batch.

## Local acquisition rule

Full-text acquisition is a deterministic local-runtime task. Use the installed Python runtime through `lrc fulltext acquire . --tier <retained|evidence|core> --json`.

The acquisition command itself does **not** call an AI model once per paper. Do not make Codex/OpenCode search, open, and download papers one by one when the local runtime can perform the batch.

Only lawful open/public locations may be used. Never bypass paywalls, logins, CAPTCHAs, institutional access controls, or robots restrictions.

## Ranking contract

Run `lrc corpus rank . --to evidence --json` and later `lrc corpus rank . --to core --json` when routed by `lrc next`.

The explainable ranking engine uses a balanced set of signals, including:

- relevance to Research Intent and triage label;
- triage priority/confidence;
- evidence potential from available title/abstract metadata;
- bibliographic quality and multi-provider provenance;
- capped citation/anchor value;
- temporal relevance when appropriate;
- selected-focus alignment;
- research-stream coverage.

Citation count must never be the sole ranking criterion. Preserve representation across meaningful streams rather than simply taking the first N highest-scoring records.

Ranking based on metadata/abstract is not full-text analysis. Keep the ranking basis and confidence explicit.

## Orchestration

For an existing project, begin with `lrc next . --json` and follow its structural action.

When a corpus checkpoint is returned, stop and present the choice in researcher-friendly language. After the researcher decides, continue ranking or local acquisition automatically until the next genuine checkpoint.

On macOS, if `lrc` is not visible to a GUI AI host after installation, use `$HOME/.local/bin/lrc` as the launcher path and continue from the same project state.
