# E02 — Which experiment should we run next?

**Track:** 02 Orchestration or 03 Benchmarking · **Shape:** decision support under uncertainty

**One-liner:** Given two competing hypotheses, have the system propose the experiment that
most efficiently distinguishes them, and evaluate whether its choices actually beat a
scientist's default.

## Problem

Choosing the next experiment is the highest-value decision in a research programme and the
least supported by software. LLMs asked for experiment ideas produce long lists of plausible
suggestions with no notion of which one is *discriminating* versus merely confirmatory.

## Current alternative

A lab meeting.

## What we build

The system takes competing hypotheses and a set of feasible assays, and ranks experiments by
expected discrimination: which outcome would change our belief most, and which experiments
would leave us equally uncertain whatever the result. Expected information gain is computed
explicitly rather than asserted in prose.

The sharp version of the claim: **most proposed experiments are confirmatory, and we can show
that quantitatively.**

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Hypothesis representation, possibly from A05 | Structured objects | Yes |
| Outcome prediction under each hypothesis | BioNeMo models where the assay is predictable computationally | Yes — NVIDIA, this is the load-bearing link |
| Proposal, scoring, and explanation | Rosalind / OpenAI | Yes — OpenAI |
| Orchestration and evaluation | NVIDIA Agent Toolkit | Yes |

## Data

Retrospective validation is the trick that makes this evaluable in a weekend: take a published
research programme where the decisive experiment is known, present the system with the state
of knowledge beforehand, and see whether it proposes the experiment that was actually decisive.

## MVP by Saturday 18:00

Three historical cases, ranked experiment proposals for each, and the rank the actually
decisive experiment received. Plus the confirmatory-versus-discriminating split across all
proposals.

## The demo frame

A historical case. The system's top proposal next to what the lab actually did next, and how
long the field took to get there.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 9 | The highest-leverage decision in research |
| NVIDIA + OpenAI use | 6 | NVIDIA only if outcome prediction is genuinely computational |
| Execution | 5 | Case construction is slow and needs real domain knowledge |
| Originality | 9 | Very few teams will attempt decision-theoretic framing |
| Presentation and repro | 7 | Compelling story, small and arguable sample |

## Risks and kill criteria

- Hindsight bias: we choose cases where the answer is known and the framing is obvious. Have
  one person build the cases *blind* to the system's output.
- Three cases is a small sample and a judge will say so. Own it on the slide: call it an
  illustration of a method, not evidence of performance.
