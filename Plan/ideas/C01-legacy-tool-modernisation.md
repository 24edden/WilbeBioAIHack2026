# C01 — Resurrect a dead bioinformatics tool

**Track:** 01 OSS Build · **Shape:** archaeology, then packaging

**One-liner:** Take a genuinely useful bioinformatics tool that no longer builds, make it
install in one command, and make it callable by an agent.

## Problem

A large amount of published bioinformatics method work is effectively lost: a tarball, a
Makefile written for a compiler from 2009, no tests, a dead download link. People reimplement
from the paper or give up.

## Current alternative

Giving up, or a week of build archaeology per tool.

## What we build

Pick one tool. Get it building in a container, add a regression test suite pinned to outputs
from the paper, publish it, and wrap it as an Agent Toolkit tool with a typed interface so an
agent can call it.

The agent-callable wrapper is what makes this a hackathon project rather than a chore.

## Architecture

| Box | Tech | Load-bearing? |
|---|---|---|
| Build, container, test suite | Docker, CI, Codex as the build assistant | Build-time only |
| Typed tool interface | NVIDIA Agent Toolkit | Yes — NVIDIA |
| Agent that uses the revived tool for a real task | Rosalind / OpenAI | Yes — OpenAI |

## Data

Whatever the tool consumes. The paper's own example data is ideal, because matching the
published output is the regression test.

## MVP by Saturday 18:00

One tool building reproducibly, tests passing, wrapper working, and an agent using it to
answer a question that genuinely needs that tool.

## The demo frame

`docker run` on a tool that has not built since 2011, reproducing the paper's exact numbers,
then an agent invoking it as part of a workflow.

## Rubric self-score (ours, 1–10)

| Criterion | Score | Why |
|---|---|---|
| Scientific relevance | 6 | Real value, but indirect, and depends entirely on tool choice |
| NVIDIA + OpenAI use | 5 | Codex does the work but is build-time; wrapper is thin |
| Execution | 7 | Very likely to produce *something*, hard to produce something exciting |
| Originality | 5 | It is the track brief, so other OSS-track teams will do something similar |
| Presentation and repro | 8 | The artifact is the most durable here |

## Risks and kill criteria

- Tool choice is the whole game and must happen Friday. A tool nobody misses scores a 3 on
  relevance regardless of how well we package it.
- Build archaeology is unbounded. **Two-hour timebox per tool, then move to the next
  candidate.** Have three candidates ranked before starting.

## Verdict

The reliable floor. Low ceiling. Worth holding as a fallback rather than a first choice, and
worth noting it is the one idea here that definitely produces something useful even if the
weekend goes badly.
