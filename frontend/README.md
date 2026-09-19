# Frontend — investigation UI

Streamlit UI for the patient failure-investigation agent system. Owns the
visualisation half of the contract in [`../ARCHITECTURE.md`](../ARCHITECTURE.md);
the backend (`hack-infra`) owns the engine.

## Run it

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Opens on <http://localhost:8501>. **No backend needed** — it starts in Mock mode.

## The two modes

| Mode | Source | Needs |
|---|---|---|
| **Mock** (default) | replays a fixture from `fixtures/`, sleeping the real inter-event gaps so it animates | nothing |
| **Live** | `POST /investigate` then streams `GET /events/{run_id}` | the backend on `localhost:8000` |

Both paths yield the same `Event` objects and fold into the same `RunState`, so
what you rehearse in mock mode is what you get live. Mock mode is the daily dev
loop and the zero-token rehearsal path — same reasoning as `RUN_MODE=mock` on
the backend.

### Fixtures

- `demo_run.json` — three specialists converge on a B2M-loss verdict at 0.78
  confidence, with the critic cross-examining zygosity and **excluding** a weak
  finding rather than folding it in.
- `demo_abstain.json` — the same machinery on a question the bundle cannot
  answer. The critic **abstains**. This is the honesty case; keep it in the demo,
  it is the thing that separates us from "an LLM guesses".

Add a fixture by dropping a `{"events": [...]}` file in `fixtures/`. It appears
in the sidebar automatically. Saving a real run's event log as a fixture makes it
replayable with no backend — worth doing for anything that demos well.

## Where the agents show up

The brief is that you can *see* agents spin up and talk to each other. Four
places, all driven by the same event fold:

1. **Agent graph** (Graphviz) — nodes appear as `agent_spawned` arrives. Solid
   arrows are spawns, dashed labelled arrows are agent-to-agent messages. Status
   badge per node (`●` working, `✓` done, `✗` failed), and whichever agent just
   acted gets a heavy dark border so the eye follows the investigation.
2. **Agent conversation** — `agent_message` events as a chat, `sender → recipient`.
   This is where the critic's push-back reads.
3. **Agent cards** — a roster that grows as agents spawn, each showing role,
   status, step count and its latest line.
4. **Timeline / Agents / Raw events tabs** — the full log, for when a judge asks
   "is this real?".

## Layout

```
frontend/
  app.py            Streamlit entry point, layout + the streaming loop
  smoke_test.py     headless check of the fold + graph; run before pushing
  requirements.txt
  fixtures/         replayable runs
  ui/
    events.py       SHARED CONTRACT — the event schema. Coordinate changes.
    state.py        folds events into RunState; every panel is a view of this
    stream.py       live SSE client + fixture replay, both yielding Events
    graph.py        RunState -> Graphviz DOT
    components.py   the render functions
```

## Conventions worth keeping

- **Rendering is a pure function of `RunState`.** A saved event log replays to an
  identical screen. Don't reach around it for live-only state.
- **Event parsing is forgiving.** Unknown event types, missing fields and
  malformed payloads render as an error row rather than raising — a backend
  schema change must not blank the screen mid-demo.
- `ui/events.py` mirrors the backend contract. Changing a field name there is a
  two-worktree conversation, not a local edit.

## Checks

```bash
python frontend/smoke_test.py
```

Folds every fixture, asserts agents spawn, converse, finish and produce a verdict,
builds the graph, and confirms malformed events degrade instead of raising.
