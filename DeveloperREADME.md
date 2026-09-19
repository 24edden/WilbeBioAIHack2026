# Developer README

Working notes for the team. Setup and run instructions go here once we have something to run.

## Context files

`Context/` holds the event material we want agents to know about:

| File | Contents |
|------|----------|
| [Context/challengeWeb.md](Context/challengeWeb.md) | Event brief, the four tracks, speakers |
| [Context/judgingCriteria.md](Context/judgingCriteria.md) | Scoring rubric, submission requirements, prizes |

They are written as plain markdown with headings and tables so they read well both for us
and for a model. If you add a new one, keep that style: short frontmatter block at the top
saying what the file is, then headings rather than walls of prose.

Good candidates to add as we go: notes from mentor sessions, API/tooling docs we keep
re-reading, dataset descriptions, and the decisions we've already made and don't want to
relitigate.

## Getting the context into an agent

### Claude Code and Codex

Both are already wired up, see [How CLAUDE.md and AGENTS.md work](#how-claudemd-and-agentsmd-work)
below. For a one-off question you can also point at a file directly in a Claude Code
prompt with `@`:

```
@Context/judgingCriteria.md does this plan score well on execution?
```

That pulls the file in for that prompt only, which keeps the context window clean.

### Web UIs (claude.ai, ChatGPT)

Upload the `Context/*.md` files as attachments at the start of a conversation, or paste
them in. Worth doing for slide-writing and pitch-framing work, where you want the judging
criteria in front of the model but don't need the repo.

### Connecting the repo directly

Both Claude and ChatGPT can connect to a GitHub repo, which saves re-uploading. Only
useful once the repo is public or we've granted access, and it's no substitute for the
files above, connectors are better at answering questions about code than at absorbing a
brief.

## How CLAUDE.md and AGENTS.md work

There are two files at the repo root, [CLAUDE.md](CLAUDE.md) for Claude Code and
[AGENTS.md](AGENTS.md) for Codex. They serve the same purpose for different tools:

- The tool reads its file automatically when it starts a session in this repo, before you
  type anything. There's no command to run.
- Both files are deliberately short. They say what the project is, list the files in
  `Context/`, and say when to read them. The agent reads a `Context/` file when the work
  calls for it rather than loading everything up front.
- The two files currently have identical content. If you change one, change the other.
  They're duplicated because each tool only looks for its own filename, which is annoying
  but not worth a symlink on Windows.

What to put in them: things that apply to every session and that an agent can't work out
from the code. Conventions, where to find things, constraints we've agreed on. What not to
put in them: anything long, and anything that duplicates `Context/`, link to it instead.

Claude Code can also inline a file into `CLAUDE.md` with `@Context/challengeWeb.md` on its
own line, which loads the full contents into every session. We're not doing that, since
on-demand reading is cheaper and the files aren't needed for most tasks. Worth switching
if we find agents repeatedly ignoring the brief. Note that this `@` import is a Claude
Code feature, Codex just reads `AGENTS.md` as plain text.

## Conventions

- One branch per workstream, merge into `main` when it runs.
- Write down setup steps as you discover them, in this file. The judging criteria include
  reproducibility by another team, so a working README is worth actual points.
