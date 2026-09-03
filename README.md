# Literature Review Construct

**A practical toolkit to help researchers build a stronger literature review with AI — while keeping the final academic judgment and writing with the researcher.**

**Current beta:** `0.1.0b3`

Literature Review Construct (LRC) is designed for lecturers, researchers, graduate students, and research teams who want help with the most time-consuming parts of a literature review: finding papers, organizing the literature, understanding the main research streams, identifying possible research directions, and preparing a clear structure for writing.

You do **not** need to know Python or programming to use LRC.

The easiest way to use it is with **Codex** or **OpenCode** on your computer.

---

## What can LRC help you do?

LRC can help you:

- define the topic and scope of your literature review;
- search for relevant academic papers;
- use papers you already have as starting material;
- remove duplicates and prioritize more useful studies;
- follow references and citations from important papers;
- collect open-access full text when it is legally available;
- identify major research streams, theories, methods, findings, and disagreements;
- build a **Research Landscape** showing how the literature is organized;
- suggest possible **Research Directions** for your study;
- build a **Literature Review Blueprint** to guide your writing;
- prepare short draft fragments for you to review and rewrite;
- organize papers and references in your research folder;
- export references for EndNote;
- prepare a Word **Researcher Writing Pack**;
- optionally prepare an AI-use statement based on what AI actually did in the project.

LRC is mainly designed for **narrative literature reviews** in the current beta.

### What LRC does not do

LRC is not intended to write a complete submission-ready literature review for you.

It also does not automatically claim that a research gap is completely new, and it does not bypass publisher paywalls, logins, CAPTCHAs, or access restrictions.

The researcher remains responsible for checking important sources, making the final academic decisions, and writing or approving the final literature review.

---

# The easiest way to get started

For most users, the whole setup is simply:

1. Install **Codex** or **OpenCode**.
2. Download LRC.
3. Install LRC once on your computer.
4. Create a separate folder for your research project.
5. Open that research folder in Codex or OpenCode.
6. Tell the AI what literature review you want to build.

You do not need to copy LRC into every research project.

---

# Step 1 — Install an AI app

You only need **one** AI app. For the current beta, we recommend starting with **Codex** or **OpenCode**.

## Option A — Codex

Codex is available on Windows and macOS through OpenAI's desktop experience.

Official information:

- https://openai.com/codex/
- https://chatgpt.com/download/

### To install

1. Open the official download page above.
2. Download the desktop app for your operating system.
3. Install it normally.
4. Sign in with your ChatGPT/OpenAI account.

If you already use Codex on your computer, you can skip this step.

### Why choose Codex?

Codex is the simplest option if you already have a ChatGPT account and want to work with your research folder through a graphical desktop app.

---

## Option B — OpenCode

OpenCode is an open-source AI agent available as a desktop app, terminal app, and IDE extension.

Official information and downloads:

- https://opencode.ai/docs/
- https://dev.opencode.ai/download

### To install the desktop version

1. Open the OpenCode download page.
2. Download the Windows or macOS version.
3. Install and open OpenCode.
4. Connect the AI provider/model you want to use.

Inside OpenCode, the `/connect` command can be used to configure a provider.

OpenCode supports different AI providers, so it can be useful if you want more flexibility in model choice or cost.

---

## Other supported apps

LRC also includes support for several other AI environments, including:

- Claude Code;
- Cursor;
- Windsurf;
- Gemini CLI;
- GitHub Copilot;
- Cline.

However, **Codex and OpenCode are the recommended starting points for beta testing** because they have received the most hands-on testing in our current workflow.

---

# Step 2 — Install Literature Review Construct

You install LRC **once on your computer**.

You do not need to install Python manually.

## Windows

### Simple method: Download ZIP

1. On this GitHub page, choose **Code → Download ZIP**.
2. Extract the ZIP to a permanent folder, for example:

```text
C:\Tools\literature-review-construct\
```

3. Open that folder.
4. Double-click:

```text
install.bat
```

5. Wait until the installation finishes.
6. Close and reopen Codex/OpenCode if it was already running.

That is all most Windows users need to do.

### If Windows shows a security prompt

Because this is a small research toolkit rather than a signed commercial application, Windows may ask whether you want to run the script. Only continue if you downloaded the toolkit from this repository.

---

## macOS

### Simple method: Download ZIP

1. On this GitHub page, choose **Code → Download ZIP**.
2. Extract the ZIP to a permanent folder, for example:

```text
~/Tools/literature-review-construct/
```

3. Open **Terminal**.
4. Move into the extracted folder.
5. Run:

```bash
bash install.sh
```

6. Wait until installation finishes.
7. Close and reopen Codex/OpenCode if it was already running.

You do not need to install Python manually; the installer prepares the required runtime.

---

# Step 3 — Create a folder for your research

This is important: **your research folder should be separate from the LRC toolkit folder**.

For example:

```text
Documents\Research\Working Capital\
```

or:

```text
Documents\Research\Bank Efficiency\
```

Think of LRC as an application that is installed once. Each study then gets its own folder.

For example:

```text
Literature Review Construct
    installed once on the computer

Research Project A
Research Project B
Research Project C
```

Do not create your research project inside the downloaded LRC source-code folder.

---

# Step 4 — Start your first Literature Review project

Open **your research folder** in Codex or OpenCode.

Then simply type something like:

> **Start a new Literature Review Construct project in this folder. Help me define the Research Intent before you begin searching.**

You can also give the topic immediately:

> **Start a new Literature Review Construct project. My topic is working capital management and firm performance. I want the literature to help me identify a useful research direction.**

LRC will normally need a few basic pieces of information, such as:

- your topic or early research question;
- the publication period you want to search;
- the language of the papers;
- any country, industry, or research context that matters;
- whether you already have some papers.

You do not need to have a perfect research question before starting. One purpose of LRC is to let the literature help shape the research direction.

---

# If you already have papers

If you already have useful PDF papers, you can use them as seed literature.

Once the LRC project has been created, place your PDFs in:

```text
papers/user_uploads/
```

Then tell Codex/OpenCode:

> **I added papers to `papers/user_uploads`. Use them as seed literature, preserve the original files, and do not assume they are all relevant.**

LRC will treat these papers as a starting point rather than automatically assuming every uploaded paper is important.

---

# What happens after you start?

You can mostly work by talking normally with the AI.

A typical project develops through these stages:

### 1. Research Intent

Clarify what literature should be studied.

### 2. Literature Discovery

Search broadly, organize papers, remove duplicates, and identify promising areas.

### 3. Research Landscape

Show the major themes, streams, theories, methods, important papers, agreements, and disagreements in the literature.

### 4. Research Direction

LRC suggests possible directions. You decide which direction is most useful for your study.

### 5. Literature Review Blueprint

LRC prepares the structure and argument flow that can guide your literature review writing.

### 6. Working Draft and Researcher Pack

LRC can prepare short draft fragments, references, papers, source-checking tasks, and a Word Researcher Writing Pack.

The purpose is to give you a strong evidence base and writing structure — not to replace the researcher as the author.

---

# When will LRC ask me to decide something?

LRC tries to avoid interrupting you for routine technical work.

It should mainly stop when your academic judgment is useful, for example when you need to:

- confirm or change the research scope;
- decide whether the literature search is sufficient;
- choose among possible Research Directions;
- accept or revise the Literature Review Blueprint;
- verify important sources before final writing.

You should not need to approve every search batch, duplicate removal, file operation, or technical step.

---

# Where are my results saved?

Everything stays inside your research folder.

A typical project will gradually contain folders such as:

```text
papers/
references/
outputs/
```

The most useful folders for researchers are:

### `papers/`

Your paper library, including downloaded full text and papers you supplied yourself.

### `references/`

Working reference files, including EndNote-compatible export where available.

### `outputs/`

Researcher-facing outputs such as the Research Landscape, Evidence Map, Research Direction, Literature Review Blueprint, Working Draft fragments, and Researcher Writing Pack.

There is also a hidden/internal project folder called `.litreview`. You normally do not need to open or edit it.

---

# How do I continue the project another day?

Open the **same research folder** again in Codex/OpenCode and say:

> **Continue this Literature Review Construct project from its saved state. Do not repeat completed work. Continue until you need a research decision from me.**

LRC saves project state locally, so you should not need to start again from the beginning.

You can also move between supported AI hosts while keeping the same research folder, although behavior may vary slightly between hosts during beta testing.

---

# Do I need to collect every possible paper?

No.

LRC may discover hundreds or even thousands of records, but a good narrative literature review does not necessarily need every paper that can technically be found.

The more important questions are:

- Are the important research streams covered?
- Are the main arguments supported by credible studies?
- Do you have enough strong full-text evidence for the claims you want to make?
- Is the literature sufficient for your research purpose?

For many projects, a well-selected set of strong papers is more useful than trying to maximize the number of downloaded PDFs.

The researcher decides when the evidence base is sufficient.

---

# Full-text papers

LRC can automatically look for legally available open-access full text.

If a paper cannot be downloaded automatically, LRC may ask you to obtain it through:

- your university/institutional library;
- an author-provided copy;
- another legal source;
- a PDF you already have.

LRC does not bypass paywalls or publisher access controls.

You do not need to achieve 100% full-text coverage before continuing your literature review.

---

# Updating or reinstalling LRC

Your research projects are stored separately from the toolkit, so updating or repairing LRC should not require you to restart a research project.

## Windows

After downloading/pulling a newer version, run:

```text
install.bat
```

again.

To uninstall LRC, run:

```text
uninstall.bat
```

The uninstall process is designed not to delete your separate research folders, papers, or outputs.

## macOS

After updating the toolkit folder, run again:

```bash
bash install.sh
```

Your existing research folders remain separate.

---

# Optional: for users comfortable with PowerShell or Terminal

**You do not need this section for normal use.**

LRC has a local command-line tool that can perform some mechanical tasks without keeping Codex/OpenCode busy. This can be useful if you are comfortable with PowerShell/Terminal and want to reduce AI-token usage during long operations.

For example, inside a research folder you can run:

```powershell
lrc fulltext acquire .
```

to continue lawful open-access full-text retrieval without asking the AI model to wait for the task.

To see papers that still need researcher/library action:

```powershell
lrc fulltext queue .
```

If you want to enable Unpaywall as an additional open-access source for the current PowerShell session:

```powershell
$env:UNPAYWALL_EMAIL="your-email@example.com"
```

Then run the acquisition command again.

This is optional. A normal user can simply ask Codex/OpenCode to continue the project.

For large or slow full-text batches, direct PowerShell/Terminal use can be more convenient because it avoids keeping a long AI session open and can reduce model usage.

---

# Frequently asked questions

### Do I need to know programming?

No. The normal workflow is conversational.

### Do I need Git?

No. You can download the toolkit as a ZIP file.

### Do I need to install Python?

No. The installer prepares the required runtime.

### Do I need an AI subscription?

You need access to at least one AI host/model supported by the application you choose. Codex uses your OpenAI/ChatGPT setup; OpenCode can connect to different model providers.

### Does LRC write the final literature review for me?

No. It helps construct the evidence base, research landscape, structure, and draft material, but the final review remains researcher-authored.

### Can I use my own papers?

Yes. Put them in `papers/user_uploads` after starting the project.

### Do I need every paper in full text?

No. Full-text quality and coverage of the important literature matter more than reaching an arbitrary number of papers.

### Can I stop and continue later?

Yes. Reopen the same research folder and ask LRC to continue from its saved state.

### Can I use a different AI app later?

The project state is stored locally, so supported hosts can work from the same research folder. Cross-host behavior is still being tested during beta.

---

# Current beta notes

The current beta is focused on narrative literature reviews.

Some scholarly databases may temporarily limit requests, some publisher links may not provide a direct PDF, and some papers will still require library access or manual researcher verification.

Output quality may also vary depending on the AI host and model you use.

For the current beta, the most tested workflow is:

**Windows + Codex/OpenCode**

macOS support is also included and remains part of beta testing.

---

# More detailed documentation

If you want more detailed prompts, maintenance instructions, or testing information:

- [`QUICK_START.md`](QUICK_START.md) — practical start/resume templates and additional usage
- [`BETA_READINESS.md`](BETA_READINESS.md) — beta behavior and testing notes

---

## License

MIT
