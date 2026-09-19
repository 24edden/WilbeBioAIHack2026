# TRACE frontend

A Streamlit research workspace with editable inputs, agent configuration, a live
agent network, directed messages, inspectable findings and source references.

## Interactive demo and recorded cases

**Demo** runs the bundled sample through the real local investigation engine with
explicitly mock providers. Edit the question and select specialists: those inputs
change the investigation, including hypothesis rejection and abstention. No backend
server, credentials or external model calls are needed. Model outputs remain simulated;
this is not an unrestricted language-model chat. Demo ignores live-provider environment
settings, and model overrides are unavailable.

Install both the root and frontend requirements for interactive Demo. `DemoSource` in
`ui/adapters.py` streams normalized events directly from the local async engine and
cleans up when the stream closes. It also resolves the backend package ahead of
Streamlit's similarly named `frontend/app.py`. A frontend-only installation reports a
clear dependency error instead of switching to a live provider.

**Mock** remains fixed recorded playback with its saved question. **Live** connects to
the configured backend; that server may itself run mock or live providers. These are
three different execution sources, not interchangeable labels.

## Run

From the repository root, so `.streamlit/config.toml` styles the native widgets:

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

No backend is needed for **Explore a recorded case**. It replays a saved question,
evidence and agent outputs; the question and agent settings cannot silently alter
a recording. The default fixtures cover a conclusion and an abstention.

**Investigate my data** accepts files and an editable question, or the optional
server sample. Files and the selected configuration are submitted only when the
user clicks **Start investigation**. The connected backend may use mock providers; connected
transport is not evidence that a live model is running.

```bash
python -m uvicorn app.main:app --port 8000
streamlit run frontend/app.py
```

## Progressive user flow

The workspace reveals one step at a time:

The four section headers are keyboard-accessible navigation buttons. The active
section is highlighted and labeled current. Unavailable sections stay disabled:
Question needs evidence, Investigation needs a submitted run, and Results needs a
completed run. Header navigation saves current draft edits before transitioning and
never submits work. After completion, Investigation opens the recorded activity
without showing failure/retry controls or calling the source again.

The Research question panel is available in every section. It opens on the Question
step and can be minimized elsewhere. A single editor updates the next-run draft;
the submitted question is shown separately once a run exists. Editing from Evidence,
Results or completed Investigation never changes an existing run. While a request
is actively streaming, the submitted question remains readable and the next-run
draft stays editable; changing it never alters the active request. Recordings show their fixed question with an explicit
Use an editable demo action that creates a draft without starting any work.

1. **Evidence**: choose a recording or upload files. Connection settings and playback
   speed are optional expanders. Nothing is uploaded to the backend at this step.
2. **Question & agents**: enter the question, select specialists and optionally expand
   model settings. A recording keeps its original question and agent configuration.
3. **Investigation**: starting explicitly submits the request and reveals the network
   and directed messages. A background worker consumes the submitted snapshot once;
   navigating or rerendering never resubmits it. Supported sources expose real
   cancellation and wait for cleanup before showing a stopped result.
4. **Results**: the conclusion appears first. Evidence, agent activity and run details
   provide progressively deeper inspection; raw events remain in an expander.

Draft values live in a plain session dictionary separate from widget state, so Back
preserves question, selected agents, model fields and file bytes even when Streamlit
removes widgets from the previous step. Returning to evidence shows saved filenames;
Remove saved files clears the saved selection and resets the uploader. A new file
selection replaces the saved files. No backend upload occurs before Start.

Start takes independent copies of the draft into a frozen `RunRequest` snapshot.
Editing next-run settings cannot change the submitted request or completed result.
View previous result returns to the preserved report without a new run. Start a new
investigation resets the draft; the previous report remains reachable until a new
run is explicitly submitted. This is session-local state, not persistent storage.

Startup failures and streams that end without `run_complete` stay on Investigation
with the error and explicit Retry/Edit actions. Retry creates a new attempt from the
submitted snapshot; it does not claim to resume the old backend job.

## Where to change things

Results offer **Replay agent activity**, which folds a snapshot of that run's
saved events into a separate `RunState`. Playback supports pause, next event,
restart and speed selection. It makes no model/API calls, compresses long waits,
and leaves the original report and next-question draft intact. `ui/replay.py`
owns timing; the existing polling fragment renders the graph and messages.

**Run follow-up** submits a new investigation with the submitted evidence and
settings, plus bounded prior question, conclusion, findings and weak-point context.
The user prompt stays short in the UI. `ui/followup.py` sends the context through
the existing question-based adapter contract, explicitly labeling generated claims
as untrusted context to recheck. Previous results remain available in the session
(up to five). Recorded cases use a clearly labeled, context-only simulated idea
review because their original source files are not necessarily available.

Question-mark help beside controls and result panels uses `ui/help.py` with
immediate CSS hover/focus tips. Text appears on hover and hides when the pointer
leaves; keyboard focus also reveals it. Keep the copy in `ui/help_text.py` current when changing providers,
datasets or scientific interpretation.

| Change | Edit |
|---|---|
| Product name, title, description, question, dataset/input copy | `ui/config.py`: `ProductProfile` and `PROFILE` |
| Allowed file extensions, whether files are required, sample availability | `ProductProfile.input_extensions`, `require_files`, `sample_available` |
| Known role color groups, review-stage roles, decorative role preview | `ProductProfile.role_groups`, `review_roles`, `preview_roles` |
| Labels for the four observed workflow stages | `ProductProfile.stages` |
| Fixture labels/default | `ProductProfile.fixture_labels`, `default_fixture` |
| Available recordings | `frontend/fixtures/`, or `TRACE_FIXTURE_DIR` environment variable |
| Default server address | `TRACE_BACKEND_URL` environment variable, or the Evidence step's Connection settings |
| HTTP routes, request/response fields, event mapping | `ui/stream.py`: `BackendContract` |
| A different transport, polling/local process, data source | `ui/adapters.py`: implement `InvestigationSource`, replace `source_for` |
| Main inputs and session lifecycle | `app.py` (stage controller and persistent draft) |
| Agent settings and panel composition/order | `ui/layout.py` |
| Question-mark help explanations | `ui/help_text.py`: `HELP` |
| Reusable panels, graph and appearance | `ui/components.py`, `ui/graph.py`, `ui/theme.py`, `.streamlit/config.toml` |
| Normalized event/view state | `ui/events.py`, `ui/state.py`; keep these stable when changing wire formats |

The file extension list controls the picker only. The new backend must actually
support the selected formats. `preview_roles` supplies three labels on the idle
illustration, not an allowed-agent list. `stages` supplies four milestone labels
for the current layout. Unknown runtime roles are displayed with their actual
name and a fallback specialist color; they are not dropped.

## Adapter boundary

`RunRequest` contains `mode`, `question`, `backend`, optional `fixture`, `speed`,
`sample`, `uploads` (name/bytes pairs) and `config`. `InvestigationSource` exposes:

```python
capabilities(backend: str) -> dict
events(request: RunRequest) -> Iterator[Event]
```

`ReplaySource` and `BackendSource` implement that boundary. Views consume only
normalized `Event` objects folded into `RunState`; they do not inspect HTTP bodies.
`BackendContract` has default routes compatible with the existing server and these
mapping hooks:

- `start_payload(question, file_ids, config)` builds the entire start request.
- `parse_file_ids(body)` and `parse_run_id(body)` normalize response identifiers.
- `map_event(raw)` converts a decoded SSE JSON record to `Event`.
- `map_capabilities(body)` converts the server catalog to the UI shape below.

The contract also configures upload, sample, start, events, report and capabilities
paths, and the multipart file field name. Pass a custom contract to `BackendSource`
in `source_for`; no renderer changes are required. Existing low-level functions in
`stream.py` retain their old signatures, with optional keyword-only contract/config
arguments. Invalid event mappings produce visible error events while later events
continue. Source startup/iteration failures appear in the workspace.

## Agent and model controls

The connected source reads `/capabilities` (cached for 15 seconds). Expected
normalized shape:

```json
{
  "run_mode": "mock",
  "specialist_roles": [{"id": "clinical", "label": "Clinical"}],
  "required_roles": ["orchestrator", "critic"],
  "defaults": {
    "specialists": ["clinical"],
    "reasoning_model": "server model id",
    "variant_model": "server model id",
    "embedding_model": "server model id"
  },
  "model_overrides_supported": false
}
```

The panel sends selected unique specialist IDs, not a fictitious replica count.
Its total includes the required agents. The current backend requires two specialist
roles to support its conclusion gate; one specialist is useful for inspection.
Change or clear `ProductProfile.single_specialist_note` for another evidence gate.
If model overrides are supported, users can enter model IDs for shared reasoning,
variant analysis and literature embeddings. These are provider model IDs, not a
discovered model list. Credentials remain server-side. Mock providers disable model
overrides while still honoring the actual agent roster.

If capabilities are unavailable (including an older backend), ordinary runs remain
available using server defaults and the panel explains that configuration is
unavailable. Effective settings are supplied by `run_started.payload.config`, visible
in the separate Run configuration expander, raw events and the backend report; requested controls are not a claim of success.

## Weak-point assessment

Results includes a **Weak points** tab with the assessed count, backend-supplied
rationale, proposed next evidence and expandable finding/source references. It
consumes `run_complete.payload.weak_points`, the same object exposed by
`GET /report/{run_id}`. Demo, connected runs and replay share this event path;
the UI does not fetch a second assessment or derive scientific weaknesses locally.

The normalized object is `{status: "assessed" | "not_assessed", items: [...]}`.
Each item supplies `id`, `category`, `title`, `rationale`, `next_evidence`,
`finding_ids` and `sources`. Existing categories include evidence gaps, conflicting
findings, source gaps, provider failures and scope limits. Unknown categories retain
their backend name. Missing/unsupported assessment payloads show **Not assessed**,
which is distinct from an assessed result returning zero items. Older recordings
therefore never receive fabricated analysis. Tooltips state this assessment's scope.

## Checks

```bash
python frontend/smoke_test.py
python -m pytest -q tests/test_frontend_contract.py tests/test_frontend_adapter.py tests/test_frontend_flow.py
```

Smoke checks cover both recording outcomes and malformed events. Integration checks
cover actual backend events and a replacement contract with different routes,
request fields, catalog and event format. AppTest has also verified the connected
panel sends a selected two-specialist roster that produces exactly those agents plus
the required planner/critic, and rejects an empty selection before starting.

Event timestamps display elapsed run time, retaining raw timestamps unchanged.
Confidence is labeled as a model/heuristic score, not a calibrated probability.
Motion respects `prefers-reduced-motion`; the compact step indicator adapts to narrow screens.

The **Astral light** toggle beside TRACE switches the whole workspace between the
original dark palette and white surfaces with blue/violet accents. A static
constellation decorates the header; reading areas stay clear. Native form controls,
status colors, graph edge labels and the isolated voice component share the choice.
The setting remains in Streamlit session state through navigation, reruns and new
investigations; it does not persist after a new browser session. Palette rules live
in `ui/theme.py`; Graphviz uses `build_dot(..., theme="astral")` and voice receives
the same theme in its component data. Adding a theme does not change run contracts.


## Rendering and run responsiveness

One session-owned source worker feeds a bounded event queue. A Streamlit fragment
folds batches on the main thread every 300 ms and paints at most once per polling tick. The question
editor and section headers remain usable during a run. Starting another run is
disabled until the current worker ends; next-run edits stay separate.

Cancel stops local demo/replay work cooperatively, or invokes the backend's real
cancel endpoint when advertised. Cancelled partial results are labeled explicitly.
Unsupported backends never receive a cosmetic cancel button. No close-connection
operation is described as remote cancellation. Source errors and incomplete streams
remain visible and require explicit retry.

`tests/test_frontend_runtime.py` verifies queue bounds, nonblocking execution, cleanup
and unsupported cancellation. Flow tests exercise draft edits/navigation during a
slow run and verify a 100-event burst produces one activity paint. See
[INTEGRATION.md](../INTEGRATION.md) for lifecycle limits and the additive cancel/metrics
contract. Streamlit 1.64 or newer is required for the optional browser voice component.


## Optional voice controls

Voice setup lives in the first Evidence step, before an investigation begins.
It groups recognition consent, spoken-update preferences, voice selection and
preview. Later steps show compact operational voice controls with a Voice settings
button that returns to setup. Preferences and reviewed dictation survive navigation.
The browser may use its vendor's speech service; the UI explains this before the
user enables listening. TRACE does not send audio to its backend or call a paid
speech API. Users review/edit the transcript and explicitly apply it to the next-run
question. Navigation commands use the same evidence/run availability guards as the
section buttons; they never submit or cancel an investigation. Recorded questions
remain fixed. Unsupported browsers retain typed input.

Optional spoken announcements use fixed workflow facts for section changes, the
planner/critic milestones and terminal outcomes. Findings and patient data are not
spoken. Announcements and microphone capture remain opt-in. The component assets
live in `frontend/static/voice.*`; editable helper logic is `ui/voice.py`.


### Task-aware teams and proposal reviews

When the capability catalog advertises `task_modes`, Agent setup offers Auto,
Evidence investigation, and Idea review. Auto delegates routing to the backend;
only explicit investigation sends a specialist roster. Idea review uses the
backend's fixed research, support, challenge, planner and critic team. Connected
users can select **Start from an idea without files** on Evidence. Demo imports
the same backend catalog and resolver, omitting unrelated bundled patient data
for idea reviews. Model outputs remain simulated in Demo.

Role/skill cards use safe local SVG IDs in `ui/icons.py`; unknown IDs fall back
to a generic icon. Colors accompany written Support, Challenge and Neutral
labels. The network renders actual directed message events, including handoffs
whose recipient spawns later. Results show backend discussion turns, assumptions,
references and source provenance separately from scientific findings. A completed
idea review does not assert scientific validation.
