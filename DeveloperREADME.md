# Developer README

Working notes for the team.

## Responsive execution and profiling

The UI runs event sources in a session-owned worker and drains batches on the
Streamlit script thread. Source workers must never call Streamlit or mutate its
session state. The submitted question/configuration is a snapshot; editing the
next draft does not change a running investigation. Keep the adapter boundary when
replacing the backend. See [ARCHITECTURE.md](ARCHITECTURE.md) and
[Plan/architecture-review.md](Plan/architecture-review.md).

Variant scoring uses at most eight workers per investigation and reuses identical
biological inputs within that run. Each original upload's provenance is retained.
This is not a cross-user cache or a cache of reasoning responses. The API provides
real cancellation at `POST /runs/{run_id}/cancel`; closing an SSE connection does
not stop a backend run. Reports and terminal events share execution metrics.

Reproduce the small synthetic performance check without keys or live model calls:

```powershell
.venv/Scripts/python.exe scripts/profile_workflow.py --output .deploy/profile-new.json
```

Use a new output filename. [Plan/performance-check.json](Plan/performance-check.json)
records three trials per case before/after: repeated copies of five variants went
from 60 scoring calls to five while preserving the findings and verdict. Small-case
wall times were effectively unchanged. Paced cases include simulated waits; these
measure orchestration and resource use, not live inference or scientific accuracy.

Voice controls use the browser's speech APIs, with no server transcription model or
new API key. Recognition is opt-in and may use the browser vendor's service. It
requires browser support, microphone permission, and HTTPS or localhost. Spoken
stage updates are opt-in and use local device voices when available. Unsupported
features show text guidance; typing and navigation remain available.

## Comparing models and configurations

The new `eval/` runner uses the existing Python dependencies. From the repository root:

```powershell
.venv/Scripts/python.exe -m eval --output eval/results/comparison-001.jsonl --concurrency 2
```

This runs a token-free, six-trial mock comparison on three frozen repo cases. Choose
a new output filename each time. Read [eval/README.md](eval/README.md) for live
configuration, actual token accounting, and replacing the backend adapter; see
[Plan/model-evaluation.md](Plan/model-evaluation.md) for the researched benchmark
recommendation. Mock behavioral passes are not model-performance or scientific scores.

## Hosting and demo deployment

[infra/README.md](infra/README.md) documents the single-host Docker Compose setup,
readiness checks, Brev access and its current validation status. The API remains
private and uses one worker because uploads and runs are stored in memory.

[Plan/hosting-and-demo.md](Plan/hosting-and-demo.md) compares hosting options and
sets out a live presentation with clearly labeled precomputed results and recorded
fallbacks. The service is deployed on `agentic-takeoff-cpu` in mock mode at
<https://trace-z484f0h2c.gobrev.dev> (NVIDIA sign-in and an allowed account required).
The containers, connected API workflow and UI through SSH forwarding have been
verified. See [infra/DEPLOYMENT.md](infra/DEPLOYMENT.md) for release fingerprints,
test results and the remaining authenticated-browser check.

## Connecting to NVIDIA Brev from Windows

Verified on 19 September 2026: the Brev CLI is installed and authenticated inside
the `Ubuntu` WSL distribution (`/home/ed/.local/bin/brev`). Run from PowerShell:

```powershell
wsl -d Ubuntu -- bash -lc 'brev ls'
wsl -d Ubuntu -- bash -lc 'brev refresh'
wsl -d Ubuntu -- bash -lc 'brev shell agentic-takeoff-cpu'
# Run a single remote command:
wsl -d Ubuntu -- bash -lc 'brev exec agentic-takeoff-cpu "hostname"'
```

`brev refresh` repairs missing or stale SSH host configuration; it resolved
`Could not resolve hostname agentic-takeoff-cpu` during this check. The current
instance is in `London-AI-Brev`, is running, and is a CPU machine (`n2d-highmem-4`)
with no GPU listed. Use `brev ls` to confirm the current instance before connecting.

## Running the frontend

Run from the repository root so `.streamlit/config.toml` themes the native controls.
For backend/dataset replacement boundaries and the small UI contract, see
[INTEGRATION.md](INTEGRATION.md).

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Opens on <http://localhost:8501> with the single prompt composer and **Play the pet demo**. This runs the workflow on the
bundled synthetic case with an editable question and agent selection, simulated
model outputs, and no API keys. Install both root and frontend requirements for this
mode. Recorded playback remains available. Set `TRACE_BACKEND_URL=http://localhost:8000` before starting the frontend to connect the same three-screen interface to the backend. The connected backend can
itself run in mock mode; the UI labels simulated output explicitly.

Before pushing frontend changes: `python frontend/smoke_test.py` (headless, no Streamlit).

Details, fixture format and the UI conventions are in
[frontend/README.md](frontend/README.md). The event schema shared with the backend is
`frontend/ui/events.py` and [ARCHITECTURE.md](ARCHITECTURE.md). Changing a field name
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
when the repo has no `CLAUDE.md`. If both files exist, Claude reads `CLAUDE.md` and
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
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --env-file .env

# or headless, printing the agent stream to the terminal
.venv/Scripts/python.exe -m app.cli "Why did this patient fail?" samples/*

# tests (no network; includes grounding and frontend event-contract regressions)
.venv/Scripts/python.exe -m pytest -q
```

`samples/` holds one worked patient: a VCF, a labs CSV and clinical notes for a
metastatic colorectal cancer case that progressed on FOLFIRI + cetuximab. `POST
/demo/sample-patient` loads the same three files into the service in one call, which
is the demo path — no file picker on stage.

The API command above loads `.env` explicitly. For the headless CLI, export the
variables in your shell before running; `app.config` itself reads process environment
variables, not `.env` files. Install `frontend/requirements.txt` into the same virtual
environment to run the backend-to-frontend contract tests and the Streamlit app.

The current orchestration implementation is the plain async fallback described in
`ARCHITECTURE.md`; NVIDIA Agent Toolkit integration is not implemented. Live BioNeMo
paths and model names are provisional adapters, not verified deployed NIM services.
Missing reasoning credentials return HTTP 503 before creating a run; live failures
never switch silently to fixtures.

Grounding regressions cover multiple uploaded files, original note/CSV line numbers,
withholding model claims with missing or ambiguous source references, and abstention
when a second specialist does not corroborate the evidence. The confidence values
and this gate are demo heuristics, not calibrated probabilities.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/upload` | Multipart patient files. Returns `file_id`s and the parsed record count per file. |
| `POST` | `/demo/sample-patient` | Loads the bundled sample patient. Same response shape as `/upload`. |
| `POST` | `/investigate` | `{question, file_ids}` → `{run_id}`. Starts the run in the background. |
| `GET` | `/events/{run_id}` | SSE stream of the event schema. Replays from the start, so connecting late is fine. |
| `GET` | `/events/{run_id}/log` | The same events as one JSON array, for tests and debugging. |
| `GET` | `/report/{run_id}` | Structured report. Readable while the run is still going (`status: running`). |
| `POST` | `/runs/{run_id}/cancel` | Stops an active investigation, waits for cleanup, and preserves its partial report. Repeated requests return the existing terminal status. |
| `GET` | `/runs`, `/health` | What is running, and which mode the service is in. |
| `GET` | `/capabilities` | Implemented agent controls and safe configured model defaults. |

`POST /investigate` also accepts optional `config`: choose one to three unique
`specialists` from `genomics`, `clinical`, and `literature`; the orchestrator and
critic remain required. Live runs can override `reasoning_model`, `variant_model`,
and `embedding_model` for that run on the already-configured endpoints. Mock runs
reject model overrides rather than pretending a name changes the fixtures. See
[INTEGRATION.md](INTEGRATION.md) for examples, adapter hooks, and compatibility rules.

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
| `REASONING_BASE_URL` / `REASONING_API_KEY` / `REASONING_MODEL` | OpenAI base URL, empty key, `gpt-4o-mini` | Set model to `gpt-rosalind-research` with an approved project's key for Rosalind. |
| `REASONING_API` | `auto` | Selects Responses for Rosalind and chat completions for other models. Explicit `responses` / `chat_completions` also supported. |
| `REASONING_TIMEOUT_SECONDS` / `REASONING_MAX_OUTPUT_TOKENS` | `180` / `16000` | Reasoning timeout and output budget, including internal reasoning tokens. Uses `max_output_tokens` for Responses and `max_completion_tokens` for chat. |
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

For a free branded audience URL, domain options, QR preparation and the capacity
distinction between 50 viewers and 50 investigations, see
[Plan/public-demo-hosting.md](Plan/public-demo-hosting.md). The existing private
Brev link is not yet an anonymous audience demo.

GPT-Rosalind now has a Responses adapter. Follow
[Context/rosalind-integration.md](Context/rosalind-integration.md) for the verified
model ID, approved-project access requirement, `.env` settings and the
`scripts/check_reasoning.py` lookup/smoke checks. No API credential was configured
locally during implementation, so live generation remains unverified.

Set `RUN_MODE=live` and fill the credentials. The live provider raises rather than
degrading into invented output. A clinical-only run exercises Rosalind without
BioNeMo; its limited evidence still goes through the existing abstention gate.
Genomics and Literature also need confirmed BioNeMo NIM paths and request shapes.
The factory does not silently mix live and mock providers.

## Current frontend: three states

The `codex/pet-investigation-ui` branch now exposes only Prompt, Running and Results.
See [frontend/README.md](frontend/README.md) for setup and [frontend/QA.md](frontend/QA.md)
for the acceptance audit. The old classic/wizard switch and advanced UI paths have
been removed. The logo returns home without canceling active work or losing a draft.

The prompt is the original single rounded composer with integrated drop/picker and
file chips. It uses a dependency-free Streamlit v2 component (Streamlit 1.64+).
The UI uses the existing normalized events, source adapters and scientific result
components. Shared light/dark mode applies everywhere and persists during navigation.

Without `TRACE_BACKEND_URL`, submissions use the local mock engine. The demo sample's
unmodified public events are delivered over about 25 seconds; its timer is interruptible.
Real connected runs are never held behind a replay queue. Source completion immediately
opens the result while watching a run; Home navigation is respected if the user is
preparing another draft.

Local preview command:

```bash
python -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false --theme.base dark --theme.primaryColor '#d6fb73' --theme.backgroundColor '#080b09' --theme.secondaryBackgroundColor '#101612' --theme.textColor '#f0f5ee'
```

Validate with `python -m pytest -q`, `python frontend/smoke_test.py` and
`node tests/composer_browser_test.mjs`. Restart the dev server when Python interfaces
change, to avoid mixing cached imports with a new controller. The exact macOS/Python
3.12 preview packages are recorded in `frontend/requirements-preview.lock.txt`.

All pet files are permanently right-facing. They are public static assets; never
write user uploads or secrets into `frontend/static/`.

### Integrated pet UI (`codex/pet-ui-integration`)

This branch starts at `codex/pet-investigation-ui` and adds a settings drawer for
evidence, supported agent/model controls and browser voice preferences. Run with
Streamlit 1.64 or newer using the command above, or use port 8504 to keep the old
preview running separately. Restart Streamlit after Python module changes.

Theme switching and voice preferences are browser-only. Dictation requires an
explicit opt-in and click, supported browser speech recognition, and HTTPS or
localhost. The local volume meter animates the small microphone icon. Dictation
edits the draft; it never starts an investigation. Spoken updates use installed
device voices by default; online voices are a separate opt-in.

The network uses a lightweight SVG layout and counters fold observed events. Results can replay saved events
without executing another analysis. Requests snapshot their evidence and settings;
changing the drawer cannot rewrite a running request. Both upload surfaces share
the 20-file, 20 MB per file and 40 MB total limit.

`AgentProfiles/agent-profiles.json` and `source-lock.json` are pinned copies from
`docs/agent-profiles` at `7f8e31a`. They describe the separate nine-role Brev
harness, not this repository's local demo engine. The UI resolves descriptions
for reported skill IDs and provides a clearly labeled configured-profile reference.
It does not infer model calls, loaded skill versions or accepted NVIDIA results
from capability metadata. New services should implement the adapter/event contract
in `frontend/ui/adapters.py` and `frontend/ui/events.py`; importing profiles alone
does not connect the Brev harness.

Additional checks: `node tests/pet_microphone_test.mjs` exercises permission gating,
draft handling and media cleanup without accessing a real microphone. Keep API
keys in server environment configuration, never in browser assets or Git.

Integration validation: 191 Python tests passed before the final SVG replacement;
the new SVG renderer has a focused edge-attribution/escaping test. Composer, voice,
microphone and client-control Node checks passed. Browser checks covered the drawer,
agent selection, profile reference, live updates and unchanged theme geometry.
Repeated live Graphviz updates caused preview responsiveness problems; the integrated
network now renders bounded SVG instead. Final end-to-end browser revalidation was
curtailed at the user's request to ship promptly. Real microphone capture, provider
inference and 50-user hosting capacity were not exercised in this integration pass.

### Team TBD read-only connection

Set `TEAM_TBD_CAPSULE` to the private external
`team-tbd-results-capsule-2026-09-20-v1` directory to enable the connected pet
workspace. Start it separately on loopback port 8504, leaving the existing services
on 8081 and 8082 unchanged:

```bash
export TEAM_TBD_CAPSULE="/absolute/path/to/private/team-tbd-results-capsule-2026-09-20-v1"
.venv/bin/python -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8504 --browser.gatherUsageStats false --theme.base dark --theme.primaryColor '#d6fb73' --theme.backgroundColor '#080b09' --theme.secondaryBackgroundColor '#101612' --theme.textColor '#f0f5ee'
```

The workspace defaults to explicitly labeled frozen replay. Live reads fetch the
selected existing run, with optional 15-second refresh; no connected control
submits scientific work or changes backend settings. Unset `TEAM_TBD_CAPSULE` to
retain the original UI. Keep the capsule outside Git and public static assets.
See [frontend/TEAM-TBD.md](frontend/TEAM-TBD.md) for environment setup, source
routing, adapter mappings, integrity bounds, snapshot interpretation and validation.

The Team TBD connected workspace now displays only Ana GSE28460 and CAR-T/CD19,
in that order, with a black/lime theme. Open **Agent collaboration** to trace
upstream/downstream work, evidence, skills/model receipts and acceptance checks.
The overview and findings include direct drilldown buttons. Existing capsule
histories remain unchanged outside the two-study platform view.
