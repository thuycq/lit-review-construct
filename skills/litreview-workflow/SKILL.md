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

Help the researcher construct the literature behind a study: Research Intent, discovery, Research Landscape, source-disciplined Evidence Map, Research Direction, Literature Review Blueprint, and bounded Working Draft fragments. Never turn the Working Draft into a seamless submission-ready literature review. The researcher verifies sources, chooses citations, resolves scholarly judgments, and authors final prose.

## Activation and resume

- Existing project: require `.litreview/project.yaml` in the current workspace.
- New project: initialize only after an explicit researcher request to start Lit Review Construct.
- An unspecified continuation begins with `lrc next . --json`.
- Local state is authoritative; do not reconstruct project state from chat history.

## Checkpoint rule

A human checkpoint is for a **genuine scholarly decision**, not a technical operation.

Stop when `human_checkpoint_required: true`. Never silently choose:
- Research Intent/scope;
- whether seed literature exists when the project asks;
- scholarly focus/refocus or scope change;
- whether discovery is sufficient when the navigator returns a decision checkpoint;
- Research Direction;
- Blueprint acceptance;
- researcher interpretation when evidence genuinely conflicts.

Do **not** create checkpoints for deduplication, batching, progressive triage, citation chaining, OA resolution, Evidence Map refresh, consistency QA, claim-strength QA, reference export, Word export, or final package materialization. Follow non-human `next_action` results automatically and call `lrc next . --json` again until a genuine checkpoint or meaningful artifact is reached.

In particular, `next_action: refine` is a structural beta action: priority triage → citation chaining from core seeds → triage graph additions → rebuild narrowing review. It is not researcher approval and should run without asking the researcher to type “refine” after every round.

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
- `litreview-fulltext` — lawful OA coverage;
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
