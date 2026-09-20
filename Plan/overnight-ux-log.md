# Overnight UX iteration log

## 20 September 2026: supporting records on demand

Problem: opening a completed result serialized and sent its entire raw event log,
even though the Raw events panel was collapsed. Large provenance bundles also
generated hidden content before the scientist requested it.

Implemented one bounded change:

- Raw events are prepared only when their panel opens. The complete record remains
  available; no event or field is dropped.
- Findings and weak points with more than 12 combined source/reference records
  prepare those supporting records on demand. Findings, rationales and suggested
  next evidence remain visible immediately.
- Small reference panels and result tabs keep their existing browser-local
  switching. They do not gain a server round trip.
- Deferred panels use a Streamlit fragment, so opening or closing a large detail
  reruns that panel rather than the whole workflow. Opening details makes no model
  or provider request. Keys include the run ID to keep separate runs independent.

Implementation: `frontend/ui/details.py` is the reusable disclosure boundary;
`components.py` and `layout.py` pass render functions without preparing their data
in advance. No endpoint, result schema, app navigation or theme change was needed.
This uses the installed Streamlit 1.64 API already required by the frontend.

Validation: **28 tests passed** across `test_frontend_details.py`,
`test_frontend_weak_points.py` and `test_frontend_flow.py`. A synthetic 1,000-event
report verifies that its closed panel does not iterate or serialize the event
list, opening retains every record, and closing stops preparation. Additional
checks cover independent provenance panels, instant small provenance, visible
weak-point rationale and retained source records. Existing complete workflow,
follow-up and navigation checks pass. Browser validation is coordinated with root;
no provider latency or 50-user performance claim is implied by these tests.

Command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_frontend_details.py tests/test_frontend_weak_points.py tests/test_frontend_flow.py -q -p no:cacheprovider --basetemp .deploy/overnight-ux-tests
```

Next candidates from the research agent: turn a weak point's suggested evidence
into an editable follow-up draft, and link actual challenge/revision messages by
their existing `reply_to` IDs. Both should preserve the completed report and
require a separate user action to submit new work. Larger findings lists still
render eagerly; measured pagination is a separate pass rather than part of this
change.

## Parent integration and overnight handoff

- Combined suite: 186 tests passed, with two existing dependency deprecation
  warnings. Separate help and theme lifecycle Node checks also passed.
- Browser verification: opening Raw events added the JSON panel while every
  existing tooltip ID stayed unchanged, confirming no surrounding page rerender.
- Slow mock execution exposed a failed idle-render optimization: Streamlit removed
  the graph between polls even when its placeholder was declared outside the
  fragment. The skip was removed; regular painting remains. Planner and specialist
  graphs were visible after the correction. The longer final check then stalled
  in the in-app browser, so a complete sustained-run visual check remains pending.
- The API is back on port 8001 in mock mode with latency scale 0.2. The UI remains
  on port 8502. The temporary microphone fixture server on 8503 has been stopped.
- Next pass: weak-point follow-up drafting, then a separately verified browser-owned
  activity surface. Do not reintroduce a conditional paint in the existing fragment.
- A thread heartbeat schedules half-hourly passes through 09:00 Europe/London on
  20 September 2026. Coordinate active workers before editing; finish with validation
  and a morning summary, then pause the automation.

## Pass 2: weak point to a reviewable follow-up

Every weak point can now prepare an editable follow-up beside the selected
limitation. The suggestion uses the actual original question, title, rationale
and requested next evidence. Its wording keeps that evidence unresolved and asks
what the supplied data can establish. A visible caption explains that drafting
does not add the requested evidence.

The scientist can edit, discard or explicitly run the suggestion. Each weak point
has its own draft, separate from the freeform follow-up input. Preparing another
suggestion never overwrites those drafts. Drafting, editing and discarding make no
provider/upload request, change no completed result, and do not start or cancel a
job. An explicit Run uses the existing bounded follow-up context and settings.
Recorded cases retain their separate simulated idea-review behavior, with no
original files or unrelated sample sent for reanalysis.

The existing freeform input previously lived in a form. Unsubmitted typing could
be lost when a separate weak-point button reran the page. It now persists outside
the form, with its own explicit Run button. Drafts are stored separately from
widget state, keyed to the result's session identity; they survive navigation and
returning to saved results. Their lifetime follows the bounded retained-result
history. The global research-question draft is unchanged by suggestion creation.

Validation: **36 tests passed** across frontend flow, follow-up, weak-points and
lazy-details tests. New interaction checks cover unsent typing and a separate
button in the same interaction, navigation persistence, independently edited
suggestions, discard, empty input, exactly one explicit submission, immutable
previous reports, saved-result draft restoration and recording semantics. Root
coordinates the live browser check; it is not claimed by these tests.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_frontend_flow.py tests/test_frontend_followup.py tests/test_frontend_weak_points.py tests/test_frontend_details.py -q -p no:cacheprovider --basetemp .deploy/overnight-followup-tests
```

Files: `frontend/app.py`, `frontend/ui/components.py`, `frontend/ui/layout.py`,
`frontend/ui/followup.py`, and their frontend flow/follow-up tests. No endpoint,
schema, theme, deployment or service changes were required.

### Pass 2 parent verification

- Full suite: **192 passed**, with the two existing dependency deprecation
  warnings. The help dismissal Node check now runs in the regular pytest suite.
- Browser: completed a fresh Demo run, replayed its 52 recorded events, paused,
  stepped once and resumed to completion with the final graph retained.
- Browser: typed a manual follow-up, opened the causal-limit weak point, prepared
  a separate suggestion, edited it and explicitly submitted it. A new Demo report
  appeared. Reopening the original saved result restored both the original manual
  draft and the edited weak-point question. No live provider was called.
- Longer quiet-provider runs and audience concurrency remain separate checks;
  this successful short Demo/replay does not settle the earlier tab-stall cause.
- Next small feature: resolve a discussion `reply_to` identifier into the actual
  prior argument. Research notes explain why this currently needs less schema work
  than finding-ID navigation. Keep causal interpretation separate from debate.

## Pass 3: inspect the argument being answered

Structured discussion turns now offer a native disclosure for the exact earlier
argument named by `reply_to`. Its summary identifies the original turn number,
agent and phase. Opening it shows the full prior text, source ID and assigned
perspective, plus the actual recorded chain in its original order. The panel does
not generate a summary, diff or claim that a revision improved scientific quality.
All original turns, assumptions, open questions, provenance and raw reply IDs
remain accessible in the full discussion.

`frontend/ui/discussion.py` resolves exact, unique string IDs. It never substitutes
an adjacent or similarly named message. Missing references, duplicate IDs,
self-links, cycles, later-turn references and legacy/unusable identifiers produce
plain explanations with no fabricated connection. A malformed ancestor prevents
the chain being presented as valid. Source text is escaped, and the prior text
preserves its line breaks. The design worker added shared theme-variable styles,
wrapping for long IDs/text, native focus behavior and a 44px disclosure target.

The disclosure uses browser-native `details`/`summary`. Opening it invokes no
endpoint or model and does not rerun the Streamlit page. Only the directly linked
argument's full text is repeated; the rest of the chain stays compact.

Validation: **51 tests passed**, with the two existing dependency deprecation
warnings, across discussion, actual simulated idea-review, lazy-details and full
frontend-flow checks. Coverage includes exact IDs, unrelated intervening turns,
case/whitespace mismatches, duplicates, self-links, cycles, missing ancestors,
later references, legacy/malformed IDs, escaped source text, record ordering and
retained assumptions/provenance. A current Demo review resolves its genuine
inventory → opening → challenge → revision chain.

Root's initial browser check also passed: a new simulated idea review displayed
the revision's exact challenge text, the recorded chain and unchanged help IDs on
opening. Keyboard, theme and narrow-layout checks are being completed separately.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_frontend_discussion.py tests/test_idea_review.py tests/test_frontend_details.py tests/test_frontend_flow.py -q -p no:cacheprovider --basetemp .deploy/overnight-discussion-tests
```

Files in this workstream: `frontend/ui/components.py`, new
`frontend/ui/discussion.py`, `tests/test_frontend_discussion.py` and this log.
The parallel design worker owns the matching CSS in `frontend/ui/theme.py`.

### Pass 3 parent verification

- Full suite: **210 passed**, with the two existing dependency deprecation
  warnings. `git diff --check` passed, apart from informational CRLF notices.
- A fresh local Demo idea review showed the exact challenge text linked by the
  revision. Opening the disclosure preserved surrounding help node IDs, with no
  page rerender. Demo outputs remain simulated.
- Enter closed the focused disclosure; Space opened it. Focus stayed on its
  summary. At 390px viewport width every disclosure wrapped within its bounds.
- Switching to Astral with the disclosure open preserved every disclosure's
  measured width, height and open state. The viewport override was reset.
- No deployment or live provider calls. Long quiet-provider waits and audience
  concurrency remain separate unresolved checks.
- Next experiment: retain exact finding IDs and existing stance metadata through
  frontend normalization, then inspect the source claim from a weak point. Treat
  stance as an assigned perspective, never as proof of correctness.

## Pass 4: weak point to the exact referenced finding

Finding events now preserve the backend's exact `finding_id` and its allowlisted
`supports` / `contradicts` / `neutral` stance. Missing or unsupported stance remains
unknown. New fields follow the existing dataclass fields, preserving positional
constructor compatibility, and reference lookup tolerates older in-session finding
objects without IDs. Attached provenance is copied into the normalized finding so
later mutation of input dictionaries cannot rewrite its source records.

Within a weak point's References panel, a native disclosure now resolves each
unique exact ID to its original claim, producer, reported relation to the
hypothesis and attached source records. Canonical `kind`, `ref`, `locator` and
`quote` fields are labeled, and all legacy/unknown fields remain visible. Quotes
are explicitly source excerpts supplied with the finding; no retrieval or
verification is implied. Stance is separate from the review agents' assigned
support/challenge perspectives and does not assert that a claim is correct.

Missing, ambiguous, malformed and legacy IDs are explained without substituting
nearby or similarly named claims. Raw reference IDs and weak-point source records
remain available. Claim text and every source field are escaped. Empty provenance
is disclosed explicitly.

Small reference panels remain browser-local. Large reference sets or large/deep
attached provenance keep the existing lazy outer panel; a bounded metadata check
decides this without serializing the content. Opening the inner finding disclosure
is browser-native. No endpoint, model, app navigation or draft behavior changed.

Validation: **54 tests passed**, with the two existing dependency deprecation
warnings, across finding references, weak points, lazy details, contract, replay
and frontend flow. Checks cover normalization, invalid/unknown stance, exact and
duplicate matches, old finding objects, escaping, retained canonical/legacy source
fields, empty sources and deferred large provenance. A real local Demo produced
finding IDs that matched its weak-point references exactly.

Root browser verification passed on a fresh clinical-only Demo: the linked CEA
claim and all three supplied file/line/quote records appeared. Enter/Space toggled
the native disclosure with focus retained and unchanged surrounding tooltip IDs.
At 390px width panels stayed within the viewport and retained 44px summary targets.
Astral/dark switching preserved numeric dimensions and open state. Viewport reset.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_frontend_finding_refs.py tests/test_frontend_weak_points.py tests/test_frontend_details.py tests/test_frontend_contract.py tests/test_frontend_replay.py tests/test_frontend_flow.py -q -p no:cacheprovider --basetemp .deploy/overnight-finding-tests-final
```

Files: `frontend/ui/events.py`, `frontend/ui/state.py`,
`frontend/ui/components.py`, new `frontend/ui/finding_refs.py`,
`tests/test_frontend_finding_refs.py` and this log. Existing discussion disclosure
styles were reused, so no CSS changes were needed in this pass.

### Pass 4 integration result and next experiment

- Full suite: **227 passed**, with the two existing dependency deprecation
  warnings. `git diff --check` passed with informational CRLF notices only.
- Local browser verification is recorded above. No live provider calls or
  deployment; this does not establish scientific accuracy or audience capacity.
- Fresh research ranked honest feedback during quiet provider waits above a new
  comparison panel. Next experiment: a browser-owned elapsed display anchored to
  local run submission, clearly separated from backend measured execution time
  and replay time. Verify a ten-second silent source, completion and cleanup.
  A ticking clock must never imply that the provider is known to be progressing.

## Pass 5: an honest clock through quiet waits

Investigations now show **Time since local submission** in a browser-owned clock
outside the 300ms activity fragment. `BackgroundRun` creates a unique clock identity
and monotonic submission anchor before starting its source worker, then freezes
the local duration after cleanup. Browser ticks derive from `performance.now()`
and the initial elapsed offset. Same-run rerenders retain the anchor; they never
reset the clock. Hidden tabs stop scheduled ticks and recompute from the anchor
on return. New runs replace the previous clock, and unmount removes timers and
listeners. A completed clock cannot be restarted by a stale active descriptor.

The label explicitly separates this local wait from provider progress or health.
After termination a separate line shows valid backend-measured execution time,
or unavailable when no valid duration exists. Boolean, negative, nonfinite and
overflowing values are not presented as measurements. Recorded runs and saved
playback have **Recording time** instead, derived from their saved event span.
The existing live stat now says **Event span**, or **Backend time** only when a
valid terminal measurement is present. Graph painting still runs on every poll;
the previously failed skip optimization was not reintroduced.

The clock uses `role="timer"` with `aria-live="off"`, stable tabular digits and
the existing browser theme event. Ticks make no Python callbacks, model requests
or screen-reader announcements. The design worker owns matching component CSS.

Validation: the clock/runtime/replay/full-flow group passed **45 tests**. After
adding a further overflowing-integer metric check, the clock-specific suite
passed **13 tests**. Node's controlled clock covers ten silent seconds, same-key
remount, stale cleanup, sixty hidden-tab seconds, resume, completion, stale active
data, new runs and interval/listener cleanup. Python verifies the submission
anchor precedes the worker, silence does not reset it, and completion freezes it
separately from backend measurement. Root runs the combined suite separately.

Root's ignored local browser fixture passed: a deliberate ten-second sleep plus
UI inspection time advanced the clock from 00:00:00 to 00:00:24 while script-pass
and source-event counts stayed unchanged. Explicit same-run rerender retained
elapsed time. Completion froze the display, unmount/remount retained the terminal
value, and a new run reset to zero. Theme switching kept dimensions stable; 390px
layout had no horizontal overflow. Role and live-region attributes were verified.
The viewport was reset; full app Demo/replay integration was still being checked
when this entry was written.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_run_clock.py tests/test_frontend_runtime.py tests/test_frontend_replay.py tests/test_frontend_flow.py -q -p no:cacheprovider --basetemp .deploy/overnight-clock-tests
.venv/Scripts/python.exe -m pytest tests/test_run_clock.py -q -p no:cacheprovider --basetemp .deploy/overnight-clock-validation
```

Component API for an isolated fixture: `clock_data(job, state)` returns
`runKey`, `active`, `elapsedMs` and `measuredMs`; `render_run_clock(data)` uses
the stable component key. A manually supplied descriptor can exercise updates
without invoking any providers. The production integration omits the clock for
recordings, saved replay and older retained workers lacking a submission anchor.

### Pass 5 parent integration result

- Full suite: **240 passed**, two existing dependency deprecation warnings.
  Whitespace validation passed with informational CRLF notices.
- Main-app clinical-only Demo completed normally: local submission duration and
  backend-measured 1.7s were distinct. Saved replay completed 27/27 events with
  Recording time and no local submission clock. Returned the app to Results.
- The isolated browser fixture and its port-8503 server were stopped. Existing
  app/API services remain available. No deployment or live provider calls.
- Fresh research's next experiment: a non-interrupting, outcome-specific notice
  when a run finishes while the scientist edits another section. Preserve their
  draft and focus; distinguish completed, cancelled and failed outcomes rather
  than presenting every terminal state as success.
- This timer does not resolve the earlier long-run tab stall or graph repaint
  cost. Those need separate measurements and a stable rendering boundary.

## Pass 6: a finished run does not interrupt the next draft

When a background run ends while the scientist is editing Evidence or Question &
agents, the polling fragment now shows an inline outcome notice and an explicit
View action. Completion does not rerun the whole page, move focus, navigate,
overwrite the draft or start another run. Voice milestone updates also stop
forcing full reruns while an editor is open. Results navigation in the header
refreshes on the next ordinary interaction; the notice's action is available
immediately and saves the latest question widget value before navigating.

Outcome wording distinguishes a completed result, abstention, cancellation,
terminal error, unknown terminal status and a stream that ended without a final
result. A recorded error followed by confirmed completion does not silently
reclassify the whole run as failed. Missing final results open Activity; confirmed
outcomes open Results. Cancellation does not promise that partial findings exist.
Recordings are labeled as saved output, and replay never publishes a new outcome
notice. Once the scientist has viewed the outcome, its notice is not repeated.

The notice uses a calm shared-theme surface with a polite, atomic status region.
Its native action button is outside that live region. Error, unknown and abstained
verdicts now match their notice, including idea review: they no longer fall through
to a green success label. The original recorded output remains visible.

Browser testing caught a real first-click problem: when an uncommitted text edit
blurred, the newly available View previous result control shifted the polling
fragment's position. Streamlit derives fragment identity from that position, so
the action was remounted midclick. Reserving the existing control's position with
a persistent empty slot fixed this without a custom DOM handler or new component.

Validation: **53 tests passed** across outcomes, full frontend flow, runtime and
replay. After adding four further idea-review verdict cases, all **17 outcome
tests passed**. Actual background tests cover complete, abstained, cancelled,
terminal error, source exception and missing-final-event outcomes while editing,
plus explicit View, retained drafts, no retry and replay suppression. Root's live
browser fixture verified that terminal arrival preserved the focused textarea's
value and caret. After the stable-slot correction, the first pointer activation
opened Results and returning to setup restored the exact uncommitted draft.
Additional cancelled/error/theme/narrow browser checks were in progress when
this entry was written.

The fragment's originally scheduled 300ms polling can continue after termination
until the next normal full interaction. That bounded scheduling tradeoff avoids
remounting an editor to turn off the timer; repeated notice markup stays identical.
A separate scheduling optimization can follow. Graph and clock boundaries were
not changed in this pass.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_outcomes.py tests/test_frontend_flow.py tests/test_frontend_runtime.py tests/test_frontend_replay.py -q -p no:cacheprovider --basetemp .deploy/overnight-outcome-tests-final
.venv/Scripts/python.exe -m pytest tests/test_outcomes.py -q -p no:cacheprovider --basetemp .deploy/overnight-outcome-copy-tests
```

Files: `frontend/app.py`, new `frontend/ui/outcomes.py`, the bounded verdict fix
in `frontend/ui/components.py`, outcome/flow tests and this log. The design worker
owns the notice CSS in `frontend/ui/theme.py`.

### Pass 6 parent integration result

- Full suite: **264 passed**, with two existing dependency deprecation warnings.
- Controlled production-UI fixture confirmed that a completed run preserves the
  editor's exact unsubmitted value, DOM ID, caret and focus. After the stable-slot
  fix, one pointer click opened Results; Edit setup restored that draft exactly.
- Cancelled outcomes displayed Investigation stopped without claiming findings
  existed. At 390px the notice did not overflow, and both themes had equal numeric
  width and height. The viewport override was reset.
- Restarted the temporary fixture to load the final imported renderer. A terminal
  error then displayed consistent error wording in both notice and Results.
- Status markup is polite and atomic, with its button outside the live region.
  Actual screen-reader speech and repeated-announcement behavior were not listened
  to; do not claim a full accessibility audit.
- Temporary fixture tab and server stopped. Main app remains at port 8502. No
  deployment, live providers or scientific validation in this pass.
- Next experiment: make the bounded prior context in a follow-up inspectable,
  including what was omitted, without implying it is fresh or verified evidence.

## Pass 7: inspect prior context before running a follow-up

Manual and weak-point follow-up editors now show an inspectable prior-context
block before their explicit Run action. One `ContextInspection` instance shares
the exact bounded payload between those editors and the queued request; metadata
about selection and shortening remains in the UI and adds no model tokens. The
existing `context_for` payload and selection are unchanged, and the completed
record and new editable question remain separate.

The preview reports included versus available findings, weak points and discussion
turns. It names the first-eight, first-six and last-four selection rules as recorded
order rather than importance. Source-reference counts use references attached to
the included findings as their denominator, and references attached to omitted
findings are counted separately. Omission wording applies only to this prior-context
payload: a weak point outside the first six may still appear in the new question.
Question, conclusion, claim, source-reference, kind, role and discussion text caps
are reported in characters, including the actual pre-truncation JSON length of each
selected source reference. Source references are serialized once for the shared
payload, and truncated strings are shown literally without attempted repair.

Native disclosures expose shortened-field details and the exact escaped JSON
payload without a rerun. Large selected provenance keeps an outer lazy disclosure
so its payload and metadata are not prepared until requested. Reopened results
reconstruct the same preview. A carried legacy payload remains inspectable while
comparison counts, selection order, omissions and shortening stay unknown; the
copy does not claim that an original record is unavailable elsewhere in history.
The preview explicitly distinguishes prior generated context from the full prompt,
new question, separately reused files and independently verified evidence.

Validation: **44 tests passed** across preview, follow-up, frontend flow and lazy
details. After the final saved-context wording correction and added selected-weak-
point/recording cases, **11 targeted tests passed**. Tests compare the preview to
the actual request context at the source boundary for manual, suggested and
recorded follow-ups; cover empty and legacy records, exact caps, Unicode and HTML
escaping, lazy preparation, single serialization, reopening and unchanged records.
`git diff --check` passed for the owned files.

Root's synthetic production-UI fixture verified 8 of 10 findings, 6 of 8 weak points,
4 of 6 discussion turns, 24 of 32 references on included findings, eight references
on omitted findings and 42 shortened fields. Enter and Space operated the native
exact-payload disclosure with stable focus and tooltip IDs. Its parsed preview
matched the actual captured request context after explicit Run. Remaining browser
theme/narrow/weak-point checks and the full suite are handled by root.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_followup_preview.py tests/test_frontend_followup.py tests/test_frontend_flow.py tests/test_frontend_details.py -q -p no:cacheprovider --basetemp .deploy/overnight-context-tests
.venv/Scripts/python.exe -m pytest tests/test_followup_preview.py tests/test_frontend_followup.py tests/test_frontend_flow.py::test_recorded_weak_point_followup_uses_simulated_review_without_original_files -q -p no:cacheprovider --basetemp .deploy/overnight-context-review-tests
```

Files: `frontend/app.py`, `frontend/ui/followup.py`, new
`frontend/ui/followup_preview.py`, preview/flow tests and this log. Existing native
disclosure styles were reused, with no CSS, endpoint, provider or service changes.

### Pass 7 parent validation completed

- Full suite: **272 passed**, two existing dependency deprecation warnings, using
  `pytest tests -q -p no:cacheprovider --basetemp .deploy/overnight-pass-7-tests`.
- Production UI with synthetic records and a local capture source confirmed the
  manually inspected payload matched the actual submitted context. The selected
  eighth weak point remained in the editable new question, independently of the
  prior-context block's first-six limit. Both editors showed the same counts.
- At 390px, the expanded exact payload wrapped without horizontal overflow.
  Its summary was 44px tall. Switching dark to astral preserved exact disclosure
  dimensions and open state. Enter and Space operated the native disclosure.
- Temporary fixture tab/server closed and viewport restored. Main local app left
  open. No provider calls or deployment; synthetic records were UI test data only.
- Next experiment: improve recognition of saved runs that share a question,
  keeping identity, mode and outcome visible before opening a result. Research
  remains ongoing; no assumption that this is the next change without inspection.

### Pass 8 parent validation completed

- Full suite: **284 passed**, two existing dependency warnings, using
  `pytest tests -q -p no:cacheprovider --basetemp .deploy/overnight-pass-8-tests`.
- Local synthetic history used four identical long questions with differing modes,
  outcomes and IDs sharing a prefix. Selecting a cancelled record left the current
  report intact; explicit keyboard Open restored the exact cancelled result and
  its unsent draft. The final ID-first version also restored the selected recorded
  abstention and its distinct draft, with the recording limitation visible.
- Mobile QA caught a question-first dropdown clipping all options to the same
  text. ID-first labels fixed this: a fresh 390px screenshot showed distinct IDs
  and written outcomes. ArrowDown/Enter selection worked and the full question
  remained visible in the selected preview.
- Native identifier details opened with Enter, had a 44px summary and no horizontal
  overflow at 390px. Theme switching preserved exact dimensions and open state.
  Selector changes retain the existing Streamlit rerun; metadata toggles are local.
- Temporary fixture server/tab stopped and viewport restored. Main app remains
  open. No provider calls or deployment. Next pass: measure quiet-run rendering
  and interaction responsiveness before selecting another implementation.

## Pass 8: recognize a saved result before opening it

The saved-results selector previously used mutable list positions and the first
100 question characters, making repeated questions indistinguishable. It now
selects by the existing stable session record ID. Labels start with a compact,
collision-safe ID, followed by the recorded outcome, connection mode and question
excerpt. Shared ID prefixes expand just far enough to distinguish every retained
entry. A changed list order therefore does not silently select another record;
when the selected entry is no longer available, selection resets to an available
entry rather than reusing its old numeric index.

Before Open selected result, a clearly labeled preview shows the full recorded
question, mode and outcome. Its native disclosure provides the exact session ID,
backend ID, saved connection mode and execution mode reported in saved configuration.
A different submitted question remains available there too. Missing or unfamiliar
metadata stays explicit. Live connection describes the route, not confirmed live
inference. Backend IDs can repeat or be absent, and these session records are not
presented as durable storage. Completed, abstained, cancelled, error and unknown
outcomes remain distinct; there is no blanket success badge.

Selection only inspects small metadata and never walks event or finding histories.
The full question and all identifiers are escaped and wrap using existing styles.
Static identifiers open in a native client-side disclosure. Changing the native
Streamlit selection still reruns the script, which keeps the explicit Open action
bound to server state without adding a risky fragment boundary. Selecting and
opening neither starts a run nor changes the selected report's saved context.
Existing per-result follow-up drafts and the current setup draft are preserved.

Root's 390px browser check found that question-first labels hid every distinguishing
field in the native one-line menu. The final labels put identity and outcome first;
this correction passed a fresh browser check after reloading the fixture's imported
helper. Earlier browser checks confirmed preview-only selection, explicit
keyboard Open restoring the expected result and unsent follow-up, a 44px native
metadata summary, no narrow-screen overflow, and unchanged disclosure geometry and
open state across themes.

Validation: **44 tests passed** across history and the complete frontend flow.
Cases cover identical long question prefixes, colliding short local IDs, duplicated
or blank backend IDs, unknown mode/status, abstention and errors, escaped full
questions, untouched large output, stable selection after reorder, five-entry
retention, old in-session numeric selector migration, exact request/context
restoration and preserved unsubmitted drafts. No additional source request occurs
on selection or opening. `git diff --check` passed for the owned files. The first
test attempt exposed a test import path shadowing the backend package; the test
was corrected to use package imports, with no production workaround.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_history.py tests/test_frontend_flow.py -q -p no:cacheprovider --basetemp .deploy/overnight-history-tests-fixed
```

Files: `frontend/app.py`, new `frontend/ui/history.py`, history/flow tests and this
log. No CSS, provider, endpoint, service or deployment changes. Root completed the
fresh mobile menu check and full-suite integration; see parent validation above.

## Pass 9: keep live help readable through quiet polls

Measurement rejected graph-string caching as the most useful bounded change for
this fixture. A local seven-batch microbenchmark of 1,000 calls per batch on the
bundled 5-agent, 23-event recording measured median pure Python work of 0.0136ms
for DOT construction, 0.0034ms for stats and 0.0120ms for conversation markup.
These measurements exclude browser layout and interaction latency.

Root's held-source production-UI fixture then observed a real quiet period with
five agents and seven events. Over 41.109 seconds, paints and DOT builds increased
from 55 to 192, about 3.33 per second. The instrumented Python paint time increased
813.263ms and DOT construction time 5.785ms. The graph remained visible, but the
three activity help IDs changed on every poll. Keyboard focus moved from the
network help button to BODY after a quiet poll, dismissing its visible tooltip.
The unrelated research-question help ID remained unchanged. This demonstrates a
specific reading interruption, not a measured input-latency or provider problem.

Help controls now accept an optional caller-scoped `help_key`. The live activity
view uses stable keys for its run configuration, network and messages help. Its
scope includes the local result ID, with separate live and replay prefixes.
Unscoped callers retain independent generated identities, so repeated controls
elsewhere do not accidentally share a tooltip. The same quiet activity help
produces identical complete HTML, including its anchor and aria-describedby target;
changed help text still updates and all supplied text remains escaped.

Every activity paint and graph call is preserved. No cache, early return, polling
change or new animation was added. Scope is deliberately limited to the three
fragment-owned help controls. This does not claim reduced browser layout cost,
fewer graph paints, a fixed long-tab stall or measured latency savings.

Validation: **40 tests passed** across help identity, full frontend flow and replay.
Thirty identical help paints produce one markup value; different controls, runs
and replay scopes have distinct IDs. Two simultaneous test activity views retain
six unique tooltip relationships. Repeated paints still emit both graphs, and a
new event changes their DOT while help remains stable. Tests also cover updated
help text, safe identifiers, escaping, native widget return values and unchanged
unscoped uniqueness. `git diff --check` passed for the owned files. Root handles
the fresh browser focus/hover/cancellation checks and full-suite integration.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_help_identity.py tests/test_frontend_flow.py tests/test_frontend_replay.py -q -p no:cacheprovider --basetemp .deploy/overnight-help-identity-tests
```

Files: `frontend/app.py`, `frontend/ui/layout.py`, optional-key forwarding in
`frontend/ui/help.py` and `frontend/ui/components.py`, the new help-identity tests
and this log. No CSS, provider, endpoint, service or deployment changes.

### Pass 9 parent verification completed

- Full suite: **288 passed**, two existing dependency warnings, using
  `pytest tests -q -p no:cacheprovider --basetemp .deploy/overnight-pass-9-tests`.
- Fresh fixed quiet fixture retained all three activity help IDs, actual keyboard
  focus on Agent network help, and its visible tooltip through ongoing polls.
  Escape dismissed the tip; focus and dismissal persisted through more polls and
  a single released message. Event count changed from seven to eight exactly once,
  the message appeared once, and the graph remained visible.
- Expanded Agent details remained open through quiet polls. At 390px the activity
  page had no horizontal overflow; theme switching retained help geometry and IDs.
  The local clock advanced independently of the unchanged event count.
- The baseline fixture also confirmed navigation to Question, typing and explicit
  cancellation remained available during silence; cancellation cleanup produced
  the stopped notice. These are functional observations, not latency measurements.
- Released terminal event opened Results with the synthetic outcome. Saved replay
  reached nine of nine events with a visible graph and a distinct replay help ID.
- Fixture tab/server stopped, viewport reset, main app retained. No deployment,
  provider calls, 50-user test, INP claim or claim that the earlier long-tab stall
  is resolved. Pointer-hover continuity was not separately measured this pass.

### Pass 10 parent verification completed

- Full suite: **303 passed**, two existing dependency warnings, using
  `pytest tests -q -p no:cacheprovider --basetemp .deploy/overnight-pass-10-tests`.
- Browser baseline: 98 retained synthetic entries exposed only the latest 40,
  ending at message 056. The new closed large panel prepared zero timeline rows.
  Its pages contained entries 98..59, 58..19 and 18..1: all 98 unique entries,
  with no gaps or duplicates. Older/Oldest/Newest worked with keyboard activation.
- Paging kept the panel open and outside help IDs unchanged, confirming the page
  action remained within its fragment. The newest page returned to entry 98.
- At 390px the oldest message retained Unicode, literal markup and a 400-character
  unbroken identifier without horizontal overflow. Theme switching preserved exact
  timeline width and height. Existing wrapping styles sufficed.
- The real bundled sample recording retained 52 entries. Its oldest page exposed
  the initial planner call, result, message and run-start entry; Newest returned to
  entry 52. No new inference was performed. Tool summaries remained explicitly
  separate from their full raw payloads.
- Temporary fixture/server stopped, viewport restored, main app retained. No
  deployment or scientist study. Next experiment: a teammate retrieves an earlier
  decision; add search/filter controls only if paging proves insufficient.

## Pass 10: make the full activity timeline reachable

The Results panel called itself Full activity timeline but rendered only the last
40 retained timeline entries. The bundled recordings have 52 and 55 entries, so
their earliest activity was already hidden behind Raw events. Message.text is no
longer capped at 300 characters by this renderer; however, Event.text deliberately
shortens structured tool arguments/results into readable summaries. The new view
keeps that distinction explicit and leaves the full supplied payloads in Raw events.

Histories of up to 40 entries remain ready behind a native expander. Larger
histories prepare no timeline HTML while closed, then use an isolated fragment to
render one window of at most 40 entries. Newest, Newer, Older and Oldest controls
provide bounded access to every retained entry. Each page reports its displayed
range, total and page count, and every row includes its original arrival ordinal
and event type. Ordering remains reverse arrival order, even when timestamps are
equal or out of order. Full Message.text, Unicode, literal markup, agent identity,
recipient and relative time remain accessible. Existing styles preserve whitespace
and wrap long text; no new CSS was needed.

Pager state uses the local session result ID plus the view name, so saved records
with the same backend ID do not share a page cursor. An older window keeps its
recorded boundary if entries arrive later; Newest explicitly returns to the latest
window, and shorter records clamp safely. The live conversation remains bounded
to its latest 12 messages, now labeled with the included and total message counts
and its forward arrival order. Graph painting and polling are unchanged.

Validation: **56 tests passed** across activity history, lazy details, help identity
and the complete frontend flow. Cases cover 0/1/40/41/80/81/98 entries, equal and
out-of-order timestamps, all-page coverage without gaps or duplicates, older-window
anchoring, shorter records, distinct local IDs with a shared backend ID, no work in
a closed large panel, full escaped text and unchanged raw payloads. The app-level
test confirms Older preserves an unsent follow-up, exact report/request/context,
and source request count. AppTest lacks stateful-expander serialization during a
button click; tests explicitly retain that browser-owned state, and the actual
browser confirmed the expander stays open. `git diff --check` passed for owned files.

Root's production-UI fixture retrieved all 98 entries in 40/40/18 windows with a
98-entry union and no overlap. Enter operated Older and Newest; surrounding help
IDs stayed unchanged, confirming that page controls rerendered only the fragment.
The oldest entry retained Unicode, escaped literal markup and long text. At 390px
the timeline did not overflow, and theme switching preserved exact dimensions.
The actual bundled recording check and full suite subsequently passed; see the
parent validation above for the 52-entry recording and 303-test result.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_activity_history.py tests/test_frontend_details.py tests/test_help_identity.py tests/test_frontend_flow.py -q -p no:cacheprovider --basetemp .deploy/overnight-activity-history-final-tests
```

Files: new `frontend/ui/activity.py`, `frontend/ui/components.py`,
`frontend/ui/layout.py`, history/flow tests and this log. No app entry-point, CSS,
provider, endpoint, service or deployment changes.

## Pass 11: save a receipt of the selected request

Results now offers Request receipt for this result. A selected saved result has a
separately labeled receipt before its Open action, so exporting it does not change
the current report. Opening either lazy panel prepares its JSON and exposes a
download that uses the installed Streamlit `on_click="ignore"` behavior. Closed
panels perform no receipt serialization. Keys include the view and local record ID;
changing the selected record cannot leave the previous owner's download visible.
There is no global or session payload cache and no extra Prepare button.

The versioned receipt reads the saved RunRequest rather than the current editor,
current capability defaults or a newly rebuilt follow-up context. It preserves
the submitted question and JSON prior context exactly, plus requested mode, sample
flag and allowlisted task mode, specialists and model settings. Omitted settings
are counted explicitly. A recording includes its playback speed and a note that
this is a playback request, not the original model invocation. Session/backend
IDs, recorded question, terminal status, abstention and execution mode reported
in saved configuration are separate outcome metadata. A recorded question can
differ from the submitted one without either being overwritten.

Upload contents and names, backend connection URL, credentials, local fixture
path, unknown configuration fields, provider instructions and full raw/result
payloads are not added to the receipt. Supplied question and prior context remain
included; this is not a claim that their research text contains no sensitive data.
Missing legacy requests stay null. Unsupported context objects are not stringified
into a misleading or potentially revealing substitute: their context becomes
unavailable with an explicit note. The UI and exported scope distinguish this
receipt from a full model prompt, reproducibility bundle or resumable session.

Validation: **48 tests passed** across receipts, full frontend flow and lazy
details. Checks cover exact saved question/context/settings, independent exported
copies, excluded synthetic connection/config/upload/path sentinels, requested
versus reported settings, Demo/Live/recording modes, unknown/cancelled/error and
abstained outcomes, missing legacy fields, unsupported objects, closed-panel zero
preparation and owner changes. The download widget has ignore_rerun set. App-level
checks confirm selected export leaves the current run, submitted context, unsent
follow-up and source request count unchanged. `git diff --check` passed for owned
files. Root handles actual browser download bytes, layout and full-suite checks.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_receipt.py tests/test_frontend_flow.py tests/test_frontend_details.py -q -p no:cacheprovider --basetemp .deploy/overnight-receipt-tests
```

Files: `frontend/app.py`, new `frontend/ui/receipt.py`, receipt/flow tests and this
log. No CSS, provider, endpoint, service or deployment changes.

## Morning cutoff closeout

On resumption at approximately 09:58 London, the cutoff had passed. No new feature
iteration was started; the automation was paused and final validation completed.
Full suite: **313 passed**, two existing dependency warnings, with
`--basetemp .deploy/overnight-final-tests`. Receipt browser download verification
was interrupted; only its preparation/current-owner UI had been observed. Actual
downloaded bytes and selected-owner browser download remain unverified. The local
frontend was restarted on 8502 and its initial page checked. See
`Plan/overnight-morning-summary.md` for release limits and completed work.
