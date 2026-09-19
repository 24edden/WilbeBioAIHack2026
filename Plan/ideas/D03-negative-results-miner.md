# D03 — Mining what did not work

**Track:** 04 Open · **Shape:** extraction from an underused corpus

**One-liner:** Extract negative and inconclusive results from papers — the conditions that
failed, the constructs that did not express — and make them searchable before someone repeats
them.

## Problem

Negative results are buried in supplementary material and in sentences like "initial attempts
using X were unsuccessful". They are never indexed. Labs repeat each other's failures
continuously, and this is one of the largest avoidable costs in experimental science.

## Current alternative

Nothing. There is no search engine for what did not work.

## What we build

An extraction pipeline over open-access full text that finds negative-result statements,
normalises them into structured claims (entity, method, outcome, context), and exposes a
search over them. Includes a confidence score and a link back to the exact sentence, because
an unsourced negative claim is worse than no claim.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Full-text retrieval | Open-access corpus, for example PubMed Central OA subset | Yes |
| Negative-statement extraction and normalisation | Rosalind / OpenAI | Yes — OpenAI |
| Embedding and semantic search at scale | GPU embedding, NVIDIA stack | Yes — NVIDIA, and it scales with corpus size |
| Pipeline orchestration | NVIDIA Agent Toolkit | Yes |

## Data

PubMed Central open-access subset, restricted to one subfield so results are dense enough to
be convincing. Breadth is the enemy here.

## MVP by Saturday 18:00

A few thousand papers in one subfield, extracted negative claims, search interface, and
precision measured by manually checking a sample of 50 extractions.

## The demo frame

Search a construct or condition and surface three papers that quietly reported it failing,
each with the sentence highlighted. Then ask the room whether anyone has lost a month to
something like this.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 9 | Large, real, and immediately legible to any researcher |
| NVIDIA + OpenAI use | 7 | Embedding at scale is genuine NVIDIA work; extraction is genuine OpenAI work |
| Execution | 6 | Corpus handling is a time sink; precision measurement is manual |
| Originality | 8 | Rarely attempted, and the framing is memorable |
| Presentation and repro | 7 | Public corpus, though a full rerun is expensive |

## Risks and kill criteria

- Extraction precision is low and the search returns noise. Mitigation: measure precision on
  50 samples by Saturday afternoon. **If precision is under roughly 60%, narrow the claim type
  drastically** — for example only "construct did not express" — rather than trying to fix
  general extraction.
- Corpus download and parsing eats Saturday. Pre-download Friday night if the network allows.
