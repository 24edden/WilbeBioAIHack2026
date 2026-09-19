# The five minutes

Six judges scoring five criteria. The talk is judged directly on criterion 5 and is the
*only* evidence they have for criteria 1 and 4. Treat it as a fifth of the work, not as an
afterthought.

## Structure

Five minutes is roughly 600 words spoken. That is one idea per slide and no more.

| Time | Slide | Job | Criterion it serves |
|---|---|---|---|
| 0:00–0:45 | **The problem** | A specific person with a specific problem, not a field-level abstraction. Name the current alternative | Scientific relevance |
| 0:45–1:15 | **The insight** | The one non-obvious thing we realised. If there isn't one, find it before Sunday | Originality |
| 1:15–3:00 | **The demo** | Recorded, narrated live. The longest block by far | Execution |
| 3:00–4:00 | **The evidence** | The one chart. The baseline comparison. The honest limitation | Relevance + execution |
| 4:00–4:30 | **How it is built** | Architecture in three boxes. Name where NVIDIA and OpenAI are load-bearing | NVIDIA/OpenAI use |
| 4:30–5:00 | **Repo and what is next** | One command to reproduce. What we would do with another week | Reproducibility |

## Rules

**Open with the problem, not the architecture.** The commonest opening is "we built a
multi-agent pipeline using X, Y and Z", which asks the judges to care about a solution before
they know the problem. Name the person who has the problem.

**The demo is the centre.** Nearly two minutes. Recorded Saturday night, narrated live so it
stays human. If the demo is not the best part of the talk, the talk is wrong.

**One chart, not four.** Each finalist plan names its one chart. Extra charts subtract; nobody
absorbs four plots in thirty seconds.

**State a limitation out loud.** "This is fifty variants, not a clinical validation."
"The protocol was reviewed by one scientist." This costs nothing with technical judges and buys
a great deal of credibility, and it pre-empts the question that would otherwise land in Q&A.

**Name the NVIDIA and OpenAI components explicitly**, in one sentence, pointing at boxes. The
judges are scoring this criterion directly and are from those companies. Make it trivial to
score, and make it honest: if something was incidental, do not claim otherwise, because these
particular judges will know.

**Say what you would do next.** Signals you understand the shape of the real problem beyond
what you built.

## Who presents

One or two people. Three is too many for five minutes.

The person framing the problem should be whoever most credibly owns the science, regardless of
who wrote the most code.

We have no lab and therefore no practitioner endorsement to lean on, so **credibility has to
come from the evidence and from precise framing** rather than from someone in a lab coat
saying it works. Concretely: cite where the problem is documented, and be exact about what was
measured. Vagueness that would have been covered by a scientist's say-so is now exposed.

## Rehearse twice, with a timer

Everyone is over time. The first rehearsal reveals by how much; the second fixes it. Cut a
slide rather than talking faster.

Rehearse the transition into the demo specifically. That is where talks stall.

## Submission checklist

From `Context/judgingCriteria.md`:

- [ ] Slides using the **official submission template** — get it Friday, do not rebuild it Sunday
- [ ] **A single GitHub repository** with all code to reproduce results and demos
- [ ] Repo access granted to whoever the organisers specify
- [ ] Demo recording embedded or linked, in case the room's setup fails

## Questions to have answers ready for

- Why not just prompt a frontier model directly? *(Have the number.)*
- What would it take to use this for real?
- What is the failure mode you are most worried about?
- How much of this did the agent write versus you? *(Be honest and specific. Codex-heavy
  development is expected and interesting here, not embarrassing.)*
- What would you do with another week?
