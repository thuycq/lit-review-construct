# Literature Review Construct

**Build the literature behind your study — without handing authorship to AI.**

**Current beta:** **`0.1.0b2`**

Literature Review Construct is a local-first toolkit that helps researchers **find, understand, organize, and structure the literature for a research project**.

It is designed for researchers who want AI assistance with literature discovery and synthesis while keeping the important academic decisions — source verification, interpretation, research direction, citation choice, and final writing — under human control.

The current beta supports **Windows and macOS** and can be used with several AI hosts.

---

# What is an AI host?

An **AI host** is the application or agent you work in. Examples include Codex, OpenCode, Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot, and Cline.

The **model/provider** is the AI service used inside that host. Depending on the host, that might be an OpenAI, Anthropic, Google, or another model.

Literature Review Construct integrates with the **host**. It does not force you to use one particular model or provider.

Your account, subscription, API key, free tier, usage limit, and model choice remain managed by the host/provider you choose.

---

# Supported AI hosts

The current beta installs adapters for:

| AI host | Beta support | How Literature Review Construct is recognized |
|---|---|---|
| **Codex** | Supported | Global skills + project `AGENTS.md` |
| **OpenCode** | Supported | Global skills + `/lr` shortcut |
| **Claude Code** | Supported | Global skills + `/lr` shortcut |
| **Cursor** | Supported | Agent Skills + project `AGENTS.md` |
| **Windsurf** | Supported | Agent Skills + project `AGENTS.md` |
| **Gemini CLI** | Supported | `/lr` shortcut + gated Gemini context |
| **GitHub Copilot** | Supported | Agent Skills + project `AGENTS.md` |
| **Cline** | Supported in beta | Global skills; Cline Skills must be enabled |

The same Literature Review Construct core workflow is used across all hosts. The host adapter only helps the AI host discover and follow that workflow.

This means the literature-review logic is **not rewritten separately for each AI product**.

---

# What Literature Review Construct does

Literature Review Construct can help you:

- define the scope of a literature review;
- search scholarly literature broadly before narrowing;
- identify major research streams, debates, methods, and recurring findings;
- progressively filter a large literature set without requiring you to screen every paper;
- follow citations and references from important papers;
- collect lawful open-access full text when available;
- organize source-linked evidence while keeping uncertainty visible;
- compare possible Research Directions;
- build a Literature Review Blueprint;
- create short, editable Working Draft fragments;
- prepare a researcher-facing paper library;
- export working references to EndNote;
- prepare a Word **Researcher Writing Pack** containing what you need to finish the literature review;
- optionally generate an AI-use statement based only on AI activities actually recorded in the project.

## What it does **not** do

Literature Review Construct is **not** designed to:

- write a complete submission-ready literature review for you;
- make final scholarly judgments on your behalf;
- guarantee that every paper in the world has been found;
- perform a PRISMA/systematic-review workflow in the current beta;
- treat an abstract as equivalent to a checked full-text finding;
- bypass paywalls, logins, CAPTCHAs, or publisher access controls;
- automatically claim that a proposed research gap is globally new.

The final literature review remains **researcher-authored**.

---

# Quick start

The basic setup is the same regardless of AI host.

1. Install the AI host you want to use.
2. Download or clone Literature Review Construct once.
3. Install Literature Review Construct on your computer.
4. Create a new folder for one research project.
5. Open that research folder in your AI host.
6. Start with a normal-language request.

Universal start prompt:

> **Start a new Literature Review Construct project in this folder. Help me define the Research Intent before you begin searching.**

Universal resume prompt:

> **Continue this Literature Review Construct project from its saved state. Do not repeat completed work. Continue technical steps automatically and stop only when you need a research decision from me.**

You do **not** need to copy the toolkit into every research project.

---

# Before you install

## Recommended environment

The beta currently targets:

- **Windows 10/11** or a current **macOS** release;
- an internet connection for literature search and lawful open-access retrieval;
- at least one supported AI host;
- optional EndNote if you want to import the generated `.enw` file.

You do **not** need to install Python manually. The Literature Review Construct installer provisions its Python runtime through `uv`.

---

# Step 1 — Choose and install an AI host

You only need **one** supported host. Installing several is optional.

## Codex

Official information:

- https://openai.com/codex/
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan

Install/sign in to Codex using your OpenAI/ChatGPT setup, open your research folder as the working folder, and use the universal start prompt.

## OpenCode

Official documentation:

- https://opencode.ai/docs/

OpenCode supports multiple model providers. Configure the provider you want through OpenCode, for example with `/connect`.

After Literature Review Construct is installed, open your research folder and type:

```text
/lr
```

`/lr` starts a new project in a new folder or resumes the saved project when one already exists.

## Claude Code

Official documentation:

- https://code.claude.com/docs/

The installer adds the Literature Review Construct skills and a convenient shortcut:

```text
/lr
```

You may also use the universal start/resume prompts.

## Cursor

Official documentation:

- https://cursor.com/docs/

Open your research folder in Cursor Agent and use the universal start prompt. Literature Review Construct uses installed Agent Skills plus the project `AGENTS.md` created when the project starts.

## Windsurf

Official documentation:

- https://docs.windsurf.com/

Open the research folder in Windsurf Cascade and use the universal start prompt. Literature Review Construct uses installed Agent Skills plus the project `AGENTS.md`.

## Gemini CLI

Official documentation:

- https://google-gemini.github.io/gemini-cli/

The installer adds:

```text
/lr
/lr-status
```

The Gemini integration is globally available but activates only when the current folder is already a Literature Review Construct project or when you explicitly start one.

## GitHub Copilot

Official documentation:

- https://docs.github.com/en/copilot/

Use an agent-capable Copilot environment that can access the local research folder, then use the universal start prompt. Literature Review Construct installs compatible Agent Skills and relies on the project's `AGENTS.md` for project-specific instructions.

## Cline

Official documentation:

- https://docs.cline.bot/

Cline supports Agent Skills, but its Skills feature is currently an experimental feature. Enable **Skills** in Cline Settings → Features before beta testing Literature Review Construct.

Then open the research folder and use the universal start prompt.

---

# Step 2 — Install Literature Review Construct

You install the toolkit **once per computer/environment**, not once per research project.

## Windows

### Download ZIP

1. Download the repository ZIP from GitHub.
2. Extract it to a permanent folder, for example:

```text
C:\Tools\literature-review-construct\
```

3. Double-click:

```text
install.bat
```

### Clone with Git

```powershell
git clone https://github.com/thuycq/literature-review-construct.git
cd literature-review-construct
```

Then double-click `install.bat` or run it from the toolkit folder.

## macOS

### Download ZIP

1. Download the repository ZIP from GitHub.
2. Extract it to a permanent folder, for example:

```text
~/Tools/literature-review-construct/
```

3. Open Terminal in the toolkit folder and run:

```bash
bash install.sh
```

Using `bash install.sh` means you do not need to adjust executable permissions after extracting a ZIP.

### Clone with Git

```bash
git clone https://github.com/thuycq/literature-review-construct.git
cd literature-review-construct
bash install.sh
```

## What the installer does

The Windows and macOS installers:

- install/provision Python 3.12 through `uv`;
- install the global `lrc` runtime;
- install the same canonical Literature Review Construct skills for supported Agent-Skills hosts;
- install OpenCode `/lr` commands;
- install Claude Code `/lr`;
- install Gemini CLI `/lr` and `/lr-status` plus a gated global context;
- preserve the activation rule: **globally installed does not mean globally active**.

The installer does **not** install or sign you into the AI hosts themselves.

After installation, close and reopen your AI host so it reloads skills and commands.

### Installation check

Open PowerShell or Terminal and run:

```text
lrc version
```

Expected beta version:

```text
0.1.0b2
```

Most researchers do not need to run `lrc` directly during normal use.

---

# Toolkit folder vs. research folder

The **toolkit folder** is where Literature Review Construct itself lives.

Windows example:

```text
C:\Tools\literature-review-construct\
```

macOS example:

```text
~/Tools/literature-review-construct/
```

A **research folder** is one specific study:

```text
Research/Bank_Efficiency_Project/
```

For another study, create another folder:

```text
Research/Working_Capital_Project/
```

Do not clone Literature Review Construct separately for each study.

Think of it like this:

```text
Literature Review Construct toolkit
        ↓ installed once
Supported AI host
        ↓ opens
Research Project A
Research Project B
Research Project C
```

---

# Starting a new research project

You can begin with only a topic. You do not need a perfect research question before starting.

## Simple start

> **Start a new Literature Review Construct project. My topic is financial liberalization and bank efficiency in Vietnam. Help me define the literature scope before searching.**

## Structured start

> **Start a new Literature Review Construct project using the following brief. Use what I already provide, ask only for missing information that materially affects the literature search, and then continue with the workflow.**
>
> **Topic:**  
> **Research question or early idea:**  
> **Publication period:**  
> **Language(s):**  
> **Country/industry/context:**  
> **Main concepts or variables:**  
> **Existing papers:** Yes / No  
> **Anything I want to include or exclude:**

You can leave fields blank if you do not know them yet.

---

# If you already have papers

After initialization, the project contains:

```text
papers/user_uploads/
```

Place your existing PDFs there, then say:

> **I added papers to `papers/user_uploads`. Scan them as seed literature, preserve the original files, and do not assume they are all relevant.**

Researcher-provided papers are starting material, not automatically core evidence.

---

# How the workflow works

Literature Review Construct handles technical work internally, while the researcher makes the decisions that require academic judgment.

## 1. Research Intent

You confirm what literature the project should study: topic/question, publication period, language, relevant geographic/institutional scope, and important inclusion/exclusion boundaries.

## 2. Discovery Focus

The toolkit searches broadly and gives you an early map of the literature. You decide which research streams or perspectives should be prioritized.

After that, Literature Review Construct can automatically handle technical narrowing such as:

- deduplication;
- priority triage;
- citation/reference chaining;
- reassessing marginal search gain;
- deciding when another technical refinement batch is no longer useful.

You should not need to approve every refine batch.

Useful prompt:

> **Show me the main research streams found so far, explain how they differ, recommend the strongest focus options for my study, and let me decide.**

When the literature looks sufficiently developed:

> **Assess whether the current literature is sufficient for a narrative review. If it is, recommend finishing discovery and building the Research Landscape. If not, explain only what is materially missing.**

The researcher still decides whether discovery is sufficient.

## 3. Research Landscape and Evidence Map

After discovery finishes, Literature Review Construct organizes the retained literature into major streams, important papers, theories, methods, agreements/disagreements, recent developments, and provisional underexplored areas.

It also builds an Evidence Map so downstream synthesis can be traced to sources.

## 4. Research Direction

The toolkit proposes several possible Research Directions. These are suggestions, not decisions.

> **Compare the candidate Research Directions by contribution, evidence strength, feasibility, and risk. Recommend the strongest options, but do not choose for me.**

You can select, modify, combine, reject, or request alternatives.

## 5. Literature Review Blueprint

After a direction is selected, Literature Review Construct builds a Blueprint describing:

- the purpose of each section;
- argument flow;
- evidence anchors;
- contradictions and weaknesses;
- unresolved researcher decisions;
- source-verification needs.

> **Show me the Literature Review Blueprint as a researcher would use it to write the review. Highlight the argument flow, section purposes, evidence weaknesses, and any decisions I should make before accepting it.**

The Blueprint requires explicit researcher acceptance.

## 6. Working Draft and Researcher Handoff

After Blueprint acceptance, Literature Review Construct creates **bounded Working Draft fragments** rather than a seamless final literature review.

> **Show me the actual Working Draft fragments, not a technical summary. Present them section by section with concise source-verification notes and researcher tasks.**

At handoff, Literature Review Construct prepares the paper library, references, EndNote file, and Researcher Writing Pack.

---

# Recommended prompt library

These prompts work across supported hosts unless a host-specific shortcut such as `/lr` is noted.

## Start

> **Start a new Literature Review Construct project in this folder. Help me define the Research Intent before you begin searching.**

## Resume

> **Continue this Literature Review Construct project from its saved state. Do not repeat completed work. Continue technical steps automatically and stop only when you need a research decision from me.**

## Add seed papers

> **I added papers to `papers/user_uploads`. Scan them as seed literature, preserve the original files, and do not assume they are all relevant.**

## Review discovery focus

> **Show me the main research streams found so far. Explain the differences, recommend the most promising focus options, and let me decide.**

## Finish discovery

> **Assess whether the current literature is sufficient for a narrative review. If it is, recommend finishing discovery and building the Research Landscape. If not, explain only what is materially missing.**

## Choose a Research Direction

> **Compare the candidate Research Directions by contribution, evidence strength, feasibility, and risk. Recommend the strongest options, but do not choose for me.**

## Review the Blueprint

> **Show me the Literature Review Blueprint as a researcher would use it to write the review. Highlight the argument flow, section purposes, evidence weaknesses, and any decisions I should make before accepting it.**

## Review the Working Draft

> **Show me the actual Working Draft fragments, not a technical summary. Present them section by section with concise source-verification notes and researcher tasks.**

## Prepare the researcher handoff

> **Continue to the researcher handoff. Prepare the paper library, working references, EndNote file, and Researcher Writing Pack. Do not write a submission-ready final literature review.**

## Review remaining verification tasks

> **Show me only the remaining source-verification tasks that matter before I write the final literature review, using paper titles rather than internal IDs.**

## Generate an AI-use statement

> **Generate the optional AI-use statement using only activities actually recorded in this Literature Review Construct project.**

---

# Researcher-facing project folders

A typical project looks like:

```text
Research_Project/
├── AGENTS.md
├── papers/
│   ├── full_text/
│   ├── abstract_only/
│   └── user_uploads/
├── references/
│   ├── references_used.enw
│   ├── references_used.csv
│   └── references_manifest.md
├── outputs/
│   ├── 01_research_intent.md
│   ├── 02_seed_inventory.md
│   ├── 03_research_landscape.md
│   ├── 04_evidence_map.md
│   ├── 05_research_direction.md
│   ├── 06_literature_review_blueprint.md
│   ├── 06b_literature_review_working_draft.md
│   └── LitReview_Researcher_Writing_Pack.docx
└── .litreview/
```

Researchers normally work with:

```text
papers/
references/
outputs/
```

`.litreview/` is the toolkit's internal project state. You normally do not need to open or edit it.

---

# Paper library

## `papers/full_text/`

Lawful open-access PDFs acquired by the toolkit. When possible, filenames use the DOI as a stable identity.

Example:

```text
doi_10.1016__j.jbankfin.2024.107123.pdf
```

## `papers/abstract_only/`

Readable notes for working literature currently used by the Blueprint/Working Draft but without local full text. These files are not substitutes for the original papers.

The toolkit does not generate thousands of abstract files for the entire discovery corpus.

## `papers/user_uploads/`

Researcher drop zone. Your original files should not be silently renamed, moved, or deleted.

---

# References and EndNote

`references/references_used.enw` is an EndNote Tagged import file generated from canonical bibliographic records rather than AI-written citation strings.

`references/references_used.csv` provides a quick audit of authors, year, title, DOI, section usage, full-text status, and researcher-verification status.

`references/references_manifest.md` summarizes the working reference package.

Always check imported bibliographic fields before final submission.

---

# Researcher Writing Pack

The main Word handoff is:

```text
outputs/LitReview_Researcher_Writing_Pack.docx
```

It is designed for a researcher who now needs to finish writing the literature review.

It includes:

1. research focus and selected direction;
2. accepted review structure;
3. what each section needs to establish;
4. actual Working Draft fragments;
5. remaining researcher decisions;
6. source-verification tasks using paper titles rather than internal IDs;
7. working references;
8. a final writing checklist.

It deliberately excludes internal IDs, JSON, `.litreview` paths, provider/API logs, tests, technical provenance, and the optional AI-use statement.

---

# Understanding evidence status

Literature Review Construct separates three states:

## Full text available

A PDF exists locally. This only means it can be read.

## AI checked against full text

The AI checked the relevant evidence against the paper rather than relying only on the abstract.

This is still not researcher verification.

## Researcher verified

You explicitly checked the relevant source yourself.

The toolkit should never silently convert “PDF downloaded” into “verified evidence.”

---

# Open-access full text

Literature Review Construct may use lawful public/open locations reported by scholarly services such as OpenAlex, Semantic Scholar, and optional Unpaywall support.

It does not bypass publisher paywalls, institutional logins, CAPTCHAs, or access controls.

If lawful full text is unavailable, a paper may remain part of the project as abstract-level literature until you obtain it separately.

---

# Resuming and switching hosts

The project state is stored in the local research folder, not in the old chat conversation.

You can close one supported host and later open the same folder in another supported host.

Example:

1. start discovery in OpenCode;
2. close OpenCode;
3. open the same research folder in Cursor or Codex;
4. use the universal resume prompt.

Host-specific shortcuts:

```text
OpenCode:    /lr
Claude Code: /lr
Gemini CLI:  /lr
```

The local Literature Review Construct state remains the source of truth.

---

# Updating Literature Review Construct

If you cloned the repository:

```text
git pull
```

Then reinstall:

Windows:

```text
install.bat
```

macOS:

```bash
bash install.sh
```

If you downloaded a ZIP, download the new version, extract it, and run the appropriate installer again.

Close and reopen your AI host afterward.

Updating the toolkit does not require creating new copies of existing research folders.

---

# Beta testing guide

Version **`0.1.0b2`** expands the beta from the original Windows/Codex/OpenCode test to **Windows + macOS and multiple AI hosts**.

The most useful beta feedback is about researcher experience.

Notice whether:

- Literature Review Construct activates only when you intend to use it;
- installation works on your operating system;
- the host discovers the Literature Review Construct skills/shortcut after restart;
- the same project resumes correctly after changing hosts;
- technical steps proceed without unnecessary confirmations;
- discovery avoids repetitive refine loops;
- Research Landscape, Research Direction, and Blueprint outputs are understandable;
- abstract-only evidence remains appropriately cautious;
- anything is incorrectly labeled “verified”;
- downloaded PDFs are easy to find;
- `references_used.enw` imports cleanly into EndNote;
- the Researcher Writing Pack contains what you need without technical clutter;
- Suggested next messages move forward rather than repeat completed work;
- different hosts preserve the same product boundary and researcher-facing behavior.

## Reporting a beta problem

Usually send:

1. operating system;
2. AI host;
3. what you asked;
4. what the host replied or did;
5. what you expected instead.

You normally do not need to send `.litreview/` internals unless debugging specifically requires them.

---

# Frequently asked questions

## Do I need to use Codex or OpenCode?

No. They remain supported, but the beta also installs adapters for Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot, and Cline.

## Do I need an API key?

That depends on the AI host/provider you choose. Literature Review Construct itself does not require provider credentials to be stored in the research folder.

## Can I use different models?

Yes. Model selection is handled by the AI host. Literature Review Construct provides the research workflow and local project structure.

## Can I switch AI hosts halfway through a project?

Yes, as long as both hosts can access the same local research folder and have the Literature Review Construct adapter installed.

## Does Literature Review Construct write the final literature review?

No. It provides literature construction, evidence organization, Blueprint, bounded Working Draft fragments, and a Writing Pack. Final prose remains researcher-authored.

## Is this a systematic-review / PRISMA tool?

Not in the current beta. It is designed for narrative literature reviews with progressive triage.

## Can I add papers I already have?

Yes. Put them in `papers/user_uploads/` and ask Literature Review Construct to scan them as seed literature.

## Why are some papers only in `abstract_only`?

Because metadata/abstract may be available even when lawful local full text is not. Detailed claims remain provisional until the paper is checked.

## Why didn't Literature Review Construct download a paywalled paper?

Literature Review Construct does not bypass access restrictions. Obtain it lawfully through your institution or another source and add it to `papers/user_uploads/`.

## Do I need to understand `.litreview/`?

No. Researchers normally use only `papers/`, `references/`, and `outputs/`.

---

# Current beta limitations

- narrative literature reviews only;
- scholarly providers may rate-limit or return incomplete metadata;
- lawful open-access availability is not guaranteed;
- bibliographic records may still require researcher correction;
- the toolkit cannot guarantee global novelty of a proposed gap;
- final source verification remains the researcher's responsibility;
- output quality varies by host and model;
- multi-host adapters are new in `0.1.0b2` and host-specific edge cases are expected during beta;
- Cline Skills support is itself experimental in Cline;
- macOS support is new in `0.1.0b2` and should be beta-tested on multiple real machines.

---

# Optional AI-use statement

At the end of a project, Literature Review Construct can generate an optional AI-use statement based only on activities actually recorded in the project, such as search assistance, evidence organization, Research Landscape synthesis, Research Direction suggestions, Blueprint construction, and Working Draft fragments.

It should never claim AI performed activities that were not recorded.

The AI-use statement remains separate from the Researcher Writing Pack by default.

---

# For developers and advanced testers

Most researchers do not need internal documentation.

Developer/beta details are in:

```text
BETA_READINESS.md
```

The `.litreview/` folder contains authoritative machine-readable project state used for resume, provenance, and debugging.

---

# License

MIT License.

---

## Beta principle

**Literature Review Construct should remove technical burden, not remove scholarly responsibility.**

The toolkit should do repetitive technical work automatically and ask the researcher only when a meaningful academic decision is required.
