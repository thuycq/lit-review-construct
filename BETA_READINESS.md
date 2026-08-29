# Lit Review Construct 0.1.0b1 — Beta Readiness

This beta is the first build intended for a small real-user test after an end-to-end OpenCode benchmark. The benchmark validated the core research logic but exposed product/UX problems that are explicitly addressed here.

## Beta acceptance target

A beta tester should be able to:

1. install once on Windows;
2. open a dedicated research folder in Codex Desktop or OpenCode;
3. explicitly start/resume an LRC project without the toolkit activating in unrelated workspaces;
4. move through Research Intent → Discovery → Research Landscape → lawful OA coverage → Evidence Map → Research Direction → Blueprint → bounded Working Draft → researcher package;
5. make scholarly decisions without being asked to approve routine technical operations;
6. receive researcher-facing artifacts without reading CLI/JSON/internal IDs;
7. find downloaded papers, abstract-only working references, EndNote import, and the Researcher Writing Pack in obvious project folders;
8. use the Word Writing Pack to continue writing without needing to understand workflow internals;
9. retain clear source/evidence verification boundaries and final researcher authorship.

## Benchmark findings incorporated

### Checkpoint reduction

The benchmark repeatedly stopped for `refine` even after the researcher had already selected a focus. Beta treats bounded refinement as technical work. Runtime may automatically run up to three citation-refinement rounds and stop earlier on low/sharply declining marginal graph gain. High untriaged percentage alone does not force more refinement.

### Researcher-facing mode

Normal responses should hide implementation logs, JSON, CLI commands, UUIDs, internal paper IDs, line numbers and test details. A checkpoint should state what completed, what it means, the genuine scholarly choices, a recommendation, and exactly one natural-language Suggested next message.

Artifact requests show substantive artifact content first rather than a developer report about the file.

### Researcher Writing Pack

The benchmark showed that a Word handoff can still be technically correct while being poor for an end user if it simply concatenates workflow artifacts and audit detail.

Beta therefore exports `outputs/LitReview_Researcher_Writing_Pack.docx` as a **writing aid**, not an audit report. It contains only what a researcher needs to finish the literature review:

1. research focus and selected direction;
2. accepted literature-review structure and section purposes;
3. actual Working Draft fragments;
4. researcher tasks/decisions and source-verification checklist;
5. cross-section/final writing checklist;
6. working references and pointers to EndNote/paper folders.

The Word pack must not expose paper/evidence IDs, `.litreview` state paths, provider logs, test output, JSON fields, technical provenance, or the optional AI-use statement. Those remain separate for audit/debug use.

### Evidence-state safety

Three states are distinct:

- Full text available;
- AI checked against full text (`source_basis=full_text`);
- Researcher verified (explicit human verification only).

A renderer/host must never rename availability or AI checking as researcher verification.

### Claim-strength safety

Abstract/provisional support may not be rendered as established/proven/confirmed evidence. Universal absence/gap claims must be bounded to the reviewed corpus in a narrative/progressive review unless independently verified. Working Draft save runs mechanical QA for common regressions.

### Paper library

Researcher-facing structure:

```text
papers/
├── full_text/
├── abstract_only/
└── user_uploads/
```

Toolkit OA PDFs prefer DOI-based Windows-safe names. User-uploaded files are not renamed/moved automatically. Legacy cache remains internal provenance only.

### OA coverage

The earlier 30-paper acquisition pass looked like a product cap. Beta makes `max-papers` a batch size and advances through retained literature via a resolution cursor. Closed/unresolved literature remains in the project.

### Reference handoff

Final package includes:

```text
references/
├── references_used.enw
├── references_used.csv
└── references_manifest.md
```

EndNote export is generated from canonical scholarly metadata rather than draft citation strings.

### Suggestion engine

Suggested next messages are natural language, context-aware, and forward-only. A final handoff should not suggest re-showing an artifact that was just shown. A saturated discovery checkpoint may recommend finish while preserving researcher agency.

### State/data resilience

Malformed JSONL lines should not strand a project. Partial provider success is preserved when another provider fails/rate-limits.

## Intended human checkpoints

The beta aims for a small number of substantive checkpoints:

1. Research Intent / seed decision as needed;
2. Discovery scholarly focus/scope decision and later explicit finish decision (technical refine rounds happen between these without extra clicks);
3. Research Direction selection;
4. Blueprint acceptance;
5. Researcher handoff and subsequent human verification/authorship.

Not every implementation action is a human checkpoint.

## Known beta limitations

- Narrative review only; no PRISMA/systematic-review completeness claims.
- Scholarly provider APIs can rate-limit or return incomplete metadata; partial success is preserved but coverage is never guaranteed exhaustive.
- OA resolver uses lawful public/provider-reported locations only. Institutional subscription access is not automated.
- Canonical metadata may still require researcher correction before final reference submission; `.enw` is an import handoff, not a guarantee that every publisher field is perfect.
- Researcher verification is currently a human responsibility; beta prevents false verification labels but does not yet provide a rich per-claim verification UI.
- Codex/OpenCode hosts can differ in how aggressively they auto-select globally installed skills; activation gating is encoded in project/skill/wrapper contracts but should be explicitly tested on both hosts.
- The Blueprint/Working Draft remain construction artifacts, not submission-ready prose.

## Beta tester observations to collect

Prioritize behavioral findings rather than low-level logs:

- Did LRC activate only in the intended workspace?
- Did any technical step unnecessarily ask the researcher to decide/click?
- Did Discovery stop/refocus at a sensible time?
- Were provider failures recoverable?
- Were Research Landscape / Direction / Blueprint choices understandable?
- Did any abstract-only claim sound more certain than its source basis?
- Did any output misuse “verified”?
- Were downloaded PDFs easy to find and sensibly named?
- Did `references_used.enw` import correctly into EndNote?
- Could the researcher use the Word Writing Pack to continue writing without understanding LRC internals?
- Did the Word pack contain any technical/debug material that did not help writing?
- Was the final package understandable without opening `.litreview/`?
- Did any Suggested next message loop backward or expose CLI?
- Did the Working Draft remain bounded enough that final authorship clearly stayed with the researcher?

## Release gate

Before merging beta to `main`:

- version synchronized across package, installer and README;
- Windows + Ubuntu CI green;
- beta regression tests green;
- Researcher Writing Pack regression test confirms technical internals are excluded;
- OpenCode `/lr` activation/researcher-mode contract installed;
- package command available;
- no known state-machine infinite loop in discovery refinement or OA coverage.
