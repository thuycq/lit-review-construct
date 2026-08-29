# Lit Review Construct — Quick Start

Lit Review Construct can begin in either of two ways:

- **Conversational Start** — tell the agent what you are thinking about and answer targeted questions as the scope becomes clearer.
- **Fast Start** — paste a prepared Research Brief so the agent can skip questions you have already answered.

The Fast Start templates below are prompts for **Codex Desktop or OpenCode while the research workspace folder is open**. You do not need to run `lrc` commands yourself.

## Minimal Fast Start

Copy this block, replace the bracketed values, and paste it into the host:

```text
Start or continue this as a Lit Review Construct project using the Research Brief below.
Do not ask me to repeat information already provided. Persist the project state locally and follow the Lit Review Construct workflow. Ask follow-up questions only if information is missing, contradictory, or materially affects the literature scope.

RESEARCH BRIEF
Topic or research question: [your topic or question]
Publication period for literature retrieval: [e.g., 2010–2026]
Paper language(s): [e.g., English]
Existing related papers: [none / use PDFs in the project papers folder / external folder: PATH]

Research Intent confirmation: I confirm the information above as my initial Research Intent.
Seed-literature decision: [No seed papers / Index and acknowledge the specified papers as seed literature. Preserve provenance and do not assume they are relevant.]

After recording these decisions, continue from local project state. Search broadly before making strong research-gap claims, and stop whenever the workflow requires a researcher decision.
```

If all minimum fields are present and the confirmation statements are explicit, the agent should not ask the basic onboarding questions again.

## Detailed Fast Start

Use this version when you already know more about the study but still want the literature to shape or challenge your initial idea.

```text
Start or continue this as a Lit Review Construct project using the Research Brief below.
Do not ask me to repeat information already provided. Persist the project state locally and follow the Lit Review Construct workflow. Ask follow-up questions only when they would materially change the literature search or interpretation.

RESEARCH BRIEF
Topic: [working title or broad topic]
Research question, if already known: [question / not fixed yet]
Publication period for literature retrieval: [from year–to year]
Paper language(s): [language(s)]

Research context, if relevant: [country/region/industry/market/population]
Unit of analysis, if relevant: [firms/banks/households/countries/etc.]
Key constructs or variables already of interest: [optional]
Methods or data constraints already known: [optional]
Known theories, authors, or papers: [optional]

Current goal: [explore broadly / refine an existing idea / find a defensible research direction / update an existing literature review]
Existing related papers: [none / project papers folder / external folder: PATH]

Preferences or boundaries:
- [anything the literature search should include or avoid]
- [optional journal/discipline orientation]
- [optional date, geography, or study-type constraints]

Research Intent confirmation: I confirm the information above as my initial Research Intent. Treat optional items as starting preferences, not facts that the literature must support.
Seed-literature decision: [No seed papers / Index and acknowledge the specified papers as seed literature. Preserve provenance and do not assume they are relevant.]

Continue through broad multi-source discovery. First show me the provisional research landscape and candidate directions that emerge from the literature. Let me decide whether to continue broadly, focus, combine streams, or change scope before making strong gap or novelty claims.
```

## Example

```text
Start this as a Lit Review Construct project using the Research Brief below.
Do not ask me to repeat information already provided. Persist the project state locally and ask only questions that materially affect the literature scope.

RESEARCH BRIEF
Topic: Working capital management and firm performance
Research question, if already known: Not fixed yet; I want the literature to help identify a defensible direction.
Publication period for literature retrieval: 2000–2026
Paper language(s): English
Research context, if relevant: Firms, with particular interest in emerging markets
Key constructs or variables already of interest: Working capital management, cash conversion cycle, profitability, firm performance
Current goal: Explore broadly first, then narrow based on the research landscape.
Existing related papers: None

Research Intent confirmation: I confirm the information above as my initial Research Intent. Treat optional items as starting preferences, not facts that the literature must support.
Seed-literature decision: No seed papers.

Continue through broad multi-source discovery. First show me the provisional research landscape and candidate directions that emerge from the literature. Let me decide whether to continue broadly, focus, combine streams, or change scope before making strong gap or novelty claims.
```

## What the template does not bypass

Fast Start removes repetitive onboarding; it does **not** remove scholarly checkpoints. The agent must still stop when researcher judgment is needed, including decisions about changing/focusing the discovery scope, finishing discovery, selecting a Research Direction, and accepting the Literature Review Blueprint.

The toolkit should also surface contradictions or important scope problems even when the brief is pre-confirmed. A prefilled prompt is permission to move faster, not permission to ignore evidence that challenges the initial idea.
