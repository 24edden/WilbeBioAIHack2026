# TRACE · Team TBD

A scientist-facing workspace over the durable Team TBD scientific engine: ask a
question, follow nine scientific roles, inspect evidence and accepted handoffs,
and request guarded follow-up work. The black/lime pet homepage and Ana-then-CD19
saved-study explorer share the same interface.

The default `frontend/app.py` uses the scientific `/api/runs` API. Original
hypotheses, immutable decision versions, models, skill receipts, governance,
budgets and provider outcomes remain owned by `scientific_backend/`.

## Start

Use Python 3.12+ and two separate environments. From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r frontend/requirements.txt
# Set up the actual engine, its pinned public evidence and optional licensed tools:
# Follow scientific_backend/SETUP.md, then start its private service.
export TEAM_TBD_BACKEND_URL=http://127.0.0.1:8080
./scripts/start_scientific_frontend.sh
```

Open <http://127.0.0.1:8505> and choose **Connect scientific service**. This performs
GET reads only. **Start investigation** explicitly submits live scientific work.
The service must have a running worker and a previously verified research model.
There is no implicit demo, model replacement, upload API or fallback service.
See [backend setup](scientific_backend/SETUP.md) for environment variables,
private source hydration, optional tool entitlements, and the explicit capability
check required before live work. Installing source alone does not grant model or
plugin entitlement.

For an already running service, set `TEAM_TBD_BACKEND_URL` to its loopback origin
or private SSH tunnel. Do not replace existing services or runtime databases.
The application is a private, single-user loopback workspace without public-host
authentication.

## Frozen read-only studies

The existing frozen link remains supported. Set `TEAM_TBD_CAPSULE` to the sealed,
external `team-tbd-results-capsule/1.0` directory before starting the frontend:

```bash
export TEAM_TBD_CAPSULE=/absolute/path/to/team-tbd-results-capsule-2026-09-20-v1
./scripts/start_scientific_frontend.sh
```

The homepage buttons open Ana first, then CD19. Bookmarks retain
`?run=<run-id>&view=Overview&mode=replay`. Frozen pages verify recorded file hashes
and expose no scientific submission controls. Their files and original backend
runs are not changed. The capsule is private and is not included in this repo.

Selecting **Live reads** is an explicit read from the recorded source; a failed
connection never substitutes replay data. Its separate **Open live investigation
controls** button opens guarded writes. New live-run URLs use `?active_run=<id>`.
See [frontend contract](frontend/TEAM-TBD.md).

## Verify and reproduce

```bash
.venv/bin/python -m pip install -r requirements.txt pytest pytest-asyncio
# Both environments must be installed. The contract subprocess auto-selects
# scientific_backend/.venv, or set TEAM_TBD_TEST_PYTHON to that environment.
.venv/bin/python -m pytest tests -q
node tests/composer_browser_test.mjs
# Run the scientific engine suite in its own environment and working directory:
cd scientific_backend
.venv/bin/python scripts/check.py
```

Backend tests use fixtures and mocked vendors; no paid run, prediction, sequence
search or model probe is required for integration validation. Optional tests read
existing private snapshots/services only. See [release validation](docs/RELEASE-VALIDATION.md)
and [integration details](docs/FULL-STACK.md).

Source releases should use a reviewed commit (`git archive HEAD`), never archive a
working directory containing private runtime data. The source includes backend
code, role instructions, tests, pinned manifests, install hooks, frontend assets
and setup instructions. Provider credentials, external plugin bytes, full omics
inputs and sealed run archives stay outside public Git.

## Earlier prototype

The earlier small-role backend remains in `app/`, and its interface is explicitly
`frontend/legacy_app.py`. Files under `infra/` deploy that historical prototype.
They are not the scientific-engine startup path. Existing public development
history is retained; unrelated documentation PRs are not part of this release.
