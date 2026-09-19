# Frontend: investigation UI

Streamlit UI for the patient failure-investigation agent system. Owns the
visualisation half of the contract in [`../ARCHITECTURE.md`](../ARCHITECTURE.md).
The backend (`hack-infra`) owns the engine.

## Run it

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Opens on <http://localhost:8501>. **No backend needed**, it starts in Mock mode.

## The two modes

| Mode | Source | Needs |
|---|---|---|
| **Mock** (default) | replays a fixture from `fixtures/`, sleeping the real inter-event gaps so it animates | nothing |
| **Live** | `POST /investigate` then streams `GET /events/{run_id}` | the backend on `localhost:8000` |

In Live mode the sidebar defaults to **the bundled sample patient**, which loads
server side via `POST /demo/sample-patient`. That is the stage path: no file
picker, nothing to drag around during a demo. Turn the toggle off to upload your
own VCF, labs CSV and notes instead.

To run both halves:

```bash
python -m uvicorn app.main:app --port 8000   # backend, mock mode by default
streamlit run frontend/app.py                # frontend, switch to Live
```

Both paths yield the same `Event` objects and fold into the same `RunState`, so
what you rehearse in mock mode is what you get live. Mock mode is the daily dev
loop and the zero-token rehearsal path, the same reasoning as `RUN_MODE=mock` on
the backend.

### Fixtures

- `demo_run.json`: three specialists converge on a B2M-loss verdict at 0.78
  confidence, with the critic cross-examining zygosity and **excluding** a weak
  finding rather than folding it in.
- `demo_abstain.json`: the same machinery on a question the bundle cannot
  answer. The critic **abstains**. This is the honesty case. Keep it in the
  demo, it is the thing that separates us from "an LLM guesses".

Add a fixture by dropping a `{"events": [...]}` file in `fixtures/`. It appears
in the sidebar automatically. Saving a real run's event log as a fixture makes it
replayable with no backend, worth doing for anything that demos well.

## Layout of the page

The **question is the entry point of the program**, so it sits at the top of the
main column at display size, not in the sidebar. The sidebar holds run settings
only. Everything below the question is the investigation unfolding:

1. **Stat strip**: agents, events, findings, elapsed.
2. **Agent graph** (Graphviz): nodes appear as `agent_spawned` arrives. Solid
   arrows are spawns, dashed labelled arrows are agent-to-agent messages. Status
   badge per node, and whichever agent just acted takes a heavy dark outline so
   the eye follows the investigation.
3. **Agent conversation**: `agent_message` events as a chat, sender to
   recipient. This is where the critic's push-back reads.
4. **Agent roster**: cards that animate in as agents spawn, each showing role,
   status, step count and its latest line. A live agent has a pulsing dot.
5. **Verdict**, then **Findings / Timeline / Agents / Raw events** tabs, for when
   a judge asks "is this real?".

## Colour policy

Decided with the `dataviz` skill's validator rather than by eye, and recorded in
`ui/theme.py`.

Agents are coloured by **function** (planner, specialist, critic), not by role.
Six role hues fail the all-pairs colourblind and normal-vision separation floors
in both light and dark mode; three pass every check (worst all-pairs
normal-vision delta E 24.0 light and 20.9 dark, CVD 9.2 and 9.4). Individual role
identity is carried by the role name written on every node and card, so nothing
depends on hue alone. The Agents tab is a plain table that works with no colour
at all.

Two rules follow from that and are worth keeping:

- **Hue is a mark, never text.** Colour appears as bars, dots, chips and node
  fills. Label text wears ordinary ink, which keeps contrast compliant on both
  themes.
- **Status colours are reserved.** Good, warning and critical carry confidence
  bands and run state only. They are never reused as an agent colour, so a red
  node never means "an agent" and an amber verdict always means "abstained".

To retarget the palette, change `GROUP_COLORS` in `ui/theme.py` and re-run the
validator in the `dataviz` skill.

## Files

```
frontend/
  app.py            Streamlit entry point, layout + the streaming loop
  smoke_test.py     headless check of the fold + graph; run before pushing
  requirements.txt
  fixtures/         replayable runs
  ui/
    events.py       SHARED CONTRACT. The event schema; coordinate changes.
    state.py        folds events into RunState; every panel is a view of this
    stream.py       live SSE client + fixture replay, both yielding Events
    graph.py        RunState to Graphviz DOT
    theme.py        design tokens, colour policy, the stylesheet
    components.py   the render functions
```

## Conventions worth keeping

- **Rendering is a pure function of `RunState`.** A saved event log replays to an
  identical screen. Do not reach around it for live-only state.
- **Event parsing is forgiving.** Unknown event types, missing fields and
  malformed payloads render as an error row rather than raising, because a
  backend schema change must not blank the screen mid-demo.
- **Markup is hand-written, styled from `theme.py`.** Panels are built from HTML
  against the design tokens rather than assembled from default widgets, so the
  page reads as one surface. New panels should take their colour and type from
  the tokens, not invent values.
- `ui/events.py` mirrors the backend contract. Changing a field name there is a
  two-worktree conversation, not a local edit.

## Checks

```bash
python frontend/smoke_test.py
```

Folds every fixture, asserts agents spawn, converse, finish and produce a verdict,
builds the graph, and confirms malformed events degrade instead of raising.
