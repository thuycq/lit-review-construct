# Literature Review Construct

**A practical toolkit for building a stronger literature review with AI — while keeping academic judgment, source verification, and final writing with the researcher.**

**Current beta:** `0.1.0b3`

Literature Review Construct (LRC) is designed for lecturers, researchers, graduate students, and research teams who want help with the most time-consuming parts of a literature review: finding papers, organizing the literature, understanding the main research streams, identifying possible research directions, and preparing a clear structure for writing.

You do **not** need to know Python or programming to use LRC.

For normal use, you mainly work inside an **AI host** such as **Codex Desktop** or **OpenCode**. LRC is installed once on your computer, while each research project stays in its own ordinary folder.

---

## What can LRC help you do?

LRC can help you:

- define the topic and scope of your literature review;
- use papers you already have as seed literature;
- search for relevant academic papers from multiple scholarly sources;
- remove duplicates and screen a large search result set;
- identify major research streams and promising areas;
- narrow a large retained corpus into **Evidence Candidates** and then **Core Papers**;
- collect lawful open-access full text using a local Python runtime;
- organize theories, methods, findings, contradictions, and evidence gaps;
- build a **Research Landscape**;
- build a source-disciplined **Evidence Map**;
- suggest possible **Research Directions** while leaving the final choice with the researcher;
- build a **Literature Review Blueprint** to guide writing;
- prepare bounded draft fragments for the researcher to review, rewrite, or reject;
- organize papers and references in the research folder;
- export working references for EndNote;
- prepare a Word **Researcher Writing Pack**;
- optionally prepare an AI-use statement based on what AI actually did in the project.

LRC is mainly designed for **narrative literature reviews** in the current beta.

### What LRC does not do

LRC is not intended to produce a complete submission-ready literature review that the researcher can use without checking.

It also does not automatically claim that a research gap is completely new, and it does not bypass publisher paywalls, logins, CAPTCHAs, or access restrictions.

The researcher remains responsible for checking important sources, making the final academic decisions, choosing citations, and writing or approving the final literature review.

---

# The easiest way to get started

For most users, the whole setup is:

1. Install one supported **AI host** — we currently recommend **Codex Desktop** or **OpenCode**.
2. Download the LRC toolkit from this GitHub repository.
3. Install LRC once on your computer.
4. Create a separate folder for your research project.
5. Open that research folder in Codex or OpenCode.
6. Tell the AI what literature review you want to build.

You do **not** need to copy LRC into every research project, and you do **not** need VS Code for normal use.

---

# Step 1 — Choose and install an AI host

An **AI host** is simply the application you open to work with LRC. The host talks with you, reads the current research folder, and calls the LRC tools when needed.

You only need **one** host.

For the current beta, the recommended starting points are:

- **Codex Desktop** — simplest if you already use ChatGPT/OpenAI and prefer a graphical desktop workflow;
- **OpenCode** — useful if you want more flexibility in choosing an AI provider/model.

## Option A — Codex Desktop

Official information:

- https://openai.com/codex/
- https://chatgpt.com/download/

### Install Codex

1. Open the official download page.
2. Download the desktop application for Windows or macOS.
3. Install it normally.
4. Sign in with your OpenAI/ChatGPT account.
5. If Codex was already open before you installed LRC, close and reopen it after the LRC installation so the new skills are visible.

### Start an LRC project in Codex

After LRC has been installed:

1. Create a normal folder for your research, for example:

```text
Documents\Research\Working Capital\
```

2. Open **that research folder** in Codex Desktop.
3. Do not open the downloaded LRC source-code folder as your research project.
4. Start with a simple prompt such as:

> Start a new Literature Review Construct project in this folder. Help me define the Research Intent before searching.

For an existing project, reopen the same research folder and say:

> Continue this Literature Review Construct project from its saved state. Do not repeat completed work.

Codex should then use the LRC skills installed on your machine and work with the local project state in that folder.

### When Codex is a good choice

Choose Codex if you want the simplest desktop experience and already have access through your OpenAI/ChatGPT setup.

---

## Option B — OpenCode

Official information:

- https://opencode.ai/docs/
- https://dev.opencode.ai/download

OpenCode is available in several forms, including desktop and terminal-based workflows. For most non-technical testers, the desktop version is the easiest starting point.

### Install OpenCode

1. Open the OpenCode download page.
2. Download the Windows or macOS version.
3. Install and open OpenCode.
4. Connect the AI provider/model you want to use.
5. If needed, use OpenCode's `/connect` command to configure a provider.
6. Close and reopen OpenCode after installing or updating LRC so the LRC commands/skills are refreshed.

### Start an LRC project in OpenCode

1. Create a separate research folder.
2. Open that folder in OpenCode.
3. Start normally by typing:

> Start a new Literature Review Construct project in this folder.

After installation, OpenCode also provides the shortcut:

```text
/lr
```

For an existing project, open the same research folder and ask LRC to continue from the saved state.

### When OpenCode is a good choice

Choose OpenCode if you want more flexibility in AI providers/models or want to use a lower-cost/free provider when available.

---

## Other AI hosts

The repository also contains adapters for several other coding-agent environments. However, **Codex Desktop and OpenCode are the recommended beta paths** because they currently receive the most hands-on testing.

If you are testing LRC for the first time, start with one of those two.

---

# Step 2 — Install Literature Review Construct

You install LRC **once on your computer**.

The installer prepares the LRC runtime and installs the skills/adapters used by the supported AI hosts.

Your research projects stay separate from the toolkit, so updating or reinstalling LRC should not require you to start your research again.

## Windows — recommended and most tested

### Easiest method: Download ZIP

1. On this GitHub page, click **Code → Download ZIP**.
2. Extract the ZIP to a permanent folder, for example:

```text
C:\Tools\literature-review-construct\
```

3. Open the extracted folder.
4. Double-click:

```text
install.bat
```

5. A terminal/PowerShell window will open and prepare the LRC runtime.
6. Wait until the installer reports that installation is complete.
7. Close the installer window.
8. Close and reopen Codex Desktop/OpenCode if either application was already running.

That is all most Windows users need to do.

### What the Windows installer does

The installer prepares the runtime needed by LRC, installs the current LRC skills/adapters, and makes the `lrc` command available to supported AI hosts.

You do **not** need to manually install Python, configure a virtual environment, or use VS Code for normal use.

### If Windows shows a security prompt

Because LRC is a small academic toolkit rather than a signed commercial application, Windows may show a security warning before running the installer.

Only continue if you downloaded the toolkit from this repository.

### If Windows installation appears to finish but Codex/OpenCode still does not see LRC

First try:

1. close Codex/OpenCode completely;
2. reopen the AI host;
3. open your research folder again;
4. ask it to start or continue Literature Review Construct.

If you recently updated the toolkit, run `install.bat` again so the installed skills match the newest repository version.

---

## macOS — beta

macOS uses a separate installer because its shell, permissions, paths, and application environment differ from Windows.

LRC does **not** require PowerShell on macOS.

### Easiest method

1. On this GitHub page, click **Code → Download ZIP**.
2. Extract the ZIP.
3. Open the extracted folder in Finder.
4. Double-click:

```text
install.command
```

5. Terminal should open automatically and run the setup.
6. Wait until the installer reports that installation is complete.
7. Close and reopen Codex/OpenCode.

The macOS installer creates a **private LRC Python 3.12 runtime** for the toolkit. Normal users do not need to install Homebrew, PowerShell, VS Code, or manually manage Python environments.

### If macOS does not open `install.command`

Open **Terminal**, move to the extracted LRC folder, and run:

```bash
bash install.command
```

If needed, you can also run:

```bash
bash install.sh
```

### If the macOS installation fails

LRC writes an installation log here:

```text
~/Library/Logs/LiteratureReviewConstruct/install.log
```

If you are reporting a Mac installation problem, this is the most useful file to send to the toolkit maintainer.

LRC also creates the launcher here:

```text
~/.local/bin/lrc
```

Sometimes a macOS graphical application may not immediately inherit the same PATH as Terminal. In that case, LRC can use the full launcher path above instead of relying on the short `lrc` command.

### macOS support status

Windows is currently the most tested platform. macOS installation is also tested in automated macOS CI, but real lecturer-machine testing is still part of the beta process.

---

# Step 3 — Create a folder for your research

Your research folder should be **separate from the LRC toolkit folder**.

For example:

```text
Documents\Research\Working Capital\
Documents\Research\Bank Efficiency\
Documents\Research\Financial Liberalization\
```

Think of the setup like this:

```text
LRC toolkit
    installed once

Research Project A
Research Project B
Research Project C
```

Each project keeps its own papers, references, outputs, and local state.

Do not create the research project inside the downloaded LRC source-code folder.

---

# Step 4 — Start your first project

Open **your research folder** in Codex or OpenCode.

Then type something simple, for example:

> Start a new Literature Review Construct project in this folder. Help me define the Research Intent before searching.

Or give the topic immediately:

> Start a new Literature Review Construct project. My topic is working capital management and firm performance. I want the literature to help me identify a useful research direction.

LRC will normally ask for a few basic pieces of information such as:

- the topic or early research question;
- the publication period;
- the language of the papers;
- country, industry, or context constraints if relevant;
- whether you already have papers.

You do not need to have a perfect research question before starting. One purpose of LRC is to let the literature help shape the research direction.

---

# If you already have papers

If you already have useful PDF papers, you can use them as **seed literature**.

Once the project has been created, place PDFs in:

```text
papers/user_uploads/
```

Then tell Codex/OpenCode:

> I added papers to `papers/user_uploads`. Use them as seed literature, preserve the original files, and do not assume they are all relevant.

LRC will inventory the files, detect duplicates/versions where possible, and use them as a starting point rather than automatically treating every uploaded paper as important.

---

# What happens after I start?

LRC keeps seven broad researcher-facing phases:

1. **Research Intent** — define what literature should be studied.
2. **Seed Literature** — inventory any papers you already have.
3. **Discovery & Corpus Refinement** — search broadly, triage results, then prioritize the retained corpus.
4. **Evidence Mapping** — organize what the important papers actually contribute.
5. **Research Direction** — compare defensible directions and let the researcher choose/refine one.
6. **Literature Review Construction** — build the review blueprint and bounded draft material.
7. **Researcher Handoff** — export the package for final source checking and researcher writing.

The toolkit tries to automate routine technical work and stop mainly when a real researcher decision is needed.

---

# How does LRC reduce a large paper set?

After search and title/abstract triage, you may still have many **Retained Papers**.

LRC now uses this funnel:

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

- **Retained Paper** — relevant enough that it should not yet be discarded.
- **Evidence Candidate** — likely to contribute useful evidence to the review.
- **Core Paper** — high-priority paper for deeper reading, evidence construction, and synthesis.

LRC does not simply keep the most-cited papers.

At the Retained and Evidence Candidate stages, it uses an explainable metadata/title/abstract ranking that considers:

- relevance to the Research Intent;
- triage priority and confidence;
- evidence potential visible in the abstract;
- bibliographic and source-provenance completeness;
- a capped citation/anchor signal;
- recency when appropriate;
- alignment with the selected research focus;
- coverage of the different research streams.

The selector first protects representation across identified research streams, then fills the remaining places using the overall ranking.

Papers that are not promoted to the next tier are **not deleted**. They remain in the project and can be revisited, downloaded, or promoted later.

This stage is still a **metadata/title/abstract prioritization**, not a full-text methodological-quality assessment.

---

# When LRC asks whether to download or refine first

At the Retained and Evidence Candidate checkpoints, LRC gives you a choice.

### Option 1 — Acquire the current corpus now

LRC tries to retrieve lawful open-access full text for the current set using the **local Python runtime**.

This gives broader immediate full-text coverage, but it may download many papers that are later deprioritized.

### Option 2 — Refine first

LRC narrows the corpus first, so fewer papers need to be acquired and deeply read later.

This is usually more efficient when the retained corpus is large, but the narrowing decision is initially based mainly on metadata/title/abstract information.

At the Core Paper stage, LRC can again ask whether you want to acquire missing Core Papers before deep evidence work or continue with the current coverage and keep missing papers as explicit verification tasks.

The final choice stays with the researcher. LRC should explain the trade-off and recommend an option based on the current paper count, full-text coverage, workload, and evidence needs.

### Does local paper acquisition use AI for every paper?

No.

The bulk acquisition process is a deterministic local-runtime task. The Python runtime performs DOI/OA lookup, download attempts, file checks, and batching without asking the AI model to browse each paper one by one.

The surrounding Codex/OpenCode conversation may still use normal model turns to start the command and inspect the result, but the download loop itself is not an AI-per-paper workflow.

---

# When will LRC ask me to decide something?

LRC tries not to interrupt you for routine technical steps.

It should mainly stop when your academic or workflow judgment matters, for example when you need to:

- confirm or change the Research Intent;
- decide whether discovery is sufficient;
- decide whether to acquire the current paper tier or refine first;
- choose among possible Research Directions;
- accept or revise the Literature Review Blueprint;
- decide how to handle important missing full text;
- verify important sources before final writing.

You should not need to approve every search batch, duplicate removal, file rename, download attempt, or other mechanical step.

---

# Where are my results saved?

Everything stays inside the research folder.

A typical project gradually looks like this:

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

### `papers/`

Your paper library, including papers you supplied and full text collected legally by the toolkit.

### `references/`

Working reference files, including EndNote-compatible export where available.

### `outputs/`

Researcher-facing outputs such as the Research Landscape, Evidence Map, Research Direction, Literature Review Blueprint, bounded working draft, and Researcher Writing Pack.

### `.litreview/`

Internal project state used by LRC to continue the project without rebuilding it from the chat history.

You normally do not need to edit this folder manually.

---

# How do I continue the project another day?

Open the **same research folder** again in Codex/OpenCode and say:

> Continue this Literature Review Construct project from its saved state. Do not repeat completed work. Continue until you need a research decision from me.

LRC saves project state locally, so you should not need to restart from the beginning.

You can also move between supported AI hosts while keeping the same research folder, although cross-host behavior may still vary slightly during beta testing.

---

# Do I need to download every paper?

No.

For example, a project might look like:

```text
1,838 indexed records
145 Retained Papers
~60 Evidence Candidates
~25 Core Papers
```

These numbers are examples, not fixed quotas.

The goal is not to maximize the number of PDFs. The goal is to build a literature base that adequately covers the important research streams and provides enough strong evidence for the review you want to write.

A researcher who wants maximum local coverage can acquire the full retained set. A researcher who wants a smaller workload can refine first and acquire a higher-priority corpus later.

---

# Full-text papers and source verification

LRC can automatically look for legally available open-access full text.

If a paper cannot be downloaded automatically, LRC may ask you to obtain it through:

- your university/institutional library;
- an author-provided copy;
- another lawful source;
- a PDF you already have.

LRC does not bypass paywalls or publisher access controls.

LRC also deliberately distinguishes these states:

1. **Full text available** — a PDF exists locally.
2. **AI checked against full text** — relevant evidence was actually checked against that PDF.
3. **Researcher verified** — the researcher explicitly verified it.

A downloaded PDF is therefore **not automatically a verified paper**.

---

# Updating or reinstalling LRC

Your research projects are separate from the toolkit, so updating LRC should not require you to restart a project.

## Windows

After downloading or pulling a newer version, run:

```text
install.bat
```

again.

This refreshes the installed runtime/skills used by your AI hosts.

To uninstall LRC, run:

```text
uninstall.bat
```

The uninstall process is designed not to delete your separate research folders, papers, or outputs.

## macOS

After updating the toolkit folder, run again:

```bash
bash install.command
```

or double-click `install.command` again.

Your existing research folders remain separate.

---

# Optional: command-line use for testing or troubleshooting

**Most lecturers do not need this section for normal use.**

LRC has a local command-line tool for mechanical operations and diagnostics.

Useful commands include:

```text
lrc version
lrc next .
lrc corpus status .
lrc fulltext status .
lrc doctor .
```

Corpus controls include:

```text
lrc corpus decide . --stage retained --action acquire
lrc corpus decide . --stage retained --action refine
lrc corpus rank . --to evidence
lrc corpus rank . --to core
lrc fulltext acquire . --tier retained
lrc fulltext acquire . --tier evidence
lrc fulltext acquire . --tier core
```

These are implementation controls. The normal researcher experience should remain conversational inside Codex/OpenCode.

---

# Frequently asked questions

### Do I need to know programming?

No. The normal workflow is conversational.

### Do I need Git?

No. You can download the repository as a ZIP file.

### Do I need VS Code?

No.

### Do I need to install Python manually?

For normal installation, no. The installer prepares the runtime used by LRC. On macOS, the installer creates a private Python 3.12 runtime for the toolkit.

### Do I need an AI subscription?

You need access to at least one AI model/provider through the host you choose. Codex uses your OpenAI/ChatGPT setup; OpenCode can connect to different providers/models.

### Does LRC write the final literature review for me?

No. It helps construct the evidence base, research landscape, research direction, review structure, and bounded draft material. Final scholarly verification and writing remain with the researcher.

### Can I use my own papers?

Yes. Add them to `papers/user_uploads/` after creating the project.

### Do I need every paper in full text?

No. Full-text coverage should be strongest for the papers and claims that matter most to the review.

### Can I stop and continue later?

Yes. Reopen the same research folder and ask LRC to continue from its saved state.

### Can I use a different AI host later?

The project state is stored locally, so supported hosts can work from the same research folder. Cross-host behavior is still being tested during beta.

---

# Current beta notes

- **Primary review type:** narrative literature review.
- **Windows:** currently the most tested and stable installation path.
- **macOS:** supported in beta with a separate native installer and private runtime; real-machine lecturer testing is still ongoing.
- **Recommended AI hosts:** Codex Desktop and OpenCode.
- **Corpus refinement:** Retained Papers → Evidence Candidates → Core Papers before deep evidence work.
- **Local acquisition:** bulk full-text acquisition is performed by the local Python runtime rather than repeated AI browsing actions.
- **Final responsibility:** the researcher verifies sources, resolves scholarly judgments, chooses citations, and writes/approves final prose.

This repository is currently intended for small-group academic testing rather than commercial deployment.

---

# More detailed documentation

- [`QUICK_START.md`](QUICK_START.md) — practical start/resume templates and additional usage
- [`BETA_READINESS.md`](BETA_READINESS.md) — beta behavior and testing notes

---

## License

MIT
