# B03 — Does the agent reach for the right tool?

**Track:** 03 Benchmarking · **Shape:** orchestration-quality eval

**One-liner:** Measure whether a bio agent picks the correct tool for a task, and what it does
when the right tool is missing from its toolbox.

## Problem

Agent quality in bioinformatics is dominated by tool selection, not by model reasoning. Using
BLAST where you need HMMER, or a global aligner where you need a local one, produces output
that looks right and is wrong. Benchmarks score the final answer and miss the cause.

## Current alternative

End-to-end task benchmarks, which conflate tool choice with everything else.

## What we build

A set of tasks with a known-correct tool and known-plausible wrong tools, and three
conditions: full toolbox, toolbox missing the correct tool, toolbox containing a plausible
trap tool. We measure selection accuracy, and critically, **what happens in condition two** —
does it say the right tool is missing, or does it substitute a wrong one silently?

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Tool registry, wrapped bioinformatics tools | NVIDIA Agent Toolkit tool definitions | Yes — NVIDIA |
| Eval harness and condition matrix | NVIDIA Agent Toolkit evaluation | Yes |
| Agent under test | Rosalind / OpenAI | Yes — OpenAI |

## Data

Tasks written by the team, with the correct tool agreed in advance by whoever has the most
bioinformatics experience. 30 tasks is enough. Disagreement about the correct tool is itself
a finding, so record it.

## MVP by Saturday 18:00

30 tasks, three conditions, selection-accuracy table, plus the substitution behaviour in the
missing-tool condition.

## The demo frame

The missing-tool condition. Show the agent confidently substituting an inappropriate tool and
producing plausible output, then the same task with the tool present.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 6 | Important to builders, less visceral to a bench scientist |
| NVIDIA + OpenAI use | 8 | Agent Toolkit is the natural home for this |
| Execution | 8 | Cheap, parallel, no GPU dependency |
| Originality | 7 | Tool-selection evals exist in general agent work, less so in bio |
| Presentation and repro | 8 | Clean tables, easy to rerun |

## Risks and kill criteria

- Wrapping the classic tools takes longer than expected. Mitigation: mock the tools. We are
  measuring *selection*, so the tools do not need to actually run. This cuts a day of work
  and is a legitimate design choice — but say it on the slide, and be ready to defend it.

## Note

This shares almost all infrastructure with C02, and the wrapped registry from C02 is the
natural input to this. Together they are a plausible two-deliverable project.
