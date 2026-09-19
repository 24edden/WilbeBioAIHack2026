# A01 — Closed-loop binder design

**Track:** 02 Orchestration · **Shape:** generate → filter → iterate

**One-liner:** An agent loop that designs a protein binder against a target, computationally
screens its own designs, and uses the failures to steer the next round.

## Problem

Binder design produces thousands of candidates; the bottleneck is triage. Most pipelines
generate once, filter once, and hand a human a ranked list with no notion of *why* the
rejected ones failed.

## Current alternative (the baseline we must beat)

A human running RFdiffusion → ProteinMPNN → AlphaFold2 by hand with a fixed confidence
cutoff. Our version has to show that closing the loop — feeding failure structure back into
the next generation round — beats one-shot generation at equal compute. If we cannot show
that, this is a pipeline re-run, not a project.

## What we build

A three-round loop where each round's rejected designs are summarised into a natural-language
constraint ("hydrophobic patch at the interface", "helix propensity too low in the linker")
that conditions the next round's generation.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Generate backbone / sequence | BioNeMo NIMs (RFdiffusion, ProteinMPNN) | Yes — NVIDIA |
| Fold and score complex | BioNeMo (AlphaFold2 / ESMFold), ipTM + pLDDT | Yes — NVIDIA |
| Failure summarisation into next-round constraints | Rosalind / OpenAI | Yes — OpenAI, the novel box |
| Loop control, retries, tracing | NVIDIA Agent Toolkit | Yes |

## Data

One well-characterised target with a known binder and a PDB complex, so we have ground
truth to talk about. Do not pick a novel target; we cannot validate it and the demo becomes
unfalsifiable.

## MVP by Saturday 18:00

One target, three rounds, a plot of score distribution per round, and the actual text of
the constraints the model generated between rounds.

## Stretch

A negative control where the constraints are randomised, proving the improvement comes from
the reasoning rather than from resampling. This is worth more than a second target: it is
the difference between "scores went up" and "scores went up because of the thing we built".

## The demo frame

Three score distributions shifting right, with the model's own written explanation of what
it changed between rounds underneath.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 8 | Real bottleneck, real workflow |
| NVIDIA + OpenAI use | 9 | Both deeply load-bearing |
| Execution | 5 | Heaviest compute here; three NIMs must all work |
| Originality | 4 | The default idea. Expect other teams to pick it |
| Presentation and repro | 7 | Visual, but runs are expensive to reproduce |

## Risks and kill criteria

- NIM containers do not pull or do not fit in memory → by 14:00 Saturday, if the fold step
  is not running end to end, drop to ESMFold-only scoring and cut a generation stage.
- Compute budget exhausted by round 2 → pre-compute round 1 offline, demo rounds 2–3 live.
- Loop improvements within noise → pivot the story to B02 (robustness) using the runs
  already done. This fallback is free; the data is the same.

## Verdict

Strong on paper, weak on originality, most likely idea for another team to also pick. Only
run this if we commit to the negative control, which is the part nobody else will bother with.
