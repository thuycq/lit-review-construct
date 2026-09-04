# Literature Review Construct

**Current beta:** `0.1.0b3`

Literature Review Construct (LRC) is a local-first toolkit that helps researchers move from an early research idea to a structured literature landscape, evidence map, research direction, and literature-review blueprint.

It is designed for researchers, lecturers, and students who want AI assistance without handing the entire literature-review process over to AI.

LRC does **not** treat an AI-generated review as the final scholarly product. The researcher remains responsible for checking sources, choosing interpretations and citations, and writing/approving the final literature-review text.

## What LRC helps with

LRC can help you:

- define the Research Intent and literature scope;
- add papers you already have;
- search scholarly sources and build a broad literature corpus;
- remove duplicates and progressively triage search results;
- organize the literature into research streams;
- narrow a large retained corpus into higher-priority Evidence Candidates and Core Papers;
- acquire lawful open-access full text with a **local Python runtime** rather than making the AI download papers one by one;
- build a source-disciplined Evidence Map;
- develop candidate Research Directions while keeping the final decision with the researcher;
- construct an evidence-linked Literature Review Blueprint;
- prepare bounded working-draft fragments for the researcher to use, revise, or reject;
- export the paper library, references, Word handoff, and an optional AI-use statement.

## The workflow

LRC keeps seven broad researcher-facing phases, while the discovery phase now contains a dedicated corpus-refinement funnel.

1. **Research Intent** — clarify the topic, question, period, language, and scope.
2. **Seed Literature** — add and inventory papers you already have.
3. **Discovery & Corpus Refinement** — search, triage, then narrow the literature from Retained Papers to Evidence Candidates and Core Papers.
4. **Evidence Mapping** — extract and organize what the important papers actually contribute.
5. **Research Direction** — compare defensible research directions and let the researcher choose/refine one.
6. **Literature Review Construction** — build the evidence-linked literature-review blueprint and bounded draft fragments.
7. **Researcher Handoff** — export the research package for final source checking and researcher writing.

### Retained Papers → Evidence Candidates → Core Papers

After title/abstract triage, LRC no longer sends every retained paper directly into deep evidence work.

```text
Indexed records
      ↓
Retained Papers
      ↓
Evidence Candidates
      ↓
Core Papers
      ↓
Evidence extraction and synthesis
```

These labels mean different things:

- **Retained Paper** — relevant enough that it should not yet be excluded.
- **Evidence Candidate** — likely to contribute useful evidence to the review.
- **Core Paper** — high-priority paper for deeper reading, evidence construction, and synthesis.

The ranking is not a simple citation leaderboard. LRC considers research relevance, triage priority/confidence, evidence potential, bibliographic/source quality, recency when appropriate, capped citation/anchor value, selected-focus alignment, and coverage of the different research streams.

### How does LRC narrow the corpus?

LRC does not remove papers simply because they have fewer citations, and it does not arbitrarily keep a fixed number of papers. At the Retained and Evidence Candidate stages, LRC uses an explainable title/abstract/metadata ranking that considers relevance to the Research Intent, triage priority and confidence, evidence potential visible in the abstract, bibliographic and source-provenance information, a capped citation/anchor signal, recency, alignment with the selected research focus, and representation across identified research streams.

The selector first protects coverage across meaningful research streams, then fills the remaining places using the overall ranking. Papers that are not promoted to the next tier are **not deleted**: they remain indexed in the project and can be revisited, downloaded, or promoted later.

This narrowing step should be interpreted as **prioritization**, not as a full-text quality assessment. At this stage LRC has not yet established journal prestige, methodological rigor, causal credibility, risk of bias, or study validity from full text. Those judgments belong to later evidence work.

### A download choice at every narrowing checkpoint

At each corpus level, LRC shows the researcher the current number of papers and full-text coverage, then offers a choice.

For Retained Papers and Evidence Candidates you can either:

- **Acquire the whole current corpus locally**, then continue narrowing; or
- **Continue narrowing first**, so fewer papers need to be acquired/read later.

For Core Papers you can either:

- **Acquire all Core Papers locally before evidence work**; or
- continue with the full text already available and keep missing papers as explicit verification tasks.

These choices have different trade-offs. **Acquire now** gives broader immediate full-text coverage, but it may download many papers that are later deprioritized. **Refine first** reduces acquisition and reading workload, but it accepts a metadata/title/abstract-based prioritization step before full text is available. LRC should explain this difference and recommend an option based on the current corpus size, full-text coverage, evidence needs, and workload while leaving the final decision with the researcher.

The important point is that full-text acquisition is a **local runtime operation**. The Python runtime performs the batch work; Codex/OpenCode does not need to spend a separate AI interaction searching and downloading every paper.

LRC only retrieves lawful open/public copies and does not bypass paywalls, logins, CAPTCHAs, or access controls.

---

# Installation

You normally install LRC once. Each research project then lives in its own ordinary folder on your computer.

You do **not** need VS Code to use LRC.

## Windows — tested

1. Download the repository as a ZIP from GitHub and extract it.
2. Open the extracted folder.
3. Double-click **`install.bat`**.
4. Wait until the installer reports that installation is complete.
5. Close and reopen Codex Desktop/OpenCode if it was already running.

The installer prepares the runtime and installs the LRC skills/adapters used by supported AI hosts.

## macOS — beta

The macOS installer is separate from the Windows installer. LRC uses the same Python core, but macOS gets its own native bootstrap rather than trying to imitate PowerShell/Windows behavior.

### Normal installation

1. Download the repository ZIP and extract it.
2. Open the extracted folder.
3. Double-click **`install.command`**.
4. Terminal should open and run the setup automatically.
5. Close and reopen Codex/OpenCode after installation.

The macOS installer creates a **private LRC Python 3.12 runtime**. You do not need to install or learn Homebrew, PowerShell, VS Code, or manually manage Python environments for normal use.

### If macOS does not open `install.command`

Open Terminal, go to the extracted LRC folder, and run:

```bash
bash install.command
```

You can also run:

```bash
bash install.sh
```

If installation fails, LRC writes a diagnostic log here:

```text
~/Library/Logs/LiteratureReviewConstruct/install.log
```

That file is the most useful thing to send when reporting a Mac installation problem.

LRC also creates the launcher at:

```text
~/.local/bin/lrc
```

If a macOS GUI AI application does not immediately see the normal `lrc` command, LRC can use that full launcher path instead.

**Support status:** Windows is currently the most tested platform. macOS support is beta and is being validated on real lecturer machines as well as macOS CI runners.

---

# Which applications can I use?

The toolkit is designed primarily around **Codex Desktop** and **OpenCode**. Adapter files are also included for several other coding-agent hosts.

For ordinary use, open a dedicated research folder in the AI application and ask it to start or continue Literature Review Construct.

Examples:

> Start a new Literature Review Construct project in this folder.

or, for an existing project:

> Continue my Literature Review Construct project.

OpenCode also provides the `/lr` shortcut after installation.

## Your project stays in the research folder

A project normally looks like this:

```text
My Research Project/
├── papers/
│   ├── full_text/
│   ├── abstract_only/
│   └── user_uploads/
├── references/
├── outputs/
└── .litreview/
```

The `.litreview` folder stores local machine state so the project can be resumed without rebuilding it from the chat history.

The researcher-facing outputs remain in normal folders such as `papers/`, `references/`, and `outputs/`.

---

# Do I need to download every paper?

No.

This is exactly why the corpus-refinement checkpoints exist.

For example, a project might have:

```text
1,838 indexed records
145 Retained Papers
~60 Evidence Candidates
~25 Core Papers
```

Those numbers are examples, not fixed quotas. LRC adapts the target size to the corpus and tries to preserve meaningful research-stream coverage rather than blindly selecting the top N papers.

A researcher who wants maximum local coverage can acquire all 145 retained papers. A researcher who wants a smaller, higher-priority workload can narrow to Evidence Candidates or Core Papers first.

## Does local acquisition use my AI quota?

The acquisition command itself runs in the local Python runtime and does not call an AI model once per paper.

AI is reserved for work where judgment is useful, such as:

- relevance interpretation;
- difficult screening decisions;
- synthesis across papers;
- identifying contradictions and research streams;
- evidence reasoning;
- research-direction development;
- literature-review architecture.

Mechanical work such as DOI resolution, OA checks, PDF downloading, file inventory, and batching is pushed into the local runtime where possible.

---

# Source and evidence discipline

LRC deliberately distinguishes three states:

1. **Full text available** — the PDF exists locally.
2. **AI checked against full text** — the relevant evidence was actually read/checked against that PDF.
3. **Researcher verified** — the researcher explicitly verified it.

A downloaded PDF is therefore **not automatically a verified paper**.

Metadata/abstract-based evidence remains provisional until stronger source checking is available.

---

# Optional command-line use

Most lecturers should not need to type these commands because the AI host runs them for the researcher. They are useful for testing or troubleshooting.

```text
lrc version
lrc next .
lrc corpus status .
lrc fulltext status .
lrc doctor .
```

Examples of the new corpus controls:

```text
lrc corpus decide . --stage retained --action acquire
lrc corpus decide . --stage retained --action refine
lrc corpus rank . --to evidence
lrc corpus rank . --to core
lrc fulltext acquire . --tier retained
lrc fulltext acquire . --tier evidence
lrc fulltext acquire . --tier core
```

Again, these commands are implementation controls. The normal researcher experience should remain conversational.

---

# Current beta notes

- **Windows:** tested and currently the most stable path.
- **macOS:** beta; new native installer uses `install.command`, a private Python runtime, executable launcher, PATH setup, install manifest, and diagnostic log.
- **Corpus refinement:** new projects/rebuilt landscapes use Retained Papers → Evidence Candidates → Core Papers before deep evidence work.
- **Local acquisition:** researcher can decide when to acquire the current corpus; the batch is executed by the local Python runtime rather than by repeated AI browsing actions.
- **Final scholarly responsibility:** the researcher verifies sources, resolves scholarly judgments, chooses citations, and authors/approves final prose.

This repository is currently intended for small-group academic testing rather than commercial deployment.
