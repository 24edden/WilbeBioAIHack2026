# Reproducibility checklist

Criterion 5 asks, in the organisers' words: *"Could another team understand and reproduce the
key results using the submitted materials and repository?"*

This is a fifth of the score, it is the cheapest criterion to max out, and it is the one most
teams neglect because it is not fun at 2am. Scheduled: **Sunday 09:00–10:30**.

## The test

Hand the repo to someone who was not on the team. Can they get *the headline number* out in
under fifteen minutes on a fresh machine? Everything below serves that sentence.

If a teammate has a spare laptop, actually run this test. It finds the hardcoded path in your
home directory that you cannot see any more.

## Checklist

### Must have

- [ ] **README with the headline result at the top.** Not the architecture. The number or the
      chart, in the first screen, so a judge skimming on a phone sees the point.
- [ ] **One command to reproduce the key result.** `make reproduce`, `./run.sh`, or a single
      documented `python -m ...`. Not twelve steps.
- [ ] **Pinned dependencies.** A lockfile, or a container. "pip install these roughly" is not
      reproducible and will not be in six months.
- [ ] **The data, or a scripted way to get it.** Small inputs committed; large inputs fetched
      by a script with a checksum. Never "download it from this site and put it somewhere".
- [ ] **No hardcoded absolute paths.** The single most common reproduction failure.
- [ ] **No secrets committed**, and a `.env.example` showing what keys are needed.
- [ ] **Expected output committed** so a reproducer can diff their run against ours.

### Strongly worth it

- [ ] **A five-minute path and a full path.** "Reproduce the headline chart on cached results"
      versus "rerun everything, 3 GPU-hours". Judges will run the first if anything.
- [ ] **Cached intermediate results committed** where they are small. Lets someone see the
      result without the compute, which most reproducers cannot spare.
- [ ] **Known limitations section.** Say what is cherry-picked, what is a small sample, what
      only works on our data. Judges trust a repo that says this far more than one that does not.
- [ ] **The demo recording** linked from the README.
- [ ] **A note on what the agents wrote.** Interesting to this audience specifically, and
      honest about how the work was actually done.

### Nice if there is time

- [ ] Environment captured as a Brev launchable, so a reader can start an identical machine
- [ ] CI running the fast path on push, proving it works somewhere other than our laptops
- [ ] Architecture diagram in the README, matching the one in the slides

## README skeleton

```markdown
# <Project>

<One sentence: what it does and for whom.>

**Result:** <the headline number or chart, inline, above the fold.>

## Reproduce in five minutes
<one command, using cached intermediates>

## Reproduce fully
<one command, with the compute cost stated>

## How it works
<three boxes, one paragraph. Where NVIDIA and OpenAI are load-bearing.>

## Limitations
<the honest list>

## Demo
<link to the recording>
```

## Anti-patterns

- A README that is all architecture and no result
- `requirements.txt` with no versions
- Notebooks with out-of-order execution counts and no saved outputs
- The key result produced by a manual step nobody wrote down
- A repo whose last commit is `final final fix` at 11:58 on Sunday and does not run
