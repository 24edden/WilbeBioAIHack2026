
## 2026-09-20: Theme help target accessibility

- Observation: the theme help button was 14 by 14 CSS pixels beside a 28px-high switch.
- Change: expanded its target to 28 by 28 pixels within the existing header height, prevented flex shrinking, and added visible hover feedback. The tooltip remains immediate and opens on focus on devices without hover. Both palettes use the same dimensions; reduced-motion and client-side theme behavior remain intact.
- Files: `frontend/static/theme.css`. No app, JavaScript, voice, server or deployment changes.
- Basis: [W3C target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum/) specifies 24px targets or spacing exceptions. This targeted improvement is not a claim of whole-site conformance.
- Checks: theme JavaScript lifecycle test passed; 19 frontend flow tests passed. Static inspection confirms both palettes share target dimensions and the row remains 28px tall. Browser geometry/visual QA is deferred to the parent as instructed.
- Follow-up from research agent: assess hoverable tooltip content and Escape dismissal across help components under W3C 1.4.13. Full dismissal needs JavaScript ownership beyond this CSS-only pass.

## 2026-09-20: Hoverable and dismissible help

- Removed dead space between each help trigger and its tooltip; tooltip content now accepts pointer interaction, so moving into it retains the tip. Both shared help and the theme component preserve immediate CSS reveal and hide on pointer departure when not keyboard-focused.
- Added local Escape dismissal through the existing theme component lifecycle. Dismissal leaves focus untouched and lasts until a fresh pointer entry or focus entry, rather than reopening while moving within the same tip. Listeners are removed on component cleanup. No Python actions or extra animation were introduced.
- Files: `frontend/ui/theme.py`, `frontend/static/theme.css`, `frontend/static/theme.js`, `tests/theme_browser_test.mjs`, new `tests/help_browser_test.mjs`. Both themes keep identical geometry and existing reduced-motion treatment.
- Basis: [W3C content on hover or focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html), researched by overnight ideation worker.
- Verification: help lifecycle and theme lifecycle Node tests pass; 19 frontend flow tests pass. Parent retains browser QA ownership, including actual pointer movement and focus rendering across both palettes.

## Parent browser verification

- A fresh local page at port 8502 shows the shared help text immediately on the
  help control. Escape hides it while focus remains on that control.
- Theme switching retains the same help element IDs, confirming no page rerun.
  With the switch in view, the heading and navigation have identical x, y, width
  and height in both themes. Automatic scrolling to an offscreen switch must not
  be mistaken for a layout change when measuring viewport coordinates.
- Full pointer travel across the tooltip bridge remains a manual/browser follow-up;
  the DOM-level dismissal lifecycle tests pass.

## 2026-09-20: Pass 2 browser-access check and bounded render review

- Browser checks could not begin in this worker: both `iab` and known browser `1` were unavailable; surface inventory returned no browsers/apps. Browser ownership was released to the parent. No Demo/replay browser completion or pointer bridge result is claimed here.
- Read-only review confirms current investigation fragment paints every poll, preserving the parent fix for disappearing quiet-run activity. Conversation output is capped at 12 messages; graph size follows unique agents and relationships rather than raw event count. Replay advance consumes a finite event list.
- Remaining hypothesis for browser follow-up: Graphviz and help/cards are rebuilt around 3.3 times per second. Shared help generates new UUIDs per render, so help DOM identity can change during polling. This could contribute to focus/flicker, but does not prove the reported browser stall. No speculative code change made.
- Runtime and replay targeted tests: 10 passed. No CSS/app changes, server restarts, microphone/audio actions, or deployments.

### Pass 2 parent browser checks and caption fix

- The root task could access the browser; the empty worker inventory was scoped
  to that worker. Pointer travel from the Source help trigger into its text kept
  the tooltip visible and hovered. Clicking outside hid the tips immediately.
- A full short Demo run and replay completed. Pause, one-event Step, Resume and
  final graph retention worked. This does not establish behavior under long
  provider waits or explain the previous stalled browser tab.
- Visual review of the new follow-up editor found explanatory captions too dim.
  Computed styles confirmed Streamlit applied opacity 0.6 on top of the intended
  caption colour. Shared theme CSS now sets caption opacity to 1, preserving all
  layout dimensions. Browser computed styles confirmed the correction.
- Weak-point drafting, edited submission and restoration of both drafts from the
  saved result were verified in the real browser. The local port remains 8502.

## 2026-09-20: Pass 3 linked-argument design review

- Reviewed the UX worker's exact `reply_to` inspection proposal: native disclosure opens the actual linked prior argument and a compact recorded chain, without generating a summary or guessing adjacency. Requested role/agent plus phase in the disclosure label, with source turn IDs available inside. Missing or ambiguous IDs must remain explicitly unresolved.
- Added minimal `.argument-trace` presentation in `frontend/ui/theme.py`: one vertical reading column, native disclosure marker, 44px summary target, visible keyboard outline, readable role/phase/ID hierarchy, full whitespace-preserving text and long-ID wrapping. Narrow screens reduce padding slightly without clipping content or requiring horizontal comparison.
- Geometry and responsive rules are shared across palettes. Only existing theme variables change paint; no transitions/animations added. Static stylesheet assertions pass for dark, astral and client modes, and Python compilation passed. UX worker owns renderer/resolver tests; root owns browser checks.
- Browser acceptance: Tab to summary and toggle using Enter/Space; inspect long IDs/URLs and multiline content at narrow width; confirm exact direct prior argument and explicit chain labels; ensure colors are supplementary to written perspective labels; switch theme with disclosure open and verify unchanged bounds. No browser/server/deploy actions by this worker.

### Pass 3 parent browser validation

- Exact linked challenge text and recorded chain displayed in a new Demo review.
  Opening the native disclosure preserved surrounding help node IDs.
- Enter and Space toggled the focused summary and retained focus. At 390px width,
  all four disclosures had matching client/scroll widths and readable wrapped
  content; summaries exceeded the 44px target. A screenshot confirmed the visible
  focus ring and the phase, agent, source ID and text hierarchy.
- Theme switching preserved all four disclosures' width, height and open state.
  Responsive viewport override was reset after inspection.
- Full suite: **210 passed**, two existing dependency warnings. Long adversarial
  IDs are covered by renderer tests; browser layout checks used the actual Demo
  records. No claim of long-provider-wait or concurrency validation.

## 2026-09-20: Pass 4 exact finding inspection review

- Reviewed the exact finding disclosure proposal with UX and research workers. Existing argument-trace styles already provide a native summary, 44px target, visible focus, full-width reading order and long-token wrapping, with identical geometry across palettes. No new decorative CSS is needed for the proposed markup. Static checks confirm these rules occur once in dark, astral and client stylesheets.
- Recommended hierarchy: exact claim, producing agent/role, written reported relation to the hypothesis, then attached source records. Finding stance (supports/contradicts/neutral/unknown) must not be confused with review-agent Support/Challenge alignment. Resolving an ID is not verification of its claim.
- Requested actual backend provenance fields `kind`, `ref`, `locator`, `quote` be visibly labeled; supplied quotes are excerpts from the payload, not independently verified paper text. Missing or duplicate finding references must remain explicit rather than inferred by nearby records.
- Research basis: [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) distinguishes entities, activities and responsible agents; lineage does not prove correctness. [ALCE](https://aclanthology.org/2023.emnlp-main.398/) evaluates citation quality separately from correctness. The UI recommendations are design inferences from these sources, not claims that TRACE passed those evaluations.
- Acceptance for root/UX: open by keyboard without rerun, retain focus and open state on theme change, show exact claim/record content, preserve long IDs and multiline excerpts at 390px, explicitly show no-source/unresolved cases, and keep inspect separate from draft-follow-up action. Functional implementation/tests remain UX-owned; no browser/server/app edits by this worker.
- Next bounded design experiment: ask a scientist to locate the exact record behind one finding and explain the reported relation versus source verification. Record wrong turns or ambiguous labels before adding another view.

### Pass 4 parent verification

- Fresh clinical-only Demo: the linked CEA claim exactly matched its original
  finding. File references, line locations and three supplied excerpts displayed
  with explicit labels. Outputs remained clearly simulated.
- The large outer References panel loaded on request. Subsequent native finding
  toggles retained all 16 tooltip description IDs. Enter closed and Space opened
  the disclosure with focus on its summary.
- At 390px width all six finding disclosures had no horizontal overflow and 44px
  summaries. Screenshot review confirmed readable wrapping and visible focus.
- Both palettes retained each disclosure's numeric width, height and open state.
  An initial JSON-string comparison gave a false mismatch from property ordering;
  direct numeric comparisons passed. The temporary viewport override was reset.
- Full suite: **227 passed**, with two existing dependency warnings. No deployment,
  long-provider-wait or audience concurrency validation in this pass.

## 2026-09-20: Pass 5 quiet-wait clock presentation

- Added `frontend/static/run_clock.css` for the UX worker's client-owned timer component. The fixed-width monospace/tabular value sits beside the static 'Time since local submission' label; at narrow widths it stacks into one column. No motion or transition is used, including reduced-motion mode.
- Matched the agreed `.run-clock` label/value/measured/note contract. A separate measured-execution line reserves its normal line height while hidden during the active run. Its wording and terminal value remain UX-owned; local elapsed time is not used as a server-duration substitute or provider-health assertion.
- Both theme palettes change only colors. Static checks confirm fixed digit width, tabular numerals, no animation and no palette-specific sizing. No parent theme stylesheet changes were needed; root retains browser QA and UX owns component lifecycle/formatting tests.
- Acceptance: compare bounds at seconds/minute/hour rollover and theme switching, read at 390px without horizontal overflow, confirm no screen-reader tick announcements (`role=timer`, `aria-live=off` in UX markup), verify terminal measured duration is separate, and confirm replay uses recording time rather than this local timer.
- Next design experiment: during a deliberately quiet mock run, ask a scientist what the timer does and does not establish. If they infer provider health or completion progress, refine the label/note before adding further indicators.

### Pass 5 parent verification

- Silent-source fixture advanced from zero to 24 seconds without new events or
  full-page runs. Explicit rerender preserved the anchor. Completion froze at
  44 seconds with separately measured 44.6 seconds; remount retained the frozen
  display and a new run reset it. Timer semantics and `aria-live=off` checked.
- Theme switching retained exact numeric width and height. At 390px the clock had
  no horizontal overflow. The viewport override was reset. No hour rollover was
  exercised in the browser; formatting and lifecycle are covered by Node tests.
- A fresh main-app Demo completed with local time and a separate measured 1.7s.
  Saved replay completed all 27 events, showed Recording time and no submission
  clock. The temporary fixture tab and server were closed after verification.
- Full suite: **240 passed**, two existing dependency warnings. No live provider,
  deployment, audience load test or provider-health validation is claimed.

## 2026-09-20: Pass 6 noninterrupting outcome notice

- Added a compact `.run-outcome-notice` surface with `.run-outcome-title` and `.run-outcome-detail` in shared theme CSS. Neutral colors and an ordinary accent border avoid implying successful validation; outcome meaning must be written explicitly by the UX helper. The notice has no animation, transition, countdown or auto-dismiss.
- Shared dimensions across palettes, responsive padding and long-text wrapping preserve the current draft layout. The explicit native results/partial-results/activity action belongs outside the polite live message so an announcement does not repeat interactive labels.
- Static stylesheet checks pass for dark, astral and client modes: one common style block, text wrapping and no motion. Root retains browser QA; UX owns terminal mapping and once-per-run notification semantics.
- Guidance: [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) supports making status available without moving focus and cautions against overly chatty announcements. [Fluent toast usage](https://fluent2.microsoft.design/components/web/react/core/toast/usage) informs the choice of a persistent inline notice rather than transient timed feedback. These are design inferences, not a conformance audit.
- Acceptance: terminal complete, abstained, cancelled and error messages remain distinct; current question/files/caret stay intact when completion arrives; only the explicit action navigates; action remains keyboard reachable with existing focus styling; no repeated polite announcement on unrelated edits or theme changes.
- Next bounded experiment: type an unfinished question during a paced run, let it end, then ask the scientist to locate the prior outcome and return to the draft. Record any lost caret/text or confusion about partial results before changing notice prominence.

### Pass 6 parent browser verification

- Completion preserved the textarea value, DOM ID, caret and focus on Question.
  Browser testing exposed a lost first click during blur-driven rerender; reserving
  the previous-result control's position fixed fragment identity. One pointer
  activation then opened Results and the draft survived returning to setup.
- Cancelled and error notices used distinct wording. The final error renderer
  showed an error heading in Results. At 390px the notice had no horizontal
  overflow; theme switching kept its exact numeric dimensions. Viewport reset.
- `role=status`, polite and atomic attributes were verified with the action
  outside the status region. Screen-reader audio was not tested.
- Full suite: **264 passed**, two existing dependency warnings. Temporary test
  page/server closed. No deployment or scientific/model-quality claim.

## 2026-09-20: Pass 7 exact follow-up context preview review

- Recommended reuse of the existing native argument-trace disclosure rather than introducing another panel style. Current styles already provide a 44px summary, visible focus, whitespace-preserving text and long-token wrapping, with the same geometry in both palettes. Static checks pass for dark, astral and client exports; no CSS changes needed for the proposed structure.
- Read the actual `context_for` bounds and sent UX the first/last record selection and per-field character limits. Preview labels should distinguish Included, Not included and Shortened, describe record counts without a quality/completeness percentage, and expose the exact bounded JSON as optional detail. The same preview belongs before explicit Run for both manual and weak-point drafts, without a new confirmation step.
- Research review: label the content 'Prior generated context for this follow-up', not full model prompt or all evidence. Character limits are not token budgets. Serialized source strings shortened by existing bounds must remain literal strings, not be repaired or represented as complete citations. Inclusion does not establish that a model will use a record correctly.
- Primary guidance supplied by research worker: [WAI disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) supports native keyboard disclosure; [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/) motivates caution about assuming included context guarantees effective use, without claiming that historical study evaluates TRACE.
- Acceptance for UX/root: inspect counts against the exact submitted bounded payload; test over-limit records, long Unicode/source strings, empty context, weak-point versus manual path parity, keyboard open/close without rerun, theme persistence, and 390px wrapping. Exact payload display must not trigger a run.
- Next bounded experiment: ask a scientist to predict which prior records a follow-up will receive from the compact preview, then inspect the payload. Record count/omission misunderstandings before changing selection rules. No browser/app/service edits by this worker.

### Pass 7 parent browser verification

- Manual and weak-point previews expose the same retained/available counts.
  The eighth weak point is present in its new question even when omitted from
  the bounded prior-context block; these are visibly separate inputs.
- Native payload disclosure opens with Enter and closes with Space without a
  page rerender. At 390px, long serialized strings wrap, the summary remains 44px
  tall, and the page has no horizontal overflow. Dark/astral switching preserves
  exact disclosure dimensions and its expanded state. Viewport reset afterward.
- Full suite: **272 passed**. Preview/request equality verified with a local
  synthetic capture source; no claim about model comprehension or live hosting.

## 2026-09-20: Pass 8 distinguishable saved-run selection

- Inspected current history code: selectbox values were list indexes and labels only the first 100 question characters. Repeated questions or shared prefixes were therefore visually ambiguous. UX now owns stable local ID selection and exact selected-result preview.
- Reviewed and approved minimal recognition hierarchy: readable question plus mode/outcome in the option, compact ID as a secondary discriminator, full exact question and local/backend IDs available in the selected preview. 'Selected saved result' and explicit Open wording distinguish preview selection from the currently displayed report.
- Requested reuse of outcome semantics and transport/provider distinction: Connected can still use simulated providers; idea-review abstention is not automatically a failed review. Local session ID must remain distinct from possibly repeated backend run IDs. No fabricated timestamps, inferred model names or persistent-archive claims.
- Existing argument-trace styles cover full-question/ID wrapping, native disclosure, 44px summary and keyboard focus; shared dark/astral/client static checks pass. No CSS change needed, no new search/dashboard for a five-result session list.
- Research guidance: [Microsoft HAX recent interactions](https://www.microsoft.com/en-us/haxtoolkit/guideline/remember-recent-interactions/) supports continuity; the implementation remains session-only.
- Acceptance: create duplicate/long-prefix questions with different outcomes and identical backend IDs; preview without replacing current result or draft; keyboard-select and explicitly Open intended local ID; verify report and follow-up draft restore by ID; check 390px exact-question/ID wrapping and theme switching without geometry changes.
- Next bounded experiment: ask a scientist to reopen a specific earlier cancelled or simulated run among repeated questions. Record wrong selections and missing recognition cues before adding further metadata. Root owns browser checks; UX owns app/helper tests; no app/browser/service changes by this worker.

### Pass 8 parent verification

- The corrected ID-first labels were checked in a fresh 390px browser screenshot:
  identical questions now have visibly distinct IDs and outcomes in the dropdown.
  Full question text remains in the selected preview. ArrowDown/Enter selection
  and explicit Open restored the intended recorded result and its saved draft.
- Selecting a cancelled run did not replace the current report before Open.
  Its native identifier disclosure had a 44px summary, no horizontal overflow,
  and exactly matching dimensions/open state across dark and astral themes.
- Full suite: **284 passed**. Synthetic interface fixtures only, no model-quality,
  live deployment or observed scientist-usability claim. Temporary viewport reset.

### Pass 8 mobile finding and label-order correction

- Root's actual 390px screenshot found the native saved-result dropdown uses a no-wrap label: identical leading question text hid the later outcome, mode and ID. This concrete browser result supersedes the earlier question-first option recommendation.
- Sent UX the bounded fix candidate: lead the option with the shortest collision-safe local ID, then written outcome, source mode, and question excerpt. Keep the full exact question prominent in the selected preview. ID shortening must disambiguate all retained local records; a fixed prefix alone is not sufficient when prefixes collide.
- This is a label-order fix, not a new CSS override or broader layout change. Root/UX own implementation and repeat 390px validation; this worker made no app edits and does not claim the candidate has passed browser verification.

## 2026-09-20: Pass 9 quiet-run focus and render audit

- Read-only inspection confirms `paint_live` runs every300ms within the existing fragment; retain this behavior until a separately verified rendering boundary replaces it. Skipping paint is a known content-loss regression, not a safe optimization.
- Concrete churn source: `help.widget` generates uuid4 tooltip IDs on every call, including unchanged Run configuration, Agent network and Agent messages help within each quiet paint. Proposed bounded candidate to UX/root: stable explicit caller identity for those help surfaces, while still painting the whole fragment. Verify DOM/focus continuity before claiming benefit; identical IDs alone do not prove nodes stay mounted.
- Other inspection risks: Agent details expander label changes when roster count changes; conversation renders latest12 messages and may replace a scrolled reading surface when new messages arrive; expanded config/card content is still rebuilt in quiet polls. These are test targets, not confirmed browser defects. `render_stats` also rescans all raw event timestamps for min/max each paint, a lower-priority O(N) cost without evidence it causes the stall.
- Honest wait acceptance: in a controlled silent source, local submission clock advances independently while event count and known phase remain unchanged. No inference about provider health or percent complete. During five seconds of quiet polling, record paint count separately from event revision, retained graph presence, tooltip IDs and actual DOM identity, focused control/caret, open disclosure state and scroll offsets. Then inject one actual event and a terminal event; check exactly once folding and truthful status.
- Interaction acceptance: keyboard typing/navigation and client theme paint remain responsive; cancellation acknowledges actual cleanup and does not claim stopped merely after stream close. Test roster growth and new conversation records with an already-open/scrolled detail view. No extra animation proposed.
- Research caveat: [web.dev INP](https://web.dev/articles/inp) covers next-paint interaction latency, not provider completion; hover/scroll observations require their own checks. No blanket performance score, browser outcome or saved render count is claimed from this code review.
- Next design experiment: compare the same quiet fixture before/after a stable-help-identity patch, with identical polling and event count. Keep only changes that preserve content and improve observed focus/hover continuity. Root owns browser measurements; UX owns any implementation; this worker changed only this log.

### Pass 9 parent browser verification

- Baseline quiet polls changed live help identities and dropped keyboard focus to
  BODY, dismissing the visible tip. The fixed fresh fixture preserved actual focus,
  identity and visible help across polls, rather than merely producing matching IDs.
- Escape dismissal also persisted across polls and a newly released message.
  Graph stayed present, event count advanced once, and expanded Agent details
  stayed open. No animation, graph cache or polling reduction was introduced.
- At 390px the activity page had no horizontal overflow and theme switching
  retained help geometry/identity. Final saved replay showed all nine events and
  a separate help scope. Viewport restored and temporary fixture stopped.
- **288 tests passed**. Functional navigation/typing/cancellation worked in the
  silent fixture. No INP, pointer-hover timing or long-session stability claim.

### Pass 10 parent browser verification

- The previously truncated history now exposes all 98 synthetic entries in
  bounded pages of 40, 40 and 18, preserving arrival ordinals without duplicates.
  Keyboard navigation stays in the open panel; the rest of the page keeps its
  help identities. Closed large history has no prepared timeline rows.
- Oldest-entry Unicode, literal markup and a 400-character identifier remain
  readable at 390px with no overflow. Existing styles suffice. Theme changes
  retain exact timeline geometry; viewport restored after verification.
- The bundled 52-entry recording exposes its earliest planner activity and returns
  to the newest page without inference. Summary-versus-raw-payload copy stays
  explicit. Full suite: **303 passed**. No deployment or usability-study claim.

## 2026-09-20: Pass 10 activity history review

- Read current renderer/model: 'Full activity timeline' actually selected the latest40 timeline entries, newest first; the message feed selected latest12 agent_message entries in chronological order without a shown/total count. These are concrete scope-label mismatches, not evidence of lost raw events. UX owns the bounded navigation correction.
- Recommended exact shown range/total and written ordering, keyboard Older/Newer controls only when records exceed the page size, and no infinite scroll or automatic focus movement. Latest messages should explicitly say 'Latest12 ofN agent messages'; agent_message records can target everyone as well as a named agent.
- Count retained `state.timeline` entries, not raw events: invalid spawn records can return before logging. Timeline text is a readable projection of Event.text; tool arguments/results may be shortened to120 characters with an ellipsis. Keep full-payload availability in Raw events clear instead of claiming complete source text in timeline summaries.
- Primary guidance supplied by research: [GOV.UK pagination](https://design-system.service.gov.uk/components/pagination/) supports bounded pagination where appropriate; [WAI feed pattern](https://www.w3.org/WAI/ARIA/apg/patterns/feed/) shows focus/position obligations for automatic loading. This small history browser does not need infinite loading.
- Shared existing disclosure/button typography should suffice. Flagged existing .ev grid last column1fr/long-token wrapping as a browser test target, not a confirmed overflow defect; no speculative CSS change made.
- Acceptance for UX/root: empty/single/exact-page/one-over-page/multiple-page cases; oldest and newest retained entries reachable; visit every ordinal once with no boundary duplicate/skip; preserve agent/type/timestamp metadata; keyboard page controls, visible focus and stable selected page; theme geometry and390px long-ID/body wrapping. Ensure live feed remains bounded and no full-history serialization occurs on idle polls.
- Next bounded experiment: ask a scientist to find the first tool call and then a named later exchange in a synthetic long history. Record navigation ambiguity and mistaken assumptions about shortened text before adding filters. This worker changed only the log; no browser/app/service action or newly measured performance claim.

## 2026-09-20: Pass 11 request-receipt export review

- Reviewed actual RunRequest fields and saved-record ownership. Recommended optional Request receipt disclosure with identifiable local result ID and exact submitted question, followed by an explicit JSON download. A saved selector preview must export that selected record rather than the currently open report, and filenames should distinguish local records even when backend run IDs repeat.
- Scope copy recommended to UX: 'Saves this record’s submitted question, carried context and requested settings. Source file contents and the full model prompt are not included.' Keep known input metadata separate from file bytes, requested configuration separate from any backend-reported configuration, and bounded carried context labeled as generated prior context. Results are outside a request-only receipt.
- Recording requests describe playback, not the historical model invocation. Preserve submitted versus recorded-question distinctions if both exist; unknown values should remain absent/explicitly unrecorded rather than synthesized. No extra confirmation, general privacy warning, quality badge or reproducibility claim is needed.
- Research basis: [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) distinguishes an intended plan from actual activity; [PLOS reproducibility rules](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285) describe inputs, parameters, code and workflow beyond this minimal receipt. The export is not an archive-restoration or full reproducibility bundle.
- Acceptance for UX/root: compare downloaded JSON with the owner request snapshot for current, saved, follow-up and recording cases; preserve Unicode and literal strings; edits to the next draft do not alter the receipt; missing fields remain honest; no source bytes/results sneak into export; download alone does not submit/open another run or change selected result. Native disclosure/button keyboard focus, 390px wrapping and theme geometry use existing styles.
- Next design experiment: ask a scientist what they could and could not reconstruct from the saved receipt before viewing its contents. Refine the scope line if they expect source files, model outputs or exact execution restoration. No CSS/app/browser/service changes or test-execution claim from this log-only review.

### Morning cutoff closeout

Final suite passed 313 tests. Receipt preparation and correct current-owner text
were observed before interruption, but actual downloaded bytes and receipt mobile
layout were not verified. Earlier pass-specific browser checks remain recorded
above; do not extend their scope to the new receipt. Automation paused after the
cutoff; no new design iteration started. Frontend initial page restored on 8502.
