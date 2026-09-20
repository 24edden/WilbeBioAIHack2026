> **Earlier investigation API contract.** The default app now uses the authoritative scientific engine. See [current integration](docs/FULL-STACK.md) and [startup](README.md). This document applies to `frontend/legacy_app.py`.

# Changing the datasets, backend, and interface

The current patient-failure investigation is one implementation, not a schema the
next backend must adopt. Keep the small **UI event contract** stable and translate
new backend output at the frontend adapter boundary. A dataset service, workflow
engine, or model stack can use its own internal data structures and routes.

Read this alongside [ARCHITECTURE.md](ARCHITECTURE.md), which describes the current
patient workflow, and [frontend/README.md](frontend/README.md), which describes the
frontend modules and configuration. The domain-specific types in `app/models.py`
are internal to the current backend; do not import them into the UI.

## Ownership and change boundaries

| What changes | Place to change it | What can stay unchanged |
|---|---|---|
| Data files, parsers, reference corpus | Current backend: `app/ingest.py`, `app/corpus.py`, `samples/`, `fixtures/` | UI rendering and event vocabulary |
| Models and external tools | `app/providers/base.py` protocols, implementation modules, factory in `app/providers/__init__.py`, `app/config.py` | Current orchestration, if provider inputs/outputs are retained |
| Agent plan or execution engine | `app/engine.py` and `app/agents/` | UI, if emitted activity is normalized to the UI contract |
| Entire backend, API routes, authentication, or stream protocol | Frontend backend adapter/transport | Graph, conversations, findings, and result panels |
| Field names or shapes in a new backend's events | Adapter normalization | `frontend/ui/events.py` and `frontend/ui/state.py` |
| Branding, upload formats, examples, labels, default connection | Frontend configuration | Backend and visualization components |
| Layout, panels, visual treatment | Frontend view/components/theme | Backend calls and normalization |

The provider protocols are useful if continuing the current backend. They are not
a requirement for a replacement backend. Likewise, `PatientBundle`, the fixed
backend role enum, the local corpus, and the present criticism policy can be replaced
without teaching the visualization about the replacement's internal models.

The concrete frontend seams are:

- `frontend/ui/config.py`: the `ProductProfile` controls copy, input extensions,
  sample availability, required files, role groups, review roles, and workflow stages.
- `frontend/ui/adapters.py`: `RunRequest` carries mode, question, backend address,
  fixture/speed, sample choice, uploads, run configuration and optional follow-up
  context. `InvestigationSource`
  provides `capabilities(backend)` and `events(request)`; the latter yields UI `Event`
  objects. `source_for` selects recorded playback or connected execution.
- `frontend/ui/followup.py`: wraps the selected source for follow-ups, appending
  bounded prior claims to the execution question while preserving the short user
  question in the UI. The HTTP request shape is unchanged. Replace this wrapper
  if a future backend offers structured conversation context or parent-run IDs.
- `frontend/ui/replay.py`: animates a snapshot of normalized saved events locally.
  It neither reruns providers nor mutates the completed report. Replays and prior
  results are scoped to the current Streamlit session, not durable storage.
- `frontend/ui/stream.py`: `BackendContract` defines endpoint paths, upload field,
  `start_payload(question, ids, config)`, `parse_file_ids(body)`, `parse_run_id(body)`,
  `map_event(raw)`, and `map_capabilities(raw)`. Use these hooks for a differently
  shaped HTTP/SSE backend. Implement a different source for a different protocol.
- `frontend/ui/layout.py`: reusable run-state panels. Rendering should not build
  HTTP requests or interpret replacement backend DTOs.

## Current HTTP API

These are the current default adapter's inputs, not requirements for every server.

| Operation | Current request | Current response |
|---|---|---|
| Upload | `POST /upload`, multipart field `files`, repeated per file | `{"files":[{"file_id":"file-123","filename":"observations.csv","kind":"labs","n_records":12}]}` |
| Start | `POST /investigate`, JSON `{"question":"What explains the change?","file_ids":["file-123"]}` | `{"run_id":"run-123"}` |
| Follow activity | `GET /events/run-123` | SSE, JSON in `data:` frames |
| Fetch report | `GET /report/run-123` | Current backend report object; retain it as downloadable data |
| Load bundled example | `POST /demo/sample-patient` | Same shape as upload; optional demo convenience |
| Discover implemented controls | `GET /capabilities` | Safe role catalog, server defaults, provider mode, whether model overrides are supported |

An unknown uploaded file or run returns 404. A blank question returns 400. Missing
live reasoning credentials return 503 before creating a run. Other backend failures
may be emitted as events after the run starts. Do not hide transport failures by
switching to recorded data.

The default service stores files and runs in process memory. Restarting it loses IDs.
It replays the event history to late SSE subscribers, sends keepalive comments, and
closes the stream at the end. It does **not** currently implement durable runs,
authentication, resume cursors, or interactive messages to an agent. Cancellation
is implemented through the explicit endpoint documented below.
The UI prompt starts a new investigation; it is not mid-run steering.

## Per-run agent and model controls

The current backend accepts this optional addition to the start request:

```json
{
  "question": "What explains the change?",
  "file_ids": ["file-123"],
  "config": {
    "specialists": ["genomics", "literature"],
    "reasoning_model": "your-configured-reasoning-model",
    "variant_model": "your-configured-variant-model",
    "embedding_model": "your-configured-embedding-model"
  }
}
```

Model IDs above are placeholders, not available-model recommendations. Omit all
three model fields in mock mode. They are sent to the existing configured server
endpoints in live mode; choosing an ID does not install a model or switch providers.
The API does not test model availability in advance. An unsupported ID is reported
through the ordinary provider-error path when it is invoked.

`specialists` accepts one to three unique values: `genomics`, `clinical`, `literature`.
The explicit selection determines which agents dispatch, including when the planner
does not propose a selected role. The orchestrator and critic always remain, giving
three to five agents total. Reducing the roster may cause the critic to abstain if
there is no second contributing specialist. Duplicate roles, an empty explicit
selection, unsupported roles, blank model IDs, and unknown config fields are rejected.

Omitting `config` preserves the original planner-driven roster and environment model
defaults. Omitting `specialists` within `config` also retains planner selection.
Model overrides apply to one run only, with a private settings copy: the reasoning
model is shared by planner, specialist reasoning, and critic; variant and embedding
models are used by their respective bio calls. There are no per-agent reasoning model
overrides yet. Credentials, endpoint locations, and mock/live mode remain server-side.

Example capabilities (configured IDs vary by installation):

```json
{
  "run_mode": "live",
  "specialist_roles": [
    {"id": "genomics", "label": "Genomics"},
    {"id": "clinical", "label": "Clinical"},
    {"id": "literature", "label": "Literature"}
  ],
  "required_roles": ["orchestrator", "critic"],
  "defaults": {
    "specialists": ["genomics", "clinical", "literature"],
    "reasoning_model": "configured-reasoning-model",
    "variant_model": "configured-variant-model",
    "embedding_model": "configured-embedding-model"
  },
  "model_overrides_supported": true
}
```

These are implemented controls and configured defaults, not model discovery. In mock
mode the model fields are disabled and overrides are rejected with 422: fixtures do
not change when a model name changes. Recorded playback has no adjustable execution
configuration. The chosen/effective configuration appears in `run_started.payload.config`
and the report's `config`; the final report also records the actual selected roster.
For a planner-selected run, its roster is not known at `run_started` and is initially
null. Capabilities' default specialist list is the explicit UI selection, not a
promise that an unconfigured legacy request spawns all three roles.

## Normalized UI event contract

`frontend/ui/events.py::Event` is the display boundary. `RunState.apply()` folds
these events into the view model. An adapter should yield ordered `Event` objects
with a consistent run ID, even if its upstream uses polling, WebSockets, renamed
fields, or a different workflow framework.

```json
{
  "type": "agent_message",
  "ts": 1234567890,
  "run_id": "run-123",
  "agent_id": "quality-1",
  "agent_role": "quality_control",
  "parent_id": "analysis-1",
  "payload": {"text": "Two input batches need separate normalization."}
}
```

`ts` is milliseconds, ordered within a run. IDs are opaque strings. `agent_role`
is a display label at the frontend boundary; a replacement adapter need not restrict
it to the current backend's genomics/clinical/literature roles. For a spawn event,
`parent_id` names the spawning agent; for a message, it names the recipient. Preserve
that distinction when mapping a backend's separate parent/recipient fields.

| Type | Payload consumed by the UI | Meaning |
|---|---|---|
| `run_started` | `question`, optional `files` and `run_mode` | Starts the run; use readable file labels in the normalized payload |
| `agent_spawned` | `task`, optional `rationale` | Agent identity and graph parent |
| `agent_message` | `text` | Agent communication; recipient is envelope `parent_id` |
| `tool_call` | `tool`, `args` | Activity shown in the timeline |
| `tool_result` | `tool`, `result` | Tool output summary; full output can remain in raw data |
| `finding` | `finding`, optional `confidence`, `provenance` | A surfaced result and its evidence |
| `run_complete` | `verdict`, optional `confidence`, `abstained`, `abstain_reason`, `caveats` | Terminal result; `abstained` is a real boolean |
| `error` | Human-readable `message` (current backend uses `error`) | Failure to display, not proof that the whole run is finished |

Example normalized finding:

```json
{
  "type": "finding",
  "ts": 1234567891,
  "run_id": "run-123",
  "agent_id": "quality-1",
  "agent_role": "quality_control",
  "parent_id": "coordinator-0",
  "payload": {
    "finding": "Batch B has fewer usable observations.",
    "provenance": [{"kind":"file","ref":"observations.csv","locator":"rows 12–38"}]
  }
}
```

Confidence is optional, finite, and between 0 and 1 when supplied. Do not turn a
retrieval score, likelihood, arbitrary rank, or missing value into confidence merely
to populate a gauge. Omit it if the backend does not supply a meaningful measure.
The current backend's confidence and corroboration checks are heuristics, not
calibrated probabilities or proof of independent evidence.

Keep real provenance when translating results: file and row, dataset record ID,
paper reference, or tool output ID. A source identifier existing does not itself
prove the associated claim is scientifically correct. Missing provenance must remain
missing, not be filled with a plausible-looking citation.

## Adapter responsibilities

### Results weak-points assessment

The backend and frontend share one additive object: `GET /report/{run_id}` returns
`weak_points`, and the terminal `run_complete` event contains the identical object
at `payload.weak_points`. No separate weak-points endpoint or second request is needed.
The local interactive Demo uses the same engine and therefore emits the same contract.

```json
{
  "status": "assessed",
  "items": [{
    "id": "hypothesis-conflict",
    "category": "conflicting_findings",
    "title": "Findings point in different directions",
    "rationale": "Recorded findings support and contradict the proposed cause; this does not establish a conflict between independent studies.",
    "next_evidence": "Compare the linked sources and identify evidence that distinguishes the explanations.",
    "finding_ids": ["finding-1", "finding-2"],
    "sources": [{"kind":"file","ref":"notes.txt","locator":"line 1","quote":null}]
  }]
}
```

The example illustrates the schema, not an assessment of a real patient. Categories
are `evidence_gap`, `conflicting_findings`, `source_gap`, `provider_failure`, and
`scope_limit`. Every item includes a rationale, the next evidence to inspect/obtain,
existing linked finding IDs, and deduplicated existing provenance objects. Operational
failures use `provider_failure` even when their origin is agent execution/input parsing;
the title and rationale describe them as agent/tool failures, not a model diagnosis.

The current audit is deterministic and adds no model call. It examines parsed input
coverage, contributing specialist roles, existing support/contradiction stances for a
hypothesis, cited source identifiers against the run's uploads/retrieval/tool outputs,
error events, abstention, and explicit mock/causality limitations. It never invents
conflicting studies, measures source entailment, or interprets heuristic confidence
as a calibrated probability. A resolved identifier does not prove that its source
supports the claim. A finding-role count does not establish independent evidence.

`{"status":"not_assessed","items":[]}` is the default while a report runs. Older
recordings and replacement backends that omit the field remain **not assessed** in the
UI. `{"status":"assessed","items":[]}` means this bounded audit detected no listed
weakness, not that the science was validated. Failed engine runs can still return an
assessed operational-failure item. These are evidence-review suggestions, not diagnoses
or treatment recommendations. Replacement backends may supply their own assessment
through the same object without adopting the current patient-specific audit.

### Source transport and normalization

1. Convert uploads and the question into the backend's own request format. Return
   opaque file/run identifiers to the controller; keep backend DTOs inside the adapter.
2. Convert upstream activity to the events above. Preserve unknown activity as a
   readable timeline event rather than silently dropping it. Normalize error text,
   file labels, booleans, timestamps, and optional metrics before rendering.
3. Produce one ordered event sequence for one run. If reconnecting to a service that
   replays history, de-duplicate before folding it into existing state, or rebuild
   state from the complete replay. The current state reducer is not idempotent.
4. Distinguish a complete result, a backend failure, and a broken connection. A stream
   closing without a terminal event is not a successful investigation. Never invent
   a successful `run_complete` to make the UI finish.
5. Keep mock provider execution separate from fixture playback. Connected mock mode
   analyzes the submitted inputs through real control flow with simulated model
   outputs. Recorded playback reuses a fixed question and fixed outputs.

The report is separate from the normalized event sequence. Existing visual panels
derive their result from `run_complete`, so a replacement report may retain its own
structure for download. Add a report view model only when a panel actually needs one;
do not make the whole frontend depend on the current `Report` class.

## Compatibility and teammate handoff

There is no schema version or negotiation protocol on the current wire. Additive
payload fields can pass through without a version bump. For renamed fields or a new
server API, implement a separate adapter and select it explicitly; do not scatter
conditional backend detection through panel code. If multiple incompatible APIs must
coexist later, negotiate a named version in the adapter/health handshake and reject
unsupported versions clearly. That mechanism is a future decision, not implemented
capability.

For a new backend, provide one upload response, one start response, a short successful
event capture, an abstention/no-result capture, and a failed-run capture. Write adapter
tests against those captures, then fold the normalized events through `RunState`.
Verify that files and prompts reach the backend, agent-to-agent edges resolve, source
references survive, and a terminal result or failure is visible.

Existing checks:

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe frontend/smoke_test.py
```

`tests/test_frontend_contract.py` checks the current backend's actual SSE events
against the UI reducer for a completed investigation, a rejected hypothesis, and an
empty-evidence abstention. `tests/test_grounding.py` covers source matching and upload
provenance for the current backend. Keep those current-backend tests while adding the
replacement adapter's tests; they should not constrain its internal domain model.
`tests/test_run_config.py` verifies that roster controls change dispatch and that
model overrides reach outgoing provider requests without leaking into another run.
Those provider requests are intercepted in tests; they do not validate a live vendor
deployment or spend tokens.

## Responsive execution and cancellation

`ui/runtime.py` owns one `BackgroundRun` per Streamlit session. It takes a copied
`RunRequest` and an `InvestigationSource`; its daemon worker only reads that source
and writes a bounded queue (1,024 events). It never reads Streamlit/session state or
renders UI. A main-thread fragment drains up to 256 events every 300 ms, folds them
in order and redraws the activity panel at most once per polling tick (including idle ticks
to retain Streamlit fragment output). Raw events remain
available. A new run cannot replace an active worker; different session objects and
copied requests prevent cross-run event/draft mutation.

Draft editing and stage navigation remain available while work runs. The worker
continues if the scientist views another section; completion enables Results without
forcing them away from an edited draft. Fragment timers stop after the worker and
queue are terminal. Queue backpressure bounds transport backlog, not the complete
raw event log. An independent watcher expires the worker lease after 120 seconds without a drain.
It requests real backend cancellation when supported; otherwise it detaches
observation without claiming the remote job stopped. The default SSE adapter checks
detachment even on heartbeats and times out after 120 seconds without any frame.
After consumer expiry, ordinary records may be discarded to allow cancellation
cleanup to proceed; the terminal outcome is retained separately. Unsupported remote
jobs may outlive a disconnected browser. This is not durable task storage or a
multi-process run registry.

Optional additive cancellation contract:

- `/capabilities.cancellation_supported: true` enables connected cancellation.
- `POST /runs/{run_id}/cancel` returns `{run_id, status}` only after task cleanup.
- The stream returns `run_complete.payload.status: "cancelled"`, `cancelled: true`,
  and partial findings/weak points. Repeated cancellation is idempotent.
- `BackendContract.cancel_path` and `BackendSource.cancel(request)` provide the
  replaceable transport hook. Run IDs come from the start response. Cancellation
  HTTP work uses a separate worker; it does not block the page.
- Demo/replay cancellation closes the local source on its own worker and waits for
  generator cleanup. It reports cancellation only after cleanup succeeds. Simply
  closing connected SSE never produces a fabricated cancellation result.

Terminal payloads may add `agent_statuses` (agent ID to actual status) and `metrics`.
The reducer no longer declares an agent done on its first finding. Status maps
preserve completed, failed and stopped agents; older captures retain fallback
behavior. The completed duration prefers backend measured `wall_ms` (or
`wall_time_ms`) over event timestamp spacing. Metrics appear under Run details;
no token counts or calibrated confidence values are inferred.


### Task-aware frontend contract

Optional capabilities `task_modes`, `skills`, and `review_roles` populate the
workflow selector and skill cards. Each role carries `id`, `label`, `skills`,
`alignment` and `icon`; icons are mapped to a local allowlist. Missing catalogs
retain the existing investigation-only controls. The frontend sends
`config.task_mode` only when advertised. It sends `specialists` only for explicit
investigation, preserving automatic backend routing and the fixed review team.

`run_started.config` records effective `task_mode`, `requested_task_mode` and
`routing_reason`. `agent_spawned.payload` adds `skills`, `alignment` and `icon`.
`agent_message.payload.discussion` supplies a structured turn while the existing
`agent_id` and `parent_id` remain the directed conversation contract. Recipient
spawn order does not discard messages. Terminal `discussion` replaces the turn
list with the authoritative report list. Discussion fields include `phase`,
`text`, `assumptions`, `evidence_refs`, `open_questions`, `reply_to`, `basis` and
`provenance`; the UI displays these without inferring scientific findings.
`run_complete.task_mode=idea_review` selects the design-review result wording.
Cancelled/error terminal states retain their own status regardless of task mode.
