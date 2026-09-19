# B02 — Robustness and calibration profile for biomolecular models

**Track:** 03 Benchmarking · **Shape:** systematic perturbation sweep

**One-liner:** Map where a structure-prediction or property-prediction model's confidence
stops meaning anything, by perturbing inputs in controlled ways and charting the response.

## Problem

People read pLDDT and similar confidence scores as if they were probabilities. They are
well-behaved on inputs resembling training data and poorly behaved elsewhere, and users have
no map of the boundary.

## Current alternative

Folklore. "Disordered regions give low pLDDT." True, but not a map, and not quantitative for
the cases people actually hit.

## What we build

A perturbation sweep. Take a set of proteins with known structures, apply graded
perturbations, and chart predicted confidence against actual accuracy at each level:

- truncation from the N or C terminus, in steps
- point mutations, from 1 to N, conservative versus radical
- shuffling a loop region while leaving the core intact
- homolog replacement at decreasing sequence identity
- low-complexity or repeat insertions
- domain swaps between unrelated proteins

Output: confidence-versus-accuracy curves per perturbation type. The deliverable is the map,
plus the specific regimes where confidence stays high while accuracy collapses.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Model under test | BioNeMo NIM, ESMFold or AlphaFold2 class | Yes — NVIDIA, it is the subject |
| Sweep orchestration, batching, caching, eval | NVIDIA Agent Toolkit | Yes |
| Perturbation design, result interpretation, write-up | Rosalind / OpenAI | Medium — must do real work, see risk |

## Data

Proteins with experimental structures, chosen across fold classes. 20 proteins by 6
perturbation types by 5 levels is 600 predictions — plan the compute budget at hour 1 and cut
the grid to fit rather than discovering the overrun at hour 20.

## MVP by Saturday 18:00

Three perturbation types, 10 proteins, complete curves, and one clearly identified regime
where the model is confidently wrong.

## The demo frame

A single confidence-versus-accuracy plot with a red region annotated "here it is confident
and wrong", and the structure overlay for one such case: predicted versus experimental.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 8 | Everyone using these models needs this and nobody has it |
| NVIDIA + OpenAI use | 6 | NVIDIA central; OpenAI side is weak unless designed in properly |
| Execution | 7 | Mostly a compute-scheduling problem, which is a good problem to have |
| Originality | 7 | Robustness studies exist; a same-day map with structure overlays is fresh |
| Presentation and repro | 9 | Deterministic sweep, fully scriptable, trivially reproducible |

## Risks and kill criteria

- The OpenAI half is decorative, which costs criterion 2. Fix by making the reasoning layer
  choose the next perturbation adaptively — an active search for the failure boundary rather
  than a fixed grid. That also makes it a better project.
- Compute overrun. Pre-commit to a grid that fits in half the budget, and treat the rest as
  headroom for reruns.

## Note

This is A01's fallback. If the design loop fails, the runs already done can be re-framed as
this, with no new data collection.
