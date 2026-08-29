# Lit Review Construct 0.1.0b2 — Beta Readiness

This beta extends the first end-to-end OpenCode benchmark into a **cross-platform, multi-host beta** while preserving the same local-first research workflow and product boundary.

## Beta acceptance target

A beta tester should be able to:

1. install once on **Windows or macOS**;
2. use at least one supported AI host: Codex, OpenCode, Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot, or Cline;
3. explicitly start/resume an LRC project without the toolkit activating in unrelated workspaces;
4. move through Research Intent → Discovery → Research Landscape → lawful OA coverage → Evidence Map → Research Direction → Blueprint → bounded Working Draft → researcher package;
5. make scholarly decisions without being asked to approve routine technical operations;
6. receive researcher-facing artifacts without reading CLI/JSON/internal IDs;
7. find downloaded papers, abstract-only working references, EndNote import, and the Researcher Writing Pack in obvious project folders;
8. switch supported hosts while using the same local research folder and continue from authoritative saved state;
9. retain clear source/evidence verification boundaries and final researcher authorship.

## Host architecture

Lit Review Construct core is host-independent. Host adapters only provide discovery/invocation instructions.

Canonical skills are installed into compatible Agent Skills locations. Current adapters cover:

- Codex;
- OpenCode;
- Claude Code;
- Cursor;
- Windsurf;
- GitHub Copilot;
- Cline;
- Gemini CLI (custom command + gated GEMINI.md context).

Global installation must never mean global activation. Every host adapter must activate only when `.litreview/project.yaml` exists or the researcher explicitly asks to start/use Lit Review Construct.

## Benchmark findings incorporated

### Checkpoint reduction

Technical refinement after researcher focus selection is automatic and bounded. High untriaged percentage alone does not force endless refine loops.

### Researcher-facing mode

Normal responses hide implementation logs, JSON, CLI commands, UUIDs, internal paper IDs, line numbers and test details. Artifact requests show substantive artifact content first.

### Researcher Writing Pack

`outputs/LitReview_Researcher_Writing_Pack.docx` is a writing aid rather than an audit report. It contains research focus, accepted structure, actual Working Draft fragments, researcher tasks/decisions, source-verification checklist, final writing checklist and working references.

It must not expose paper/evidence IDs, `.litreview` paths, provider logs, test output, JSON fields, technical provenance, or the optional AI-use statement.

### Evidence-state safety

Three states remain distinct:

- Full text available;
- AI checked against full text (`source_basis=full_text`);
- Researcher verified (explicit human verification only).

### Claim-strength safety

Abstract/provisional support may not be rendered as established/proven/confirmed evidence. Narrative-review absence/gap claims remain corpus-bounded unless independently verified.

### Paper library

```text
papers/
├── full_text/
├── abstract_only/
└── user_uploads/
```

Toolkit OA PDFs use stable identifier-based names. Researcher files are not silently renamed/moved.

### OA coverage

`max-papers` is a technical batch size rather than a product cap. OA coverage advances through retained literature and preserves unresolved/closed records.

### Reference handoff

```text
references/
├── references_used.enw
├── references_used.csv
└── references_manifest.md
```

EndNote export uses canonical scholarly metadata rather than AI-written citation strings.

## Intended human checkpoints

1. Research Intent / seed decision as needed;
2. Discovery focus/scope decision and later explicit finish decision;
3. Research Direction selection;
4. Blueprint acceptance;
5. Researcher handoff and subsequent human verification/authorship.

Technical batching, dedupe, triage, citation chaining, OA resolution, evidence refresh, QA, formatting and packaging are not researcher checkpoints.

## Known beta limitations

- Narrative review only; no PRISMA/systematic-review completeness claims.
- Scholarly providers may rate-limit or return incomplete metadata.
- OA retrieval uses lawful public/provider-reported locations only.
- Canonical bibliographic metadata can still require researcher correction.
- Researcher verification remains a human responsibility.
- Output quality varies across AI hosts/models.
- Multi-host behavior is newly broadened in `0.1.0b2`; host-specific edge cases are expected during beta.
- Cline Skills is an experimental Cline feature and must be enabled by the user.
- macOS installation is new in `0.1.0b2`; installation and path behavior should be tested on both Apple Silicon and Intel Macs where possible.
- The Blueprint/Working Draft remain construction artifacts, not submission-ready prose.

## Beta tester observations to collect

For every test, record operating system + AI host. Prioritize:

- Did installation succeed without manual Python setup?
- Did LRC activate only in the intended workspace?
- Did a host discover the LRC skills/shortcut after restart?
- Could the same research folder resume correctly after changing hosts?
- Did technical steps unnecessarily ask the researcher to decide/click?
- Did Discovery stop/refocus sensibly?
- Were provider failures recoverable?
- Were Landscape / Direction / Blueprint outputs understandable?
- Did any abstract-only claim sound too certain?
- Did any output misuse “verified”?
- Were PDFs easy to find and sensibly named?
- Did `references_used.enw` import correctly into EndNote?
- Could the researcher use the Word Writing Pack without understanding LRC internals?
- Did Suggested next messages move forward?
- Did the Working Draft preserve final researcher authorship?

## Release gate

Before merging `0.1.0b2` to `main`:

- version synchronized across package, Windows installer, macOS installer and README;
- **Windows + macOS + Ubuntu CI green**;
- multi-host adapter regression tests green;
- `bash -n install.sh` passes on macOS CI;
- Windows installer PowerShell syntax passes;
- OpenCode, Claude Code and Gemini `/lr` adapter files are present;
- portable/global skill roots are covered for Cursor, Windsurf, GitHub Copilot and Cline;
- Researcher Writing Pack regression remains green;
- no known state-machine infinite loop in discovery refinement or OA coverage.
