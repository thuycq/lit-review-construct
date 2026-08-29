---
description: Resume or continue the current Lit Review Construct project only when the workspace is an LRC project or the researcher explicitly invokes /lr
---

Use the installed `litreview-workflow` skill and the authoritative local project state.

Activation gate:
- Continue only when the current workspace contains `.litreview/project.yaml`, or when the researcher explicitly asks to start Lit Review Construct.
- Do not activate LRC for generic literature questions in unrelated workspaces.

Run `lrc next . --json`, then follow the returned specialized skill and structural next action. Do not reconstruct project state from chat history.

## Researcher-facing mode (default)

Treat runtime JSON, CLI commands, provider diagnostics, internal IDs, file line numbers, test names, and implementation logs as hidden technical detail. Use them to act, not as the normal response.

For non-human structural actions, continue automatically through the technical work until either:
1. a genuine researcher decision is required, or
2. a meaningful researcher-facing artifact/result is ready.

Do not create micro-checkpoints for deduplication, batching, progressive triage, citation chaining, OA resolution, evidence refresh, consistency QA, package preparation, or formatting.

When `human_checkpoint_required: true`, stop before recording the decision. Present only:
- what was completed,
- what it means for the research,
- the small set of genuine scholarly choices,
- the recommendation and why,
- exactly one natural-language `**Suggested next message:** ...`.

When the researcher asks to *show* an artifact, show its substantive content (or a readable section-by-section rendering) first. Do not replace the artifact with a developer report describing file paths and JSON fields.

Evidence wording must preserve three distinct states:
- **Full text available**: a local PDF exists.
- **AI checked against full text**: the evidence record has `source_basis=full_text`.
- **Researcher verified**: only after explicit researcher verification. Never rename either of the first two states as researcher-verified.

Preserve the product boundary: help construct literature, evidence, research direction, Blueprint, and bounded Working Draft fragments; do not write a complete final literature review for direct submission.
