# Scorecard

All 16 candidates scored against the five judging criteria from `Context/judgingCriteria.md`.

**These are our own estimates, not judges' scores.** They are guesses made before knowing the
team or the compute. Their value is in the *ranking and the spread*, not the absolute numbers,
and specifically in showing where a cheap fix moves a project several points.

**Revised for the no-wet-lab constraint.** We cannot run experiments, cannot use
lab-generated data, and cannot have a practitioner validate output in the room. Four ideas
dropped as a result; the affected rows are marked and the reasoning is in
[06-iteration-log.md](06-iteration-log.md), pass 7.

Criteria, all equally weighted, 1–10 each: **Sci** scientific relevance and impact ·
**Tech** effective NVIDIA and OpenAI use · **Exec** execution · **Orig** originality ·
**Pres** presentation and reproducibility.

## Ranked

| # | Idea | Sci | Tech | Exec | Orig | Pres | Total | Note |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| [B01](ideas/B01-reasoning-failure-benchmark.md) | Bio agent failure benchmark | 8 | 7 | 8 | 9 | 9 | **41** | No weak criterion, no lab needed |
| [A02](ideas/A02-variant-triage.md) | Variant triage with abstention | 9 | 8 | 7 | 6 | 9 | **39** | Labelled data is the edge |
| [B02](ideas/B02-nim-robustness-suite.md) | Model robustness map | 8 | 6 | 7 | 7 | 9 | **37** | Free fallback for A01 |
| [B03](ideas/B03-tool-selection-benchmark.md) | Tool selection benchmark | 6 | 8 | 8 | 7 | 8 | **37** | Safe, slightly dry |
| [D03](ideas/D03-negative-results-miner.md) | Negative results miner | 9 | 7 | 6 | 8 | 7 | **37** | Best one-sentence pitch here |
| [E02](ideas/E02-experiment-selection.md) | Experiment selection | 9 | 6 | 5 | 9 | 7 | **36** | Brilliant if it works |
| [A05](ideas/A05-hypothesis-tiny-moves.md) | Incremental hypothesis editing | 7 | 6 | 5 | 9 | 8 | **35** | Highest vapour risk |
| [B04](ideas/B04-methods-reproduction-benchmark.md) | Paper reproduction benchmark | 9 | 6 | 4 | 8 | 8 | **35** | Execution risk is severe |
| [A04](ideas/A04-single-cell-agent.md) | Single-cell agent | 7 | 7 | 7 | 5 | 8 | **34** | Solid, unmemorable |
| [E01](ideas/E01-design-to-bench.md) | Design to bench handoff | 7 | 9 | 5 | 7 | 6 | **34** | **Was 39. No lab = no validation** |
| [D02](ideas/D02-assay-qc.md) | Assay QC diagnosis | 7 | 4 | 9 | 6 | 8 | **34** | Was 36. Fault model now unvalidatable |
| [A03](ideas/A03-protocol-compiler.md) | Protocol compiler | 7 | 4 | 8 | 7 | 8 | **34** | Was 37. Lost its demo moment |
| [A01](ideas/A01-binder-design-loop.md) | Closed-loop binder design | 8 | 9 | 5 | 4 | 7 | **33** | Everyone else's idea too |
| [C02](ideas/C02-bio-tool-registry.md) | Typed tool registry | 5 | 8 | 8 | 5 | 7 | **33** | Infrastructure, reads as plumbing |
| [C01](ideas/C01-legacy-tool-modernisation.md) | Revive a dead tool | 6 | 5 | 7 | 5 | 8 | **31** | The reliable floor |
| [D01](ideas/D01-lab-notebook-extractor.md) | Notebook extraction | 6 | 3 | 8 | 5 | 7 | **29** | Was 29. Self-authored data is circular |

## What the table actually says

**Read the columns, not the totals.** The totals are close and small differences are noise.
Four structural patterns matter more:

### 1. The no-lab constraint cost us the entire bench-facing family

A03, D02, D01 and E01 all lost 3–5 points, and they lost them in different columns for the
same underlying reason: **each one's evidence was going to come from a practitioner, and we
have no practitioner.** A03 lost its demo moment, D02 lost the check that its synthetic faults
are realistic, D01 is now scoring itself on pages it wrote, and E01 can no longer claim the
thing it exists to claim.

The general lesson is worth carrying into Saturday: **an idea whose evidence depends on access
you do not have is not a smaller version of that idea, it is a different and much weaker one.**
Ask of any new idea: *where does the evidence come from, and can we get it by Sunday?*

### 2. What survives is computational end to end

Every remaining strong candidate — B01, A02, B02, B03, D03 — needs only public data, models
and compute. That is not a coincidence; it is the shape of project this constraint selects
for. Stop mourning the lab ideas and lean into it.

### 3. The strongest ideas by Tech are still the weakest by Originality

A01 scores 9 on Tech and 4 on Originality. The reason the NVIDIA stack fits so naturally is
that it is the intended demo path, which is exactly why several teams will walk it.
**Where the sponsor stack fits with no thought, expect company.**

### 4. Nothing ambitious scores above 5 on Execution

The high-ceiling ideas all score 4–5 there. A weekend rewards cheapness more than teams
expect: an unfinished brilliant idea presents worse than a finished modest one, and Execution
is 20% on its own.

## Selection

Finalists are **B01**, **A02** and **D03**, spanning the risk range rather than taking the top
three by total:

- **B01** — floor. Cheapest to execute, no weak criterion, no GPU dependency, degrades
  gracefully, artifact outlives the weekend.
- **A02** — middle. Real data with real labels, a genuine number to report, moderate risk.
- **D03** — ceiling. Replaces E01. Fully computational, the most memorable pitch on the list,
  and GPU embedding at corpus scale is honest NVIDIA work rather than decoration.

Full plans in [finalists/](finalists/). **E02 is the alternative ceiling pick** if the team is
strong on domain knowledge and wants the more intellectually ambitious project; it scores
higher on originality and much worse on execution. C01 remains the emergency fallback.
