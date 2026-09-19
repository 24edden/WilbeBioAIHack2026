# D02 — Assay QC and failure diagnosis

**Track:** 04 Open · **Shape:** anomaly detection with an explanation layer

**One-liner:** Feed in plate reader output and get back not just "this plate failed" but a
specific, testable hypothesis about which physical step caused it.

## Problem

Plate-based assays fail in patterned, diagnosable ways — edge effects from evaporation, a
drifting multichannel pipette, a column skipped, a reagent added twice. Analysts spot the
obvious ones and miss the subtle ones, and the diagnosis lives in senior people's heads.

## Current alternative

Eyeballing a heatmap, plus experience.

## What we build

Two layers. A deterministic layer detects spatial patterns: row and column effects, edge
gradients, periodicity matching a multichannel head, single-well outliers. A reasoning layer
maps the detected pattern to candidate physical causes with a suggested check — and this
mapping is grounded in a written knowledge base, not invented by the model at runtime.

That grounding is the difference between a real tool and plausible-sounding nonsense.

**Without lab access, the knowledge base must be sourced from literature and published QC
guidance rather than from colleagues**, with a citation per entry. That is slower, but it is
also more defensible on a slide and more reproducible than "a scientist told us".

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Spatial pattern detection | Deterministic statistics | Yes |
| Pattern to cause mapping | Rosalind / OpenAI over a curated knowledge base | Yes — OpenAI |
| Orchestration and evaluation | NVIDIA Agent Toolkit | Yes |
| NVIDIA model layer | Weak | See risks |

## Data

Synthetic plates with injected known faults, which give exact ground truth. This was always
the strength of the idea and it survives the no-lab constraint intact.

What does not survive is the check that **our synthetic faults resemble real ones**. Substitute:
build the fault generator from published descriptions of plate artifacts, cite each one, and
look for public plate-reader datasets to compare the generated patterns against. State the
limitation plainly rather than implying the faults are validated.

## MVP by Saturday 18:00

Six fault types injected synthetically, detection and diagnosis accuracy for each, and a
confusion matrix showing which faults get mistaken for which.

## The demo frame

The confusion matrix, plus one worked case: a plate with two overlapping faults where the
system separates them. Overlapping faults are the case human eyeballing genuinely fails at, so
it is the honest place to claim an advantage.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 7 | Real pain, but argued from literature rather than shown |
| NVIDIA + OpenAI use | 4 | Same structural weakness as A03 and D01 |
| Execution | 9 | Synthetic ground truth makes this the safest build on the list, unaffected by the no-lab constraint |
| Originality | 6 | Plate QC tools exist; causal diagnosis from the pattern is less common |
| Presentation and repro | 9 | Synthetic data ships with the repo, fully reproducible |

## Risks and kill criteria

- Criterion 2. Unless an NVIDIA component becomes load-bearing, caps out around 7/10 overall.
- Synthetic faults do not resemble real ones, making the accuracy numbers meaningless. With no
  lab to check against, this risk is **unmitigated** — the only defence is citing each fault
  type to a published description and saying clearly on the slide that validation against real
  plates is future work. A judge who runs plates will ask.

## Verdict

Still the safest build on the list, but the no-lab constraint turned its main weakness — an
unvalidated fault model — from fixable into permanent. Combined with the Tech score of 4, not
a candidate. The synthetic-fault generator remains a good instance family for B01.
