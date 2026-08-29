# Lit Review Construct

**Build the literature behind your study — without handing authorship to AI.**

**Current beta:** **`0.1.0b1`**

Lit Review Construct is a local-first toolkit that helps researchers **find, understand, organize, and structure the literature for a research project**.

It is designed for researchers who want AI assistance with literature discovery and synthesis, but still want to keep the important academic decisions — source verification, interpretation, research direction, citation choice, and final writing — under human control.

The toolkit currently supports **Codex** and **OpenCode** on Windows.

---

## What Lit Review Construct does

Lit Review Construct can help you:

- define the scope of a literature review;
- search scholarly literature broadly before narrowing;
- identify major research streams, debates, methods, and recurring findings;
- progressively filter a large literature set without requiring you to screen every paper;
- follow citations and references from important papers;
- collect lawful open-access full text when available;
- organize evidence from papers while keeping track of how strong that evidence is;
- compare possible research directions;
- build a Literature Review Blueprint;
- create short, editable Working Draft fragments to help you begin writing;
- prepare a researcher-facing paper library;
- export the references currently used in the review to EndNote;
- prepare a Word **Researcher Writing Pack** that brings together what you need to finish the literature review;
- optionally generate an AI-use statement based only on AI activities actually recorded in the project.

## What it does **not** do

Lit Review Construct is **not** designed to:

- write a complete submission-ready literature review for you;
- make final scholarly judgments on your behalf;
- guarantee that every paper in the world has been found;
- perform a PRISMA/systematic review workflow in the current beta;
- treat an abstract as equivalent to a verified full-text finding;
- bypass paywalls, logins, CAPTCHAs, or publisher access controls;
- automatically claim that a research gap is globally new.

The final literature review remains **researcher-authored**.

---

# Quick start

If you already have Codex or OpenCode installed, the basic setup is:

1. Download or clone this repository once.
2. Double-click **`install.bat`**.
3. Create a new folder for your research project.
4. Open that research folder in Codex or OpenCode.
5. Start Lit Review Construct with a normal-language request.

Example:

> **Start a new Lit Review Construct project. Help me define the scope of my literature review before searching.**

You do **not** need to copy the toolkit into every research project.

---

# Before you install

## Recommended environment

The current beta is designed primarily for:

- **Windows 10 or Windows 11**;
- an internet connection for literature search and lawful open-access retrieval;
- either **Codex** or **OpenCode** as the AI host;
- optional EndNote if you want to import the generated reference file.

You do **not** need to install Python manually. The Lit Review Construct installer handles its own Python runtime through `uv`.

---

# Option A — Use Lit Review Construct with Codex

Codex is available through OpenAI and can be used from the desktop app, web, CLI, or IDE. For this beta, the easiest path is to use **Codex on the desktop and open your research folder as the working folder**.

Official Codex information:

- https://openai.com/codex/
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan

## Install and prepare Codex

1. Install or open the ChatGPT/Codex desktop experience for Windows.
2. Sign in with your ChatGPT account.
3. Confirm that you can open Codex and work with a local folder.
4. Install Lit Review Construct using `install.bat` as described below.
5. Close and reopen Codex after the Lit Review Construct installation.
6. Create or choose a dedicated research folder and open that folder in Codex.

Then start with:

> **Start a new Lit Review Construct project in this folder. Help me define the Research Intent before you begin searching.**

For an existing project, use:

> **Continue this Lit Review Construct project from its saved state. Do not repeat completed steps, and only stop when you need a research decision from me.**

Lit Review Construct uses the access already available through your Codex/ChatGPT setup. It does not store your ChatGPT password or account credentials inside the research project.

---

# Option B — Use Lit Review Construct with OpenCode

OpenCode is an open-source AI coding agent that can run in a terminal, desktop app, or IDE environment.

Official OpenCode documentation:

- https://opencode.ai/docs/

## Install OpenCode on Windows

For the Lit Review Construct beta, the simplest tested setup is **OpenCode running directly in Windows**, because `install.bat` installs the Lit Review Construct skills and commands into your Windows user profile.

You can install OpenCode using one of the methods documented by OpenCode.

### Using npm

```powershell
npm install -g opencode-ai
```

### Using Chocolatey

```powershell
choco install opencode
```

### Using Scoop

```powershell
scoop install opencode
```

OpenCode's official documentation also recommends WSL for some Windows use cases. WSL is a separate environment from native Windows. If you choose to run OpenCode inside WSL, Lit Review Construct must also be installed inside that WSL environment rather than relying on the Windows installation.

## Connect a model provider

OpenCode needs access to an AI model provider.

1. Start OpenCode.
2. Use OpenCode's `/connect` command.
3. Choose the provider you want to use.
4. Follow OpenCode's authentication instructions.

Lit Review Construct does not require a particular provider. Model quality, limits, and cost depend on the provider and model you choose.

## Start a Lit Review Construct project in OpenCode

After installing Lit Review Construct:

1. Close and reopen OpenCode.
2. Open your dedicated research folder in OpenCode.
3. Type:

```text
/lr
```

If the folder is new, `/lr` should start the Lit Review Construct workflow.

If the folder already contains a Lit Review Construct project, `/lr` should continue from the saved project state.

You can also use a normal prompt instead:

> **Continue this Lit Review Construct project from its saved state. Only stop when you need a research decision from me.**

---

# Install Lit Review Construct

You only need to install the toolkit **once per computer/environment**.

## Method 1 — Download ZIP

1. Download the repository ZIP from GitHub.
2. Extract it to a permanent folder, for example:

```text
C:\Tools\literature-review-construct\
```

3. Double-click:

```text
install.bat
```

## Method 2 — Clone with Git

```powershell
git clone https://github.com/thuycq/literature-review-construct.git
cd literature-review-construct
```

Then double-click `install.bat`, or run it from Windows.

## What the installer does

The installer automatically:

- prepares the Python runtime required by Lit Review Construct;
- installs the `lrc` runtime command;
- installs Lit Review Construct skills for Codex;
- installs Lit Review Construct skills for OpenCode;
- installs the OpenCode `/lr` helper command.

After installation, close and reopen Codex/OpenCode so the host can see the new skills and commands.

### Optional installation check

Open PowerShell and run:

```powershell
lrc version
```

For this beta, the expected result is:

```text
0.1.0b1
```

Most researchers do not need to use the `lrc` command directly during normal work.

---

# Toolkit folder vs. research folder

This distinction is important.

The **toolkit folder** is where Lit Review Construct is installed from:

```text
C:\Tools\literature-review-construct\
```

Your **research folder** is the folder for one specific study:

```text
D:\Research\Bank_Efficiency_Project\
```

For another study, create another folder:

```text
D:\Research\Working_Capital_Project\
```

You do **not** need a new copy of the Lit Review Construct repository for every study.

Think of it like this:

```text
Lit Review Construct toolkit
        ↓ installed once
Codex / OpenCode
        ↓ works with
Research Project A
Research Project B
Research Project C
```

---

# Starting a new research project

You can begin with only a topic. You do not need a perfect research question before starting.

## Simple start

> **Start a new Lit Review Construct project. My topic is financial liberalization and bank efficiency in Vietnam. Help me define the literature scope before searching.**

## More structured start

> **Start a new Lit Review Construct project using the following brief. Help me check the scope first, then continue with literature discovery.**
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

The toolkit should ask only for information that materially affects the literature search.

---

# If you already have papers

After the project is initialized, Lit Review Construct creates:

```text
papers/user_uploads/
```

Place your existing PDF papers there.

Then say:

> **I have added some papers to `papers/user_uploads`. Please scan them as seed literature. Do not assume every uploaded paper is relevant; use them as starting points for discovery.**

The toolkit will keep your original files unchanged.

If you do not have any papers, simply say so when asked and continue.

---

# How the workflow works

Lit Review Construct does a lot of technical work internally, but the researcher should only need to make a small number of meaningful academic decisions.

## 1. Research Intent

You confirm what literature the project should study.

Typical decisions:

- topic or research question;
- publication period;
- language scope;
- geographic or institutional scope when relevant;
- important inclusion/exclusion boundaries.

The toolkit should not begin broad discovery until the Research Intent is clear enough.

---

## 2. Discovery Focus

The toolkit searches broadly first and gives you an early map of the literature.

You then decide which research streams or perspectives are most useful for your study.

After that, the toolkit can automatically handle technical narrowing such as:

- removing duplicates;
- prioritizing likely-relevant studies;
- following citations and references from strong papers;
- checking whether additional search rounds are still adding useful literature.

You should **not** need to approve every technical refinement round.

A useful prompt at this stage is:

> **Show me the main research streams you found, explain how they differ, recommend the strongest focus options for my study, and let me choose.**

When the literature seems sufficient for a narrative review, you can say:

> **If the current literature is sufficiently developed for a narrative review, finish discovery and construct the Research Landscape. If not, explain what is still materially missing.**

The researcher still makes the final decision to finish discovery.

---

## 3. Research Landscape and Evidence Map

Once discovery is finished, Lit Review Construct organizes the retained literature into a Research Landscape.

This helps you understand:

- the main research streams;
- important papers;
- common theories;
- methods and data typically used;
- areas of agreement and disagreement;
- recent developments;
- questions that appear underexplored in the literature reviewed so far.

The toolkit also builds an Evidence Map so later claims can be linked back to actual source material.

You normally do not need to make a separate technical decision here.

---

## 4. Research Direction

Using the Research Landscape and Evidence Map, the toolkit proposes a small number of possible Research Directions.

These are suggestions, not automatic decisions.

Ask:

> **Show me the candidate Research Directions in plain research language. Compare their contribution, evidence strength, feasibility, and main risks. Recommend the most defensible options, but let me make the final choice.**

You may:

- select one direction;
- modify it;
- combine ideas;
- reject all suggestions;
- ask for alternatives.

---

## 5. Literature Review Blueprint

After you select a Research Direction, Lit Review Construct builds a Literature Review Blueprint.

The Blueprint is the main architecture for writing the review. It explains:

- what each section should accomplish;
- how the sections connect;
- which literature supports each part;
- where evidence is weak or contradictory;
- which points still require researcher judgment or source verification.

Recommended prompt:

> **Show me the Literature Review Blueprint in a researcher-friendly format. Explain the proposed section structure, the main argument flow, the strongest evidence, the important weaknesses, and the few decisions I should review before accepting it.**

You explicitly accept or revise the Blueprint before the toolkit creates Working Draft material.

---

## 6. Working Draft and Researcher Handoff

After the Blueprint is accepted, Lit Review Construct creates **bounded Working Draft fragments**.

These fragments are designed to help you begin writing, not to replace your writing.

They should remain visibly connected to:

- source evidence;
- verification needs;
- unresolved researcher decisions;
- the accepted Blueprint.

A useful prompt is:

> **Show me the actual Working Draft fragments section by section. Keep source-verification needs and researcher decisions visible, and do not turn them into a submission-ready literature review.**

At the final handoff, Lit Review Construct prepares the researcher-facing project package automatically.

---

# Recommended prompt library

You do not need to use these exact words. They are simply safe, clear prompts for common situations.

## Start a project

> **Start a new Lit Review Construct project. Help me define the literature scope before searching.**

## Fast start from a research brief

> **Start a new Lit Review Construct project using the research brief below. Use everything I have already provided, ask only for missing information that materially affects the search, and then continue with the workflow.**

## Continue an existing project

> **Continue this Lit Review Construct project from its saved state. Do not repeat completed work. Continue technical steps automatically and stop only when you need a research decision from me.**

## Add your own papers

> **I have added papers to `papers/user_uploads`. Scan them as seed literature, preserve the original files, and do not assume they are all relevant.**

## Review discovery focus

> **Show me the main research streams in the literature found so far. Explain the differences, recommend the most promising focus options, and let me decide.**

## Finish discovery

> **Assess whether the current literature is sufficient for a narrative review. If it is, recommend finishing discovery and building the Research Landscape. If it is not, explain only what is materially missing.**

## Choose a Research Direction

> **Compare the candidate Research Directions by contribution, evidence strength, feasibility, and risk. Recommend the strongest options, but do not choose for me.**

## Review the Blueprint

> **Show me the Literature Review Blueprint as a researcher would use it to write the review. Highlight the argument flow, section purposes, evidence weaknesses, and any decisions I should make before accepting it.**

## Review the Working Draft

> **Show me the actual Working Draft fragments, not a technical summary. Present them section by section with concise source-verification notes and researcher tasks.**

## Prepare the final researcher package

> **Continue to the researcher handoff. Prepare the paper library, working references, EndNote file, and Researcher Writing Pack. Do not write a submission-ready final literature review.**

## Review what still needs verification

> **Show me only the remaining source-verification tasks that matter before I write the final literature review, using paper titles rather than internal IDs.**

## Generate an AI-use statement

> **Generate the optional AI-use statement using only activities that were actually recorded in this Lit Review Construct project.**

---

# Researcher-facing project folders

A typical project will look like this:

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

You normally only need to work with:

```text
papers/
references/
outputs/
```

The `.litreview/` folder stores project state used by the toolkit. You normally do not need to open or edit it.

---

# Paper library

## `papers/full_text/`

Contains lawful open-access PDFs acquired by the toolkit.

When possible, downloaded PDFs are named using the DOI so each paper has a stable identity.

Example:

```text
doi_10.1016__j.jbankfin.2024.107123.pdf
```

If no DOI is available, another stable scholarly identifier is used.

## `papers/abstract_only/`

Contains readable notes for **working literature that is currently being used but does not yet have local full text**.

These are not substitutes for the original papers. Detailed claims from these records should remain provisional until full text is checked.

The toolkit does **not** create thousands of abstract files for the entire discovery corpus. This folder is intended for literature actually being used in the current Blueprint/Working Draft.

## `papers/user_uploads/`

This is your drop zone for PDFs you already have.

The toolkit should preserve your original filenames and should not move or rename your files without permission.

---

# References and EndNote

The `references/` folder contains the references currently used by the Literature Review Blueprint/Working Draft.

## `references_used.enw`

EndNote tagged import file.

The file is generated from the toolkit's canonical bibliographic records rather than from AI-written citation strings.

This reduces the chance that a reference is created from hallucinated citation text.

You should still check the imported references before final submission.

## `references_used.csv`

A simple audit table showing the working references and where they are being used.

Useful for checking:

- author;
- year;
- title;
- journal;
- DOI;
- section usage;
- full-text status;
- researcher verification status.

## `references_manifest.md`

A short summary of the reference package and current coverage.

---

# Researcher Writing Pack

The main Word handoff file is:

```text
outputs/LitReview_Researcher_Writing_Pack.docx
```

This is **not** intended to be a technical report.

It is organized for the researcher who now needs to finish writing the literature review.

It includes:

1. the research focus and selected direction;
2. the accepted literature-review structure;
3. what each section needs to establish;
4. the actual Working Draft fragments;
5. remaining researcher decisions;
6. source-verification tasks using paper titles rather than internal IDs;
7. working references;
8. a final writing checklist.

It deliberately excludes:

- internal paper IDs;
- evidence IDs;
- JSON fields;
- `.litreview` paths;
- provider logs;
- API errors;
- test output;
- technical provenance;
- the optional AI-use statement.

Those technical details remain available separately when debugging is actually needed.

---

# Understanding evidence status

Lit Review Construct separates three ideas that are easy to confuse.

## 1. Full text available

A PDF is available locally.

This only means the paper can be read.

## 2. AI checked against full text

The AI has checked the relevant evidence against the full paper rather than relying only on the abstract.

This still does **not** mean the researcher has verified the claim.

## 3. Researcher verified

You have explicitly checked the relevant source yourself.

Only this state should be described as researcher-verified.

The toolkit should never silently convert “PDF downloaded” into “verified evidence.”

---

# Open-access full text

Lit Review Construct may use lawful open/public locations reported by scholarly services such as OpenAlex, Semantic Scholar, and optional Unpaywall support.

It does not bypass:

- publisher paywalls;
- institutional login requirements;
- CAPTCHAs;
- access-control systems.

If lawful full text is not available, the paper can remain part of the research project as abstract-level literature until the researcher obtains the source separately.

---

# Resuming a project later

Your project is stored in the local research folder.

You can close the host and return later without relying on the old chat conversation.

## In Codex

Open the same research folder and say:

> **Continue this Lit Review Construct project from its saved state. Do not repeat completed steps.**

## In OpenCode

Open the same folder and use:

```text
/lr
```

The toolkit should inspect the local project state and continue from the correct stage.

---

# Switching between Codex and OpenCode

Because the project state is stored inside the research folder, the same project can be opened in either supported host.

For example:

1. start discovery in OpenCode;
2. close OpenCode;
3. open the same research folder in Codex;
4. ask Codex to continue the Lit Review Construct project.

The local project state — not the old chat conversation — is the source of truth.

---

# Updating Lit Review Construct

## If you cloned the repository

Open the toolkit folder and run:

```powershell
git pull
```

Then run `install.bat` again.

## If you downloaded a ZIP

Download the latest repository version, extract it, and run `install.bat` again.

After updating, close and reopen Codex/OpenCode.

Optional version check:

```powershell
lrc version
```

Updating the toolkit does not require creating new copies of your existing research folders.

---

# Beta testing guide

Version **`0.1.0b1`** is intended for small-scale beta testing.

The most useful beta feedback is about the **researcher experience**, not low-level implementation details.

While testing, notice whether:

- the toolkit starts only when you actually want to use Lit Review Construct;
- it asks you for meaningful research decisions rather than technical confirmations;
- discovery feels broad enough before narrowing;
- it avoids repeatedly asking you to “refine” the same literature;
- the Research Landscape is understandable;
- candidate Research Directions are meaningfully different;
- the Blueprint is useful as a writing structure;
- abstract-only claims remain appropriately cautious;
- anything is incorrectly labeled “verified”;
- downloaded PDFs are easy to find;
- `references_used.enw` imports cleanly into EndNote;
- the Researcher Writing Pack contains what you need to continue writing without unnecessary technical material;
- the Suggested next message actually moves the project forward rather than repeating the previous step.

## What to send when you find a problem

Usually the most useful report is simply:

1. what you asked;
2. what Codex/OpenCode replied;
3. what you expected instead.

You normally do **not** need to send files from `.litreview/` unless debugging specifically requires them.

---

# Frequently asked questions

## Does Lit Review Construct write the final literature review?

No.

It can create evidence-linked Working Draft fragments and a Writing Pack, but the final literature review remains researcher-authored.

## Is this a systematic-review / PRISMA tool?

Not in the current beta.

The current workflow is designed for **narrative literature reviews**. It uses progressive triage rather than requiring every indexed paper to be screened.

## Do I need an API key?

It depends on the host.

- **Codex:** use the access available through your OpenAI/ChatGPT account.
- **OpenCode:** connect a supported model provider through OpenCode. Provider authentication, free tiers, subscription plans, and API costs depend on the provider you select.

Lit Review Construct itself does not require you to store a provider key inside the research folder.

## Can I use free models in OpenCode?

If OpenCode provides access to a free or included model through one of its configured providers, Lit Review Construct can use that host setup. The toolkit does not require one specific model.

Output quality may vary by model.

## Can I add papers I already have?

Yes.

Place them in:

```text
papers/user_uploads/
```

Then tell Lit Review Construct to scan them as seed literature.

## Will my uploaded papers automatically be treated as relevant?

No.

Researcher-provided papers are treated as useful starting material, not automatically as relevant/core evidence.

## Can I use literature in more than one language?

Yes, if the Research Intent includes those languages.

You can also define exceptions, for example English academic literature plus Vietnamese primary regulatory documents.

## Why are some papers only in `abstract_only`?

Because the toolkit may have bibliographic metadata and an abstract but no lawful local full-text PDF.

Those papers can still help with discovery and mapping, but detailed findings should remain provisional until the full paper is checked.

## Why didn't the toolkit download a paper behind a paywall?

The toolkit does not bypass access restrictions.

You may obtain the paper through your institution or another lawful source and place the PDF in `papers/user_uploads/`.

## Can I move between Codex and OpenCode?

Yes.

Open the same research folder in the other host and continue from the saved Lit Review Construct state.

## Do I need to understand the `.litreview` folder?

No.

It is the toolkit's internal project state. Researchers should normally work only with `papers/`, `references/`, and `outputs/`.

---

# Current beta limitations

The current beta has several intentional limitations:

- narrative literature reviews only;
- scholarly search providers may rate-limit or return incomplete metadata;
- open-access availability is not guaranteed;
- imported bibliographic records may still need researcher correction;
- the toolkit cannot independently guarantee that a proposed gap is globally novel;
- final source verification remains the researcher's responsibility;
- output quality can vary across AI hosts and model providers;
- Codex and OpenCode may behave slightly differently even when using the same local project state.

These limitations are part of the beta-testing scope rather than hidden assumptions.

---

# Optional AI-use statement

At the end of a project, Lit Review Construct can optionally generate an AI-use statement based on the AI activities actually recorded in the project.

For example, the statement may describe assistance with:

- search planning;
- literature discovery;
- evidence organization;
- Research Landscape synthesis;
- candidate Research Direction suggestions;
- Literature Review Blueprint construction;
- Working Draft fragments.

It should **not** claim that AI performed activities that were not recorded.

The AI-use statement is kept separate from the Researcher Writing Pack by default.

---

# For developers and advanced testers

Most researchers do not need the internal documentation.

Developer/beta details are available in:

```text
BETA_READINESS.md
```

The `.litreview/` folder contains the authoritative machine-readable project state used for resume, provenance, and debugging.

---

# License

MIT License.

---

## Beta principle

**Lit Review Construct should remove technical burden, not remove scholarly responsibility.**

The toolkit should do the repetitive technical work automatically and ask the researcher only when a meaningful academic decision is required.
