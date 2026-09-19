# Developer README

Working notes for the team.

## Running the frontend

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Opens on <http://localhost:8501> in **Mock mode** — it replays a fixture and needs no
backend, no GPU and no tokens. Switch to Live mode in the sidebar once the backend is up
on `localhost:8000`.

Before pushing frontend changes: `python frontend/smoke_test.py` (headless, no Streamlit).

Details, fixture format and the UI conventions are in
[frontend/README.md](frontend/README.md). The event schema shared with the backend is
`frontend/ui/events.py` and [ARCHITECTURE.md](ARCHITECTURE.md) — changing a field name
there is a two-worktree conversation.

Verified on Python 3.12.10 / Streamlit 1.64 / Windows 11.

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

## Backend service (`hack-infra` worktree)

The FastAPI service, the agent orchestration and the providers. Design and the
event-schema contract with the UI live in [ARCHITECTURE.md](ARCHITECTURE.md); this
section is how to run it.

### Setup

Python 3.11 or newer.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt     # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux/Brev
cp .env.example .env
```

Nothing else. No database, no GPU, no API key: the default `RUN_MODE=mock` runs the
whole system on fixtures.

### Run it

```bash
# API on http://127.0.0.1:8000  (interactive docs at /docs)
.venv/Scripts/python.exe -m uvicorn app.main:app --reload

# or headless, printing the agent stream to the terminal
.venv/Scripts/python.exe -m app.cli "Why did this patient fail?" samples/*

# tests (35 of them, ~1s, no network)
.venv/Scripts/python.exe -m pytest -q
```

`samples/` holds one worked patient: a VCF, a labs CSV and clinical notes for a
metastatic colorectal cancer case that progressed on FOLFIRI + cetuximab. `POST
/demo/sample-patient` loads the same three files into the service in one call, which
is the demo path — no file picker on stage.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/upload` | Multipart patient files. Returns `file_id`s and the parsed record count per file. |
| `POST` | `/demo/sample-patient` | Loads the bundled sample patient. Same response shape as `/upload`. |
| `POST` | `/investigate` | `{question, file_ids}` → `{run_id}`. Starts the run in the background. |
| `GET` | `/events/{run_id}` | SSE stream of the event schema. Replays from the start, so connecting late is fine. |
| `GET` | `/events/{run_id}/log` | The same events as one JSON array, for tests and debugging. |
| `GET` | `/report/{run_id}` | Structured report. Readable while the run is still going (`status: running`). |
| `GET` | `/runs`, `/health` | What is running, and which mode the service is in. |

SSE frames carry a `data:` line only — no `event:` name — so a browser
`EventSource.onmessage`, a Streamlit polling loop and plain `curl -N` all read the
same stream. The event type is inside the JSON.

### Mock mode, and what is actually fake

`RUN_MODE=mock` fakes the **model outputs only**. The orchestrator, the agent spawning,
the blackboard the specialists talk through, the event stream, the retrieval ranking and
the abstention gate are all the real code paths. That is deliberate: it means the mock
demo and the live demo differ in one layer, and a bug found in mock is a real bug.

Two properties worth keeping:

- **Grounded in the upload.** Mock claims are built from the parsed bundle, not from
  canned prose. Hand it a different VCF and the findings change.
- **Deterministic.** Same input, same run, same wording — so a rehearsal is worth
  something. `MOCK_LATENCY_SCALE` controls only the pacing: `1.0` for the demo, `0` for
  tests, `0.2` when you are iterating.

### Environment

| Variable | Default | Notes |
|---|---|---|
| `RUN_MODE` | `mock` | `mock` or `live`. |
| `MOCK_LATENCY_SCALE` | `1.0` | Multiplier on simulated thinking time. |
| `REASONING_BASE_URL` / `REASONING_API_KEY` / `REASONING_MODEL` | OpenAI defaults | GPT-Rosalind or any OpenAI-compatible chat endpoint. |
| `BIONEMO_BASE_URL` / `BIONEMO_API_KEY` / `BIONEMO_VARIANT_MODEL` / `BIONEMO_EMBED_MODEL` | localhost NIM | Confirm the real paths against the container running on Brev. |

### Layout

| Path | What it is |
|---|---|
| `app/events.py` | Event schema and the bus. The contract with the UI. |
| `app/providers/` | `base.py` protocols, `mock.py` fixtures, `live.py` real endpoints, factory in `__init__.py`. |
| `app/agents/` | One file per specialist, plus `base.py` (agent + blackboard) and `critic.py` (the abstention gate). |
| `app/engine.py` | The orchestrator: plan, spawn, gather, criticise. |
| `app/ingest.py` | VCF / labs CSV / notes → `PatientBundle`, keeping source line numbers for provenance. |
| `app/main.py` | FastAPI transport. |
| `fixtures/` | Mock annotations, the literature corpus, and captured sample runs. |
| `samples/` | The worked patient used by the demo and the tests. |

### Handing events to the frontend

`fixtures/sample_event_log.json` and `fixtures/sample_report.json` are a full captured
run (plus `*_hypothesis.json` for the hypothesis-rejection case). The UI can be built
against those with no backend running. Regenerate after any schema change:

```bash
.venv/Scripts/python.exe scripts/capture_event_log.py
.venv/Scripts/python.exe scripts/capture_event_log.py --question "Did the patient fail because of MTHFR C677T?" --tag _hypothesis
```

### Going live

Set `RUN_MODE=live` and fill the credentials. The live provider deliberately raises
rather than degrading into invented output, so a missing key fails loudly. Two things
need confirming on site before it will work end to end — both are open questions in
[Context/tooling.md](Context/tooling.md):

1. whether GPT-Rosalind is callable programmatically, and at what URL;
2. which BioNeMo NIMs are available on Brev, and the request shape of the variant-effect
   endpoint.

`app/providers/live.py` is the only file that should need editing when those answers
arrive. If one vendor is unavailable, the factory can return a mixed pair — real
BioNeMo with mock reasoning, or vice versa — and the demo still runs.
