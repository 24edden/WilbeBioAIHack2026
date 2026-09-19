# Decision framework

Picking the idea is the highest-leverage 90 minutes of the weekend and the easiest to
waste. This is a procedure, not a discussion.

## Step 0 — before you filter anything (15 min)

Write these four facts on a whiteboard. Every later decision depends on them, and teams
routinely pick an idea before knowing them:

1. **Who is on the team?** Specifically: how many people have (a) biology domain knowledge,
   (b) bioinformatics experience, (c) shipped software. The idea must be one where every
   person has something to do by hour 3. Note that domain knowledge is still decisive even
   though we have no lab: it determines whether we can tell a good result from a bad one.
2. **What GPU do we have, for how long?** Determines whether fine-tuning is on the table
   at all. Assume inference-only until proven otherwise.
3. **What is Rosalind, concretely — API or UI?** See the open question in
   `Context/tooling.md`. If it can't be called from code, it can't be a component, and
   every plan that assumes otherwise needs its architecture redrawn.
4. **Which BioNeMo models are actually available and pre-pulled on our instance?**
   A NIM container you have to pull for the first time can cost hours.

## Step 1 — the four filters (30 min)

Run every candidate through these in order. A "no" anywhere kills it. Be ruthless; a dead
idea at hour 2 is cheap, at hour 20 it's the weekend.

**Filter 1 — Demoable in five minutes, live, to a non-expert.**
If the result is a number in a table that needs three minutes of setup to appreciate, it
will not land. Ask: *what is the single frame that makes a judge lean forward?* If nobody
can answer in one sentence, kill it.

**Filter 2 — Load-bearing NVIDIA and OpenAI components, both.**
Draw the architecture as boxes. Point at the NVIDIA box and the OpenAI box. If either is
"we ran it on a GPU" or "we used Codex to write it", the idea fails criterion 2, which is
20% of the score. Fix or kill.

**Filter 3 — A real input we can actually obtain by noon Saturday.**
Public dataset, or something we generate. **We have no lab, so no experimental data of our
own** — anything requiring it is out. "We'll find data" is not an answer. Name the file.

**Filter 3b — Evidence we can produce without access we do not have.**
Ask where the evidence for the claim comes from. If the answer involves a practitioner
validating output, a bench result, or data from an instrument, we cannot produce it. This
filter killed four otherwise good ideas; see [02-scorecard.md](02-scorecard.md).

**Filter 4 — An honest baseline exists.**
Criterion 1 asks whether the workflow is *meaningfully better than the current
alternative*. You must be able to name the alternative: the tool people use today, the
manual process, or a plain frontier model with no scaffolding. If we can't beat a bare
GPT-5-class model on the task, we are decoration on top of someone else's model.

Filter 4 is the one teams skip and judges ask about. **Assume you will be asked "did you
compare against just prompting the model?" and have the number ready.**

## Step 2 — score and commit (20 min)

Score the survivors 1–10 on each of the five criteria in [02-scorecard.md](02-scorecard.md).
Don't average away a weakness: a 3 on any criterion is worth more attention than the gap
between an 8 and a 9 elsewhere, because the criteria are equally weighted and a 3 is
usually cheap to lift to a 6.

Then **commit out loud**, with a named owner per component, and don't revisit the decision
before the Saturday-evening checkpoint. Re-litigating the idea at hour 14 is the single
most common way hackathon teams lose.

## Step 3 — pre-commit the kill criteria (10 min)

Before writing code, write down the conditions under which you'd change plan, and what
you'd change to. Deciding this while tired and behind is how teams end up shipping
nothing. Each finalist plan has a suggested fallback already.

Standard form: *"If X isn't working by \<time\>, we drop to \<smaller thing\> and the demo
becomes \<this\> instead."*

## Tie-breakers

If two ideas score the same:

1. Prefer the one where **the demo is visual**. Structures, plots, and diffs beat logs.
2. Prefer the one whose **failure mode is interesting**. A system that fails informatively
   is presentable; one that just doesn't work isn't.
3. Prefer the one **someone on the team can speak to with real domain knowledge**. Criterion
   1 is judged on scientific relevance and it shows immediately when the presenter doesn't
   actually understand the biology. This matters more, not less, now that we cannot lean on a
   practitioner's endorsement for credibility.
4. Prefer the one with **less setup risk** — fewer containers to pull, fewer accounts to
   provision, fewer things that need a mentor to unblock.

## Anti-patterns to reject on sight

- **The universal agent.** "An agent that can do any bioinformatics task." Unfalsifiable,
  undemoable, scores badly on execution because nothing is finished.
- **The wrapper.** A chat UI over an existing model with no domain logic. Fails criterion 4.
- **The training run.** Fine-tuning anything meaningful in a weekend, on shared GPUs,
  starting from a cold environment. The result arrives at 4am Sunday or not at all.
- **The dataset build.** Curating a large dataset *as the deliverable*, where the value only
  materialises after the event. Fine as a byproduct, fatal as the main artifact.
- **The five-component pipeline.** Each additional component multiplies the probability of
  a broken demo. Three boxes is usually the ceiling for a weekend.
