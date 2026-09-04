---
name: litreview-corpus
description: Refine completed narrative-review triage from Retained Papers to Evidence Candidates and Core Papers, with researcher-controlled local full-text acquisition checkpoints.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Corpus Refinement

## Objective

Bridge discovery/triage and deep evidence work without treating every retained record as equally important.

The required funnel is:

`Retained Papers -> Evidence Candidates -> Core Papers`

Keep these meanings distinct:

- **Retained Paper**: relevant/background/adjacent enough that it should not be discarded after title/abstract triage.
- **Evidence Candidate**: a retained paper prioritized as likely to contribute useful evidence to the review.
- **Core Paper**: a smaller paper set prioritized for deep reading, evidence construction, and synthesis.

Core selection is prioritization, not proof that non-core retained papers are unimportant. Papers that are not selected into the next tier remain in the project library and can be revisited later.

## Researcher acquisition checkpoints

Corpus strategy is a genuine researcher choice because it affects coverage, time, and paid-AI workflow cost.

At the Retained and Evidence Candidate checkpoints, present two choices:

1. **Acquire the whole current tier locally**, then continue refinement.
2. **Continue narrowing first**, then acquire a smaller higher-priority corpus later.

At the Core Paper checkpoint, present:

1. **Acquire all Core Papers locally before evidence work**.
2. **Continue with current full-text coverage**, preserving missing papers as explicit limitations/verification tasks.

Record the choice with the runtime. Once the researcher chooses, do not ask again for every technical batch.

## Mandatory checkpoint explanation contract

Do **not** present a checkpoint as a bare choice such as “download all” versus “reduce the number of papers.” Before asking the researcher to choose, explain what the refinement actually does, what information it uses, what it does **not** know yet, and the practical trade-off between the options.

At every Retained or Evidence Candidate checkpoint, the user-facing explanation must include all of the following:

1. **Current tier and purpose** — state what the current papers represent and what the next tier is intended to represent.
2. **How papers will be reduced** — explain that the next tier is selected by an explainable metadata/title/abstract ranking, not by arbitrary deletion or citation count alone.
3. **Signals used by the ranking** — summarize the actual ranking dimensions listed below.
4. **Coverage safeguard** — explain that the selector first preserves representation across identified research streams, then fills the remaining places by total score.
5. **What the ranking cannot establish** — it is not yet a full-text methodological-quality appraisal and it does not prove that excluded-from-next-tier papers are low quality or irrelevant.
6. **What happens to non-selected papers** — they stay indexed in the project and can still be searched, downloaded, or promoted later; they are not deleted.
7. **Trade-off between the two choices** — acquiring now maximizes immediate full-text coverage but may download many papers that will later be deprioritized; refining first saves acquisition/reading effort but accepts a metadata/abstract-based prioritization step before full text is available.
8. **A recommendation with a reason** — when one option is clearly more efficient given corpus size and existing full-text coverage, recommend it explicitly, while keeping the final choice with the researcher.

A good checkpoint explanation should sound conceptually like this:

> You currently have 145 Retained Papers. If you refine first, LRC will not simply keep the most-cited papers. It will score the retained set using relevance to your Research Intent, triage priority/confidence, evidence potential visible in the abstract, bibliographic/provenance completeness, capped citation anchor value, recency, alignment with the selected focus, and research-stream coverage. The selector first protects representation across identified streams and then fills the remaining slots by score. This is still a metadata/abstract-based prioritization rather than a full-text quality review. Papers not promoted remain in the project. Acquiring now gives broader full-text coverage; refining first is usually more efficient when the retained corpus is large because fewer papers need to be downloaded and deeply read later.

Do not copy the example mechanically; adapt it to the actual tier, paper counts, and coverage returned by the runtime.

## Local acquisition rule

Full-text acquisition is a deterministic local-runtime task. Use the installed Python runtime through `lrc fulltext acquire . --tier <retained|evidence|core> --json`.

The acquisition command itself does **not** call an AI model once per paper. Do not make Codex/OpenCode search, open, and download papers one by one when the local runtime can perform the batch.

Only lawful open/public locations may be used. Never bypass paywalls, logins, CAPTCHAs, institutional access controls, or robots restrictions.

## Ranking contract

Run `lrc corpus rank . --to evidence --json` and later `lrc corpus rank . --to core --json` when routed by `lrc next`.

The current ranking engine is deliberately explainable and uses title/abstract/metadata signals. Its score combines:

- **Research relevance** from the triage label: relevant > background > adjacent.
- **Triage priority**: core-candidate > high > medium > low.
- **Triage confidence**: higher-confidence classifications receive more weight.
- **Evidence potential** from whether a substantive abstract is available and how informative it appears at metadata level.
- **Bibliographic/provenance completeness** such as DOI, journal/authorship metadata, and confirmation across multiple scholarly providers.
- **Capped citation/anchor value** using a logarithmic contribution so highly cited older papers cannot dominate the ranking.
- **Temporal relevance** so recent work can receive additional weight without automatically displacing older anchor studies.
- **Selected-focus alignment** when the researcher has already focused the discovery campaign.
- **Research-stream coverage** so the next tier does not collapse into only the largest or highest-scoring stream.

Citation count must never be the sole ranking criterion. Preserve representation across meaningful streams rather than simply taking the first N highest-scoring records.

### Current weighting logic

The current v1 metadata/abstract score is intentionally bounded:

- research relevance: up to 30 points;
- triage priority: up to 18 points;
- triage confidence: up to 6 points;
- evidence potential: up to 8 points;
- bibliographic completeness: up to 6 points;
- multi-provider provenance: up to 6 points;
- citation/anchor value: up to 8 points and logarithmically capped;
- temporal relevance: up to 6 points;
- selected-focus alignment: up to 7 points.

After scoring, the selector first takes representatives needed to preserve the available research streams and only then fills remaining slots by total score.

### Adaptive reduction size

The toolkit does not force a fixed percentage in every project. It uses an adaptive target so small corpora are not reduced unnecessarily:

- **Retained -> Evidence Candidates**: if there are 40 or fewer retained papers, keep the full set; otherwise target roughly 45% of the source set, with a normal floor of 35 and ceiling of 90 papers.
- **Evidence Candidates -> Core Papers**: if there are 18 or fewer evidence candidates, keep the full set; otherwise target roughly 42% of the candidate set, with a normal floor of 18 and ceiling of 45 papers.

If the researcher supplies an explicit `--max-papers`, that user-specified cap overrides the automatic target within the available source count.

These target sizes are workflow heuristics, not claims that a specific literature review academically requires exactly that number of papers.

## Important interpretation boundary

Ranking based on metadata/abstract is not full-text analysis. Keep the ranking basis and confidence explicit.

In particular, do not describe `bibliographic_quality` as if LRC has already established journal prestige, methodological rigor, risk of bias, causal credibility, or study validity. At this stage it mainly reflects bibliographic completeness and source/provenance signals available to the runtime. Deeper methodological appraisal belongs in later full-text evidence work.

## How to recommend an option

Use corpus size and current full-text coverage to make a practical recommendation, but never silently decide for the researcher.

- For a **large Retained corpus with little/no local full text**, usually recommend **refine first** because downloading the entire retained set creates substantial acquisition and reading overhead before prioritization.
- For a **small Retained corpus**, acquiring first can be reasonable because the refinement stage may keep most or all papers anyway.
- At the **Evidence Candidate** stage, recommend acquisition first when the set is already manageable and the review would benefit from stronger full-text evidence before Core selection; recommend refine first when the candidate set remains large and the researcher is primarily trying to minimize acquisition cost/time.
- At the **Core Paper** stage, acquisition is normally the preferred option for evidence quality when lawful full text is still missing for many core papers; continuing without it is acceptable only when the researcher accepts explicit verification limitations.

Whenever recommending, state the reason in terms of **coverage, workload, evidence quality, and cost/efficiency**, not only the number of papers.

## Orchestration

For an existing project, begin with `lrc next . --json` and follow its structural action.

When a corpus checkpoint is returned, stop and present the choice in researcher-friendly language **using the Mandatory checkpoint explanation contract above**. After the researcher decides, continue ranking or local acquisition automatically until the next genuine checkpoint.

On macOS, if `lrc` is not visible to a GUI AI host after installation, use `$HOME/.local/bin/lrc` as the launcher path and continue from the same project state.
