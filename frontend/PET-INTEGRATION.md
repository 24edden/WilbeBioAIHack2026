> **Earlier pet integration.** The default app now uses the authoritative scientific engine. See [current integration](../docs/FULL-STACK.md) and [startup](../README.md). This document applies to `frontend/legacy_app.py`.

# Current TRACE pet integration

Base: `codex/frontend-redesign` at `0a02e984b6e52822ca4f9f30fa77755a402a87bc`.
Work branch: `codex/pet-investigation-ui`.

## One application, three states

- **Prompt:** the original rounded composer, with integrated file drop/picker and chips.
- **Running:** one pet presents the latest public agent update while the source is active.
- **Results:** the preserved scientific conclusion and progressively disclosed evidence,
  limitations, history and follow-up actions, all on the same page.

`app.py` and `ui/workspace.py` own this state machine. Legacy session state names are
migrated. No classic/wizard fallback, stage-navigation bar, source/model setup page,
voice-navigation panel or replay controls can open a second interface.

TRACE is an accessible Home button. It never cancels or submits work. A draft may
be prepared while an active run continues; duplicate submission is blocked. Completion
opens Results when watching the run, but respects deliberate Home navigation. The
source continues to be drained in the background to preserve events and its lease.

## Kept from the colleague's implementation

The normalized Event/RunState contract, real local engine, backend transport,
scientific result components, evidence/provenance and weak-point assessments are
retained. Follow-ups reuse submitted evidence and carry prior claims as untrusted
context. Reports and request snapshots remain independent of later draft edits.

## UI additions

- `ui/composer.py` and `static/composer.{html,css,js}`: dependency-free Streamlit v2
  prompt/drop component. Both browser and Python validate attachment payloads.
- `ui/pet_activity.py` and `ui/pets.py`: role casting and short public event excerpts.
  Unknown roles use the generic pet. No private reasoning is exposed or invented.
- `ui/demo_pacing.py`: mock-only 25-second event delivery. The engine runs once;
  original payloads/order/outcome are preserved. Errors bypass pacing and cancellation
  interrupts its wait. **Live sources are never artificially delayed.**
- `ui/appearance.py` / `static/workspace.css`: a shared session-local light/dark theme.
- `static/scientist-pets/`: permanently right-facing PNG/WebP/GIF assets. Never flip
  them again. Reduced-motion uses still PNGs.

The stale-prompt race in the browser component was removed: within a draft generation,
late server acknowledgements cannot replace newer typed text. New generations reset
cleanly. Follow-up drafts are kept per result and open result sections retain state
through theme changes. Connection errors no longer leave a stuck submit button.

## Preview and verification

See README.md for the single preview command and QA.md for the audit. No remote model
credentials or live scientific inference were tested. The local sample demonstration
measured 25.01 seconds, 52 events and five experts. The full suite passed 185 tests;
smoke checks and the component JavaScript harness passed as well.
