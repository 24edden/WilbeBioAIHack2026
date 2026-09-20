# Overnight research and iteration

Updated in pass 11: 20 September 2026. This document contains research, proposals
and implementation status reported by the coordinating task. No scientist testing
or model-quality result is implied. The root task owns browser verification.
Subsequent passes should update the status column rather than duplicate this list.

Morning closeout: automation paused after the cutoff. Final suite passed 313
tests. Pass-11 request receipts are implemented and covered by automated tests;
actual browser download verification was interrupted and remains outstanding.
No new iteration is scheduled. See [morning summary](overnight-morning-summary.md)
for completed work and release limitations. Proposed experiments below remain
proposals, not promises that they ran overnight.

The strongest direction is a workbench in which a scientist can **inspect a claim,
identify its limit, then choose the next question**. The existing four stages,
source-linked findings, Weak points, persistent draft, optional voice and explicit
Start already provide the foundation. The next iteration should connect these
pieces and reduce waiting, rather than introduce another crowded dashboard.

## Evidence behind the direction

- Microsoft's human-AI interaction guidance recommends making correction and
  refinement easy and giving users system-wide control. For TRACE this supports
  an editable follow-up draft, clear submitted-versus-next question labels, and
  persistent voice/model preferences. This is a design inference, not evidence
  that TRACE improves productivity. [HAX: efficient correction](https://www.microsoft.com/en-us/haxtoolkit/guideline/support-efficient-correction/),
  [HAX: global controls](https://www.microsoft.com/en-us/haxtoolkit/guideline/provide-global-controls/).
- Scientific-software usability guidance recommends early feedback from intended
  users, familiar structured input/output, and interfaces that stay comprehensible
  as data grows through aggregation or partial views. Our inference: show the
  conclusion immediately and open expensive detail only when requested. A real
  scientist walkthrough still matters; agent reviews cannot replace it.
  [List, Ebert and Albrecht, PLOS Computational Biology, 2017](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005265).
- Immediate tips must remain readable when the pointer moves onto their text,
  work from keyboard focus, and be dismissible when they obscure content. Status
  changes should be available to assistive technology without stealing focus.
  Respect reduced-motion preferences for optional animation. These are specific
  interaction checks, not a claim that the whole app conforms to WCAG.
  [W3C hover/focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html),
  [status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html),
  [interaction animation](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

The [judging rubric](../Context/judgingCriteria.md) weights scientific relevance,
effective NVIDIA/OpenAI use, execution, originality and reproducibility equally.
These UX changes mainly support relevance, execution and presentation. They do not
establish a working vendor integration; verify that separately against
[tooling context](../Context/tooling.md) and the actual release.

## Ranked ideas

Value and wow are prioritization judgments from 1 to 5, not user-study results or
predicted judge scores. Effort is a rough bounded implementation estimate and
excludes domain validation. Status distinguishes implemented portions from proposals.

| Rank | Idea and visible interaction | User value / demo wow | Effort and evidence | Status / dependency |
|---|---|---|---|---|
| 1 | **Make a weak point actionable.** Select a limitation and choose Draft a follow-up. Show the original question, the selected gap and requested evidence in an editable draft. | 5 / 4 | 1–2 h; HAX correction; existing `weak_points.items` supplies rationale, `next_evidence` and references. | Implemented and verified locally in pass 2. Separate editable suggestions preserve prior drafts and require explicit submission. Missing evidence remains missing. Not deployed in this pass. |
| 2 | **Open detail when it is useful.** Results show the conclusion and counts first; only construct large event/provenance views when opened. Paginate long finding lists while keeping totals and full export available. | 5 / 3 | 1–3 h; PLOS usability and the concrete costs in `ux-latency-audit.md`. | Raw events and large reference panels implemented and tested; root verified isolated Raw events opening in browser. Pagination and lazy rendering of every result tab remain proposed. |
| 3 | **Follow the argument that changed.** Select a revision to reveal the actual preceding challenge and opening beside it. Keep supporting/challenging skill badges and directed message links. | 4 / 5 | 2–4 h; current discussion `id`, `reply_to`, `phase`, text and assumptions are enough. | Implemented and locally verified in pass 3. Native disclosures show exact earlier arguments and reject invalid links. Keyboard, narrow-layout and theme checks passed. Not deployed or scientifically validated. |
| 4 | **A compact run receipt.** One line identifies the submitted question, execution mode, team and status. Expand for exact reported configuration and a JSON download. | 5 / 3 | 1–3 h; current request/config/events; structured output supports reproducibility. | Pass 11 selects a bounded request receipt download; implementation/verification pending. Requested settings must remain separate from reported execution. A complete reproducibility bundle still needs input identity and code/config provenance. |
| 5 | **Inspect the weakest link.** A weak-point reference opens its actual finding and available source record together. The scientist can traverse limitation → claim → evidence without copying IDs. | 5 / 4 | 2–3 h; weak-point `finding_ids` and finding provenance exist. | Implemented and locally verified in pass 4. Exact IDs, allowlisted stance and attached records are preserved. Large References panels load on demand; inner finding disclosures toggle locally. Supplied excerpts remain unverified; no deployment. |
| 6 | **A mechanism worksheet.** Put two proposed explanations next to each other: observed evidence, assumptions, conflicting observations and a measurement that would distinguish them. | 5 / 5 | 3–6 h for a clearly labelled curated synthetic worksheet; more for editable persisted artifacts. | Deferred after pass-3 review. Requires structured context and domain review; current workflow graph and stance fields cannot supply causal links. Prioritize inspecting existing evidence first. |
| 7 | **An honest model comparison explorer.** Select a frozen case and compare artifact/behavior pass, abstention, errors, time and reported tokens across models. Click a failure to inspect its trace. | 4 / 5 | 3–5 h for displaying existing eval JSONL; live comparisons require available providers and a fixed experiment. | Proposed. Mock results remain software checks, missing token usage is unknown, and causal/biological validity is not currently scored. |
| 8 | **Active waits without losing control.** Stable loading surfaces, real phase labels, elapsed time and accessible status accompany navigation/cancel. Only actual events animate message travel. | 5 / 4 | 1–3 h for remaining gaps; W3C status/motion and current latency audit. | Browser-owned local submission clock implemented and locally verified in pass 5. Quiet ticking, lifecycle, theme, narrow layout and separate replay time passed checks. It does not measure provider health or remaining work; not deployed in this pass. |
| 9 | **A readable evidence scene.** Show a lab timeline, supplied image or small mechanism graphic beside its source/context, with a visible illustrative label where relevant. | 3 / 5 | 2–4 h for one already available structured artifact; data-dependent. | Proposed. Avoid generic generated bacteria imagery that could imply patient-specific microscopy or pathogen identification. |

## Two changes to finish first

**A. Lazy supporting records: completed bounded first pass.** Raw events and panels
with more than 12 combined supporting records now defer preparation until opened.
Small panels keep browser-local switching. A synthetic 1,000-event test verifies
that the closed raw panel does not iterate or serialize its contents; opening
retains all records. The root's browser check confirmed Raw events opened without
rerendering the surrounding page. The combined suite reported 186 passing tests.
This is evidence of avoided work, not a measured provider-latency or 50-user
performance result. Result tabs and long finding lists still render eagerly.
See [UX iteration log](overnight-ux-log.md).

**B. Weak point to next draft: implemented and verified locally.** A button prepares
a separate editable suggestion from the selected limitation and original question.
Preparing it does not start a run or replace another draft. The scientist can edit,
discard or explicitly run the suggestion. The completed report and its drafts
remain available in the saved result. Verification details appear below; this pass
did not deploy the feature.

**Help tips: implemented with bounded verification.** The design worker removed
the dead gap, enabled pointer interaction with the tip, and added browser-local
Escape dismissal that retains focus. Theme help now has a 28px target. Lifecycle
tests passed; root observed instant display, Escape dismissal and retained focus
in the browser. Root also moved the pointer from the trigger into the tooltip and
confirmed the hovered text stayed visible; clicking outside hid it. Both themes
retain shared geometry. These are local interaction checks, not a whole-site
accessibility certification.

## Pass 2: weak-point drafting interaction

The existing Results follow-up submits a new run using the prior request's evidence
and configuration. The helper marks prior claims as quoted context, not new
measurements. A recorded case takes a separate simulated idea-review route and
does not reanalyze the original files. Preserve these semantics while making the
entry point easier to discover. Code basis: `frontend/app.py` Results branch and
`frontend/ui/followup.py`.

Recommended copy:

- Button: **Draft a follow-up**. Avoid Resolve, Verify or Find evidence because a
  draft does none of those things.
- Editor label: **Follow-up question**, with the selected weak-point title nearby.
- Helper: **This drafts a question using the evidence already in this run. It does
  not add the requested evidence.** For a recording, retain the existing explicit
  explanation that a follow-up reviews saved context with simulated agents.
- Suggested prompt shape: **Revisit [selected limitation]. What can the existing
  evidence establish, what remains unresolved, and how would [requested evidence]
  help distinguish the explanations?** Do not insert a claim that the proposed
  evidence exists. Missing `next_evidence` should yield a general request to name
  the needed evidence, not the literal placeholder text.
- Keep **Run follow-up** as the separate submit action. An existing typed draft
  should remain available; use an explicit replacement/append choice or present
  the suggestion separately before applying it.

These are TRACE-specific applications of the already verified HAX correction and
global-control guidance above. They support correction and deliberate user action;
they are not evidence that the generated follow-up is scientifically useful.

| Acceptance check | Required observable behavior |
|---|---|
| Drafting has no execution side effect | Selecting a weak point and preparing/editing its suggestion makes zero upload, investigate or model calls. |
| Previous work stays intact | The completed report, submitted question and evidence snapshot stay unchanged; any existing typed draft survives unless the user explicitly replaces or appends to it. |
| Context has the right identity and meaning | The selected title/rationale and requested evidence are accurately carried as unresolved context, with the right originating run/item. Missing fields are handled plainly. |
| Submission stays deliberate | One explicit Run follow-up starts one job using the reviewed text. Merely opening a panel, navigating, switching theme or rerendering cannot submit. |
| Evidence status stays honest | No new evidence is claimed or attached by drafting. Recorded cases retain their simulated-review disclosure and do not claim source reanalysis. |
| Recovery is straightforward | The scientist can edit or discard the suggestion, return to the current result and choose another weak point without losing prior work or accidentally starting a run. |

Status: implemented locally. The UX worker's 36 targeted tests passed. Root's full
suite now reports **192 passed**, including help lifecycle checks in pytest. In
the actual browser, root preserved an existing manual follow-up, prepared the
causal-limitation suggestion, edited it, and explicitly ran it to obtain a new Demo
result. Reopening the original saved report restored both drafts. This verifies
the local interaction and state preservation; it does not establish improved
scientific reasoning or live-model performance. No deployment occurred in this
pass, so rehearse the sequence on the release used for the presentation.

**Pass-3 implementation: readable reply context, verified locally.** The earlier
opaque `reply_to` caption now has a native disclosure naming the exact earlier
turn, agent and phase. It shows the complete recorded argument, source ID, assigned
perspective and order in the reply chain. Invalid, missing, duplicate, self,
cyclic, forward and legacy links receive plain explanations without a substitute
argument. Original assumptions, questions and provenance remain accessible. This
uses existing discussion data without a new endpoint or model request; it does
not claim the revision is more correct. Stable finding-ID navigation was the next
step at that point; pass 4 below completed it by retaining the previously omitted
IDs in the normalized `Finding`.

## Pass 3: make checking easier, not just more elaborate

Fresh primary-source research distinguishes useful inspection from persuasive
explanation. In five studies using a maze task and simulated AI, Vasconcelos and
colleagues found that the effort and benefits of inspecting explanations affected
overreliance. This supports a hypothesis for TRACE: put the exact related claim
and source close to the user's question so verification takes less work. It does
not demonstrate a benefit in scientific research, which their study did not test.
[Vasconcelos et al., CSCW 2023](https://arxiv.org/abs/2212.06823).

Buçinca and colleagues tested cognitive forcing designs with 199 participants.
The interventions reduced overreliance relative to simple explanation interfaces,
but the most effective designs received worse subjective ratings and benefits
varied with participants' motivation for effortful thought. Our inference is to
offer convenient, optional inspection first; do not add compulsory confirmation
screens or forced delays to every finding. Neither study implies that an animated
debate or more explanation makes a conclusion correct.
[Buçinca et al., 2021](https://arxiv.org/abs/2102.09692).

Microsoft's explanation guideline also cautions that explanation can inflate
trust and that content and design affect whether it helps. This reinforces a
specific copy rule: call a turn a revision or reply, not an improvement or proof.
[HAX explanation guidance](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-why-the-system-did-what-it-did/).

For the current reply feature, use a direct disclosure such as **Argument this
responds to**, optionally including the resolved turn number and phase. Display
the original text, agent and assigned perspective. Missing, ambiguous or self
references must not silently resolve to a nearby argument. A direct parent view
avoids recursive cycles; any future chain needs an explicit bound. Opening it must
not change the run or call a model. W3C's disclosure pattern specifies keyboard
Enter/Space activation and an exposed expanded state; use native semantics and
verify the browser interaction. [W3C disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/).

Acceptance checks sent to the UX worker: preserve exact text; resolve only the
explicit ID; handle missing/duplicate/self references visibly; open without any
request or mutation; retain keyboard toggle/expanded state; keep assigned support
or challenge separate from correctness.

Pass-3 verification: the worker reported 51 targeted tests passing; root's complete
suite passed **210 tests**, with two existing dependency deprecation warnings.
In the browser, root verified the exact earlier challenge text and unchanged help
node IDs when opening the native disclosure, confirming no surrounding page
rerender. Enter closed and Space opened it while focus remained on its control.
At a 390px viewport, the disclosure had no horizontal overflow. Width, height and
open state stayed unchanged across theme switching. These are local interaction
checks; this pass did not deploy the feature or evaluate scientific/model quality.

### Three concrete refinements for the next passes

These extend the ranked backlog instead of adding another general wish list.
Effort and value are engineering judgments, not measured outcomes.

| Next order | Refined interaction and current friction | Smallest change and check |
|---|---|---|
| 1: exact evidence behind a weakness (refines idea 5) | Weak points list opaque finding IDs; findings are sorted by heuristic confidence and omit the backend's stance. A scientist cannot readily identify the specific opposing claim. | Retain `finding_id` and allowlisted `stance` already emitted in `app/agents/base.py`, then reveal exact matching claims and their existing provenance within the weak-point reference panel. Label stance relative to the question; do not call it independent evidence. About 1–3 h. Test known, missing, duplicate and legacy IDs plus zero network calls on inspection. |
| 2: pin two findings for comparison (new interaction) | Even with direct references, comparing distant findings requires remembering one while scrolling to another. | After stable IDs exist, let the scientist pin at most two findings and inspect their text, stance and sources in one optional panel. Use stacked cards on narrow screens. No generated winner, merged confidence, or assumed contradiction. About 2–3 h. Verify exact identity through filtering, clear selection and run changes; unknown relation remains unknown. |
| 3: show what changed in a follow-up (refines idea 4) | The session retains both requests, but the user has to infer whether the question, workflow or evidence selection changed when reopening previous results. | Compare the saved parent/child `RunRequest` question, selected mode, sample flag and config in a compact disclosure. The parent run ID already travels in context; history stores copied requests. Say Evidence selection reused when appropriate, not Data verified unchanged: server sample contents and provider defaults are not hashed here. About 1–2 h. Handle an expired parent as unavailable and never reconstruct a missing request. |

Refinement 1 was selected for pass 4. Its data is already in the event
payload and the weak-point contract already refers to it. This is a frontend
normalization and lookup change, not a new scientific inference or endpoint. The
tradeoff is a small state-model change and explicit handling of older recordings;
that is now justified by the completed follow-up path's need to inspect its source.

**Challenge to the earlier mechanism worksheet idea:** defer its implementation
tonight unless the teammate supplies a reviewed, structured example. Current
`Finding.stance` only describes a finding's relation to a hypothesis; it is not a
causal edge. A polished mechanism diagram would otherwise add apparent authority
without adding checked context, interventions or a model of confounding. Keep the
causal-grounding question in the existing limitation and follow-up instead. This
trades some visual novelty for a complete, inspectable evidence path. Revisit the
worksheet when its domain/context and artifact contract are available, rather
than deriving it from agent colors or agreement.

## Pass 4: traceability is the start of checking

The pass-4 implementation preserves the backend's `finding_id` and `stance`, then
opens the exact referenced claim and its attached provenance from a weak point.
The reference should become easier to inspect without acquiring a stronger
scientific status merely because its ID resolves.

New source evidence supports that distinction. Liu, Zhang and Liang's historical
audit of four generative search engines evaluated both coverage of statements by
citations and whether each cited source actually supported its associated claim.
Fluent answers with citations still had substantial gaps. This is not a current
model ranking or an evaluation of TRACE; it motivates keeping reference presence
separate from claim support. [Liu et al., Findings of EMNLP 2023](https://arxiv.org/abs/2304.09848).

ALCE likewise evaluates fluency, answer correctness and citation quality as
distinct dimensions. Our inference is that the UI and future benchmark should not
collapse these into one evidence score. Merely displaying a quote or resolving an
identifier does not implement an entailment evaluation.
[Gao et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/).

W3C PROV-DM describes entities, the activities that use or produce them, and the
agents responsible. That distinction helps structure an inspection view: a
finding is an output, an agent produced it, and source records describe its
reported origin. This is a design analogy, not a claim that TRACE implements the
PROV standard or that lineage certifies a scientific conclusion.
[W3C PROV-DM](https://www.w3.org/TR/prov-dm/).

### Acceptance sent to implementation and design

- Resolve exact, unique finding IDs. Missing, duplicate, malformed and legacy
  references remain explicitly unresolved; no nearest-text or adjacent-finding
  substitution. Preserve the raw IDs so the scientist can inspect the mismatch.
- Show the exact claim, producing agent/role and allowlisted reported stance.
  Unknown stance stays unknown. Finding stance relates to the hypothesis; it is
  different from the Support/Challenge perspective assigned to a review agent.
- Preserve canonical `kind`, `ref`, `locator`, `quote` and any unknown metadata.
  Older fixtures use `source`, `file`, `pmid`, `line` or `sentence`; keep those
  available without silently inventing a conversion. Current `_provenance_line`
  uses legacy aliases and otherwise labels canonical records generically, so
  explicit field labels are a useful refinement in this pass.
- Name a supplied quote **Source excerpt supplied with this finding**. Escape
  source text and retain its content; do not claim it was independently fetched
  or verified. Locating a finding permits **Finding located in this run**, never
  **Evidence verified**.
- Keep native keyboard disclosure, long-text wrapping, shared theme geometry and
  the prior record/drafts intact. Opening should cause no provider request or
  page rerun. Original reference records remain accessible.

Status: implemented and locally verified. Root's complete suite passed **227
tests**, with two known dependency warnings. A fresh clinical-only Demo with mock
providers produced linked weak points. The large References panel prepared its
contents on demand; the inner native Inspect finding control then toggled locally.
The original CEA claim matched exactly, with its supplied file reference, line and
quote visible. Enter and Space retained focus, and all 16 surrounding tooltip
`aria-describedby` IDs stayed unchanged. At 390px, all six panels avoided
horizontal overflow and retained 44px summary targets. Measured width, height and
open state stayed unchanged across the two themes. No deployment, live-provider
run or scientific validation is claimed. At pass-4 closeout, the quiet-wait clock
was the proposed next experiment; pass 5 below takes it forward.

### Refined priorities after exact evidence inspection

The following preserves the pass-4 proposal and rationale. Pass 5 implements and
locally verifies the clock; the other ideas remain proposals.

| Order | Idea and bounded scope | Tradeoff / acceptance |
|---|---|---|
| 1 | **A clock that moves during quiet waits.** Current `render_stats` calls `RunState.elapsed_ms`, which uses the first/last event timestamp until completion. A dedicated browser clock could update once per second outside the activity fragment. | Higher priority than another comparison panel because all long runs can look frozen. Key it to the run/view identity and label the time honestly. It neither proves backend liveness nor removes the existing graph repaint cost. See the experiment below. |
| 2 | **Show when findings reuse the same recorded reference.** A small note can say that an identical source record appears in several findings, with links to those exact claims. | Group only explicit, equal source identifiers/locators with defined missing-value handling. Do not say different records are independent studies, or identical references are duplicate experiments. It may expose reuse without a new model request. Start with inspection, not a new score. |
| 3 | **Download one inspected claim with its context.** Export the selected claim, original question, run/claim IDs, reported stance and attached provenance as a small JSON or text file. | A narrower increment than a complete run bundle, useful for lab notes and reproducibility. Include only displayed/recorded data, identify missing fields and preserve mode labels. Do not call it a source-verified report or include unrelated evidence bytes. |

The clock needs a truthful boundary. If no actual submission-time anchor is
available, label it **Time in this run view**, not server runtime. A monotonic
client clock can interpolate between UI updates; terminal `wall_ms` remains a
separately labelled measured execution duration. Saved replay uses recording
time. MDN documents that `performance.now()` avoids system-clock adjustments but
that behavior during system sleep differs by platform. Do not claim exact elapsed
time across sleep/reload, or announce each second to screen readers.
[MDN Performance.now](https://developer.mozilla.org/en-US/docs/Web/API/Performance/now).

Feasibility judgment: a small stable clock component is a reasonable next bounded
pass; a complete browser graph renderer is not a prerequisite. Keep the existing
reliable graph repaint path until a separate rendering boundary passes its own
checks. Do not reintroduce the failed conditional paint merely to make a clock
appear efficient. Estimated clock scope is 1–3 hours including lifecycle tests,
not a promised implementation time.
`BackgroundRun` currently has polling timestamps but no submission anchor. A future
pass could record a monotonic start before its worker starts, pass a lightweight
elapsed-time descriptor to a persistent component outside `paint_live`, and label
it **Time since local submission**. A polling heartbeat is not that anchor and must
not reset it. This is a proposed design only; it provides no provider-health signal.

**Rejected or deferred:** do not create a green Verified badge or quality
percentage from the fraction of resolved references. It conflates identity with
support. Do not automatically retrieve missing quotes and present them as original
run provenance. The earlier pin-two-findings idea remains useful but moves behind
quiet-wait feedback and clear source identity; another panel could add navigation
before we know whether users need arbitrary comparison.

**Next experiment:** first use a synthetic set containing a valid reference,
missing ID, duplicate ID, missing stance, unknown provenance field and two claims
sharing a record. Check exact round-trip rendering and distinct unresolved states,
with no extra network calls. Then hold a mock source silent for ten seconds while
the proposed clock runs: the number must advance without restarting on rerenders,
navigation or theme changes; completion/cancellation must stop it; replay must
retain recorded time. Compare identities/render counts separately from latency.
An eventual scientist walkthrough should ask which claim and source a limitation
points to and whether that source has been independently checked. Until observed,
reduced verification effort remains a hypothesis, not a product result.

## Pass 5: clearer waiting without claiming progress

The selected implementation separates **Time since local submission**, terminal
**Measured execution time**, and **Recording time**. A persistent browser component
updates the first without waiting for a new provider event. Status: implemented
and locally verified. Root's full suite passed **240 tests**, with two existing
dependency warnings. This changes the display of waiting, not model speed,
provider health or durable job recovery.

Root's silent browser fixture advanced from 00:00:00 to 00:00:24 while the source
event count stayed at one and script passes stayed at three. Rerendering preserved
the anchor; theme changes preserved geometry; the counter exposed `role="timer"`
with `aria-live="off"`. Completion froze the local display at 44 seconds alongside
the actual measured 44.6 seconds. Unmount/remount retained that terminal state,
a new run reset to zero, and 390px layout had no overflow. In the main app, a fresh
clinical-only mock Demo showed local time of one second and measured execution of
1.7 seconds. Its saved Replay completed 27 of 27 events with **Recording time
1.7s** and no local submission clock. The temporary fixture was closed and its
server stopped. These are local interaction checks, not deployment, live-provider
validation, a provider-health signal or a performance benchmark.

### Fresh guidance and its limits

Microsoft's Fluent guidance recommends descriptive wait messages, keeping the
user's context, and limiting competing indicators. It reserves determinate
progress for measurable work. Applied here, one calm elapsed display can accompany
the actual reported phase; additional spinning surfaces add little information.
This is a design inference, not a measured improvement in TRACE's wait experience.
[Fluent Wait UX](https://fluent2.microsoft.design/wait-ux).

WAI-ARIA defines a timer as a changing time measurement and gives it an implicit
`aria-live="off"`. This supports a readable counter without speaking every second.
Meaningful terminal or phase changes should be conveyed separately, without
moving keyboard focus. These checks are narrower than a full accessibility audit.
[WAI-ARIA timer](https://www.w3.org/TR/wai-aria-1.2/#timer),
[W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

Browsers throttle timers and commonly suspend animation callbacks in hidden tabs.
Our implementation recommendation is therefore to calculate from an anchor,
rather than count callback invocations, and recompute on visibility return. The
earlier sleep/reload accuracy caveat still applies.
[MDN Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).

**Challenge to the selected solution:** a smoothly advancing clock can make a
stalled or disconnected request look healthy. It cannot justify Still processing,
a green health dot, a percentage, or Almost done. The explanatory text must say
what is timed, while the actual lifecycle determines phase and termination. The
user should still be able to inspect setup, prepare a draft and request supported
cancellation. A timer may also draw attention to a long wait; keep it secondary
and test whether people understand it before enlarging it for visual impact.

### Acceptance recommendations sent to the workers

1. Anchor to the local job's recorded start, not first event, last poll or component
   mount. Retain a unique local identity even before a backend run ID arrives.
   Repeated IDs, navigation and remounts must not reset or revive the wrong clock.
2. Update near once per second with tabular digits and stable layout. No Python
   callbacks or additional provider requests should be caused by a display tick.
   Keep the reliable graph repaint path unchanged in this bounded pass.
3. Stop at the actual local worker endpoint; ignore a stale active descriptor after
   termination. Keep cancellation pending distinct from cancellation completed.
   Show measured backend duration only when valid terminal metrics supply it.
4. Retain separately labelled recording time during replay, including pause and
   step. Never turn recording timestamps into a new inference-duration claim.
5. Check hidden-tab return, seconds/minutes/hours boundaries, rapid run replacement,
   cleanup, reduced motion, 390px layout and both themes. No per-second live-region
   announcement or focus movement should accompany ordinary ticking.

### Next bounded ideas, ranked after this clock

These were code-informed proposals at pass-5 closeout. The outcome notice was
selected for pass 6; the other two remain proposals.

| Order | Refined idea and observed friction | Smallest experiment and rejection boundary |
|---|---|---|
| 1 | **A quiet outcome notice where the scientist is working.** `poll_investigation` preserves a non-Investigation stage at completion, which protects draft editing; its ended-run caption only appears inside Investigation. An unlocked Results header and optional voice can make an outcome easy to miss elsewhere. | Add one inline outcome message with an explicit View results or View partial result action, based on the terminal status. About 1–2 h. Test completion, cancellation and failure while editing, with voice off: draft, focus and selected section remain intact. Do not force navigation, claim success for every terminal event, or add operating-system notifications. |
| 2 | **Fast Demo, readable Replay.** `DemoSource.mock_latency_scale` defaults to 0.25; deliberately paced mock calls remain an avoidable wait now that replay exists. This refines the latency audit into a visible setup choice. | Compare fast simulated execution with current pacing using the same question, config and evidence, then inspect the finished sequence through Replay. About 1–2 h for an explicit preset and checks. Preserve mock labels; do not silently change a rehearsed presentation or describe simulated speed as model performance. Check semantic outputs, allowing generated IDs/timestamps to differ. |
| 3 | **Reuse unchanged uploaded evidence on an explicit follow-up.** `BackendSource.events` uploads all bytes each time; the follow-up source delegates to it. This causes actual transfer/parsing work that another animation cannot remove. | With backend ownership agreed, test a session/endpoint-scoped ID cache: one upload, two separately requested investigations. About 2–4 h with invalidation checks. Changed bytes, endpoint or expired server IDs must invalidate reuse; do not cache model conclusions. Start with an instrumented local endpoint, not a claim of production latency savings. |

The first idea has the smallest contract change: normalized terminal status and
the existing Results destination already exist. It extends scientist control
without adding another dashboard. Evidence reuse can remove more real work, but
needs explicit cache lifetime and retry semantics from the backend teammate.

**Rejected or deferred this pass:** no invented ETA, heartbeat-as-health label,
automatic retry, or holding an available result until an animation finishes.
Do not add a second time-since-event clock yet: it may compete with elapsed time
and needs a clearly defined receipt-time anchor. Gating milestone reruns on spoken
updates is still worth investigating, but `render_voice_controls` currently returns
actions, not the browser's speech preference. It is not a safe one-line Python
condition until that preference contract is designed.

**Next test:** use a source that produces no events for ten seconds, then completes
or fails. Confirm that local time advances, event count stays fixed, no synthetic
phase/message appears, and the final display stops. Repeat while hidden and while
editing another section. Separately ask a teammate, What does this number tell you
about the model? If they infer health or fraction complete, revise the label or
prominence. No reduced waiting, increased trust or UX benefit is claimed before
observing that check. The conditional presentation beat is in
[the demo script](../Presentation/ux-demo-script.md).

## Pass 6: notice the outcome without losing the next question

Selected implementation: a persistent, outcome-specific notice when a run ends
while the scientist works in another section, with an explicit action to inspect
the result or activity. Status: implemented and locally verified. Root's complete
suite passed **264 tests**, with two known dependency warnings. No deployment,
live-provider test or scientific validation is claimed.

In a controlled fixture using the production UI, completion while the Question
textbox had unsubmitted text preserved its value, DOM identity, caret, focus and
selected section. Browser testing then caught a lost first View click on blur:
the newly inserted previous-result button changed the fragment's position.
Reserving that position with `st.empty()` fixed it. A fresh check confirmed the
first pointer click opened Results and Edit setup restored the exact draft.
Cancellation used stopped/partial wording without promising findings existed.
A fresh error fixture opened an error Results heading, not a green verdict.
At 390px the notice did not overflow; both themes retained its exact bounds.
The polite, atomic status markup and separate action were inspected, but actual
screen-reader announcements were not listened to.

Tradeoff: the existing 300ms fragment polling can continue after termination until
the next normal full interaction. Avoiding an automatic full rerun preserves the
active editor. This pass does not claim to remove that remaining idle work or
prove that repeated markup never reannounces in every assistive technology.

### Fresh source guidance and design judgment

W3C's status-message guidance calls for programmatically identifiable updates
without taking focus. It also warns that excessive announcements can make an app
too chatty. Our inference is one stable polite announcement for the final outcome,
not a repeated alert on every poll or rerender.
[W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

Fluent describes toasts as temporary, noncritical surfaces and says explicitly
dismissed information needs another place where it remains available. TRACE's
result and any interruption record should remain discoverable. A persistent inline
notice is therefore a better first experiment than a disappearing toast. This is
our choice for this workbench, not a rule that every async task needs a banner.
[Fluent Toast](https://fluent2.microsoft.design/components/web/react/core/toast/usage).

HAX recommends timing interruptions around the user's current task and considering
privacy when inferring context. Here the app already knows the selected section;
it can preserve editing without monitoring behavior or inferring attention.
[HAX: time services based on context](https://www.microsoft.com/en-us/haxtoolkit/guideline/time-services-based-on-context/).

**Challenge to the prior proposal:** retaining the selected section did not prove
that an unfinished draft or caret survived. Before this pass the completion branch
called `st.rerun()`, while the question was a native text widget outside the polling
fragment. The implementation now avoids that completion rerun outside Investigation,
and root checked uncommitted text at the terminal poll. The first-click bug above
confirmed why testing only a previously saved draft would have been insufficient.
A static notice that reappears after every rerender may still repeatedly announce
itself; screen-reader behavior needs an actual assistive-technology check before
claiming it is verified.

### Acceptance and copy sent to UX and design

| Recorded situation | Suggested short message | Explicit destination |
|---|---|---|
| Completed, without abstention | Results ready | View results |
| Completed with abstention | Finished without a conclusion | View results, with the reported limitation visible |
| Cancelled | Investigation stopped | View partial results only when present; otherwise the run record/activity |
| Terminal error | Investigation ended with an error | Available partial record or activity; do not imply success |
| Worker ended without a final result | No final result received | View activity, with the interruption visible |
| Unknown terminal status | Run ended | Available record, without interpreting the unknown state as success |

The message describes workflow outcome, not biological correctness. An earlier
recoverable agent error remains a warning and must not automatically override a
later explicit completed outcome. Cancellation requested is not yet cancelled.
Do not advertise results before the actual final event has been reduced.

- Keep one notice per local job identity, persistent until its record is inspected
  or superseded. Ordinary polls, theme switches and retained-history views must
  not duplicate it or revive an old job's action.
- Preserve the current stage, unsubmitted text, caret and scroll on appearance.
  An explicit View action follows the existing draft-save/navigation path; it
  never launches another investigation or silently changes the draft.
- Use written outcome and a descriptive action, not color alone. Keep a visible
  keyboard focus ring, 44px action target, readable wrapping at 390px and identical
  geometry across themes. Avoid a modal or new automatic voice announcement.
- Announce the outcome once through a polite status region without focusing it.
  Keep the actionable button outside text-only announcement content if needed;
  inspect both the semantic relationship and announcement behavior.
- Exercise completion, abstention, cancellation, terminal error, empty/interrupted
  streams, unknown legacy states and rapid run replacement. Use voice off and a
  long draft, then open the exact destination and return to the retained draft.

### Next small ideas from this code pass

| Rank | New or refined idea | Evidence, bounded change and next test |
|---|---|---|
| Completed in pass 6 | **One meaning for outcome across the notice and Results.** | Error, unknown and abstained verdicts now match the notice, including idea review. The full suite passed; a fresh browser error fixture confirmed an error heading instead of a green verdict. Original output remains visible. The fix concerns outcome presentation, not scientific quality. |
| Completed in pass 7 | **A receipt for the prior context actually carried forward.** | Preview before submission now shows included/available counts, omitted records, shortened fields and exact carried context. Local synthetic browser checks matched the displayed payload to the actual source-boundary request; manual, suggested and recorded paths have equality tests. It remains bounded generated context, not all prior evidence. Original evidence reuse is a separate contract. |
| Completed in pass 8 | **Distinguishable saved runs.** | Stable local-ID selection and ID-first option labels now distinguish repeated questions. The selected preview exposes the full question, mode, outcome and separate local/backend identities before explicit Open. Browser checks verified the exact record and its draft; five-result/session-only retention remains explicit. |

Outcome consistency was included in pass 6 rather than left as future work.
The context receipt was selected for pass 7: it exposes a consequential limit in
what the next agents receive. It and saved-run labels refine earlier
run-receipt ideas using already retained data. W3C recommends labels
that describe topic or purpose; our inference is that same-question runs need an
additional exact cue, rather than generated names or inferred differences.
[W3C headings and labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html).

**Rejected or deferred:** no disappearing-only notice, forced navigation, automatic
retry or celebratory success animation for all terminal states. No operating-system
notification permission prompt or background-resume promise: current workers and
saved results are session-local. The earlier Fast Demo choice remains useful, but
clear follow-up context now ranks ahead of it. Keep source-ID reuse with the backend
owner rather than smuggling a cache change into notification work.

**Next experiment:** the browser editing/outcome sequence above has passed; an
actual screen-reader check remains. Also ask a teammate which run ended, whether
it succeeded, and whether their new draft was submitted. Confusion should change
the copy/placement before adding more animation. For the next context-receipt
proposal, use over-limit findings/turns and compare its counts against the exact
submitted context. These are remaining checks, not observed usability results.

## Pass 7: inspect prior context before submitting a follow-up

Selected implementation: show the bounded prior-context payload before Run, with
included/omitted counts and shortened fields compared with the original record.
The payload remains generated prior claims to check, separate from the new
question and supplied evidence. Status: implemented and locally verified. Root's
full suite passed **272 tests**, with two existing dependency warnings. Tests cover
exact context equality for manual, suggested and recorded follow-ups. No live
provider, deployment or scientific/model-quality claim is made.

In root's synthetic browser fixture, the manual preview showed 8/10 findings,
6/8 weak points and 4/6 discussion turns. It separately showed 24/32 references
attached to included findings and eight references in omitted findings, with 42
shortened fields. The parsed DOM payload fingerprint matched the actual captured
`request.context`, comprising 26,751 characters in the canonical serialization.
An explicit Run follow-up completed through the synthetic source. The eighth
weak-point draft retained its selected limitation in the new question while the
prior-context list retained only the first six, with the same receipt counts.
Enter/Space toggled the native payload disclosure without a rerender. At 390px it
had no horizontal overflow and a 44px summary; dark-to-astral switching retained
exact dimensions and open state. These checks establish local UI/payload behavior,
not model use of context or improved scientific reasoning.

### Fresh evidence and the inference we draw

HAX recommends conveying how an action affects future AI behavior, including
before the action occurs. Our application is a preview beside explicit Run, so
the scientist can inspect what will accompany the follow-up without submitting it.
This does not require another confirmation or a mandatory reading checklist.
[HAX: consequences of user actions](https://www.microsoft.com/en-us/haxtoolkit/guideline/convey-the-consequences-of-user-actions/).

Liu and colleagues evaluated multi-document question answering and key-value
retrieval, finding that relevant information's position affected the tested
models' performance. This is historical research, not a finding about TRACE's
current providers. It supports a narrow caution: information being present does
not demonstrate that a model uses it effectively. A payload receipt must not
become an attention, quality or scientific-grounding score.
[Lost in the Middle, TACL 2024](https://aclanthology.org/2024.tacl-1.9/).

The W3C disclosure pattern specifies keyboard activation and exposed expanded
state. Our design inference is a compact always-visible summary with optional
exact detail, using the existing native disclosure behavior and focus treatment.
That preserves access without displaying a large serialized payload by default.
[W3C disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/).

**Challenge to usefulness:** counts alone can suggest completeness or overwhelm
the scientist with implementation detail. Eight included findings are neither
eight independent sources nor the eight most relevant findings. Current selection
is the first eight recorded findings, first six weak points and last four turns.
Describe that rule without implying a quality ranking. Give the exact payload an
optional disclosure; keep the prompt and Run action primary. Test comprehension
before adding selection controls or a context dashboard.

### Acceptance sent to UX and design

- Preview the same `context_for` result that submission uses; check exact equality
  at the source boundary. Reconstructing a similar-looking summary is insufficient.
  Opening/closing the preview must not submit, upload, call a model or alter drafts.
- Label it **Prior generated context for this follow-up**. It is not the full
  model prompt, provider instructions, fresh evidence or proof of model attention.
  Retain the separate recording limitation about original files not being reanalyzed.
- Use neutral Included, Not included and Shortened language. Make denominators
  explicit: references attached to included findings differ from references in
  the whole prior record. Do not count references dropped with a finding as if
  they were merely shortened fields in an included finding.
- Show character limits as characters, never tokens. Current caps are question
  4,000; conclusion 3,000; first eight finding claims 700 each; first three serialized
  references per included finding 600 each; first six weak-point kinds 100 and
  descriptions 500; last four discussion roles 100 and texts 600. Measure reference
  shortening after the same serialization as submission, preserving Unicode and
  literal text. Do not repair a truncated JSON-like string into a complete citation.
- Scope omission copy to **this prior-context payload**. A seventh selected weak
  point can still appear in the new question generated by `weak_point_question`;
  do not claim the whole request excludes it. User-pasted text is separate too.
- Compare against the actual parent snapshot. For a legacy payload with no parent,
  show the retained payload and Comparison unavailable; do not invent zero omissions
  or assume current caps describe how that historical payload was assembled.
- Retain keyboard access, wrap long literals at 390px and preserve disclosure
  state/geometry across themes. Compare empty, exactly-at-limit and over-limit
  records, restored history, new drafts and both follow-up entry points. UI checks
  do not establish improved scientific answers or model token savings.

### Next bounded ideas and priorities

| Rank | Refined interaction | Code basis and smallest next check |
|---|---|---|
| Completed in pass 8 | **Identify the saved run before opening it.** Refine the earlier saved-label idea with a selected-run summary containing its full submitted question, mode, exact outcome and stable identifier. | Implemented and locally verified using four synthetic records with identical questions. Selection leaves the current result untouched; explicit Open restores the exact selected record and draft. Missing reported metadata remains unknown. Browser evidence led to ID-first option labels so narrow menus retain distinct cues. |
| 2 | **Inspect one shortened original beside its carried text.** Make a shortening marker open that exact original field on demand, keeping omitted content clearly separate from the payload to send. | The current source state supplies original text; stable record order identifies the current snapshot's field. About 1–2 h after the receipt works. Test Unicode, serialized references and unavailable historical parents. No automatic Include all action, no silent context expansion and no nearest-text lookup. |
| 3 | **Export a follow-up request receipt.** Download the submitted question, exact carried context, mode and reported setup for a retained run. | A copied `RunRequest` already exists in history. About 1–2 h. Assert exported context equals the submitted context; exclude upload bytes and credentials. Label it a request receipt, not a full reproducibility bundle or the complete provider prompt. This refines prior export ideas around the newly visible payload. |

Saved-run identity was selected for pass 8: the receipt is useful only if the
scientist can tell which prior record they are inspecting. The selected-run summary
also gives a low-cost foundation for later exact parent/child comparisons. The
two other ideas remain optional; do not add both expanded panels to the default view.

**Rejected or deferred:** no context fullness gauge, token estimate from character
counts, all-evidence guarantee, mandatory acknowledgment or automatic model summary
of omitted text. Do not silently prioritize, reorder or increase the current caps
in a visibility pass. Choosing different context is a separate behavior change
that needs an explicit user control and evaluation. Larger context alone is not
evidence of better reasoning or causal grounding.

**Next experiment:** the over-limit synthetic preview/submission sequence and
selected-weak-point boundary passed local checks as recorded above. A teammate
walkthrough remains: ask what is carried forward, what is absent, and whether these
claims are new evidence. Track misinterpretation or unnecessary opening of detail
rather than asserting a usability gain. The next saved-run proposal should use two
identical questions with distinct outcomes and verify the correct preview/draft
is restored. Rehearse the context beat on the presented release; local verification
does not establish deployment.

## Pass 8: recognize the saved run before opening it

Selected implementation: identify a saved session record by question, mode,
outcome and stable identity, then show its full recorded question/details before
explicit Open. Selection should only preview; opening restores the chosen record
and its drafts. Status: implemented and locally verified. Root's full suite passed
**284 tests**, with two existing dependency warnings. No provider calls, deployment,
model-quality evaluation or real-user study occurred in this pass.

Root's production-UI fixture contained four synthetic saved records with identical
questions: Demo/complete, recording/abstained, Live/cancelled and Demo/error. Selecting
the cancelled record left the current report unchanged; Enter on Open restored
that exact record and its draft. Native ID details worked by keyboard, retained a
44px summary and avoided overflow at 390px. Dark/astral changes preserved their
exact dimensions and open state. Browser testing caught question-first option
labels being clipped until every item looked alike on a narrow menu. Labels now
start with a collision-safe ID cue, then outcome, mode and question; the final
screenshot retained distinct IDs/outcomes. ArrowDown/Enter selection then showed
the correct recorded-abstention preview. Full question/details remain available
before opening the record.

### Fresh primary guidance and limits

NN/G's recognition guidance recommends visible contextual cues and access to
recent history so users can identify earlier work without reconstructing it from
memory. Our inference is that identical question prefixes need more exact cues;
a second generated title would not reliably distinguish the underlying runs.
[Budiu, NN/G, 2024](https://www.nngroup.com/articles/recognition-and-recall/).

Microsoft HAX recommends retaining recent interaction context and making it easy
to refer to. Applied here, selecting history should preserve continuity between
the original request, its outcome and its follow-up drafts. This is design guidance,
not measured evidence that TRACE's new labels improve recall or task speed.
[HAX: remember recent interactions](https://www.microsoft.com/en-us/haxtoolkit/guideline/remember-recent-interactions/).

The FAIR principles associate findability with identity and descriptive metadata,
and accessibility with retrieval. A label can improve this local interface without
providing persistent storage or resolvable scientific identifiers. TRACE's session
record ID therefore must not be presented as a permanent archive identifier or
evidence of FAIR compliance.
[Wilkinson et al., Scientific Data, 2016](https://www.nature.com/articles/sdata201618).

**Priority challenge:** history contains only five retained results. A scientist
who runs one question may never use it, while the graph's 300ms repaint path and
earlier unresolved long-run stall affect active investigations. This is still a
reasonable bounded pass because repeated questions/models are part of the requested
workflow and the exact metadata already exists. Stop at recognition and correct
restoration; do not build search, generated summaries or a comparison dashboard.
After it, prioritize a measured responsiveness experiment over another ornamental
history feature. That ranking is a code/risk judgment, not a user-study finding.

### Acceptance sent to UX and design

- Select by the stable local session record ID, not question text or mutable list
  position. Preserve selection through saving/reordering and the five-record cap;
  if a selected entry was removed, do not silently open whichever now has its index.
- Keep written mode/outcome and a question cue in each option, with the distinctive
  ID first so narrow menus do not clip every distinguishing field. Shortened IDs
  must remain collision-safe. The selected preview exposes the full question and
  full IDs verbatim and escaped. This order incorporates the browser finding above.
- Name the **Session record ID** separately from the **Backend run ID**. Recordings
  may reuse a backend ID; missing backend identity stays Not recorded. Do not merge
  distinct local records just because their questions or backend IDs match.
- Distinguish configured source/connection mode from execution reported by the
  saved record. Live connection is not evidence that every provider was live.
  Requested model settings are not confirmed model identities; never fill missing
  historical fields from today's capability defaults or infer a timestamp from an ID.
- Use the existing outcome interpretation for complete, abstained, cancelled,
  error and unknown. Keep raw recorded detail available without a new quality score.
  Unknown metadata is preferable to a plausible generated description.
- Selection only changes the preview. Explicit Open restores the exact saved
  request/run/drafts, makes no model call, and leaves other records intact. Keep
  the current no-opening-while-active guard and the session-only retention caption.
- Check identical questions, common 100-character prefixes, short-ID collisions,
  blank/reused backend IDs, unknown modes/statuses, Unicode/markup, history-cap
  changes and saved follow-up contexts. Verify keyboard interaction, 390px wrapping,
  native disclosure state and both themes. Do not claim screen-reader speech from
  DOM checks alone.

### Refined next ideas and experiments

| Order | Bounded next step | Why this comes next and its check |
|---|---|---|
| 1 | **Measure a quiet run before choosing another rendering change.** Use a synthetic source that stays quiet for 60–90 seconds, while editing a draft and switching sections/themes. | The latency audit and earlier tab-stall note remain unresolved; the local clock does not fix them. Record render count per unchanged poll/event revision, input/cancel/navigation responsiveness, and draft/scroll retention. Keep waits observable in short checks; compare main-app Demo/replay behavior too. Optimize only the measured bottleneck, preserving the known constraint that skipping fragment painting can erase its content. This is a diagnostic experiment, not a claimed performance improvement. |
| 2 | **Compare the setup of the current and selected saved run.** Refine the earlier run-difference idea into one optional comparison of recorded question, mode and requested configuration. | Stable local identities make an exact comparison possible without another backend call. About 1–2 h. Test identical questions with one changed requested model/role; absent metadata stays unknown. Do not attribute a changed result to that setting or infer unchanged file content without hashes. |
| 3 | **Export the selected request receipt before leaving the session.** Refine the pass-7 export idea by making its ownership explicit in the selected-run preview. | History is intentionally limited and session-local. About 1–2 h. Download only that saved question, exact context, mode and recorded setup/identity; verify round-trip equality. Do not export raw input bytes or credentials, promise resumable execution, or call it the complete reproducibility bundle. |

Root selected the quiet-run measurement as the next bounded pass. It is an
evidence-gathering step before any client-rendering-boundary rewrite; it does not
authorize a random early return in the current paint path.

**Rejected or deferred:** generated run titles, backend-ID deduplication, a search
box for five entries, fabricated model/timestamp metadata, and a green Best run
badge. Neither repeated agreement nor completion is a scientific quality measure.
Persistent multi-user history remains a separate storage/access design; this UI
pass should not imply that closing the session preserves records.

**Next experiment:** restoration and narrow-menu distinction passed local checks;
a teammate walkthrough remains. Ask them to select the interrupted record, inspect
its full question, then open it and recover its draft. Check whether they can
explain the difference between session record identity and backend run identity
without help. Local browser tests do not establish that the cues are understandable
to scientists. Pass 9 below completed the quiet-run measurement and selected a
bounded help-identity correction. The verified presentation beat still needs
rehearsal on the exact presented release.

## Pass 9: measure quiet-run behavior before changing rendering

Selected work: measure a quiet synthetic investigation, distinguish repeated
construction from browser replacement costs, and choose only a narrow improvement
supported by evidence. The scoped live-help correction is implemented and locally
verified; root's full suite passed **288 tests**, with two existing dependency
warnings. Root's synthetic saved replay reached nine of nine events with a visible
graph and a distinct replay help scope. No deployment/provider test is claimed.

### Fresh primary guidance

INP measures click, tap and keyboard responsiveness through the next paint, not
the eventual result of asynchronous network work. Hover and scroll are outside
that metric. Consequently, measure input feedback, section/action completion and
worker duration separately. Automation-tool round trips are not browser input
latency; missing timing entries are not zero latency. A local scripted interaction
is not a field percentile or an audience-capacity benchmark.
[web.dev: INP](https://web.dev/articles/inp).

Streamlit documents that fragment-body elements are cleared and redrawn on rerun,
while external containers have different accumulation behavior. `st.empty` avoids
accumulating content, but the earlier observed disappearing-graph regression shows
that merely skipping a paint in this app is unsafe. Caching a pure transformation
and retaining a browser surface solve different problems. Neither follows
automatically from reducing Python calls.
[Streamlit fragment architecture](https://docs.streamlit.io/develop/concepts/architecture/fragments).

Browser guidance identifies layout work and large DOM updates as possible sources
of presentation delay, and recommends separating nonessential work from immediate
input feedback. This suggests investigating browser cost if Python construction
is cheap; it does not establish the cause of TRACE's earlier stall.
[web.dev: optimize INP](https://web.dev/articles/optimize-inp).

For live help, W3C says additional content should remain available while its hover
or focus trigger remains, unless dismissed or no longer valid. Stable scoped IDs
are the selected implementation aid, not a specific WCAG requirement or proof of
conformance. Actual focus behavior was observed through polling as recorded below;
this is not a complete accessibility audit.
[W3C hover/focus content](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html).

### Evidence that changed the first recommendation

The UX worker reported local pure-Python checks on a five-agent, 23-event fixture:
graph DOT construction about 0.0136ms/call, stats about 0.0034ms, and conversation
markup about 0.012ms. These narrow checks exclude transport, browser layout and
input handling; they are not end-to-end timings or a before/after speedup. In this
fixture they undermine the idea that caching graph text is the most useful next fix.

Root then measured a quiet synthetic browser fixture with seven events and five
agents. Over 41.109 seconds, paints and DOT builds increased from 55 to 192: 137
paints, about 3.33/s. Instrumented Python paint time increased by 813.263ms, about
5.94ms/paint; DOT time increased by 5.785ms, about 0.042ms/call including instrumentation.
These are Python-work measurements, not INP or visual response latency.

The design review found that 20 identical live-help renders generated 20 distinct
UUID-based ID/anchor strings. Root confirmed all three live help IDs changed while
the static research-question help ID stayed stable. After Shift+Tab focused the
network help and displayed its tooltip, a quiet poll moved focus to BODY and hid
the tip; the graph SVG remained present. This is direct evidence of lost keyboard
reading state, not merely redundant string construction.

Root selected stable explicit help identities scoped by result, live/replay view
and control. The implemented correction retains every existing paint and current
event handling. In the fixed quiet fixture, all three live IDs stayed unchanged;
network-help keyboard focus and its visible tip persisted across polls while
event count stayed at seven. Escape hid the tip without moving focus, and it stayed
dismissed across further polls and an injected message that changed event count
from seven to eight. The new message was visible and the graph remained present.
An open Agent details disclosure also survived quiet polling.

At 390px there was no overflow; help geometry and IDs stayed unchanged across
themes. The local clock advanced from 21 to 89 seconds while event count stayed at
seven and then eight, demonstrating why local elapsed time is not progress.
Releasing the synthetic terminal event opened Results with truthful synthetic
completion wording. Baseline navigation, typing and cancellation were available;
one cancellation completed cleanup and showed Investigation stopped. These are
local functional observations, not INP, a speedup, audience load or provider-health
measurements. No graph cache or skip-paint behavior was introduced.

### Measurement and acceptance sent to the workers

- Record event revision/count, empty batches, fragment/painter counts and wall-time
  interval separately. A repeated paint with no new event is redundant work to
  inspect, not by itself proof of visible lag.
- During a 60–90 second quiet local source, test typing, caret/selection, section
  navigation, theme changes and cancellation. Distinguish cancellation-request
  feedback from cleanup completion; the local clock still does not prove provider
  health. Compare fresh main-app Demo and saved Replay after the fixture.
- For the help correction, repeated identical renders keep the same scoped ID;
  distinct simultaneous surfaces keep distinct IDs. Every `aria-describedby`
  resolves to the right text. Changed text, new runs and restored/replayed views
  must not show a stale tooltip or link to another surface.
- Browser-check the actual trigger node, focus, hovered content and Escape
  dismissal through quiet polls. Move the pointer onto the tip. Keep graph content
  visible and real event changes current. Do not infer node retention from equal
  strings, or screen-reader behavior from markup alone.
- Preserve graph/record order, source-call counts, explicit navigation and the
  previous draft-retention fixes. No speculative early return, new provider call,
  artificial progress, or delayed result should accompany this small correction.

### Refined next ideas after evidence

| Order | Bounded idea or experiment | Trigger and limit |
|---|---|---|
| Completed in pass 9 | **Verify stable live-help identity before expanding scope.** | Scoped identities fixed the observed keyboard-focus/tooltip loss through quiet polls. Escape dismissal persisted through an injected event while the graph and new message stayed visible. All paints remain. This is a locally verified interaction-stability change, not a measured latency reduction. |
| 2 | **Attribute remaining browser replacement/layout cost.** Compare a quiet interval with a real event burst using the same fixture and controls. | Only if the sustained check shows lag or state loss: identify which subtree changes and record construction/transport/browser timing separately. A retained read-only activity component is a possible later boundary, not a decision made from paint count alone. Keep the working renderer until its replacement passes ordered-event, theme and keyboard checks. |
| 3 | **Pause the live view for reading, while collection continues.** | Only if a scientist cannot read messages during measured event bursts. A clearly marked snapshot with newer-event count and explicit Resume could preserve reading position without cancelling agents. About 2–3 h after proving that friction. Test ordered catch-up, completion and no dropped records; do not equate paused visuals with paused computation. |

**Rejected or deferred:** a graph-string cache as the default fix for this small
fixture, global slow polling that adds event/cancel lag, random skip-paint guards,
more decorative motion, or a broad frontend rewrite without attribution. A clean
short fixture run does not resolve every long-run failure, and lower Python work
does not establish improved INP or faster models.

**Next experiment:** the before/after quiet focus test and injected-event check
passed as described above, followed by the synthetic saved replay check. Investigate
further rendering only if a reproducible lag/state-loss case remains. A scientist
walkthrough can test whether burst activity is readable before selecting Pause
view. Keep any future timings tied to their measurement boundary and rehearse
the verified live-help beat on the presented release.

## Pass 10: make bounded activity history truthful and retrievable

Selected work: disclose the visible portion of activity and make every retained
timeline entry reachable in bounded pages. Implemented and locally verified in
pass 10; root's full suite passed **303 tests**, with two existing dependency
warnings. This changes inspection of recorded activity; it does not request new
inference or recover events that were never retained. No deployment or scientific
quality validation is implied.

### Concrete friction and priority

At the start of this pass, Results offered **Full activity timeline**, but its
renderer showed only the last 40 `state.timeline` entries, reversed for display.
The caption said Recent activity and earlier entries were accessible only through
Raw events JSON. The live conversation renderer showed the last 12
`state.conversation` messages without a visible count. These are different lists:
conversation contains agent messages only, while timeline contains the retained
human-readable activity entries. Neither denominator should be substituted for
the raw event count.

A read-only check using the repository's fixture loader and reducer confirmed
52 retained timeline entries in `sample_event_log.json` and 55 in
`sample_event_log_hypothesis.json`. Both have ten conversation messages and begin
with `run_started`. Thus the timeline gap already affects bundled recordings;
the conversation cap does not truncate these two cases. Root also observed a
synthetic 98-entry record showing only 40 entries in the existing browser view.

This is a stronger immediate correction than a new setup-comparison panel or
Pause live view. It resolves a demonstrated mismatch between a completeness label
and the available inspection path. Pause live view still needs evidence that
event bursts prevent reading; it would not by itself expose older entries in a
finished report. Reachable history is useful for execution and demonstration, but
does not establish better science or fulfill the rubric's vendor-integration
criterion. [Judging criteria](../Context/judgingCriteria.md).

### Fresh primary guidance and its limits

GOV.UK recommends pagination when splitting content improves performance or
usability, offers forward/back navigation, and warns that infinite scrolling can
cause keyboard problems. It recommends omitting pagination when only one page is
needed. Our inference is to keep short records simple and show an explicit range,
total and Older/Newer controls for longer records. This source does not establish
40 as the ideal scientific-workbench page size or prove a latency improvement.
[GOV.UK pagination](https://design-system.service.gov.uk/components/pagination/).

W3C's feed pattern describes the focus, loading, position and assistive-technology
coordination needed for automatically loaded content, and notes that feed
keyboard conventions are not well established. An accessible feed is possible;
it carries additional obligations. For retrieving a finished retained record,
ordinary explicit pagination is a smaller design than introducing infinite
scrolling. That is an implementation inference, not a prohibition on live feeds.
[W3C feed pattern](https://www.w3.org/WAI/ARIA/apg/patterns/feed/).

### Guidance sent to UX and design

- Name the order explicitly. Newest first means reverse recorded arrival order,
  not sorting timestamps to invent a different sequence. Equal or out-of-order
  timestamps must not move entries. Original entry ordinals make the visible
  window inspectable without claiming durable backend event identity.
- Show a range and total for retained timeline entries. Show All N or Latest 12
  of N agent messages for conversation. Handle zero without a misleading 1–0
  range. Do not describe the timeline as all internal reasoning or the full raw
  payload: `Event.text` shortens some tool results/arguments to summaries, and
  Raw events remains the detailed source record.
- The implementation uses at most 40 entries per page, with Newest/Newer/Older/Oldest
  controls on longer records. Keep the existing small-record disclosure simple;
  load the larger panel only when requested. Place controls with the visible
  history and retain ordinary keyboard operation and readable narrow wrapping.
- Scope the selected window by stable local result identity, not reused backend
  run IDs or timestamps. An explicitly selected older window should retain its
  recorded bounds when new entries arrive; returning to Newest is an explicit
  action. Replaced/shorter records need a valid clamped or reset range.
- Test 0, 1, 40, 41, 80 and 81 entries, repeated timestamps, arbitrary message text,
  different local records sharing a backend ID, and the existing replay path.
  Visiting all pages must expose each retained entry exactly once without skips
  or duplicates; changing the page must not call the source or start a run.
- Browser-check focus, exact entry boundaries, 390px layout and both themes.
  Keep the graph, existing draft and selected result intact. Test an incoming
  event while inspecting an older window if that path is supported. Bounded
  element count is a rendering property, not a measured responsiveness result.

### Local verification

Root verified that a closed large panel rendered no timeline rows. A synthetic
98-entry record was reachable in three pages: entries 98–59, 58–19 and 18–1,
containing 40, 40 and 18 entries. Their union contained all 98 entries without
duplicates or gaps. Keyboard Older, Oldest and Newest worked; page actions kept
outside help IDs unchanged and reran only the activity fragment.

At 390px, a 400-character identifier, Unicode and literal markup remained readable
without horizontal overflow; timeline geometry was identical across themes.
In the actual bundled 52-entry recording, the oldest page exposed its first 12
entries, including initial planner `reasoning.plan`, its tool result, a message
and `run_started`. Newest returned to entry 52 and a 40-row window. Inspection
used the recording without new inference. A visibly shortened tool summary also
confirmed the need for the copy directing readers to Raw events for full payloads.

These checks establish local retrieval and layout behavior, not a scientist study,
measured speedup, live-provider validation or deployment.

### Refined next ideas and rejected alternatives

| Order | Bounded idea | Evidence needed and scope |
|---|---|---|
| Completed in pass 10 | **Retrieve all retained activity in bounded pages.** | Root verified exact 40/40/18 pages for 98 synthetic entries, plus the earliest planner activity and return to newest in the bundled 52-entry recording. Keyboard, narrow layout, theme geometry and fragment-only page actions passed; no new inference. |
| Next small candidate | **Find a literal phrase across the retained activity.** | Only if the retrieval walkthrough still requires repeated scanning. `Message.text` supports exact substring matching without a model call. Search the whole retained list, not just the visible page; show match count and preserve original order/context. Roughly 1–2 h. Explain that a no-match result concerns retained display text, which may summarize a raw payload. |
| Alternative to search | **Filter activity by one recorded agent or event type.** | Useful if the actual task is following a critic or locating tool errors. Current message fields support this without inventing metadata. Roughly 1–2 h. Show matching/total counts and a clear reset; retain errors in the unfiltered default. Do not build search and filters together before a walkthrough shows which task is harder. |

**Rejected or deferred:** rendering every entry through Show all, infinite scroll,
model-generated summaries of omitted history, and making Pause view the next
default feature. The first two add volume or focus-state complexity; generated
summaries introduce new content when the task is exact retrieval. A direct
timeline-to-raw-payload shortcut is also premature without a verified identity
mapping: timestamps and agent names are not unique event keys. Keep Raw events
available rather than guessing a correspondence. None of these choices changes
the causal limits of agent discussion.

**Next experiment:** root completed the bundled-recording retrieval check. Ask a
teammate to use that recording to locate its
earliest planner decision, explain how much history is displayed, and return to
the latest entry without opening JSON or starting another run. Record wrong turns
and whether page controls or reading itself caused the effort. Then repeat with a
longer synthetic record and ask for a specific critic message. Choose literal
search or an agent filter only from that observed difficulty. This is a proposed
task-based walkthrough, not a completed scientist study or a usability score.

The optional presentation beat is now verified locally but still needs rehearsal
on the presented release. If used, replace a few seconds of the existing activity
inspection rather than extending the five-minute presentation or touring every
control. This pass did not deploy the feature.

## Pass 11: preserve a selected request beyond the session

Selected work: a JSON request receipt tied to one current or saved record, using
known submitted fields. Implementation and root verification are pending. The
receipt is a portable record of that request, not a restorable app session, the
complete provider prompt, an execution archive or a reproducibility bundle.

### Evidence and priority challenge

`save_result` stores separate copies of a completed run and its submitted
`RunRequest`, retaining the last five records in the session. Later edits cannot
be used to reconstruct the earlier submission. `RunRequest` includes question,
mode, requested config and exact carried context, as well as upload bytes,
connection endpoint and a local fixture path. This makes a small structured
export feasible, but makes serializing the entire object the wrong boundary.

The pass-7 context preview reveals exactly what was carried forward, but its
inspected text still belongs to a transient session. A receipt closes a concrete
preservation gap. By comparison, search/filter controls now lack an observed
retrieval failure after pass-10 pagination; no scientist walkthrough has occurred
to justify adding them. Export is not automatically the most important scientific
feature: verifying the release's real model/data integration and reproduction
path remains necessary. The receipt supports a limited part of the rubric's
reproducibility criterion, not proof that another team can reproduce a result.
[Judging criteria](../Context/judgingCriteria.md).

### Fresh primary guidance

Sandve and colleagues recommend retaining how each result was produced, including
exact parameters and inputs, software versions, scripts and relevant intermediate
results. A question/settings/context receipt preserves only some of this record;
it cannot substitute for actual input contents and the executed workflow. The
design inference is to export known submission facts now and state the missing
pieces explicitly, instead of calling a small JSON file reproducible science.
[Ten Simple Rules for Reproducible Computational Research, PLOS Computational Biology](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285).

W3C PROV distinguishes plans representing intended steps from activities and the
entities they used. Its model can associate an activity with the plan an agent
intended to follow; the plan alone does not describe that execution. Applied here,
requested model/role settings belong in one section and actual backend-reported
metadata in another. This is a conceptual distinction; the proposed receipt does
not claim PROV conformance or verified provenance.
[W3C PROV Data Model](https://www.w3.org/TR/prov-dm/).

RO-Crate specifies a self-describing metadata document and root dataset metadata,
and explicitly notes that its metadata document need not be an exhaustive file
inventory. Merely using JSON or adding a schema-version field would not make this
receipt an RO-Crate, nor would a standards label establish complete reproduction.
A richer package should be a separate contract if later required.
[RO-Crate 1.2 root data entity specification](https://www.researchobject.org/ro-crate/specification/1.2/root-data-entity.html).

### Minimal boundary recommended to UX and design

| Part | Include only what is known | Do not imply |
|---|---|---|
| Receipt identity | An explicit receipt schema version and the exact local record ID; a separately labelled backend run ID when recorded | Local identity is a globally resolvable accession or backend IDs are unique across recordings |
| Submitted request | Exact saved question and carried context, connection mode, requested sample flag and known requested configuration fields | Current drafts/settings are what ran; context is fresh evidence; a connection route proves live providers |
| Requested configuration | `task_mode`, `specialists`, and recorded reasoning/variant/embedding model overrides, without filling absent values from current defaults | A requested model was actually used, or omitted fields mean the latest default was used |
| Input description | Names and byte lengths of uploads attached to the saved request, if included; a recording label may use its filename without the full local path | Attached files were necessarily consumed; equal names/sizes prove equal content; the sample's bytes/version are captured |
| Reported metadata, if included | Separately labelled recorded question, status/abstention and known reported configuration values | Request and output questions are interchangeable, completion means scientific correctness, or reported configuration is independently verified |
| Scope | Plain exclusions and unavailable fields; preserve missing values instead of fabricating them | Import/resume support, complete source provenance, the full model prompt, or permanent server storage |

Exclude source-file bodies, backend endpoints/authentication, environment values,
absolute fixture paths, output findings/raw events and unsent drafts from this
bounded receipt. Do not infer missing model versions, run times or content hashes
at export. If an export timestamp is ever added, label it as export time. Preserve
the exact allowed values; if extra configuration fields are omitted, disclose that
projection rather than calling the whole configuration exact. This is a
purpose-specific boundary, not a promise to remove arbitrary sensitive text a
user may have included in their question or context.

Two current source details require explicit language. Demo may ignore attached
uploads when the sample flag is set, and idea review may use no files. Therefore
file metadata describes the request, not confirmed consumption. Recorded playback
may show a recorded question/configuration different from the submitted playback
request. Keep those separate rather than replacing the saved request with the
recorded output. Likewise, `FollowUpSource` constructs an execution question from
the question and carried context; this receipt is not every downstream prompt.

Recommended action: **Download request receipt**. A short nearby explanation is
enough: “Saves this record's submitted question, carried context and requested
settings. Source file contents and the full model prompt are not included.”
Do not add a modal, approval step or automatic publication.

### Acceptance recommendations

- Build from the exact selected record and its copied request, never the current
  draft, current model catalog or a recomputed `context_for` result. Missing
  historical requests stay unavailable. Preserve empty, null, Unicode and nested
  context values according to the versioned receipt schema.
- Decode the actual downloaded bytes and compare question/context/allowed config
  against that saved request. Cover manual and weak-point follow-ups, Demo,
  recorded playback and missing metadata. Keep requested and reported values
  distinct when they differ.
- Select two records with identical questions or repeated backend IDs and verify
  each export has its own local identity and exact data. Editing a draft, changing
  the theme or opening a different result must not contaminate prepared bytes.
- Verify exclusions with sentinel upload contents and endpoint/path values.
  Do not blindly call `asdict` on `RunRequest`. Give the file a stable safe name
  based on local record identity, not the research question or patient filename.
- Preparing/downloading a receipt must not open another result, clear drafts,
  submit a run or call the source. Check keyboard operation, 390px layout and both
  themes. Prefer preparation only when requested if serialization can be large;
  do not recompute a download through every live poll.
- Record which checks are code tests and which inspect browser download bytes.
  Seeing a download button or constructing JSON in a unit test alone does not
  prove the user receives the matching file.

### Refined next ideas and rejected alternatives

| Order | Bounded next step | Why and what to test |
|---|---|---|
| Selected, pending verification | **Export one selected request receipt.** | Existing copied request snapshots and session eviction make this concrete. Verify the downloaded JSON against the selected record and retain explicit scope limits. |
| Next small handoff candidate | **Document one checked synthetic receipt example.** | Once the schema is stable, pair a small example with its exact bundled case and a short field explanation. A reader should identify requested mode/context and the missing reproduction inputs using the JSON alone. This needs no new dashboard, model call or import feature; it remains proposed until an actual artifact is checked. |
| Later backend contract | **Capture the identity of inputs actually consumed.** | An input manifest could record content digests and parser/version identity at ingestion/execution, rather than guessing from current files during export. Agree the contract with the dataset/backend teammate first. Test identical filenames with different contents and changed sample versions. A digest proves content identity, not scientific validity or access to the original bytes. |

**Rejected or deferred:** calling the receipt a full reproducibility bundle,
including raw uploads or connection settings by default, inventing effective
model versions, regenerating prior context from the latest state, silently
sanitizing known fields while claiming exact equality, adding import-and-rerun,
and adding search/filter widgets without the still-missing walkthrough evidence.
The earlier broad compact-run-receipt idea is narrowed to a labelled portable
submission snapshot; the backend execution record remains a separate concern.

**Next experiment:** after local implementation, prepare one receipt from a
follow-up and another from recorded playback with differing submitted/recorded
questions. Decode the downloads independently of the browser and compare with
their frozen requests. Then inspect whether a reader can tell what was requested,
what was reported and what is missing for reproduction. Root can verify equality
now; the reader-comprehension check remains a proposed walkthrough if no teammate
is available. Do not convert artifact equality into a usability or science claim.

The conditional ten-second presentation beat should replace part of the existing
reproduction handoff. It becomes a verified-local beat only after root checks the
interaction and artifact; rehearse again on the exact presented release.

## Causal grounding and benchmarks

The worksheet in idea 6 should make the distinction between an observation, an
assumption, a model prediction and performed perturbation evidence explicit.
Reasoning and agreement can produce useful hypotheses, but do not supply causal
identification. DoWhy separates modeling assumptions, identification, estimation
and refutation; its documentation explains that robustness checks try to refute
observational causal estimates rather than prove them correct. TRACE can borrow
that discipline without claiming to implement DoWhy or estimate a causal effect.
[DoWhy paper](https://arxiv.org/abs/2011.04216),
[DoWhy refutation documentation](https://www.pywhy.org/dowhy/v0.13/user_guide/refuting_causal_estimates/index.html).

A useful synthetic scene is two explanations with the same observed outcome but
different predictions under a proposed test. Ask the scientist to inspect the
assumptions and choose what evidence would discriminate them. Removing a source
tests evidence sensitivity; it is not an intervention on biology. Keep proposed
experiments separate from performed ones. Detailed artifact fields are already in
[feature direction](feature-direction.md); use that contract discussion rather
than creating a competing schema overnight.

The benchmark recommendation in [model-evaluation.md](model-evaluation.md) still
fits. Terminal-Bench-Science 0.1, announced 27 August 2026, focuses on scientific
workflows and verifiable artifacts; its initial release has 70 tasks across five
domains. Its approach is a better conceptual match than a general terminal
leaderboard, but TRACE currently lacks the sandbox terminal executor needed for
those tasks. No official benchmark has been run here.
[Official release](https://www.tbench.ai/news/terminal-bench-science-0-1).

For evidence interpretation, consider a prespecified text subset of LAB-Bench;
its dataset covers scientific literature, databases, figures, tables and other
biology skills. If the teammate adds executable dataset analysis, BixBench becomes
more relevant because it evaluates multistep computational biology tasks with code
and notebook artifacts. These are distinct measurements, not interchangeable
scores. Keep external labels outside model context and report exact versions and
subsets. [LAB-Bench dataset card](https://huggingface.co/datasets/futurehouse/lab-bench),
[BixBench official repository](https://github.com/Future-House/BixBench).

## Next iteration protocol

Each scheduled pass should take one user-visible friction point, inspect current
code to avoid duplicating completed work, agree file ownership, implement one
bounded change and verify the relevant interaction. Record what changed, the
actual check, and remaining limitations. Update presentation wording only after
verification; keep browser checks on one agent at a time.

The morning walkthrough should cover these six tasks: ask a question from files;
understand which team will run; inspect a source; find a disagreement or evidence
gap; prepare a follow-up; replay activity without new inference. Record hesitation,
wrong turns and avoidable waits rather than assigning an unsupported usability
score. A short walkthrough by an available scientist should follow the agent
checks before making any claim about improved research experience.

Next research questions: Which source fields will the teammate's datasets supply?
Which artifact can be objectively checked? Which model integrations have an actual
successful trace? Which result detail is essential to the first decision? Those
answers should choose the next feature, not novelty alone.
