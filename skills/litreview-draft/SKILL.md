---
name: litreview-draft
description: Build a researcher-editable literature-review working draft after the researcher has accepted the Literature Review Blueprint. Use when the workflow should turn the accepted argument architecture into evidence-linked draft fragments without presenting them as submission-ready final prose.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: researcher-handoff
---

# Lit Review Construct — Researcher Working Draft

Use this skill only after the Literature Review Blueprint is explicitly accepted.

## Product purpose

The toolkit should not stop at an outline. It should give the researcher a **working draft to develop**. This artifact may contain researcher-editable prose across every accepted Blueprint section, but it must remain traceable to evidence and visibly preserve verification work.

The working draft is not a claim that the literature review is finished, submission-ready, citation-complete, or fully verified.

## Workflow

1. Run:

   `lrc draft prepare . --json`

2. Read `.litreview/packets/working_draft.json`.
3. Cover every accepted Blueprint section.
4. For each section, produce one to five bounded draft fragments. Each fragment should:
   - advance a specific accepted argument;
   - remain concise enough for the researcher to rewrite deliberately;
   - cite the supplied `paper_ids` and `evidence_ids` in the structured submission;
   - preserve association/causality boundaries;
   - include explicit verification notes when evidence is abstract-only, uncertain, or missing full text;
   - identify researcher decisions/tasks that cannot be delegated safely.
5. Do not introduce papers/evidence outside the section's accepted Blueprint anchors unless the researcher has asked to revise the Blueprint first.
6. Save `.litreview/packets/working_draft_submission.json`, then run:

   `lrc draft save . --input .litreview/packets/working_draft_submission.json`

7. Present the resulting `outputs/06b_literature_review_working_draft.md` as a **working draft**, with the remaining verification tasks summarized.

## What good draft support looks like

Good assistance can include:
- a coherent provisional narrative for each section;
- argument-level synthesis across multiple papers rather than paper-by-paper summaries;
- provisional transitions;
- explicit citation/evidence anchors;
- visible `VERIFY BEFORE USE` flags;
- notes showing where researcher voice, interpretation, source checking, or construct decisions remain necessary.

## Boundary

Do not:
- label the artifact a final/submission-ready literature review;
- invent citations or source findings;
- remove uncertainty to make prose sound stronger;
- turn abstract-based evidence into detailed full-text claims;
- hide that AI produced draft fragments;
- bypass the researcher's responsibility to rewrite, verify, select final citations, and approve the final prose.

The activity log records this as `draft_fragment`, so the optional AI-use statement can accurately disclose draft assistance if it actually occurred.

## Word handoff

After the working draft exists, the researcher can ask for Word export. Use:

- `lrc export docx . --artifact working-draft`
- `lrc export docx . --artifact handoff`

Markdown/JSON remains the authoritative project state. Word is an editable presentation/export artifact.
