# WilbeBioAIHack2026

Repo for the Wilbe Bio x AI hackathon (London, WilbeLABS).

This branch provides one clean agent dataset: **GEO GSE28460, 49 paired B-ALL
patients, 98 diagnosis/relapse samples and 54,675 expression probes**.

Start with [hypothesis.txt](ana-workspace/hypothesis.txt) and
[the agent task](ana-workspace/input/TASK.md). The hypothesis asks whether
cell-cycle and DNA-repair expression rises at relapse within the same patients.
These are conventional-treatment cases, not CD19 CAR-T cases.

[Dataset provenance and setup](ana-workspace/geo_relapse_benchmark/README.md)
and [shared instance paths](ana-workspace/START_HERE_GEO_RELAPSE.md) are included.

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
ana-workspace/hypothesis.txt              active hypothesis
ana-workspace/input/                     the sole agent input (directory alias)
ana-workspace/datasets/agent_access/GSE28460/  expression and required metadata
ana-workspace/geo_relapse_benchmark/       original GEO source and evaluator checks
```

## Notes

Submission needs this repo to be enough for someone else to reproduce whatever ends up in
the presentation, so keep setup steps and data sources written down here as we go.
