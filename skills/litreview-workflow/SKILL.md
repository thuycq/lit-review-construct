---
name: litreview-workflow
description: Resume and orchestrate an existing Lit Review Construct project. Activate only when the current workspace contains `.litreview/project.yaml` or the researcher explicitly invokes Lit Review Construct. Do not activate for generic literature questions in unrelated workspaces.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: orchestration
---

# Lit Review Construct — Beta Workflow Orchestrator

## Product boundary

Help the researcher construct the literature behind a study: Research Intent, discovery, corpus refinement, Research Landscape, source-disciplined Evidence Map, Research Direction, Literature Review Blueprint, and bounded Working Draft fragments. Never turn the Working Draft into a seamless submission-ready literature review. The researcher verifies sources, chooses citations, resolves scholarly judgments, and authors final prose.

## Activation and resume

- Existing project: require `.litreview/project.yaml` in the current workspace.
- New project: initialize only after an explicit researcher request to start Lit Review Construct.
- An unspecified continuation begins with `lrc next . --json`.
- Local state is authoritative; do not reconstruct project state from chat history.
- On macOS, if a GUI host cannot resolve `lrc`, retry with `$HOME/.local/bin/lrc` before asking the researcher to repair the installation.

## Checkpoint rule

A human checkpoint is for a **genuine scholarly or corpus-strategy decision**, not routine technical work.

Stop when `human_checkpoint_required: true`. Never silently choose:
- Research Intent/scope;
- whether seed literature exists when the project asks;
- scholarly focus/refocus or scope change;
- whether discovery is sufficient when the navigator returns a decision checkpoint;
- whether to acquire the whole current Retained/Evidence Candidate/Core corpus locally or continue narrowing/continue with current coverage;
- Research Direction;
- Blueprint acceptance;
- researcher interpretation when evidence genuinely conflicts.

Do **not** create additional checkpoints for deduplication, batching, progressive triage, citation chaining, local OA-resolution batches after the researcher has chosen acquisition, Evidence Map refresh, consistency QA, claim-strength QA, reference export, Word export, or final package materialization. Follow non-human `next_action` results automatically and call `lrc next . --json` again until a genuine checkpoint or meaningful artifact is reached.

In particular, `next_action: refine` is a structural beta action: priority triage → citation chaining from core seeds → triage graph additions → rebuild narrowing review. It is not researcher approval and should run without asking the researcher to type “refine” after every round.

## Corpus refinement contract

After completed discovery/triage, do not jump directly from Retained Papers to deep evidence mapping. The required funnel for new/rebuilt landscapes is:

`Retained Papers -> Evidence Candidates -> Core Papers`

Keep the meanings distinct:
- Retained = not excluded after title/abstract triage.
- Evidence Candidate = prioritized as likely to provide useful evidence.
- Core Paper = prioritized for deep reading/evidence construction.

At each corpus checkpoint, explain the current count and full-text coverage and let the researcher choose the acquisition/refinement option returned by the runtime. Local full-text acquisition runs through the installed Python runtime and does not require one AI interaction per paper.

Ranking/relevance scoring must not reduce to citation count. Preserve research-intent relevance, evidence potential, bibliographic/source quality, theoretical/methodological importance when represented by available metadata, recency where appropriate, anchor value, and research-stream coverage.

## Researcher-facing mode

Default responses must be understandable to a researcher who does not know the runtime.

- Hide JSON, CLI commands, UUIDs/internal paper IDs, file line numbers, provider/test logs, and implementation diagnostics unless debugging is explicitly requested.
- If the researcher asks to **show** an artifact, show its substantive content first; do not replace it with a technical report describing the file.
- Explain: what completed → what it means → any genuine choice → recommendation.
- Every completion/checkpoint ends with exactly one:

  **Suggested next message:** <natural-language message>

Prefer runtime `suggested_user_message`. If absent, use a natural-language fallback. Never expose `lrc ...` as the primary suggestion.

## Evidence-state contract

Never collapse these states:

1. **Full text available** — a local PDF exists.
2. **AI checked against full text** — an Evidence record uses `source_basis=full_text`.
3. **Researcher verified** — only after explicit researcher verification.

Availability is not verification. AI checking is not researcher verification. Do not use “full-text verified” as shorthand when only state 1 or 2 is true.

Abstract/metadata-based evidence must remain provisional. Gap/absence claims from narrative progressive discovery must be bounded to the reviewed corpus unless independently verified.

## Main routing

Use the skill named by `lrc next`:
- `litreview-start` — Intent/new project;
- `litreview-seeds` — researcher papers;
- `litreview-discover` — discovery, technical refinement, Research Landscape;
- `litreview-corpus` — Retained → Evidence Candidates → Core Papers and acquisition strategy checkpoints;
- `litreview-fulltext` — lawful local OA acquisition for the selected corpus tier;
- `litreview-map` — Evidence Map;
- `litreview-direction` — candidate directions + researcher choice;
- `litreview-blueprint` — evidence-linked Blueprint;
- `litreview-draft` — bounded Working Draft;
- `litreview-workflow` with `prepare_researcher_package` — final paper/reference/Word package;
- `litreview-ai-use` — optional activity-grounded disclosure.

## Researcher package

Before final handoff, when `lrc next` returns `prepare_researcher_package`, run package preparation automatically. The researcher-facing workspace should contain:

```text
papers/
├── full_text/       # toolkit-acquired lawful OA PDFs, DOI-based names when possible
├── abstract_only/   # working references without local full text
└── user_uploads/    # researcher drop zone; do not rename/move user files
references/
├── references_used.enw
├── references_used.csv
└── references_manifest.md
outputs/
└── researcher artifacts + Word handoff
```

`.litreview/` remains machine state/cache; the researcher should not need to browse it in normal use.

Reference export must come from canonical scholarly records, not AI-written citation strings. `references_used.enw` contains only references actually used by the current Blueprint/Working Draft set, not the entire discovery corpus.

## Final handoff

At `researcher_handoff`, the package already exists. Present the researcher-facing artifacts and remaining source-verification tasks. Do not suggest re-showing the Working Draft if it was just shown. AI-use disclosure is optional and must be grounded only in recorded activity.

## Context discipline

Keep large corpora local and use bounded packets. Narrative triage is progressive, not exhaustive. Do not infer that a high untriaged percentage alone requires more discovery.
