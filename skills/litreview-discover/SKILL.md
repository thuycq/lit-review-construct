---
name: litreview-discover
description: Run narrative-review literature discovery inside an active Lit Review Construct workspace. Use only when `.litreview/project.yaml` exists or the researcher explicitly invoked LRC. Handles broad retrieval, focus, progressive triage, bounded automatic citation refinement, saturation assessment, and Research Landscape construction.
license: MIT
compatibility: Codex and OpenCode
metadata:
  product: lit-review-construct
  stage: literature-discovery
---

# Lit Review Construct — Beta Literature Discovery

## Boundary

Discovery builds and narrows a sufficiently broad literature universe for a **narrative review**. Do not claim exhaustive retrieval, PRISMA/systematic-review completeness, or that all indexed records must be screened. Do not infer definitive findings or global novelty from metadata/abstracts.

The researcher controls scholarly scope, focus, and the final decision that discovery is sufficient. AI controls technical search execution, deduplication, progressive triage, citation chaining, and map rebuilding between those checkpoints.

## Resume

Begin/resume with `lrc discover next . --json` and follow the structural action. Keep technical output hidden in researcher-facing mode.

If a provider fails/rate-limits, keep successful results from other providers and preserve the failure in state. Never erase an iteration because one provider failed.

## Funnel

**Intent → broad Query Plan/retrieval → early map → researcher focus/scope checkpoint → focused retrieval → automatic bounded refinement → saturation checkpoint → researcher finish → Research Landscape.**

Large corpora remain local. Use bounded packets.

## Broad discovery and early map

When routed to broad planning/retrieval:
1. create several interpretable complementary query families;
2. save and execute the Query Plan across available OpenAlex/Crossref/Semantic Scholar providers;
3. preserve discovery provenance and deduplicate conservatively;
4. build the early provisional map before deep filtering.

At the first meaningful map, stop for the researcher to choose/adjust focus, broaden, or change scope. Streams and gaps are provisional.

## Researcher discovery decisions

When `next_action=researcher_decision_required`, present researcher-friendly choices only. The actual scholarly actions are:
- **focus/refocus** — choose/re-prioritize scholarly streams;
- **continue/broaden** — expand the literature universe with complementary query families;
- **change scope** — revise the Research Intent;
- **finish** — researcher declares current discovery sufficient for the narrative-review purpose;
- **filter more** — explicit optional request to screen more of the existing corpus without broadening.

A recommendation is allowed; it is not a recorded decision. Record only explicit researcher choice.

If runtime returns `discovery_saturated=true` / `recommended_option=finish`, explain why finish is reasonable using marginal search/graph gain and stability, not simply the percentage untriaged. The researcher still decides.

## Progressive triage

When routed to `continue_triage`:
- prepare a bounded priority batch (normally 100);
- classify title/abstract/metadata as `relevant`, `background`, `adjacent`, `out_of_scope`, or `unresolved`;
- assign priority `core_candidate`, `high`, `medium`, `low`;
- use short auditable rationale/tags;
- save the batch and immediately continue according to runtime.

Triage is not full-text screening. Prefer `unresolved` over guessing.

## Automatic beta refinement

When `next_action=refine`, **do not ask the researcher to approve another refine round**. This is technical narrowing after a scholarly focus has already been selected.

Complete one bounded cycle:
1. priority-triage an existing-corpus batch if requested;
2. citation/reference chaining from a small set of strong relevant/core seeds (never all records; max 20 seeds);
3. preserve partial provider success and deduplicate graph additions;
4. priority-triage a bounded graph-addition batch;
5. rebuild/save the narrowing review;
6. call `lrc discover next . --json` again.

Beta stopping policy is handled by runtime: at most three automatic citation-refinement rounds, with earlier stopping when marginal graph gain is low or drops sharply. Do not create a human checkpoint between those technical rounds.

Untriaged records may remain numerous because citation expansion can enlarge the universe. High untriaged percentage alone is not a reason to keep refining.

## Citation graph discipline

Citation chaining complements keyword search. Use strong core/relevant seeds only. Preserve `.litreview/data/paper_graph.jsonl`. Citation count is not relevance. Graph additions must re-enter dedupe + triage.

## JSONL/provider resilience

- Never allow one malformed JSONL record to strand the project; tolerant loaders may skip/report it.
- Normalize/sanitize embedded line breaks in provider strings before JSONL write.
- Preserve successful providers when OpenAlex/S2/Crossref fails or returns zero.

## Final Research Landscape

Only after the researcher explicitly chooses `finish`:
1. prepare current Landscape from retained triaged `relevant/background/adjacent` literature;
2. exclude out-of-scope records;
3. retain unresolved/untriaged/provider limitations as warnings;
4. identify anchors, streams, debates, methods, recent developments, contradictions and unresolved questions;
5. save the Research Landscape and continue automatically to lawful OA coverage/Evidence Mapping.

Do not make universal gap/absence claims from the bounded Landscape. Use language such as “within the reviewed corpus…” until stronger verification exists.

## Researcher-facing response

Hide CLI, IDs, JSON, line numbers and test/provider logs by default. Give the researcher field-level meaning, not implementation detail, and end with exactly one runtime/fallback **Suggested next message**.
