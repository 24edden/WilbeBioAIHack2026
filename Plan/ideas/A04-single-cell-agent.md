# A04 — Single-cell analysis agent with a sanity layer

**Track:** 02 Orchestration · **Shape:** analysis pipeline driven by an agent

**One-liner:** An agent that takes a raw single-cell dataset through QC, clustering and cell
type annotation, and flags the analysis decisions a human would want to override.

## Problem

scRNA-seq analysis is a long chain of judgement calls — QC thresholds, number of PCs,
clustering resolution, annotation — and the defaults are wrong often enough to matter. Junior
analysts accept defaults; the results look fine and are subtly wrong.

## Current alternative

A scanpy or Seurat notebook with default parameters, copied from a tutorial.

The agent must beat *the default notebook*, not a human expert. That is a realistic bar and
an honest one to state on a slide.

## What we build

An agent that runs the pipeline, but at each judgement point records the decision, the
alternatives considered, and a sensitivity check: does the biological conclusion survive a
different threshold? Output is an annotated notebook plus a "fragile conclusions" section.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Pipeline steps | scanpy, wrapped as deterministic tools | Yes |
| Cell embeddings and annotation | BioNeMo single-cell model, Geneformer-class | Yes — NVIDIA |
| Decision reasoning and sensitivity narration | Rosalind / OpenAI | Yes — OpenAI |
| Orchestration and tracing | NVIDIA Agent Toolkit | Yes |

## Data

A public dataset with published cell type labels, so annotation accuracy is measurable.
CELLxGENE has candidates. Subsample hard for speed — 5k cells is plenty for a demo.

## MVP by Saturday 18:00

One dataset, end-to-end run, annotation accuracy against published labels, and at least one
genuine instance of the sensitivity check catching a conclusion that flips under a different
clustering resolution.

## The demo frame

The fragile-conclusions panel. "This cluster is labelled X at resolution 1.0 and splits into
two populations at 1.2, and here is what that changes."

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 7 | Real, though a crowded application area |
| NVIDIA + OpenAI use | 7 | Good if the single-cell model genuinely drives annotation |
| Execution | 7 | Well-trodden tooling, low surprise risk |
| Originality | 5 | Many single-cell agents exist; sensitivity analysis is the fresh angle |
| Presentation and repro | 8 | Public data, notebook output, easy to reproduce |

## Risks and kill criteria

- Becomes a scanpy wrapper with a chat box → the sensitivity checks are the project. If they
  are not working by Saturday afternoon, this idea has no core.
- Dataset too large for the time budget → subsample at load, decided at hour 1, not hour 10.
