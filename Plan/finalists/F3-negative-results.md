# F3 — A search engine for what did not work (the ceiling)

Full concept in [../ideas/D03-negative-results-miner.md](../ideas/D03-negative-results-miner.md).

Replaces the design-to-bench plan, which the no-wet-lab constraint made unverifiable. See
[../06-iteration-log.md](../06-iteration-log.md), pass 7.

**Pick this if:** we want the most memorable pitch in the room and have someone comfortable
with corpus-scale text processing. Fully computational, no lab, no experiments, no external
validation needed.

**Headline claim:** "There is no search engine for what didn't work. Labs repeat each other's
failures continuously. We built one for a single subfield in a weekend."

## Why it survived the constraint when E01 did not

Its evidence is internal. Precision is measured by manually checking a sample of our own
extractions against the source sentences — work any team member can do at a laptop. Nothing
depends on access we do not have.

## The scoping decision that decides this project

**Narrow the subfield hard, on Saturday morning.** The instinct is to ingest everything; it is
wrong. A dense, specific corpus produces search results a judge recognises as meaningful. A
broad corpus produces a demo where the top hit is vaguely related to the query and the room
stays quiet.

Pick a subfield where at least one team member can tell a good hit from a bad one. Without
that, we cannot measure precision and we cannot tell whether it works.

## Architecture, three boxes

```
OA corpus subset ──► negative-claim extraction ──► embed + index ──► search
  (PMC, one            (Rosalind / OpenAI)          (GPU embedding,     (+ sentence-level
   subfield)                                         NVIDIA)             provenance)
                        NVIDIA Agent Toolkit: pipeline orchestration, tracing, eval
```

## Hour by hour

| When | Milestone | Hard gate |
|---|---|---|
| Fri night | Corpus subset downloading | Do not spend Saturday on a download |
| Sat 09:00 | Subfield chosen. Someone on the team can judge relevance in it | If nobody can, choose a different subfield now |
| Sat 10:00 | Extraction prompt working on 10 papers, output eyeballed | |
| Sat 12:00 | **Precision spot-check on 20 extractions** | **Under ~60%? Narrow the claim type immediately** — e.g. only "construct did not express" — rather than trying to fix general extraction |
| Sat 14:00 | Pipeline running over the full subset | |
| Sat 16:00 | Index built, search returns something for a real query | |
| Sat 18:00 | **MVP complete.** Search works, provenance links resolve | |
| Sat 19:00 | Precision measured properly on 50 samples, by hand, by two people | The number for the slide. Two raters gives an agreement figure, which is better |
| Sat 21:00 | The three demo queries chosen and checked | Pick queries whose results are genuinely striking |
| Sat 22:00 | **Demo recorded.** Slides drafted | Non-negotiable |
| Sun 09:00 | README, one-command run, corpus fetch script | |
| Sun 11:00 | Rehearse twice with a timer | |

## The one demo

A query on a specific construct or condition, returning three papers that quietly reported it
failing, each with the exact sentence highlighted. Then: *"none of these are indexed anywhere.
If you searched for this, you would find the positive results and none of these."*

Choose the query so the point lands without domain expertise in the audience. Test it on
someone from another team on Saturday evening.

## The honest numbers

Report precision, and report it per claim type. Do not report recall — we cannot measure it
without an exhaustively labelled corpus, and claiming it would be the easiest thing for a
judge to puncture. **Say out loud that recall is unmeasured and why.** That is a stronger
position than a number we cannot defend.

## Kill criteria

- Extraction precision under 60% at the Saturday 12:00 check → narrow to one claim type. Do
  not attempt to fix general extraction; that is a research project, not a weekend.
- Corpus parsing fights back → drop to abstracts only. Weaker, because negative results hide in
  full text, but a working abstract-level system beats a broken full-text one. Decide by 14:00.
- Search results are unconvincing at 18:00 → the fallback is B01, reusing the extraction
  pipeline to *generate* benchmark instances. The work carries over.
