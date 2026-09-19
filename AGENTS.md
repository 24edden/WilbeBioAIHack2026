# Project instructions

Single source of project instructions for every coding agent. Codex reads this file
directly; Claude Code reads it through the `@AGENTS.md` import at the top of `CLAUDE.md`.
**Edit this file, not `CLAUDE.md`.**

Hackathon project for the Wilbe Bio x AI hack (London, WilbeLABS). Project idea is TBD.

## Context

Background lives in `Context/`. Read the relevant file before working, rather than
guessing at the event's constraints:

- `Context/challengeWeb.md` — event brief, the four tracks, speakers.
- `Context/judgingCriteria.md` — scoring rubric, submission requirements, prizes.
  Read this before writing slides, the pitch, or anything about scope.
- `Context/tooling.md` — accounts to set up (Brev, Codex, Rosalind), what each
  platform is for, and which tools count as "central to the solution" for judging
  criterion 2 versus which are just build-time tooling. Read before proposing an
  architecture. Sections marked INFERRED are team analysis, not event text.

## Planning

`Plan/` holds pre-event idea generation and execution plans: 16 scored candidates in
`Plan/ideas/`, three worked-up finalists in `Plan/finalists/`, plus the decision framework,
timeline, risk register, presentation structure and reproducibility checklist.

Start at `Plan/README.md`. All of it was written before the team, the compute and the event
details were known — treat it as scaffolding to be revised, not as decisions already made.
`Plan/06-iteration-log.md` lists the open questions that must be answered on site.

`DeveloperREADME.md` has team setup notes and conventions.

## Conventions

- One branch per workstream, merge into `main` when it runs.
- When you discover a setup step, write it into `DeveloperREADME.md`. The judges score
  reproducibility by another team, so undocumented setup costs us points.
- Prefer small, working, demoable pieces over half-finished large ones. We get five
  minutes on Sunday and a live demo counts for more than architecture.
