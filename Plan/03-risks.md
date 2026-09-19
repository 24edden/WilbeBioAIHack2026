# Risk register

Failure modes ranked by expected cost. Each has a pre-committed response, because the point of
writing these down beforehand is to avoid deciding them while tired and behind.

## Tier 1 — kills the project

### Compute does not materialise
Credits arrive late, the instance will not start, the container will not pull, someone else is
using the quota.
**Response:** every finalist has a CPU-viable degraded mode. F1 needs no GPU at all. Decide by
Saturday 13:00, then stop thinking about it. **Do not spend the afternoon retrying.**

### The idea is re-litigated on Saturday afternoon
Someone has a better idea at hour 12. It is usually genuinely better, and acting on it is
usually fatal.
**Response:** the decision is made at 10:30 Saturday and is not reopened before the 22:00
checkpoint. Write new ideas on a whiteboard marked "next time". If the current idea is truly
dead, the kill criteria will have fired already — that is what they are for.

### Nothing runs end to end until Sunday
Each component works alone; the integration is left for last and reveals a mismatch.
**Response:** the end-to-end stub at Saturday 10:30, doing nothing useful, is the cheapest
insurance available. Keep it running all weekend. It is the canary.

### The demo fails live
**Response:** the recording made Saturday night. Present the recording if anything at all is
wrong. Nobody deducts points for a recorded demo; they deduct heavily for a broken live one.

## Tier 2 — costs a criterion

### NVIDIA or OpenAI turns out to be decorative
The commonest way to lose 20% of the score without noticing.
**Response:** draw the architecture at Saturday 10:30 and ask "if I delete this box, does the
system still work?" of the NVIDIA box and the OpenAI box. If yes for either, redesign then.
Not at slide-writing time, when the honest answer becomes a slide that says less than it
should.

### No baseline comparison
Judges ask "did you compare against just prompting the model?" and there is no answer.
**Response:** the bare-model baseline is a *scheduled task*, Saturday evening, not an
opportunistic one. It is usually an hour of work and it is worth more than any feature.

### Slides written Sunday morning
Rushed, unrehearsed, over time, and the work looks worse than it is.
**Response:** slides drafted Saturday 20:00–22:00 as the story becomes clear. Sunday is for
cutting, not writing.

### The repo is unreproducible
Criterion 5 explicitly asks whether another team could reproduce the key results. A repo with
no README and hardcoded paths answers that question badly.
**Response:** [05-reproducibility.md](05-reproducibility.md), done Sunday 09:00 as scheduled
work.

## Tier 3 — costs quality

### One person becomes the bottleneck
Everything routes through whoever set up the environment.
**Response:** environment setup is documented as it happens, in `DeveloperREADME.md`, by the
person doing it. Two people should be able to run the pipeline by Saturday lunchtime.

### Scope creep disguised as polish
"Just one more feature" after the 18:00 freeze.
**Response:** the freeze. Stretch work happens on a branch and only merges if it is finished
and tested by 21:00.

### Nobody on the team can speak to the biology
Criterion 1 is scientific relevance and it is obvious within thirty seconds when the presenter
does not understand the domain.
**Response:** whoever has the most domain knowledge presents the problem framing, whatever
their coding contribution was. If nobody has domain knowledge, pick a different idea at 09:00
Saturday.

### Team burns out overnight
Three people awake at 4am produce negative value on Sunday morning.
**Response:** the 22:00 checkpoint exists so that stopping is a legitimate choice. Rehearsed
and rested beats feature-complete and incoherent, and it is not close.

## The meta-risk

**Optimising for the build instead of the score.** The natural instinct is to spend every hour
coding. The rubric gives 40% to originality and presentation-plus-reproducibility — neither of
which is improved by another feature. Roughly a third of the weekend should go to evidence,
narrative and the repo. That feels wrong while doing it and is right afterwards.
