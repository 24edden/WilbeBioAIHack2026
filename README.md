# WilbeBioAIHack2026

Repo for the Wilbe Bio x AI hackathon (London, WilbeLABS).

TRACE is a scientist-facing investigation workspace: provide files, ask a question,
watch specialist agents exchange evidence, and inspect a sourced report or abstention.
The current treatment-failure workflow is a prototype; datasets and backend behavior
are expected to change.

Team setup notes and how to load the context files into Claude, Codex, or a web UI are in
[DeveloperREADME.md](DeveloperREADME.md).

## Run locally

Python 3.11 or newer. From the repository root:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r frontend/requirements.txt
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
# In a second terminal:
.venv/Scripts/python.exe -m streamlit run frontend/app.py
```

Open <http://localhost:8501>. Recorded replay works without a backend. Connected
investigations use the server's configured providers; the default backend uses mock
model outputs and requires no keys. A connected UI does not imply live model inference.

On macOS/Linux, use `.venv/bin/python` instead. See
[DeveloperREADME.md](DeveloperREADME.md) for environment configuration and Brev access.

## Changing the system

Start with [INTEGRATION.md](INTEGRATION.md) when connecting a teammate's backend or
replacing datasets. Keep backend-specific data mapping at the frontend adapter boundary;
the backend does not need to adopt this prototype's internal patient model.

- [frontend/README.md](frontend/README.md): UI configuration, transport adapters and views.
- [ARCHITECTURE.md](ARCHITECTURE.md): current execution, UI and provider boundaries.
- [Plan/architecture-review.md](Plan/architecture-review.md): bottlenecks, implemented
  changes and remaining architecture decisions.
- [Plan/feature-direction.md](Plan/feature-direction.md): researched feature proposals,
  causal-grounding distinctions and evaluation approach; proposals are not shipped features.

## Verify

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe frontend/smoke_test.py
```

The tests include backend-to-frontend event compatibility, grounding and abstention.
They check software behavior, not clinical validity.

## Layout

```
Context/           event brief, judging criteria, tooling prep
Plan/              idea candidates, scoring, and execution plans
app/               backend API, ingestion, providers and agents
frontend/          scientist workspace and backend adapters
samples/           bundled demonstration input files
tests/             backend and integration checks
AGENTS.md          project instructions for coding agents (edit this one)
CLAUDE.md          one-line import of AGENTS.md, for Claude Code
```

## Notes

Submission needs this repo to be enough for someone else to reproduce whatever ends up in
the presentation, so keep setup steps and data sources written down here as we go.
