# F2 — Variant triage with calibrated abstention (the middle)

Full concept in [../ideas/A02-variant-triage.md](../ideas/A02-variant-triage.md).

**Pick this if:** we have at least one person comfortable with genomics data, GPU access is
confirmed, and we want a real accuracy number rather than a qualitative demo.

**Headline claim:** "A frontier model will answer every variant question fluently. Ours
answers fewer, sources every claim, and knows which ones it cannot call — and we can show the
calibration curve to prove it."

## The core insight to protect

The project is not "an LLM interprets variants". It is **abstention as a first-class output**.
Every design decision should push toward that. If someone suggests a feature that makes the
system answer *more* questions, it is probably the wrong direction.

This matters because it is the difference between a 6 and a 9 on originality, and it is also
the only version of this project that a clinical genomicist would take seriously.

## Architecture, three boxes only

```
VCF ──► deterministic annotation ──► BioNeMo variant scoring ──► evidence assembly + abstain
        (VEP, gnomAD, cached)        (Evo2-class)                (Rosalind/OpenAI)
                                                                        │
                                          NVIDIA Agent Toolkit ─────────┘
                                          orchestration · provenance · eval
```

Resist adding a fourth. The temptation will be a literature retrieval box; it is the single
most likely cause of an unfinished project here. Add it Saturday evening if and only if
everything else is done.

## Hour by hour

| When | Milestone | Hard gate |
|---|---|---|
| Sat 09:00 | Fix the evaluation set: 50 ClinVar variants, balanced, held out | Frozen. Never look at these while prompting |
| Sat 10:00 | Annotations pre-computed and cached to a static file | **If annotation tooling is not producing output by 13:00, ship the static file and move on permanently** |
| Sat 12:00 | Genomic model scoring one variant end to end | If unavailable by 14:00, substitute deterministic predictors and say so on the slide |
| Sat 14:00 | Evidence assembly producing a report for one variant, with provenance links | |
| Sat 16:00 | Full run over all 50, confusion matrix exists | Ugly is fine |
| Sat 18:00 | **MVP complete.** Ranked output, matrix, provenance on every claim | |
| Sat 19:00 | Abstention implemented and tuned. Calibration plot | This is the project. If time is short, cut anything else to protect it |
| Sat 21:00 | Baseline comparison: bare model on the same 50 | The slide that answers "why not just prompt it" |
| Sat 22:00 | **Demo recorded.** Slides drafted | Non-negotiable |
| Sun 09:00 | Ablations if time: minus genomic model, minus retrieval | Optional |
| Sun 11:00 | README, one-command reproduction, rehearse twice | |

## The one chart

Calibration: stated confidence on the x-axis, observed accuracy on the y-axis, diagonal for
reference, bare model and ours plotted together. The bare model's curve will be flat and high;
ours should track the diagonal. **That single plot is the entire argument.**

Second-best chart: coverage versus accuracy. As abstention increases, accuracy on the answered
subset should rise. If it does not, the abstention is not informative and we need to know that
by Saturday evening, not Sunday.

## Anticipated judge questions

- *"Isn't this just RAG with extra steps?"* → The calibration curve. RAG does not abstain.
- *"How do you know the abstentions are the right ones?"* → Coverage-accuracy curve. If we
  abstain on random variants, accuracy on the remainder does not improve.
- *"Fifty variants is small."* → Agreed, and say so first. State it as a method demonstration
  with a clear scaling path, rather than being caught defending it.
- *"Would a clinician use this?"* → Have an honest answer about regulatory reality. "No, not
  as-is, and here is what would have to be true" is a much stronger answer than overclaiming.

## Kill criteria

- Genomic model unavailable → deterministic predictors, note on the slide, story survives.
- Annotation pipeline fights back → static cached file, decided at 13:00, no revisiting.
- Abstention shows no benefit by Saturday 21:00 → **pivot to F1 using the same 50 variants as
  the clean half of a corrupted-pair benchmark.** The data carries over. Make this call at
  21:00 if needed, not at 2am.
