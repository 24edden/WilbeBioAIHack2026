---
title: Hackathon Plan
purpose: Idea generation, selection, and execution plans for the Wilbe Bio x AI hack
status: pre-event, no idea chosen yet
---

# Plan

Everything here was written **before** the event, without knowing the team composition or
what compute we'll actually get. It is scaffolding to make Saturday morning fast, not a
commitment. Expect to throw half of it away.

**Known constraint: we have no wet lab access.** No experiments, no lab-generated data, no
practitioner validating output in the room. Every plan here is revised for that; four ideas
were demoted because of it, and the reasoning is in pass 7 of the iteration log.

## Read in this order

| File | What it's for |
|---|---|
| [00-decision-framework.md](00-decision-framework.md) | How to choose an idea in 90 minutes without arguing for three hours |
| [02-scorecard.md](02-scorecard.md) | All ideas scored against the judging rubric, ranked |
| [finalists/](finalists/) | The three survivors, planned hour by hour |
| [01-weekend-timeline.md](01-weekend-timeline.md) | Generic weekend schedule with hard checkpoints |
| [03-risks.md](03-risks.md) | Failure modes that kill hackathon projects, and the pre-committed responses |
| [04-presentation.md](04-presentation.md) | Five-minute structure mapped to the five criteria |
| [05-reproducibility.md](05-reproducibility.md) | The repo checklist, worth a fifth of the score |
| [06-iteration-log.md](06-iteration-log.md) | How this plan evolved, what was rejected and why, and the open questions |
| [ideas/](ideas/) | All 16 candidates, one file each |

## The one-paragraph version

The rubric has five equal criteria (see `Context/judgingCriteria.md`). Most teams will
optimise the first three and lose points on **Originality** and **Presentation &
Reproducibility**, which are worth 40% between them. The highest-expected-value shape for
this event is **a working workflow plus an honest evaluation of when it breaks** — that
single deliverable scores on scientific relevance, execution, originality (most teams
demo the happy path only), and reproducibility (the eval *is* the reproduction recipe).
Every finalist below is built in that shape.

## Ground rules baked into these plans

1. **Nothing NVIDIA/OpenAI is allowed to be decorative.** If removing a component leaves
   the system working, it isn't part of the answer to criterion 2. See `Context/tooling.md`.
2. **Demo before polish.** A recorded demo must exist by Saturday night, not Sunday.
3. **Scope is a dial, not a decision.** Each plan has an MVP that is genuinely useful and
   stretch goals that are genuinely optional.
4. **Write the slides on Saturday.** Teams that start slides on Sunday present badly.
