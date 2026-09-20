# Scientific frontend integration

`frontend/app.py` is the default Team TBD workspace. `ui/scientific_workspace.py`
uses `TeamTBDClient` for explicit control requests and the existing verified
`LiveSource`/`Capsule` presentation mapping. It never imports or executes the old
`app/` orchestrator. Start `scientific_backend/app` in its own environment and
working directory because both historical packages use the Python name `app`.

## Connection and lifecycle

`TEAM_TBD_BACKEND_URL` is the sole new-investigation origin. It must be an explicit
HTTP loopback IP origin, without credentials, paths, queries or fragments.
The client rejects redirects, disables environment proxy discovery, and sends a
matching Origin header for server-side writes. Keep Streamlit and the API bound
to loopback, including on Brev behind an SSH tunnel. No public deployment or
multi-user authentication layer is supplied by this integration.

The connection button reads health and registered cases; it never performs the
billable model/tool probe. A new investigation includes the untrimmed question,
source name, selected registered case, explicit `mode=live`, and a stable request
key. Existing backend defaults choose scientific methods. No model, role, budget,
raw upload or arbitrary tool override is sent. A question needs ten nonblank
characters; the composer supports up to 12,000 characters. Registered evidence is
prepared through the backend's hash-qualified source installation.

Accepted create responses open the actual run ID. Finite polling reads durable
run events/exports; browser reruns do not replay or create work. Pet activity is
based on recorded events. The nine roles are clinical scientist,
bioinformatician, statistician, clinical pharmacologist, molecular scientist,
translational scientist, assay scientist, coordinator and reviewer. Hand-offs,
acceptance evaluations, actual model/skill receipts, governance, scientific result
status and operation/provider status retain distinct source records.

The live controls provide cancellation, guarded resume, synthesis checkpoint
continuation, feedback, supported recipe follow-ups, attributed measurements,
research briefs, sequence discovery and qualified NVIDIA comparisons. Every
versioned mutation uses the displayed latest decision version and the service
revalidates it atomically; stale actions receive a conflict. Follow-ups use server
recommendation IDs and readiness, never user-invented recipes. Measurements need
current experiment/candidate IDs. Modeling needs exact distinct sequences and
an explicit target-retention attestation. No status is upgraded from queued to
completed just because a request was accepted.

Before a write, the session retains its exact payload and request key. A timeout,
5xx, redirect or malformed acknowledgement is uncertain, so the interface blocks
new submissions and offers explicit reconciliation with the same key. It never
automatically submits a duplicate. Cancellation and resume have no idempotency
key contract; their uncertain response is resolved by reading status. Browser
session loss also loses the session's pending key: inspect the durable runs before
creating a new request. Provider-side unknown submissions stay guarded by the
backend and are never silently repeated.

## Frozen replay remains read-only

`TEAM_TBD_CAPSULE` and `?run=…&mode=replay&view=…` retain the sealed capsule reader
and existing bookmarked routes. Ana and CD19 remain in the original order. Frozen
pages make no control requests; artifact bytes are hash checked. Saved NVIDIA
structure images appear automatically only for exact matching recorded CIF hashes;
this rendering performs no inference or sequence search. Switching to live
reads is explicit. `TEAM_TBD_MAIN_URL` and `TEAM_TBD_ANA_URL` route the two saved
sources; they do not override the new-investigation backend. Only the live-read
page offers a separate link into live controls, with the source identity retained.

The shared scientific detail views do not imply a new runthrough, new NVIDIA work,
additional independent cohorts, or GPT-Rosalind inference. Generic new runs do not
receive CD19-specific claims. A completed individual provider receipt may remain
visible inside a subsequently failed follow-up.

## Scope and installation

Scientific roles, skills, prompts, methods, workers, stores and policies are
packaged from the original authoritative service; integration adapters and
installation hooks do not replace them. Administrator workflows such as capability
probes, registered-data installation and procedural-memory release remain in the
original backend workbench/documented operator API. The new question flow exposes
only the contracts listed above and does not weaken their validation.

No private `.env`, database, full trace, sealed run export, raw omics input or
installed proprietary source-client runtime belongs in Git. Pins and install hooks
retain required provenance. See `scientific_backend/SETUP.md` for the exact public
source or authorized local-copy installation and optional external skill runtime.
A fresh install requires these documented inputs and credentials before scientific
execution; it never manufactures successful results when they are absent.
