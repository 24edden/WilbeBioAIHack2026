# Three-state frontend audit

Scope: prompt → running pets → results. The older Evidence/Question wizard, mode
selectors, model controls, voice/navigation panel and presentation replay controls
have been removed from the application. Supporting backend modules remain available
for API integrations and tests.

## Fixed

- Old buttons no longer open a different UI version. Only three state values exist,
  and legacy session names are migrated to those values.
- TRACE is a real keyboard-accessible Home button on every screen.
- Real completion immediately opens Results; no extra pet replay continues afterward.
- Home never cancels, loses or resubmits an active run. It keeps the draft and provides
  one return action. Completion respects an explicit Home navigation.
- Inputs remain editable while another run is active, but a second submission is blocked.
- Older server acknowledgements cannot overwrite newly typed browser text.
- Empty-question validation clears when the user corrects the question.
- A failed component bridge dispatch no longer leaves the composer stuck in Preparing.
- Canceled and interrupted execution get honest result states, not a scientific abstention.
- Cancel waits for source cleanup. Demo pacing can be interrupted promptly.
- The startup/native palette matches the default light interface, avoiding a dark loading flash.

## Automated coverage

The complete repository suite covers existing backend/contract behavior plus the new
three-state acceptance matrix: happy path, no duplicate dispatch, upload snapshots,
theme changes, Home during and after execution, returning to an active run, completion
while at Home, cancellation cleanup, failed/truncated/fatal sources, source startup
failure, explicit retry, prior results, follow-ups, configured-backend requests,
legacy-state migration and event bursts.

The component harness uses the actual JavaScript drop/submit/remove handlers and
checks exact file bytes, invalid types, late server acknowledgements, editing while
another run is active, clearing a new draft and recovery from a dispatch failure.
Python independently validates file names, formats, sizes and encoded contents.
Palette contrast and source-hash/role-fallback checks remain in the suite.

The timed local demo used the actual mock engine: **25.01 seconds, 52 events, 5 experts**,
ending in `run_complete`. A deterministic-clock regression verifies the same 25-second
schedule without changing event payloads, order, conclusion or source execution count.
A cancellation test covers both direct demos and follow-ups. Live sources bypass this
pacing entirely.

## Browser audit

The in-app browser exercised empty-input feedback, typing, theme switching, clickable
TRACE navigation, the single upload composer, active-run Home/return behavior,
starting a demo, automatic completion and requesting cancellation. Browser checks use
synthetic sample data only. The local preview was restarted cleanly after detecting
stale module imports from development hot-reload.

## Limits

No remote model credentials or live scientific inference were exercised. Connected
source/error/cancellation behavior is covered by deterministic adapters and existing
API tests. These are software checks, not validation of the biological conclusions.
The demo's explicit mock labels remain visible.

## Final verification result

- **185 tests passed** with the bundled Node runtime on PATH; no skipped tests.
- Frontend fixture smoke checks passed for supported and abstaining outcomes.
- The actual JavaScript component harness passed drag/drop, byte preservation,
  removal, validation, stale-acknowledgement, active-run editing and retry checks.
- Browser: attached a synthetic CSV in the single composer, preserved it through
  theme/Home actions, submitted it and received the correctly limited result for
  those inputs. Opened evidence/provenance and limitations in place.
- Browser: verified an open follow-up and its text survived a theme change; submitted
  it through the same Running screen and observed its Results screen.
- Browser: verified Home during a run, Return to investigation, and cancellation;
  the paced demo stopped promptly and displayed Canceled without a false abstention.
- Browser: 390 px mobile checks measured a 390 px document, exactly one pet while
  running, and readable result cards. The viewport was restored afterward.
- Development dependencies emit two existing Starlette/httpx deprecation warnings;
  no frontend exception remained in the final browser checks.
