# B04 — Can an agent reproduce a paper's analysis?

**Track:** 03 Benchmarking · **Shape:** end-to-end reproduction attempt, scored

**One-liner:** Give an agent a methods section and the raw data, and score how close it gets
to the published figure — and where exactly it goes off the rails.

## Problem

Computational reproducibility in biology is poor. Methods sections omit parameters, versions
and preprocessing. If an agent can reproduce an analysis, that is a real capability claim; if
it cannot, *the reason it fails* is a direct measurement of what methods sections leave out.

Note the second framing is the better one, and it wins either way. Design for it.

## Current alternative

A graduate student spending a week failing to reproduce a figure and assuming it is their fault.

## What we build

3 to 5 papers with public data and a reproducible headline figure. The agent gets the methods
text and the data, and produces an analysis. We score similarity to the published result and
categorise every divergence: missing parameter, ambiguous ordering, undocumented filtering,
version drift, or agent error.

The **divergence taxonomy is the deliverable.** The reproduction score is the hook.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Methods comprehension and analysis planning | Rosalind / OpenAI | Yes — OpenAI |
| Execution environment, tools, tracing | NVIDIA Agent Toolkit on Brev | Yes |
| Any model-based analysis step in the papers | BioNeMo, if the chosen papers use such methods | Choose papers so this is true |

## Data

Choose papers Friday night, not Saturday. Criteria: public raw data under 1 GB, a figure
reducible to a small number of statistics, and a methods section under two pages. Bulk
RNA-seq differential expression papers are the safest choice.

## MVP by Saturday 18:00

Two papers attempted, one at least partially reproduced, and a fully categorised divergence
list for both.

## The demo frame

Published figure and agent figure side by side, then the divergence list with the single
missing sentence in the methods that caused the biggest deviation.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 9 | Reproducibility is a first-order problem in the field |
| NVIDIA + OpenAI use | 6 | OpenAI strong, NVIDIA weak unless papers are chosen for it |
| Execution | 4 | **Highest risk here.** Data wrangling is unbounded and unglamorous |
| Originality | 8 | Rarely attempted, very quotable if it works |
| Presentation and repro | 8 | Strong artifact, though our own runs are heavy |

## Risks and kill criteria

- Data acquisition eats the weekend. This is the likeliest failure and it is not a clever
  failure. Pre-commit: **if the data is not downloaded and loading by Saturday 12:00, drop to
  one paper.** If it is not loading by 16:00, abandon and fall back to B01.
- Nothing reproduces at all, and the demo is a list of failures. This is survivable only if
  the divergence taxonomy is sharp. Build it first, not last.
