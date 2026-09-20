# WilbeBioAIHack2026

Repo for the Wilbe Bio x AI hackathon (London, WilbeLABS).

This branch prepares an agent benchmark for paired childhood leukaemia diagnosis
and relapse. The active hypothesis concerns reproducible expression changes that
can nominate resistance-associated processes and experiments.

The downloaded GEO data contain **49 paired B-ALL patients for discovery and 27
paired B-ALL patients for validation**. An additional 14 paired T-ALL patients are
kept separate. These are conventional-treatment cohorts, not CD19 CAR-T cohorts.

Start with the [hypothesis](ana-workspace/hypothesis/hypothesis.txt),
[agent task and inputs](ana-workspace/datasets/agent_access/paired_all_relapse/TASK.md),
and [dataset provenance and reproducibility guide](ana-workspace/geo_relapse_benchmark/README.md).

Notes on the event brief, tracks, and judging criteria are in [Context/](Context/);
pre-event candidate ideas and plans are in [Plan/](Plan/).

Team setup notes and how to load the context files into Claude, Codex, or a web UI are in
[DeveloperREADME.md](DeveloperREADME.md).

## Setup

Downloaded matrices are included and can be read with pandas. To rebuild
the prepared inputs and run integrity checks, follow the
[dataset setup](ana-workspace/geo_relapse_benchmark/README.md#reproduce-and-evaluate).

## Layout

```
Context/           event brief, judging criteria, tooling prep
Plan/              idea candidates, scoring, and execution plans
AGENTS.md          project instructions for coding agents (edit this one)
CLAUDE.md          one-line import of AGENTS.md, for Claude Code
ana-workspace/hypothesis/                 active hypothesis
ana-workspace/datasets/agent_access/paired_all_relapse/  active agent inputs
ana-workspace/geo_relapse_benchmark/       GEO source files, preparation, evaluator checks
ana-workspace/archive/cd19_car_t_previous/ archived previous hypothesis and inputs
```

## Notes

Submission needs this repo to be enough for someone else to reproduce whatever ends up in
the presentation, so keep setup steps and data sources written down here as we go.
