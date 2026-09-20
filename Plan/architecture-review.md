# Architecture and performance review

19 September 2026. Based on the checked-out implementation. This review separates
observed bottlenecks from proposed improvements. The bounded P0/P1 changes below
are now implemented, with measured results recorded at the end. P2 items remain
follow-up work. Task-aware teams and bounded idea review are documented in the
current [architecture](../ARCHITECTURE.md).

## Main finding

The major interaction problem is the synchronous event-consumption loop in
`frontend/app.py`. It consumes each event and rebuilds the live panels before
asking for the next one. `DemoSource` also advances its asyncio runner from this
generator, so rendering pauses the demo engine itself. A connected backend runs
independently, but its UI still waits inside SSE iteration and repaints every event.
This makes controls difficult to use during an investigation and couples visible
speed to rendering work.

The backend already runs specialists concurrently. Genomics also schedules all
variant scores concurrently with an unbounded `gather`, which risks excessive
tasks/requests as datasets grow. Every live provider request opens a new HTTP
client. Literature re-embeds the immutable corpus alongside each query and may
wait up to 12 seconds for the first genomics finding, which is emitted only after
all scores and interpretation are ready. These are distinct bottlenecks and must
not be presented as one measured speedup.

## Agreed priorities

| Priority | Change | Measurable result | Owner |
|---|---|---|---|
| P0 | Session-owned background source worker; main-thread fragment drains bounded event batches and renders once per batch | Event producer advances without waiting for UI paint; question/navigation respond while an investigation runs; render count drops under bursts | Frontend |
| P0 | Real acknowledged cancellation, including local Demo | Cancelling stops pending work, preserves partial findings and produces one terminal state; no orphan run labelled running | Backend + frontend |
| P1 | Bounded variant worker pool and per-run duplicate-score coalescing | Peak provider concurrency stays within configured bound; equivalent repeated variants require fewer provider calls; each source remains traceable | Backend |
| P1 | Add run timing/work counters to terminal event and report | Report first useful output and total run time, count scored/unique variants and emitted tool calls without guessing model latency or token use | Backend; root benchmarks |
| P2 | Reuse a run-scoped HTTP client with explicit close | Fewer connection setups after meaningful local/provider measurement; cancellation closes resources | Follow-up unless time remains |
| P2 | Versioned reference-corpus embedding cache | Cache keyed by exact corpus content, provider endpoint, model and embedding semantics; no cross-patient result cache | Follow-up after live embedding semantics verified |

Do not remove peer coordination or the critic to create a faster-looking graph.
Do not change the scientific input, silently skip variants, fabricate progress
percentages, or compare a smaller task as if it were an equivalent speedup.

## Shared lifecycle contract agreed for implementation

Retain HTTP start + existing SSE. A new polling endpoint is unnecessary for the
chosen background worker design. Keep existing event types so recorded fixtures
and backend replacements continue to work.

- Add `POST /runs/{run_id}/cancel`, returning `{run_id, status}`. Return 404 for an
  unknown run. Repeating cancellation on a terminal run returns its current state.
- Advertise `cancellation_supported` in capabilities only when implemented.
- Add `cancelled` as a report status and terminal `run_complete.payload.status`.
  A cancellation event also carries `cancelled: true`, `abstained: true`, a clear
  cancellation message and partial evidence/weak-points context. Cancellation is
  an operational state, not a conclusion that scientific evidence was weak.
- The cancel response must acknowledge stopped work, not merely request a cancel.
  Cancel and await child tasks. Handle cancellation before the engine coroutine
  has begun. Emit exactly one terminal event, then close its bus.
- Never interpret closing a connected SSE stream as cancelling the backend run.
  The frontend must invoke the endpoint or explain that cancellation is unavailable.
- Timing/counter payloads are additive. State the clock and meaning of each field.
  A count of emitted `tool_call` events is not a count of all provider requests:
  not every reasoning call emits a corresponding tool event in the current engine.

The shipped terminal payload/report adds `metrics` and `agent_statuses`. Metrics
are `wall_ms`, `planning_ms`, `specialists_ms`, `synthesis_ms`, `variant_requests`,
`variant_unique_requests`, `variant_cache_hits`, `variant_peak_concurrency`.
Durations use `perf_counter`; concurrent specialist phase time is not a sum of
agent times. Variant counters are not token usage or all provider requests.

## Frontend lifecycle details

Keep an immutable submitted `RunRequest` separate from the editable question and
agent draft. A session run handle owns its worker, queue, cancellation route and
generation ID. Starting a second investigation must explicitly stop/supersede the
first handle and fence off stale events; a widget rerun must not resubmit it.

The worker must not call Streamlit APIs or read/write Session State. Only the
fragment drains events into `RunState`. Render the graph/messages at most once per
batch, keeping the full event record for inspection. Stop automatic polling on
terminal state. If users navigate away, maintain enough polling/draining or an
explicit background run policy so a full queue cannot strand the worker.

Streamlit documents `st.fragment(run_every=...)` for periodically updating part of
a page and warns that writing into external containers can accumulate elements.
Keep the live elements inside the fragment or use an explicit empty placeholder.
[Fragment documentation](https://docs.streamlit.io/develop/concepts/architecture/fragments).
Custom worker threads should avoid Streamlit commands, consistent with the
[threading guidance](https://docs.streamlit.io/develop/concepts/design/multithreading).

Keep the phase model small: idle, running, cancelling, complete, cancelled, error.
In particular, transport failure is not successful completion, and cancellation
must not mark every unfinished agent successful. Current frontend code marks an
agent done on its first finding; lifecycle status should ultimately come from an
explicit agent-completion signal, not inferred output activity.

## Backend and data independence

Preserve `ReasoningProvider`/`BioProvider` protocols as the model seam, and
`BackendContract`/`InvestigationSource` as the replaceable backend seam. The dataset
teammate should replace parsers and normalized scientific input, not the UI graph.
Keep credentials, endpoints and worker limits in server configuration; expose
only supported controls and safe effective settings.

Deduplication must use every biological/model input that affects a score. Keep
source file/line attached to each original observation even when its computation
is shared. Do not merge conflicting annotations, genome builds or zygosity merely
because labels match. Run-scoped reuse avoids stale data or privacy boundaries
from a speculative global cache.

HTTPX recommends reusing `AsyncClient` rather than repeatedly instantiating one
in a hot loop to benefit from connection pooling. A future client lifecycle must
close cleanly at run completion/cancellation and not cross incompatible asyncio
loops in local Demo/test execution. [HTTPX async guide](https://www.python-httpx.org/async/).

For scientific power, build on the new weak-points assessment, stable finding IDs,
provenance inspection and evaluation suite. The visual artifact proposal in
[visual-storytelling.md](visual-storytelling.md) remains a separate future seam.
Do not bundle a React rewrite, vector database, multi-host queue, agent toolkit
migration or automatic causal discovery into this performance pass.

## Verification and deployment criteria

1. Measure the same input/provider configuration before and after: time to first
   event, first finding and terminal event; events processed; render batches;
   peak variant concurrency; duplicate provider calls; cancellation latency.
2. Synthetic delayed providers test concurrency and lifecycle without paid API
   calls. Label these software measurements, not Rosalind/BioNeMo benchmarks.
3. Test burst delivery, idle waiting, reruns, navigation, queue pressure, two
   consecutive runs and terminal/error races. Preserve source provenance and
   grounding/abstention regressions.
4. Cancel during planning, scoring, peer waiting, synthesis and immediately after
   submission. Ensure a partial report is inspectable and no tasks continue filing
   findings after terminalization.
5. Root runs the full integration suite and the hosted browser smoke check before
   redeployment. One API worker remains necessary while stores are process-local.

The Brev CPU service can demonstrate these changes without GPU allocation. It
still uses in-memory uploads/runs and lacks durable jobs and per-user data
ownership. Those are post-demo service requirements, not fixed by faster widgets.
Rosalind needs approved credentials for live generation; BioNeMo mappings remain
unverified, and NVIDIA Agent Toolkit is not implemented. Architecture diagrams
must reflect this rather than claim the earlier plan has already shipped.

## Measured result

[Raw comparison and all trials](performance-check.json) use
[scripts/profile_workflow.py](../scripts/profile_workflow.py) on Windows 11 /
Python 3.12, three trials per case, mock providers and no live API calls.

| Workload | Before median | After median | Score calls | Peak simultaneous calls |
|---|---:|---:|---:|---:|
| Sample, simulated waits disabled | 2.35 ms | 3.60 ms | 5 to 5 | 1 to 1 |
| Sample, simulated latency scale 0.2 | 2.074 s | 2.058 s | 5 to 5 | 5 to 5 |
| Twelve repeated VCF uploads, 60 rows | 0.558 s | 0.567 s | 60 to 5 | 60 to 5 |

Matched trial hashes confirm unchanged findings and verdicts for all three cases.
The demonstrated improvement is duplicate-call/resource reduction; small-case
wall time is effectively unchanged. The default worker limit is eight, retaining
parallel execution of the sample's five variants. These are software measurements,
not evidence of faster live scientific inference. UI responsiveness and cancellation
also require browser interaction checks.

## Optional voice boundary

Voice uses Streamlit 1.64 [components v2](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component).
The helper emits reviewed question text or an allowlisted navigation intent. The
app applies normal draft and stage-availability checks; voice never submits runs.

Recognition needs disclosure, opt-in and a microphone button. Browser
[speech recognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
can use its vendor's service and is not supported everywhere. TRACE receives only
applied text and has no audio-upload endpoint. Fixed stage announcements select
voices marked [`localService`](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService)
by default, with on-screen fallback when none exists. A picker favors local voices
whose reported names indicate enhanced/natural quality and offers explicit preview.
Online voices require a separate disclosure/opt-in and explicit selection. No
research question or medical finding is generated/narrated. Names are a selection
heuristic, not a guarantee of voice quality or vendor-service availability.
Mock browser-API tests verify consent, explicit action, cleanup and rerender behavior;
they do not establish real microphone quality or vendor-service availability.
