# C02 — A typed tool registry for bioinformatics agents

**Track:** 01 OSS Build · **Shape:** infrastructure

**One-liner:** Wrap the classic command-line bioinformatics tools as typed, tested,
agent-callable tools, so agents stop shelling out and guessing flags.

## Problem

Every team building a bio agent rewrites the same brittle subprocess wrappers around the same
dozen tools, with no schemas, no validation and no tests. Agents pass wrong flags, misparse
output formats, and fail silently.

## Current alternative

Ad hoc subprocess calls with the flags in the prompt.

## What we build

A registry of tools with typed inputs and outputs, input validation before execution, parsed
structured output instead of raw text, and a test per tool. Plus a conformance suite that any
agent framework can run.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Tool definitions and registry | NVIDIA Agent Toolkit | Yes — NVIDIA |
| Schema generation from tool help text and man pages | Rosalind / OpenAI | Yes — OpenAI, and genuinely useful here |
| Demonstration agent using the registry | OpenAI models | Yes |

Using a model to *generate* the schemas from documentation, then validating them by execution,
is the part that makes this interesting rather than a weekend of typing.

## Data

Tool documentation and the tools themselves.

## MVP by Saturday 18:00

8 to 12 tools wrapped, schemas auto-generated and validated by round-tripping real
invocations, tests green, one demo agent that composes three of them into a task.

## The demo frame

Same task, two agents. One shells out and fumbles flags. One uses the registry, is refused at
validation time for an invalid combination, corrects itself and succeeds.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 5 | Infrastructure. Judges may read it as plumbing, not science |
| NVIDIA + OpenAI use | 8 | Agent Toolkit native, and schema generation is real OpenAI work |
| Execution | 8 | Highly parallel across a team, scales down cleanly |
| Originality | 5 | MCP servers for bio tools already exist |
| Presentation and repro | 7 | Useful artifact, unexciting demo |

## Risks and kill criteria

- Boring on stage. The validation-catches-the-error demo is the only compelling frame, so
  build it first and make sure the caught error is a realistic one.
- Duplicates existing MCP work. Check on Friday. If a good registry already exists, **use it
  and build B03 on top instead** — that is a better project anyway.
