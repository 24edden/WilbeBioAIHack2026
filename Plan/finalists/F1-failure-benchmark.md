# F1 — Bio agent failure benchmark (the floor)

Full concept in [../ideas/B01-reasoning-failure-benchmark.md](../ideas/B01-reasoning-failure-benchmark.md).
This is the execution plan.

**Pick this if:** the team is mixed-ability, compute is uncertain, or we want the highest
probability of having something complete on Sunday. It is the only finalist with no hard
dependency on GPU availability.

**Headline claim:** "Agents are confidently wrong on broken biological inputs. Here is how
often, by failure type, and here is what fixes it."

## Why it wins points

| Criterion | The argument we make |
|---|---|
| Scientific relevance | Whether these tools can be trusted on messy real data is a precondition for using them at all |
| NVIDIA + OpenAI | Agent Toolkit evaluation harness is the core, not a wrapper; OpenAI models are the systems under test |
| Execution | A benchmark is complete at any size. 40 pairs is a result, 20 pairs is a smaller result |
| Originality | Every other team demos the happy path. We are the only ones measuring the sad one |
| Presentation and repro | The suite plus harness *is* the reproduction package |

## Team split

Parallelises better than any other finalist, which is why it suits a team that has not worked
together before.

- **Two people on instances.** Write corrupted/clean pairs. Needs domain knowledge, no coding.
  This is where anyone with biology background contributes directly and immediately, whatever
  their coding experience.
- **One person on the harness.** Agent Toolkit eval, run matrix, result storage.
- **One person on the scaffold.** The intervention that improves detection: a verification
  step, a required tool call, a structured check.
- **One person on presentation.** From hour 4, not hour 30.

## Hour by hour

| When | Milestone | Hard gate |
|---|---|---|
| Sat 09:00 | Team split, corruption taxonomy agreed on a whiteboard | 6 types named |
| Sat 11:00 | 3 instances written, harness runs them end to end | **If the harness cannot run one instance by 12:00, mock the runner and keep writing instances** |
| Sat 13:00 | Difficulty calibrated: detection rate is neither 0% nor 100% | If everything is detected, make corruptions subtler now, not tomorrow |
| Sat 16:00 | 25+ pairs, first full run, first chart exists | Chart exists even if ugly |
| Sat 18:00 | **MVP complete.** 40 pairs, two configurations, per-type chart | This is the presentable minimum. Stop adding instances after this |
| Sat 20:00 | Scaffold implemented, second run comparing with and without | The finding, not just the benchmark |
| Sat 22:00 | **Demo recorded.** Slides drafted end to end | Non-negotiable. A recording means a laptop failure on Sunday is survivable |
| Sun 09:00 | README, repro instructions, one-command run | |
| Sun 11:00 | Rehearse twice, with a timer | Under 5:00 including questions setup |
| Sun 12:00 | Freeze. No code changes | |

## The one chart

Detection rate by corruption type, two bars per type (bare model, with scaffold). Worst bar
annotated with the actual model output underneath, confidently wrong.

Build this chart at hour 6 with fake numbers, then fill it in. Knowing the target picture
prevents the usual failure of collecting results that do not compose into a slide.

## Corruption taxonomy, first draft

| Type | Example | Why realistic |
|---|---|---|
| Frameshift | Single base deletion in a CDS | Happens constantly in real submissions |
| Wrong organism | Mouse gene symbols in a human analysis | The classic silent error |
| Swapped labels | Two sample labels exchanged in a matrix | Undetectable downstream, catastrophic |
| False premise | "Explain why X represses Y" when it does not | Tests sycophancy directly |
| Truncated file | FASTA cut mid-record | Trivial, and worth knowing if it is missed |
| Unit change | Concentration in mM labelled µM | Numerically silent |

Add one type per real anecdote collected from mentors and other attendees on Friday.
**Anecdote-sourced corruptions are both better science and better slide material** than
invented ones — and with no lab of our own, other people's experience is the only source of
realism available to us. Collect deliberately and write the anecdotes down verbatim.

## Kill criteria and fallbacks

- Agent Toolkit eval harness is unworkable → run the matrix in plain Python, note it honestly,
  and keep the Toolkit for tracing only. Costs a point on Tech, saves the project.
- All corruptions detected → lower the signal until they are not. If genuinely undetectable
  at any subtlety, that is itself the finding: report it, and pivot the talk to "current models
  are better at this than expected, here is where the boundary is".
- Reads as attacking the sponsors → test *configurations*, not vendors. Ship the scaffold that
  fixes it. Frame as "how to use these models safely", which is also the honest framing.
