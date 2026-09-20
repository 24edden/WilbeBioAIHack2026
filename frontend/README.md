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

Each weak point offers **Draft a follow-up**. Its editable suggestion uses the
reported limitation and requested evidence, without claiming that evidence exists.
Drafting makes no model or upload request. Manual and suggested drafts stay
separate, survive navigation and restore with saved results. Explicit Run and
Discard controls keep submission separate from editing. Draft retention follows
the retained session results; this does not add permanent storage.

The saved-result picker uses stable session record IDs rather than list positions.
Options lead with a distinguishable ID and outcome so repeated questions remain
recognizable on narrow screens. Selecting a record previews its full question,
mode and identifiers; **Open selected result** restores its report and drafts.
Native metadata disclosures toggle locally. The picker still uses Streamlit's
selection rerun to choose the record for Open. A Live connection describes the
transport route; only saved execution metadata can report its provider mode.

Question-mark help beside controls and result panels uses `ui/help.py` with
immediate CSS hover/focus tips. Text appears on hover and hides when the pointer
leaves; keyboard focus also reveals it. Keep the copy in `ui/help_text.py` current when changing providers,
datasets or scientific interpretation.

Live activity help uses stable `help_key` values scoped by local result and view,
so quiet polls preserve a focused tooltip and its Escape-dismissed state. Live and
replay scopes are separate. New polling views should supply a unique view/control
scope; ordinary unscoped helpers retain independent IDs. The activity fragment
still paints every poll to preserve its content; this is not a render cache.

Results' **Full activity timeline** exposes every retained activity summary in
reverse arrival order. Small histories open locally; larger histories prepare one
40-entry page on demand, with Newest, Newer, Older and Oldest controls. Paging is
confined to its Streamlit fragment and scoped to the selected session result.
Entry numbers and displayed/total counts make the window explicit. Structured
tool summaries may be shortened by the event adapter; Run details > Raw events
retains their supplied payloads. The live message feed still shows at most 12
messages and now states that limit beside the retained message count.

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
The browser stores the choice in local storage and changes a root attribute without
calling Python or rerunning the page. Both palettes ship in `ui/theme.py`; Graphviz
edge text uses CSS colours and voice listens for the local theme event. The compact
switch lives in `static/theme.*`. Adding a theme does not change run contracts.


## Rendering and run responsiveness

One session-owned source worker feeds a bounded event queue. A Streamlit fragment
folds batches on the main thread every 300 ms and repaints the activity surface.
Streamlit clears fragment-owned content between polls, so skipping unchanged paints
needs a separate client-owned rendering boundary before it can be enabled safely.
During quiet periods CSS supplies a moving progress sweep. Phase labels reflect preparation, planning,
specialist work and critique; the sweep is not a completion percentage. The question
editor and section headers remain usable during a run. Starting another run is
disabled until the current worker ends; next-run edits stay separate.

Agent/model capability discovery runs in a session-owned background thread, started
while choosing evidence. A slow service cannot block question editing or navigation.
The initial Start control waits for discovery to settle; Start itself never waits on
an HTTP capability request. Known controls stay cached for that endpoint/mode until
the user selects Refresh available models and agents. Refresh failures retain the
last successful snapshot with an error message.

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

One microphone icon toggles capture, with separate connecting, listening, speaking,
finishing and error states. Its waveform uses a local Web Audio analyser; audio is
never recorded or sent by that analyser. SpeechRecognition still uses the browser's
speech service. If audio analysis is unavailable, speech events drive a fallback
animation. Silence settles the waveform; finish, failure, consent revocation and
true component unmount release the analyser tracks. Same-key UI updates preserve
the capture session. Reduced-motion preferences suppress continuous animation.

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

Replies with valid `reply_to` links offer **View earlier argument**. This native
browser disclosure shows the exact earlier turn and recorded response chain,
without a server rerun. Missing, ambiguous or invalid links show an explanation;
TRACE never guesses a connection from neighboring turns. Source text, assumptions
and references remain available in the original discussion.

Weak-point reference panels also offer **Inspect finding** for an exact, unique
finding ID. The view retains the original claim and attached source fields,
including file locations and supplied excerpts. Reported stance describes the
finding's relation to the hypothesis, not its correctness. Missing or ambiguous
references stay unresolved. Small panels open locally; large source collections
load when the outer References panel is opened, then individual finding
disclosures toggle in the browser.

During an investigation, **Time since local submission** advances in the browser
even when no events arrive. It uses a run-specific monotonic anchor, preserves it
across page updates and stops at completion. Backend-reported measured execution
time is displayed separately. The clock does not indicate provider health or
progress. Replay shows **Recording time** instead. No per-second Python callbacks,
screen-reader announcements or clock animations are used.

If a run ends while Evidence or Question setup is open, a persistent inline notice
offers an explicit action to inspect its outcome. Completion, abstention,
cancellation, errors and an interrupted stream use distinct wording. Receiving
the notice does not navigate, remount the editor or submit its draft. The action
preserves the current question, and reviewing the outcome suppresses repeat
notices. Results headings also distinguish errors and unknown terminal states.

Both follow-up editors offer a **Prior generated context** preview before Run.
It shows retained and omitted records, per-field shortening, and the exact bounded
context copied into the request. The first eight findings, first six weak points
and last four discussion turns retain their existing selection rules; counts are
not a completeness or quality score. The new question, reused files and provider
instructions are separate. Large previews prepare their contents on first open;
inner disclosures toggle locally. Saved payloads remain inspectable without
inventing original totals or truncation metadata. Recording follow-ups keep the
existing simulated idea-review behavior without the original uploaded files.
