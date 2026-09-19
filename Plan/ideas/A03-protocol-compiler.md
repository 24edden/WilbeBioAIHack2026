# A03 — Wet-lab protocol compiler

**Track:** 04 Open, or 02 · **Shape:** natural language in, checked executable protocol out

**One-liner:** Turn a loosely described experiment into a step-by-step protocol where every
number is computed by real code, and every ambiguity is surfaced as a question instead of
being silently guessed.

## Problem

Protocols in papers are underspecified. Scientists reconstruct them by hand, make arithmetic
errors in dilutions and molarity, and discover the gaps at the bench. An LLM asked to do this
will cheerfully invent a plausible concentration, which is exactly the failure that makes
scientists distrust these tools.

## Current alternative

Copy the methods section, adapt by hand, check the maths twice, ask a colleague.

## What we build

A compiler, not a chatbot. The LLM does extraction and planning. A deterministic layer does
arithmetic, unit handling and constraint checking: volumes fit the vessel, concentrations are
achievable from available stocks, incompatible reagents are flagged. Underspecified inputs
become explicit questions with suggested defaults.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Extraction and planning | Rosalind / OpenAI | Yes — OpenAI |
| Unit and quantity solver, constraint checks | Deterministic Python with a units library | Yes, and the point is that it is not the model |
| Orchestration, human-in-the-loop question gates | NVIDIA Agent Toolkit | Yes |
| Model layer | **No natural NVIDIA component** | **This is the problem, see risks** |

## Data

Published methods sections, and protocol repositories such as protocols.io where the same
procedure appears in several versions. **We have no lab access, so there is no bench
validation available** — the evaluation has to be constructed instead of observed.

The workable substitute: take a protocol that exists in two published versions, give the
compiler the vaguer one, and check whether the questions it raises are exactly the details the
more precise version specifies. That is a real, checkable test of whether it finds the right
gaps, and it needs nobody's bench time.

## MVP by Saturday 18:00

Three protocols compiled, one deliberately ambiguous input showing the system asking rather
than guessing, one arithmetic trap where a bare LLM gets the dilution wrong and the compiler
does not, and the vague-versus-precise gap-detection score.

## The demo frame

Side by side: the LLM confidently outputs a wrong molarity, the compiler outputs the correct
one plus a question. Then the gap-detection result — of the N details the precise protocol
specifies and the vague one omits, the compiler asked about M of them.

Without a bench scientist to confirm the errors are realistic, **the arithmetic trap must be
verifiable from first principles on the slide**, so the audience checks the maths themselves
rather than taking our word for it.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 7 | Real problem, but we cannot show it landing with a practitioner |
| NVIDIA + OpenAI use | 4 | Fatal weakness, no natural NVIDIA component |
| Execution | 8 | Low compute, mostly software, very achievable |
| Originality | 7 | "Compiler not chatbot" framing is distinctive |
| Presentation and repro | 8 | Cheap, reproducible; the demo lost its human confirmation |

## Risks and kill criteria

- Criterion 2 is the kill risk, not execution. A 4 there caps the total. Either find a
  load-bearing NVIDIA component — for example the protocol expresses a construct that came
  out of a BioNeMo design step, making the compiler the last mile of a design pipeline — or
  accept losing a fifth of the score.
- **No bench validation is available to us.** Everything rests on the vague-versus-precise
  construction. If that comparison cannot be set up by Saturday lunchtime, this idea has no
  evidence behind it and should be dropped.

## Verdict

Good product, poor rubric fit, and the no-lab constraint removed the demo moment that made it
compelling. **Not a candidate for this event.** Kept on the list because the deterministic
quantity solver is a reusable component, and because it explains why E01 exists.
