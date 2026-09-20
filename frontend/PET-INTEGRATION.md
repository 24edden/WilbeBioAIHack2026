# Pet frontend integration

Base: `codex/frontend-redesign` at `0a02e984b6e52822ca4f9f30fa77755a402a87bc`.
Work branch: `codex/pet-investigation-ui`.

## Kept from TRACE

The backend, normalized Event/RunState contract, all existing data sources,
background execution, cancellation, reports, evidence/provenance, weak points,
follow-ups and result renderer are unchanged. `ui/layout.py`, `ui/components.py`,
`ui/state.py` and `ui/events.py` have no changes in this integration.

## Added

- `static/composer.{html,css,js}` + `ui/composer.py`: the original single prompt/drop
  surface hosted as a Streamlit v2 component. File chips, picker and full-surface
  drop are one component. Typed input and file bytes are validated and turned into
  the existing immutable RunRequest. Action IDs prevent duplicate submission.
- `ui/pet_start.py`: bridges composer actions to the existing source/mode settings.
- `ui/pet_activity.py`: a separately paced, single-expert presentation of actual
  normalized public events. It never changes the report, simulates provider calls,
  or invents scientific findings. Excerpts use at most two original sentences,
  with truncation marked and full text preserved in the activity/results views.
- `ui/pets.py`, `static/pets.css`: the one-pet/one-bubble stage, with local animations
  and reduced-motion stills. Role names come from the run; unknown roles use the
  generic pet. Character casting is visual and does not alter expertise.
- `static/scientist-pets/`: all nine permanently right-facing pets, copied from the
  user's verified pack. Original animation timing and transparency are preserved.

## Important distinctions

Demo runs the existing local engine with mock providers and no separate backend
server. Mock plays recorded events. Live retains the existing HTTP/SSE adapter;
no new remote service was configured or verified. Pause/Next expert affect the
presentation only. Source completion is labeled honestly, and Open results skips
remaining presentation without rerunning or changing the result.

The upload component transfers draft bytes to this Streamlit frontend session;
files reach the investigation source only on explicit Start. Browser events are
untrusted: extension, basename, byte size, decoded size, total size and base64 are
checked server-side. Run requests keep independent snapshots of the draft.

## Verification

Baseline: 175 tests passed, 1 skipped, and frontend smoke checks passed.
The integration adds coverage for preserved upload bytes and result evidence,
explicit quick-demo routing, classic setup access, queued event order, pause/step,
unknown-role fallback, HTML escaping and component attachment validation.
The JavaScript harness exercises the actual component drop/submit/remove handlers.

Local browser review covered the prompt, file chips, real local-demo submission,
pet presentation and original Results. No public deployment is part of this work.
