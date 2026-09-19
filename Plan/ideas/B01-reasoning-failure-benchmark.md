# B01 — A benchmark for how bio agents fail

**Track:** 03 Benchmarking · **Shape:** adversarial eval suite + harness + results

**One-liner:** A test suite of biological tasks containing deliberately broken inputs, which
measures not whether an agent gets the right answer but whether it notices it cannot.

## Problem

Bio agent benchmarks measure accuracy on well-posed questions. Real research inputs are
mislabelled, contradictory, wrong-species, or simply absent. The dangerous failure is not a
wrong answer, it is a confident answer over a broken input. Nobody measures that.

## Current alternative

Accuracy-on-clean-data benchmarks, which every model passes well enough to be misleading.

## What we build

A suite of task instances in matched pairs: a clean version and a corrupted twin. Corruptions
are realistic, not adversarial nonsense:

- a protein sequence with a frameshift introduced
- gene symbols from the wrong organism, silently
- an expression matrix where two sample labels are swapped
- a question whose premise is false ("explain why gene X represses Y" when it does not)
- a file that is truncated mid-record
- units changed without changing the number

The metric is the **detection rate**: how often the system flags the problem rather than
producing fluent output. Report it per corruption type, because the profile is the finding.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Eval harness, run matrix, tracing, scoring | NVIDIA Agent Toolkit evaluation tooling | Yes — NVIDIA, this is the core |
| Systems under test | Rosalind / OpenAI models, with and without scaffolding | Yes — OpenAI |
| Bio-specific task instances | BioNeMo models as tools available to the agent under test | Medium |

## Data

Small, hand-built, and honest about it. 40 to 60 matched pairs is enough to show a profile.
Provenance for every instance so others can extend the suite.

## MVP by Saturday 18:00

Six corruption types, roughly 40 pairs, run against at least two configurations, with a
per-corruption detection-rate chart.

## Stretch

Show that a specific scaffold — a verification step, a tool-use requirement — raises
detection rate measurably. That turns a benchmark into a finding.

## The demo frame

One slide, a bar chart of detection rate by corruption type, with the worst bar highlighted
and the actual model output underneath it, confidently wrong. That image is the whole talk.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 8 | Directly about whether these tools are safe to use in research |
| NVIDIA + OpenAI use | 7 | Agent Toolkit eval is central; BioNeMo needs deliberate inclusion |
| Execution | 8 | Low compute, parallelisable across the team, degrades gracefully |
| Originality | 9 | Most teams will demo the happy path; we measure the unhappy one |
| Presentation and repro | 9 | A suite plus a harness is the most reproducible artifact possible |

## Risks and kill criteria

- Models detect everything and all bars are at 100%, leaving no story. Unlikely, and easily
  fixed by making corruptions subtler. Test three instances by hour 3 to calibrate difficulty.
- Suite looks arbitrary. Mitigation: each corruption type must map to a real incident someone
  on the team or a mentor has seen. Collect those anecdotes Friday night; they are also the
  best slide material.
- Reads as criticism of the sponsors' models. Mitigation: frame as "where scaffolding helps",
  test configurations rather than vendors, and include the scaffold that fixes it.

## Verdict

Cheapest to execute, hardest to make boring, and the only idea here whose value survives the
weekend as a reusable artifact.
