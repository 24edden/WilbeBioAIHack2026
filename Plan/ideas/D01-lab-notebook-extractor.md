# D01 — Lab notebook to structured record

**Track:** 04 Open · **Shape:** vision extraction with uncertainty

**One-liner:** Photograph a handwritten lab notebook page and get a structured, searchable
record, with every low-confidence field marked for human review rather than quietly guessed.

## Problem

Enormous amounts of experimental detail live in handwritten notebooks and never become data.
Retrospective analysis is impossible; institutional memory leaves with the postdoc.

## Current alternative

Manual transcription, which nobody does, or nothing, which everybody does.

## What we build

Vision extraction into a schema — date, sample IDs, conditions, volumes, observations — with
per-field confidence, and a review UI that shows the cropped image region next to each
extracted field. The interaction model is the product: extraction you can audit at a glance.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Vision extraction | OpenAI vision models | Yes — OpenAI |
| Schema, validation, review workflow | Agent Toolkit plus a small UI | Partly |
| NVIDIA component | **Weak, same problem as A03** | See risks |

## Data

**No lab access means no real notebook pages.** Written by us: invented experiments in our own
handwriting, deliberately varied across writers, with messiness injected on purpose —
crossings-out, marginal notes, a coffee ring, a page written in a hurry.

This is a genuine loss of realism and it is the idea's core problem now. The upside is that
the page set becomes publishable with the repo, which the real-notebook version never was.

## MVP by Saturday 18:00

Five pages, structured output, review interface with image crops, and honest per-field
accuracy measured against manual transcription of those same pages.

## The demo frame

A messy real page, the structured output beside it, and the three fields the system correctly
refused to guess.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 6 | Real, but we can only demonstrate it on pages we wrote ourselves |
| NVIDIA + OpenAI use | 3 | **Disqualifying without redesign** |
| Execution | 8 | Very achievable, pleasant demo |
| Originality | 5 | Document extraction is well-trodden; the audit UI is the fresh part |
| Presentation and repro | 7 | Self-authored pages ship with the repo, so reproduction is actually easier |

## Risks and kill criteria

- Criterion 2 kills this outright unless an NVIDIA component is designed in.
- **Circularity.** We write the pages, we know what they say, and we score the extraction
  against our own transcription. A judge will notice that we chose the difficulty. There is no
  fix available without real pages.

## Verdict

Do not pick. Kept on the list as the clearest illustration that the most useful idea and the
best-scoring idea are not the same thing — and now, that a data source you cannot access is a
hard constraint rather than an inconvenience.
