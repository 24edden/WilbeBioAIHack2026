# UX and latency audit

20 September 2026. Source review of the frontend, source adapters, execution
worker, API, agent pipeline, providers, evaluation runner and deployment. File
locations refer to this checkout; function names remain useful if nearby UI
changes move the lines. The microphone and client-side theme changes are being
handled in the parallel frontend workstream.

## Main finding

Most investigation work already runs off the UI thread. The remaining avoidable
waits are around that work: a blocking capability lookup before navigation/start,
repeated rendering while nothing has changed, and preparation or repeated transfer
of evidence. These should be removed before increasing model concurrency. During
real inference waits, animate stable client-side surfaces and show observed
workflow state. Do not delay a completed result so its animation can finish.

This is a code audit, not a live provider benchmark or a 50-user load test. The
isolated change made by the audit agent is the parsing isolation described below.

## Implemented in the accompanying frontend pass

- Theme switching now uses `frontend/static/theme.*` and browser local storage. A
  switch changes CSS and voice colours without a Python event or page rerun.
  Browser verification retained the same help-element IDs and layout coordinates.
- The microphone is a single icon toggle. A browser-local analyser drives the
  waveform; speech-event animation is the fallback. Synthetic-audio browser checks
  covered speaking, silence, stopping and permission errors without accessing a
  physical microphone. Reduced-motion preferences are respected.
- Capability discovery now uses `frontend/ui/capabilities.py` off the main UI
  thread and prefetches while evidence is selected. The initial Start button waits
  for the catalog to settle, but navigation and typing remain available. Starting
  a run reads an existing snapshot; explicit refresh replaces the 15-second TTL.
- CSS animates the actual wait, with preparation/planning/specialist/critique
  labels instead of a fabricated percentage. A slow-run browser check caught
  Streamlit clearing activity between unchanged polls even with an external
  placeholder. Reliable painting on every poll is retained until a separate
  client-owned rendering boundary is implemented and verified.

The table below preserves the original audit evidence. Capability discovery and
parser isolation are implemented. The overnight UX pass also defers raw event
serialization and large provenance details. Idle graph rendering, caches,
provider pooling and audience admission still need dedicated implementation.

Pass 5 adds a browser-owned submission clock outside the polling fragment. It
advances without events or Python callbacks, freezes after worker cleanup and
separates local duration, measured backend execution and recording time. A silent
fixture, main-app Demo and saved replay were checked; the full suite passed 240
tests. The clock is not a provider-health check and does not fix graph repainting.

Passes 6 through 8 add non-disruptive terminal notices while editing, exact bounded
follow-up context inspection, and distinguishable saved-result selection. They
preserve explicit navigation/submission and client-side metadata disclosures.
Pass 8 passed 284 tests plus local browser checks. The next diagnostic is a quiet
run measuring unchanged poll/render counts and input, navigation and cancellation
responsiveness. No idle-paint optimization is claimed; skipping paint in the
current fragment remains a known content-clearing regression.

Pass 9 measured 137 additional paints over 41.109 quiet seconds with the same
seven events and five agents. Instrumented Python work was about 5.94ms per paint;
DOT construction was a small fraction. This is not browser latency. The concrete
defect was regenerated activity help IDs dropping keyboard focus and dismissing
the tooltip. Caller-scoped stable help identities fixed that behavior in a fresh
browser check, including Escape dismissal through quiet polls and a new event.
Every paint is retained. Full suite: 288 passed. Browser layout cost, audience
capacity and the earlier long-tab stall remain unmeasured or unresolved.

Pass 10 replaces the misleading last-40-only Full activity timeline with bounded,
on-demand access to every retained summary. Closed large histories prepare no
timeline rows; page actions run only within their fragment. Browser checks covered
all 98 synthetic entries and earliest planner activity in the bundled 52-entry
recording. Message previews remain capped at 12 with a visible total. Full suite:
303 passed. This is an inspection/completeness fix, not measured latency savings.

## Prioritized findings

| Priority | Evidence and user impact | Bounded change and acceptance check |
|---|---|---|
| P0, frontend workstream | `frontend/app.py:76`, `backend_capabilities`, and `frontend/ui/stream.py:111`, `fetch_capabilities`: a synchronous HTTP request has a five-second timeout and a 15-second cache lifetime. It is called on the main page thread in Question setup and again in `start`, before the background worker exists. A cache miss can therefore make navigation or Start wait. The lookup suppresses the usual spinner. | Keep a session-owned capability snapshot, refresh in a background worker, and never synchronously refresh inside Start. Show cached controls with a refreshing indication; scope the snapshot to endpoint and mode so an old server's catalog cannot leak into a new connection. Test a deliberately stalled capability endpoint: navigation, question editing and Start feedback should remain responsive. Do not advertise cancellation until the correct backend confirms support. |
| P0, fixed here | `app/main.py:113`, `upload`; `:142`, `load_sample_patient`; `:163`, `investigate`: all three async handlers called synchronous `build_bundle` on the API event loop. Larger input could block other users' health, events and cancellation requests. Sample file reads were synchronous too. | Parsing now uses FastAPI's existing worker pool; sample reads do too. Store mutations remain on the event loop. `tests/test_api_responsiveness.py` holds the parser open and checks that `/health` responds before parsing finishes, for all three routes. This improves concurrent responsiveness; it does not make parsing itself faster or make the submitting request return before parsing completes. |
| P1 | `frontend/app.py`, `poll_investigation`, and `frontend/ui/layout.py:84`, `paint_live`: the graph, cards and message panel are rebuilt every 300 ms even on an empty event batch. At 50 simultaneously active UI sessions this permits about 167 activity renders per second before considering user interaction. That is arithmetic from the schedule, not measured CPU utilization. `frontend/ui/replay.py:31` also advances saved playback through a server fragment although the recording already exists locally to the UI session. | Move playback timing and visual interpolation into a browser component. Retain a persistent activity surface updated by event revision, with idle heartbeat/status handled separately. Merely skipping `paint_live` inside the current fragment can erase the panel, so this needs a rendering-boundary change rather than an early return. Verify no graph rebuilds during a five-second quiet period, retained content and expansion/scroll state, and unchanged ordered event reduction. |
| P1 | `frontend/ui/layout.py:141`, `render_results`, renders every tab; line 180 eagerly serializes the full raw event list inside a collapsed expander. `frontend/ui/components.py:190`, `render_findings`, emits all findings and source details. A long report costs time and payload size even if the user only reads the conclusion. | Keep small tab switches client-side, but lazily create heavy raw-event/provenance views and paginate large findings lists. The installed Streamlit layout implementation supports opt-in stateful tabs/expanders; use that only where deferred work outweighs an extra round trip, or use a client-owned panel. Check an expanded synthetic report for initial payload/render cost and ensure full evidence remains accessible. |
| P1 | `frontend/ui/adapters.py:178`, `BackendSource.events`, loads sample files or uploads all bytes on every run. `frontend/ui/followup.py:41`, `FollowUpSource.events`, delegates unchanged evidence to that same path. The API parses for upload counts and parses again at investigation start. Every follow-up therefore retransfers unchanged files, creates additional stored copies and repeats parsing. | Reuse backend file IDs for unchanged evidence within the same user session and endpoint. Invalidate on evidence changes or an unknown-ID response after server restart. Keep a content/parser-version keyed parsed representation if profiling warrants it. Test follow-up with unchanged input: one upload, two explicitly requested investigations; changed input or restarted backend must invalidate reuse. Never cache generated conclusions as if they were new analysis. |
| P1 | `app/providers/reasoning_http.py:107`, `_request`, and `app/providers/live.py:193`, `_post`, create and close an HTTP client per call. Concurrent variants repeat connection setup rather than using a pool. | Give providers an explicit run-scoped async client lifecycle, close it on normal completion/error/cancellation, and retain endpoint/model isolation. Validate connection reuse against a local instrumented server before claiming latency savings. Do not introduce a process-global async client across the local demo's separate event loops. |
| P1 | `app/agents/literature.py:29` waits for a genomics finding for up to 12 seconds before embedding query plus the entire immutable corpus. `app/agents/genomics.py:53` waits for all score calls and a reasoning step before publishing findings. Thus useful peer-grounded retrieval sits behind a genuine serial dependency, while corpus embeddings are needlessly repeated across runs. | Cache reference embeddings by exact corpus content, endpoint/model/version and input semantics once the actual embedding provider contract is confirmed. Preparing reference vectors may run while awaiting peer findings. Preserve the peer-informed query; deleting the wait changes the scientific workflow. Test cached and uncached retrieval equivalence and cache invalidation. Do not cache patient/query embeddings across users. |
| P1 for audience hosting | `app/execution.py:8` bounds variant calls per investigation, but `app/main.py:208` admits each new investigation without a service-wide budget. Fifty active investigations could request up to 400 concurrent variant calls, plus reasoning and retrieval. `app/events.py:115` and `app/main.py:269` also use unbounded subscriber queues; stores in `app/store.py` have no retention policy. | Before opening interactive inference to an audience, add global provider admission limits and an explicit queued state, bound subscriber backlog with a clear reconnect policy, and expire old uploads/runs. Keep the already proposed static results explorer for audience viewing. Do not assume that adding Uvicorn workers fixes this: the current stores are process-local. Load-test queued, cancelled and disconnected sessions separately from read-only viewers. |
| P2 | `frontend/ui/state.py:230`, `elapsed_ms`, computes max/min over all events and only advances when an event arrives. A 30-second provider wait looks like a frozen timer even though work continues. Agent statuses primarily settle at the terminal event, so a generic count of “working” agents can lag actual completion. | Use a client-side monotonic display clock during live execution, anchored to the submitted run, then replace it with measured backend duration at completion. Distinguish queued/waiting/working only when supported by lifecycle events. Keep recording time explicitly separate from elapsed wall time. Verify that the clock advances through an event-free interval without requiring a server rerun. |
| P2 | `frontend/ui/adapters.py:52`, `DemoSource`, defaults to simulated latency; `app/providers/mock.py:34` intentionally sleeps so the audience can read the graph. This is useful presentation pacing but is avoidable waiting during ordinary use now that saved activity has replay controls. | Consider a fast interactive demo by default, with deliberate pacing confined to Replay or an explicit presentation mode. Keep simulated-output labeling. Confirm that completing the mock run immediately produces the same findings, and that users can subsequently inspect the sequence at a readable pace. |
| P2 | `frontend/app.py`, `poll_investigation`, performs a full rerun at planner/critic milestones even when spoken updates are disabled. Native controls also rerun the script for draft edits; saved playback's Pause/Step/Restart use full reruns. `frontend/ui/voice.py:59` reads component assets at registration time on full renders. | Gate speech-related work on actual need or feed milestones through the existing component update path. Keep playback controls browser-owned. Cache immutable asset text if measurement shows material cost, while preserving component registration on each Streamlit run and invalidating during development. Avoid a broad rewrite merely to save a tiny file read. |

## Make real waits feel active

These effects should be generated by the browser, with stable element dimensions,
and should stop or simplify for reduced-motion preferences.

| Moment | Immediate feedback | What must stay factual |
|---|---|---|
| Start clicked | Disable repeat submission; give the existing button a short press transition and reveal the activity surface immediately. | A run is submitted only once. An animation is not evidence that the backend accepted it. |
| Upload/prepare/connect | A local progress sweep or moving dots beside the actual preparation phase, followed by a stable network skeleton. | Say “Preparing evidence” until the adapter has a run ID. Show a byte percentage only if transfer bytes are measured. |
| Planner inference | A gentle breathing outline on the planner node and a live elapsed clock. | “Planning the investigation” is a workflow state, not a generated thought or confidence measure. |
| Tool/model request in flight | Highlight the relevant node or known edge; show the tool name and a compact running indicator. | Animate a message travelling only when a real message event arrives. Do not invent agents communicating during a quiet provider call. |
| Waiting for another agent | A softer waiting state and the dependency, when the backend reports it. | Keep waiting distinct from processing. Do not imply that all agents are actively computing. |
| Long silence | Keep navigation and cancellation available, display time since the last event, and explain that the request is still waiting. | No fake percentages, simulated findings, “almost done” claim or countdown without a defensible estimate. |
| Result ready | Short reveal of the completed result with source links and weak points, without moving existing controls. | Show the result immediately; never hold it for animation pacing. |

The existing `.loading-status` pulse, agent working dots and reduced-motion CSS
are a sound starting point. The current loading message only distinguishes
preparation from investigation; planner/specialist/critic phases provide more
useful reassurance than adding more arbitrary motion. Skeletons should reserve
the final layout so the page does not jump when real content arrives.

## Existing improvements to preserve

- `frontend/ui/runtime.py` already isolates sources in a session-owned worker,
  bounds the queue at 1,024 events, drains batches, and performs cancellation work
  away from Streamlit. The investigation is not waiting for every graph paint.
- `app/agents/base.py`, `Blackboard.wait_for`, returns immediately for an unspawned
  role and wakes when a role finishes without findings. Do not report a universal
  12-second peer delay; it is a maximum for a particular outstanding dependency.
- Variant workers are bounded and exact repeated biological inputs are coalesced
  within a run without losing source provenance. Preserve the measured distinction
  between fewer calls and faster completion.
- Weak-point analysis is derived once at termination and travels in the terminal
  event. It does not need an additional model or report request.
- Follow-up context is bounded and marked as generated prior claims. Replay calls
  no models. Tooltips and voice interactions already have local browser behavior;
  theme and microphone improvements are being completed separately.
- The evaluation runner bounds parallel trials and distinguishes queue time from
  execution time. It is an offline measurement path, not a UI loading mechanism.

## Verification of the shipped audit fix

```powershell
.venv/Scripts/python.exe -m pytest tests/test_api_responsiveness.py tests/test_api.py tests/test_ingest.py tests/test_execution.py -q -p no:cacheprovider --basetemp .deploy/api-responsiveness-tests
```

Result: **25 passed**. Three new tests hold parsing open and confirm another API
request completes before release. Existing checks retain upload record counts,
source parsing, end-to-end reports, cancellation behavior and bounded execution.
Two existing dependency deprecation warnings remain. No vendor calls, deployment
or production concurrency claim is part of this check.

For follow-up measurement, record click-to-feedback, click-to-first-event,
event-to-visible-update, idle render count and initial report payload size. Track
provider wall time separately. Browser-owned cosmetic changes should still work
while the backend is stalled, and a heavy upload should not prevent another
session from cancelling its run.
