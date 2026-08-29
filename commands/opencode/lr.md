---
description: Resume or continue the current Lit Review Construct project
---

Use the installed `litreview-workflow` skill and the authoritative local project state.

First run:

`lrc next . --json`

Then follow the returned specialized skill and structural next action. Do not reconstruct project state from chat history. If the result says `human_checkpoint_required: true`, stop and ask the researcher for that decision before recording or advancing anything.

Preserve the product boundary: help construct the literature, evidence, research direction, and Literature Review Blueprint; do not write a complete final literature review for direct submission.
