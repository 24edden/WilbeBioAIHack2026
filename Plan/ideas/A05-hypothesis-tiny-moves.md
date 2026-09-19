# A05 — Incremental hypothesis editing

**Track:** 02 Orchestration or 03 Benchmarking · **Shape:** structured reasoning over hypotheses

**One-liner:** Represent a biological hypothesis as a structured object and let an agent make
small, typed edits to it as evidence arrives, so the reasoning trace is inspectable instead of
being a wall of prose.

## Problem

When an LLM reasons about a biological hypothesis, it rewrites the whole thing each turn. You
cannot tell what changed, why, or which piece of evidence moved it. Reasoning failures are
invisible because there is no diff.

## Current alternative

Long chain-of-thought prose, or a human maintaining a hypothesis in their head and a doc.

## What we build

A hypothesis as a typed structure — entities, relationships, supporting and contradicting
evidence, confidence. The agent may only modify it through a fixed set of moves: add
mechanism, weaken claim, split into competing alternatives, retract for lack of support. Each
move is logged with the evidence that triggered it. The output is a replayable history.

This deliberately echoes the "Tiny Moves" formalism from Anna Gogleva, a listed speaker
(`Context/challengeWeb.md`). That is a reason to expect an interested judge, and a reason to
be careful: **do not present it as our invention.** Cite it, build on it, say what is ours.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Move proposal and selection | Rosalind / OpenAI | Yes — OpenAI |
| Evidence grounding, model-derived signals | BioNeMo model outputs as evidence sources | Medium, needs deliberate design |
| Move execution, validation, replay, eval | NVIDIA Agent Toolkit | Yes |

## Data

A hypothesis with a known resolution in the literature, fed evidence in chronological order,
to see whether the agent converges on the accepted answer or gets stuck. Pick something where
the field changed its mind — those are the interesting traces.

## MVP by Saturday 18:00

One hypothesis, ten evidence items fed in sequence, a visual diff of the hypothesis at each
step, and one case where a contradicting item correctly forces a retraction.

## The demo frame

The replay. Scrub through the hypothesis evolving, and stop on the moment a contradicting
paper causes the agent to weaken rather than double down.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 7 | Meta-level, about the process rather than a result |
| NVIDIA + OpenAI use | 6 | OpenAI strong, NVIDIA needs engineering to be load-bearing |
| Execution | 5 | Highest vapour risk on the list, easy to build something that only looks impressive |
| Originality | 9 | Nobody else will do this |
| Presentation and repro | 8 | The replay is a genuinely novel demo object |

## Risks and kill criteria

- Unfalsifiable output. Mitigation: the known-resolution hypothesis, so there is a right
  answer. Without that ground truth, this is a toy.
- The typed move set is too rigid or too loose, and tuning it eats the weekend. Fix the move
  set by Saturday lunchtime and do not touch it again.
