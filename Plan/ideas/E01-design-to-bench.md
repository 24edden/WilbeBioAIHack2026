# E01 — Design to bench, end to end (hybrid of A01 and A03)

**Track:** 02 Orchestration · **Shape:** computational design that terminates in an executable protocol

**One-liner:** A pipeline that designs a construct computationally and does not stop at a
FASTA file — it emits the ordering sheet and the bench protocol needed to actually make it.

## Why this hybrid exists

A01 has strong NVIDIA and OpenAI usage but weak originality. A03 has strong originality and a
strong demo but no NVIDIA component. Composed, each fixes the other's failing, and the
composition is itself the novel claim: **everyone demos design, nobody demos the handoff.**

## Status: demoted — we have no lab access

This was the ceiling pick until the no-wet-lab constraint landed. The entire claim was *"a
scientist could run this on Monday"*, and the evidence for it was a bench scientist saying so
in the room. Without that, we are asserting that a generated protocol is runnable with nothing
behind the assertion — and a confidently wrong protocol is worse than no protocol.

**Not a finalist.** Read on only if the team turns out to include someone with real bench
experience who is willing to review the output on paper and be quoted on the slide. That is a
weaker form of the same evidence, and it drops the scores below.

## Problem

Computational design outputs end at a sequence. Everything between a designed sequence and a
tube in a freezer — codon optimisation, vector choice, primer design, ordering, expression
protocol — is manual, error-prone, and where designs actually die.

## Current alternative

A computational scientist emails a FASTA to a wet-lab scientist and a week of back and forth
follows.

## What we build

Design → validate → **translate to bench artifacts**. The final stage produces codon-optimised
sequences for the intended host, a vector and cloning strategy, primers, an ordering table,
and an expression protocol with all quantities computed deterministically.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Sequence or backbone generation | BioNeMo NIMs | Yes — NVIDIA |
| Structural validation and filtering | BioNeMo folding model | Yes — NVIDIA |
| Codon optimisation, primer design | Deterministic tools | Yes |
| Strategy selection, protocol drafting | Rosalind / OpenAI | Yes — OpenAI |
| Quantity and constraint checking | Deterministic solver from A03 | Yes |
| Orchestration with human decision gates | NVIDIA Agent Toolkit | Yes |

Six boxes is over the three-box rule from the decision framework. **Cut at least two.** The
likeliest cuts: drop generation and start from a fixed designed sequence, and drop primer
design. The handoff is the story, not the design.

## The demo frame

One continuous run: target in, ordering sheet and protocol out.

The original ending — a bench scientist confirming they could run it — is unavailable. The
surviving substitute is weaker and must be framed honestly: compare the generated protocol
against a published protocol for the same construct type, and show the differences. That
demonstrates plausibility, **not runnability**, and the slide must say which one it is showing.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 7 | Still a real gap, but we cannot show we closed it |
| NVIDIA + OpenAI use | 9 | Both load-bearing throughout, unaffected |
| Execution | 5 | Too many stages. Score rises to 7 if cut to three |
| Originality | 7 | Framing survives; the memorable demo does not |
| Presentation and repro | 6 | The narrative now ends on a caveat rather than a confirmation |

Was 39 before the no-lab constraint; 34 after. The drop is entirely in what we can *show*,
not in what we can *build*, which is exactly the kind of loss that is invisible until
presentation day.

## Risks and kill criteria

- Scope. This is the most ambitious plan here and the most likely to end as four half-working
  stages. **Pre-commit to the cut at Saturday 14:00** based on what is actually running.
- **Unverifiable last mile.** This is now a precondition failure, not a risk. We cannot check
  the protocol is runnable, so the strongest honest claim is "structurally complete and
  consistent with published protocols", which is a much smaller claim than the one the idea
  was built to make.
- Overclaiming to compensate. The temptation on Sunday will be to say "a scientist could run
  this". Do not. Judges from these companies will ask who checked.
