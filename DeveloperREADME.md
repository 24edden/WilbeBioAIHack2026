# Developer README

Working notes for the team. Setup and run instructions go here once we have something to run.

## Import frozen investigation results

Use the [run archive guide](docs/run-archives/README.md) and its versioned contract to build visualizations from saved investigations without launching agents or making provider calls. Full trace bundles are retained in the local and shared Brev workspaces; this public repository carries the safe run index and import materials. Verify the bundle and asset SHA-256 checksums, preserve original run status and execution environment, and distinguish source content hashes from Git commit identities.

## Context files

`Context/` holds the event material we want agents to know about:

| File | Contents |
|------|----------|
| [Context/challengeWeb.md](Context/challengeWeb.md) | Event brief, the four tracks, speakers |
| [Context/judgingCriteria.md](Context/judgingCriteria.md) | Scoring rubric, submission requirements, prizes |
| [Context/tooling.md](Context/tooling.md) | Accounts to create, what each platform does, and which tools earn judging points |

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

There are two files at the repo root, but only one of them has content:

- **[AGENTS.md](AGENTS.md)** is the single source of project instructions. **Edit this one.**
- **[CLAUDE.md](CLAUDE.md)** is one line, `@AGENTS.md`, followed by a short Claude
  Code-specific section.

Each tool picks it up automatically when it starts a session in this repo. There's no
command to run and nothing to keep in sync.

### Why it's arranged this way

Codex reads `AGENTS.md`. Claude Code reads `AGENTS.md` too (v2.1.277 and later), but only
when the repo has no `CLAUDE.md` — if both files exist, Claude reads `CLAUDE.md` and
ignores `AGENTS.md` entirely. Two files with the same content would mean Claude and Codex
reading different copies that drift apart within a day.

The `@AGENTS.md` import is the documented way out. Claude reads `CLAUDE.md`, the import
expands `AGENTS.md` inline, and both tools end up with identical instructions from one
file. A symlink (`ln -s AGENTS.md CLAUDE.md`) does the same thing, but the docs say to use
the import on Windows: symlinks need Developer Mode or admin rights, and git checks a
committed symlink out as a plain text file unless `core.symlinks` is set, which would
leave a teammate's clone with a one-line CLAUDE.md instead of any instructions.

### What goes in them

Things that apply to every session and that an agent can't work out from the code:
conventions, where to find things, decisions we've already made. Keep it short. Anything
long goes in `Context/` with a pointer from `AGENTS.md`, so it's read on demand instead of
loaded into every session.

Claude Code can also inline a context file with `@Context/challengeWeb.md` on its own
line. We're not doing that, since on-demand reading is cheaper and most tasks don't need
the brief. Worth switching if agents start ignoring it. Note this `@` import is a Claude
Code feature, Codex reads `AGENTS.md` as plain text, so an `@path` line there is just
text on the page.

### Checking it worked

In Claude Code, run `/context` and confirm `CLAUDE.md` appears under **Memory files**, or
just ask what its project instructions say.

## Conventions

- One branch per workstream, merge into `main` when it runs.
- Write down setup steps as you discover them, in this file. The judging criteria include
  reproducibility by another team, so a working README is worth actual points.
