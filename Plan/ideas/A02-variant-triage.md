# A02 — Variant triage with provenance and abstention

**Track:** 02 Orchestration, benchmarkable · **Shape:** evidence assembly + calibrated ranking

**One-liner:** Given a variant list, produce a ranked shortlist where every ranking decision
carries traceable evidence, and the system says out loud when the evidence is too thin to call.

## Problem

Variant interpretation means reconciling annotation databases, population frequencies,
computational predictors and literature. It is slow, inconsistent between analysts, and LLM
attempts at it confabulate citations — which in this domain is worse than useless.

## Current alternative (the baseline we must beat)

An analyst with VEP output and a browser, working down a spreadsheet. Also: asking a
frontier model directly, which is fast, fluent and unreliable.

Our claim must be **provenance and calibration, not raw accuracy**. Matching an analyst's
accuracy in a weekend is implausible. Making every claim checkable, and abstention explicit,
is achievable and is the thing that would actually get used.

## What we build

A pipeline that takes a VCF, annotates deterministically, scores with a genomic foundation
model, and has a reasoning layer assemble a per-variant case where each sentence is either
linked to a retrieved record or flagged as model opinion. Variants with insufficient evidence
go to an explicit "cannot call" bucket rather than being ranked anyway.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Deterministic annotation (VEP, gnomAD frequencies) | Classic tools, wrapped as agent tools | Yes, and deliberately not an LLM |
| Variant effect scoring | BioNeMo genomic model, Evo2-class | Yes — NVIDIA |
| Evidence assembly and abstention decision | Rosalind / OpenAI | Yes — OpenAI |
| Orchestration, provenance tracking, evaluation | NVIDIA Agent Toolkit | Yes |

## Data

ClinVar variants with known pathogenic/benign labels, held out of the prompt. Gives a real
accuracy number and a real calibration curve — rare for a hackathon, very convincing on a slide.

## MVP by Saturday 18:00

50 held-out variants, ranked, with a confusion matrix against the labels and a provenance
link on every claim.

## Stretch

Calibration plot: does stated confidence track accuracy? Ablations: same pipeline minus the
genomic model, minus retrieval, showing each component earns its place.

## The demo frame

Two reports for the same variant side by side. The bare model is fluent and cites something
that does not exist. Ours is shorter, sourced, and abstains on two variants. Then click a
citation and show it resolves.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 9 | Genuine clinical pain, abstention is the right framing |
| NVIDIA + OpenAI use | 8 | Both central, provided the genomic model does real work |
| Execution | 7 | Data is easy; risk is scope creep in the reasoning layer |
| Originality | 6 | Variant agents exist; calibrated abstention is the original part |
| Presentation and repro | 9 | Public labelled data, small, fully reproducible |

## Risks and kill criteria

- Evo2-class model unavailable on our instance → substitute any BioNeMo scorer, or drop to
  deterministic predictors and say so on the slide. The abstention story survives either way.
- Annotation tooling eats Saturday → pre-compute annotations for a fixed 50-variant set and
  ship them as a static input file. Decide by 13:00.
- "It is just RAG" objection from a judge → the answer is the calibration curve. Build it early.
