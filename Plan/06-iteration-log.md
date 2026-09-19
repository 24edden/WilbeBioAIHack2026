# Iteration log

How this plan was built, what was rejected, and what each pass changed. Kept because the
rejected reasoning is worth as much as the conclusions when the team revisits this on Saturday
morning and wants to know whether a given idea was already considered.

---

## Pass 1 — diverge

Generated 16 candidates with no filtering, spanning all four tracks: five orchestration, four
benchmarking, two OSS, three open, two hybrids.

**Observation:** the generator kept producing variations on "an agent that does X with a
biological dataset". The genuinely distinct shapes turned out to be few:

- **Loop** — generate, evaluate, feed back (A01, E01)
- **Assemble** — gather evidence, weigh it, produce a judgement (A02, D03)
- **Map** — probe a system systematically, chart where it breaks (B01, B02, B03)
- **Translate** — convert between representations humans struggle to bridge (A03, D01, E01)
- **Decide** — choose the next action under uncertainty (A05, E02)

Worth keeping as a generator: if a new idea does not fit one of these five shapes, it is
probably genuinely novel and worth extra attention. If it fits, ask which existing candidate
it duplicates.

---

## Pass 2 — score and find the structure

Scored all 16 against the rubric. Three patterns emerged that no single idea revealed:

**The bench-facing trap.** A03, D02 and D01 are the most *useful* ideas — the ones a bench
scientist would actually want — and score 3–4 on the NVIDIA/OpenAI criterion. Useful-to-humans
and load-bearing-GPU-model pull in opposite directions. This is invisible until you score the
ideas side by side.

*(Pass 7 note: this family was later eliminated for an unrelated second reason — no lab access
means no way to evidence them. Two independent problems, same set of ideas.)*

**The originality-tech anticorrelation.** A01 scores 9 on tech and 4 on originality. Where the
sponsor stack fits with no thought, expect several teams to arrive at the same place.

**Execution is scarcer than ideas.** Nothing ambitious scored above 5 on execution. The
implication is uncomfortable but real: **for a weekend, a smaller idea executed fully beats a
larger idea executed partly**, because execution and presentation together are 40% of the score
and both collapse when the build overruns.

---

## Pass 3 — combine to fix weaknesses

Rather than picking winners, took the two highest-scoring ideas with *complementary* failures
and composed them. A01 (tech 9, originality 4) plus A03 (tech 4, originality 7) became E01,
scoring 9 and 8. The composition — design that terminates in a runnable protocol — is more
original than either half.

**Generalised rule:** when two ideas fail on *different* criteria, composition is usually
cheaper than fixing either one. Other pairings worth considering if the team dislikes the
finalists:

- **B03 + C02** — build the tool registry, then benchmark selection over it. Two deliverables,
  one infrastructure.
- **A05 + E02** — structured hypotheses, then choose experiments that discriminate between
  them. Coherent, ambitious, probably too much for a weekend.
- **D02 + B01** — plate QC as one instance family inside the failure benchmark.
- **A02 + B01** — variant triage where the eval set contains corrupted inputs. This is the
  documented pivot path for F2 and costs nothing to keep open.

---

## Pass 4 — adversarial review of the finalists

Read each finalist as a hostile judge.

**Against F1 (failure benchmark):** *"You built a test suite, not a system. Where is the
science?"* — Real risk. Mitigation is the scaffold that improves detection: it turns a
benchmark into a finding, and a finding is a result. **Do not present F1 without the
intervention arm.**

**Against F2 (variant triage):** *"This is retrieval with a confidence score."* — Answered only
by the calibration curve. If the curve does not show separation from the bare model, the
project has no claim. Build it Saturday evening, not Sunday.

**Against F3 (design to bench):** *"Did anyone check the protocol is correct?"* — If the answer
is "the model generated it", the project is worse than nothing, because a confidently wrong
protocol is a safety claim we cannot support. Hence the rule that every quantity comes from
deterministic code and a named human reviewed the output.

**Common weakness across all three:** each depends on one piece of evidence — a chart, a curve,
a person. That is correct for a five-minute talk, but it means **the evidence must be scheduled
as work, not hoped for**. All three plans now put it on the Saturday-evening timeline explicitly.

---

## Pass 5 — contingency on the biggest unknown

The plans assume Rosalind can be called from code. If it is a UI-only research workbench, the
"OpenAI box" in every architecture changes.

**If Rosalind is API-callable:** plans stand as written.

**If Rosalind is UI-only:** use standard OpenAI models as the programmatic reasoning layer, and
use Rosalind for the work it is good at — building the eval instances in F1, investigating the
variants in F2, drafting the protocol knowledge base in F3 — then **say exactly that on the
slide.** "We used Rosalind to construct the benchmark and OpenAI models in the loop" is a
truthful, specific claim, and specificity reads better to these judges than a vague assertion
of deep integration.

This question is first in the Saturday 09:00 checklist for a reason: it is the only unknown
that changes an architecture rather than a parameter.

---

## Pass 6 — what would make a judge remember us

Six judges will watch many five-minute talks. Scores get discussed afterwards, and the projects
that survive discussion are the ones with a *handle* — one image or sentence that someone can
repeat.

Candidate handles:

- **F1:** "the benchmark of what these models miss" — a bar chart of confident wrongness
- **F2:** "the model that knows when to shut up"
- **F3:** "from FASTA to the freezer"

If a project cannot be compressed to a handle, the talk needs work. This is not spin: the
compression forces you to know what the contribution actually is, and a project that resists
compression usually has not decided.

**Test for the team:** on Saturday at 18:00, everyone independently writes the handle on a
sticky note. If they do not match, the project is not yet one thing, and the talk will show it.

---

## Pass 7 — the no-wet-lab constraint

Learned that we have **no wet lab access**: no experiments, no lab-generated data, and no
practitioner available to validate output in the room.

This was not a small edit. It changed the finalist set.

**What it killed, and why each died differently:**

| Idea | Before | After | What was actually lost |
|---|:--:|:--:|---|
| E01 design to bench | 39 | 34 | The claim *was* "a scientist could run this Monday". Nobody can say so |
| A03 protocol compiler | 37 | 34 | The demo moment: a practitioner confirming the error is real |
| D02 assay QC | 36 | 34 | The check that our synthetic faults resemble real ones. Now permanently unvalidated |
| D01 notebook extraction | 29 | 29 | Realism. We now write the pages we score ourselves, which is circular |

Note the scores moved for **different reasons across different columns** — demo, validation,
circularity — but the root cause is one thing: each idea's evidence was going to come from
someone with lab access.

**The generalisable rule**, now Filter 3b in the decision framework:

> Ask where the evidence for the central claim comes from. An idea whose evidence requires
> access you do not have is not a smaller version of that idea — it is a different and much
> weaker one, and the weakness only becomes visible on presentation day.

**What replaced E01 as the ceiling pick:** D03, the negative-results miner. Chosen over E02
(experiment selection, which scores higher on originality) because D03's evidence is entirely
internal — precision measured by hand-checking our own extractions — and its execution risk is
lower. E02 is documented as the alternative for a team that wants the more ambitious project
and has the domain knowledge to build the historical cases.

**What did not change:** B01 and A02 were unaffected. Both were already fully computational.
In hindsight that is why they scored well in pass 2 — not luck, but because evidence you can
generate yourself is more robust to constraint changes than evidence you have to go and get.

**Two things this constraint makes better, not worse:**

1. Self-authored and synthetic data can ship with the repo. The lab-data versions of these
   ideas could not have been published, which would have cost points on criterion 5.
2. It removes a whole class of Sunday-morning disaster where the validating scientist is
   unavailable, busy, or disagrees with the output.

**One thing to watch:** without a practitioner's endorsement, credibility has to come entirely
from evidence and precise framing. Every vague claim that a scientist's say-so would have
covered is now exposed to six technical judges. Both the presentation and reproducibility
documents were updated for this.

---

## Open questions this plan cannot resolve

Answer these on Friday and Saturday morning, then revise:

1. Team composition, and specifically who has real biology domain knowledge. With no lab, this
   is what determines whether we can tell a good result from a bad one — which is now the
   binding constraint on idea choice.
2. What Rosalind is. See pass 5.
3. GPU allocation and duration. Decides whether F2 and F3 are available.
4. Which BioNeMo models are pre-pulled on our instance.
5. Whether the tracks constrain judging, or are only for mentor allocation. `Context/` does not
   say, and it affects whether a benchmarking project competes against orchestration projects.
6. Whether other teams have picked the same idea. Worth asking around on Saturday morning.
   Originality is scored *relative to what other teams did*, per the rubric wording, which means
   it is partly an empirical question we can actually investigate.
