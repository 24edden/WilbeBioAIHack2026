# Scientist experience and demo script

Review date: 19 September 2026. This is a source-code review and a proposed
presentation sequence, not a new browser test. It feeds the combined
[demo script](demo-script.md). Effort estimates are rough engineering time for a
bounded prototype, not commitments.

The experience should make three things obvious: **what the scientist asked, what
the agents actually did, and what remains unresolved**. The most memorable moment
is a scientist inspecting a challenge and deciding what to investigate next.
Agent count and fluent speech are supporting details.

## What can be demonstrated now

The [deployment record](../infra/DEPLOYMENT.md) documents the earlier verified
staged interface, editable demo, persistent question and Weak points. The current
repository also implements background execution, cancellation, voice controls,
skill descriptions/icons and bounded idea review. Those newer features must pass
the final deployed browser rehearsal before the presenter calls them shipped.

| Present in current source | Exact user control or limitation |
|---|---|
| Four clickable sections, persistent question and copied submitted request | The next draft can change while the submitted run remains unchanged. This is not mid-run agent steering. |
| Task mode and evidence-specialist selection | Auto has visible routing rules. Explicit Evidence investigation exposes one to three specialist roles. Idea review uses its fixed five-role team. |
| Skills and alignment metadata | Roles describe executable capabilities. Support/Challenge are assigned perspectives, not a truth score or independent scientific evidence. |
| Directed discussion messages and revision | Supporter proposes, challenger responds, supporter revises, critic synthesizes. The research role inventories supplied records; it does not search the web. |
| Responsive background job, visible loading state and cancellation | One active run per session. Cancellation preserves partial findings; a browser disconnect is not an assured backend cancellation. |
| Weak points with rationale, next evidence and references | The backend assessment is shown unchanged. Missing assessment is visibly distinct from an assessment returning no issues. |
| Optional dictation and spoken stages | Recognized text is reviewed before applying. Voice cannot submit or cancel. Speech covers workflow cues, not research findings. Voice quality depends on available browser/device voices. |

The deployed CPU demonstration uses simulated providers. Running the real
orchestration in Demo is different from replaying a saved case, and neither proves
live model inference. Say which one is on screen once, before starting.

## Seven improvements, in priority order

All additions in this table are **proposed** unless explicitly called existing.
Protect the functioning upload, question, execution and result path first.

| Priority / idea | Why it helps; smallest useful interaction | Data/API boundary; rough effort |
|---|---|---|
| 1. A compact run receipt | Scientists need to know which question a result belongs to. Existing draft/submission separation is strong. Add a compact strip showing submitted question, input count, task mode, selected roles and run status. Expand it into the exact configuration; offer a download of the displayed run. | Current `RunRequest`, run configuration, files and raw events support a session export. Include mode, timestamps and available model identifiers; mark missing identifiers unknown. A reproducible input checksum manifest needs backend support beyond this first UI receipt. About 1–3 hours. |
| 2. Turn a weak point into the next question | A list of limitations should lead to a decision. Add “Use this in my next question” beside one item. Prefill the editable draft with the weak point and its requested evidence, then take the scientist to Question & agents. Never automatically start or claim the missing evidence exists. | Existing `weak_points.items` supplies ID, rationale, `next_evidence` and finding references. No new endpoint is needed for draft preparation. Preserve the original run and require explicit Start. About 1–2 hours. |
| 3. Show how an argument changed | A moving graph is difficult to read quickly. Beside an active Support → Challenge edge, show the opening argument, the challenge, and the actual revision as three labelled turns. The scientist can open the preceding turn directly. | Existing discussion `id`, `phase`, `reply_to`, `agent_id`, assumptions and references are sufficient. Resolve turn IDs in the UI; do not manufacture a model-generated “change summary.” Current network and discussion already exist; linked turn comparison is about 2–4 hours. |
| 4. Skill cards that explain their limits | Choose a team by what it can do. Show one recognisable icon per skill, a plain label, and one short scope statement, such as “Evidence review: inspect supplied records.” Keep alignment as a separate badge. This answers why an agent appeared. | Use `/capabilities` skill catalog and agent-spawn metadata. Current role cards and every skill chip have native SVG icons, including explicit catalog ID aliases. Optional scope descriptions require an additive catalog field; that remaining improvement is about 1–2 hours. |
| 5. Claim-to-source inspection in one place | A scientist should be able to inspect evidence without mentally resolving IDs. Opening a weak-point finding reference should reveal that finding, its source label and available file/line information together. An exact excerpt can be a later addition. | Frontend already holds findings and provenance: link these first, about 1–2 hours. Exact excerpt rendering requires a bounded source lookup contract and valid source identity; it is not available merely because a PMID or file ID exists. Allow another 2–4 hours for that separate contract and renderer. |
| 6. Honest progress with a visible next step | “Working” should tell the scientist what is happening. Keep the existing immediate loading state and responsive navigation; distinguish preparing evidence, agent work, critical review and cancellation cleanup from actual events. Show elapsed time, not an invented completion percentage or ETA. | Current lifecycle, agent statuses, timestamps and terminal metrics support this. Use text alongside motion, retain reduced-motion behavior, and never declare completion on the first finding. A clearer phase strip is about 1–2 hours. |
| 7. A quiet voice companion | Make voice feel conversational through timing and concise language. Preview and choose the best available voice before the demo; play one cue when planning starts and one when critical review begins. Keep microphone state obvious and stop speech immediately on request. | Current browser component already provides preview, voice choice, reviewed transcription, opt-in online voices and fixed stage announcements. No paid speech service is needed for this iteration. Additional prosody tuning/rehearsal is under 1 hour; consistently natural speech across devices would be a separately designed service, not a claim about the present implementation. |

The smallest next polish bundle is items 2, 4 and the first part of 5. They turn
existing backend structure into useful interactions with little architectural
change. Items 1 and 6 improve orientation. Item 3 is the strongest debate demo
enhancement if time remains. Avoid building all seven before a full rehearsal.

Do not frame the debate as agents battling until one wins. Frame it as a proposal
being challenged and revised. Colour, labels and directed edges can make the
exchange engaging without implying that persuasive language establishes truth.

## Five-minute working script

This sequence uses current implementation only. Proposed buttons above are not
part of the script. Rehearse with the exact release and projector dimensions.

| Time | Presenter action | Speaker line |
|---|---|---|
| 0:00–0:25 | Show Evidence with the sample ready. | “A scientist needs more than a plausible answer. They need to see which evidence was used, how it was challenged, and what is still missing. TRACE puts that investigation under their control.” |
| 0:25–1:00 | Select the interactive demo. Open the persistent question, use the default treatment-failure question, and continue. If voice has passed rehearsal, dictate a short synthetic question and explicitly apply the reviewed text. | “These are synthetic records, and this demonstration uses simulated model outputs. The question is editable. Voice is optional, and I review its text before it becomes my question.” |
| 1:00–1:40 | Select Evidence investigation. Show the specialist roster and its skills. Start. Point to the active graph and one message; if execution finishes quickly, inspect Agent activity in Results. | “I choose the relevant specialist team. The graph reflects actual role creation and messages. Each specialist works on its assigned evidence, and the critic checks the result.” |
| 1:40–2:25 | Open one result's provenance, then Weak points. Read one specific rationale and the requested next evidence from the screen. | “Here is the source attached to this finding. Now here is a weak point: [read the displayed issue]. TRACE makes that limitation inspectable and identifies evidence that would help resolve it. Multiple agents agreeing would not, by itself, establish causation.” |
| 2:25–2:50 | Open the persistent question and edit the next draft. Point back to the submitted question or current result. | “The question stays within reach. I can prepare the next investigation without changing the record of the one I just ran. Starting it is a separate, explicit action.” |
| 2:50–3:50 | Use Edit setup for another run. Enter “Evaluate the idea of testing two competing explanations for treatment resistance using a held-out dataset.” Select Review an idea and start. Inspect Support → Challenge messages, then the actual revision in Review discussion. | “A proposal needs a different team. The supporter develops it; the challenger receives that argument and questions its assumptions; the supporter then revises it. These colours represent assigned perspectives. This is structured proposal review, not a vote on scientific truth.” |
| 3:50–4:15 | Open assumptions/open questions for a discussion turn. Optionally point to Cancel if demonstrating a separately rehearsed longer run. | “The useful output is the assumption we can now test. The scientist decides what happens next. A run can also be cancelled, with the partial record retained.” |
| 4:15–4:40 | Hand off to the technical presenter or show the validated architecture/evaluation slide. | “The interface is separated from the backend by a small event contract, so our datasets and models can change without rebuilding the experience.” Follow with only the actually verified vendor and evaluation evidence. |
| 4:40–5:00 | Show the repository/reproduction reference and return to the result. | “Our demonstration records what the system did and where its conclusions stop. The next decision stays with the scientist.” |

The native voice should not speak over these lines. During the main presentation,
either enable one short rehearsed cue and pause for it, or leave spoken updates
off. A voice audition is more reliable than a claim that every device sounds human.

## Rehearsal and fallback

- Keep the five-minute path to two runs at most. Cut the second live run if the
  first is slow; use a clearly labelled captured idea-review trace only if one has
  actually been prepared. The existing saved-case selector does not imply that a
  review recording is available.
- If voice recognition fails or is unsupported, type the same question and say
  “The typed controls remain available.” Do not spend presentation time debugging
  the microphone. Never describe an untested device voice as a neural voice.
- If the network or model endpoint fails, identify the failure and switch to the
  interactive mock demo or an existing labelled recording. Do not present replay
  as fresh inference. Open a captured Results view when the graph is too fast to
  narrate; that is inspection of a finished run, not a paused computation.
- Before presenting, confirm the NVIDIA sign-in path with the presenter's account,
  choose a tested browser, preview audio, verify keyboard navigation, and check the
  graph and source text on the actual display. Keep the authenticated session open.
- Use an unsupported-hypothesis or one-specialist case as an optional question-time
  demonstration of abstention. Do not add a third live run to the main script.

## Evidence and judging fit

The [rubric](../Context/judgingCriteria.md) gives five criteria equal weight.
Inspectable sources and explicit uncertainty support scientific relevance;
responsive controls and a complete workflow support execution; the visible
challenge/revision sequence supports originality; an accurately labelled demo and
reproduction record support presentation. These UX choices do not independently
establish effective NVIDIA/OpenAI use. The technical script must show a verified,
necessary in-product integration. Brev hosting and build-time Codex alone should
not be used as that proof; see [tooling context](../Context/tooling.md).

Source basis: [architecture](../ARCHITECTURE.md), [integration contract](../INTEGRATION.md),
[feature direction](../Plan/feature-direction.md), [app flow](../frontend/app.py),
[layout](../frontend/ui/layout.py), [renderers](../frontend/ui/components.py),
[graph](../frontend/ui/graph.py), [skill catalog](../app/skills.py),
[icons](../frontend/ui/icons.py), and [voice](../frontend/ui/voice.py).

## Overnight additions, 20 September

These are short optional replacements in the five-minute script, not extra
segments to stack onto it. Research and implementation status are tracked in
[overnight ideation](../Plan/overnight-ideation.md). Rehearse against the exact
release; a proposal below becomes a demo line only after its interaction works.

| Beat | Speaker line | Demonstration requirement |
|---|---|---|
| User control, existing foundation | “This is the question the agents are answering. This separate draft is what I want to ask next. I choose when it runs.” | Show the submitted request and persistent draft without changing the completed record. |
| Actionable uncertainty, verified locally | “This missing evidence becomes a precise next question. I can edit it before starting another investigation.” | Local browser checks verified drafting, editing, explicit submission and restoration of the original report and both drafts. This pass did not deploy it; rehearse on the presented release. |
| Readable debate, verified locally | “Here is the opening proposal, the challenge it received, and the revision that followed.” | Exact earlier text, native disclosure without a page rerender, keyboard operation, narrow layout and theme stability passed local checks. Rehearse on the presented release; this pass did not deploy it. |
| Exact evidence inspection, verified locally | “This limitation points to this recorded finding and the source information attached to it.” | Exact CEA claim and supplied source details passed local browser checks, along with keyboard, narrow-layout and theme stability. Rehearse on the presented release; this pass did not deploy it. A resolved reference is not a verified claim. |
| Grounding, existing limitation | “The graph shows who communicated. It does not establish a biological cause. We inspect the evidence and the unresolved assumptions separately.” | Use the workflow graph, source references and Weak points already in the product. |
| Mechanism worksheet, future prototype | “These explanations fit the same observation. What measurement would tell them apart?” | Only use if a labelled synthetic worksheet with explicit assumptions and contrasting predictions is implemented. No claim of a performed experiment. |
| Responsive interface, clock verified locally | “This is time since I submitted the run here. I can still inspect my setup while I wait.” | Quiet ticking, terminal freeze, remount/new-run handling, themes, narrow layout and separate replay time passed local checks. Rehearse navigation and draft retention on the presented release; this pass did not deploy it. The clock does not establish provider health or faster inference. |
| Outcome notice, verified locally | “The run has ended, and my next question stays here. I choose when to inspect the outcome.” | Local checks preserved uncommitted text, caret/focus and section; the first View click opened Results and returning to setup restored the draft. Cancellation/error wording, narrow layout and theme bounds passed. Rehearse the presented release; this pass did not deploy it. |
| Follow-up context, verified locally | “Before I run this follow-up, I can inspect the previous claims it will receive, including what this context block leaves out.” | Synthetic browser checks matched the exact displayed context to the submitted request and verified manual/weak-point previews, counts, keyboard behavior, narrow layout and theme stability. Tests cover recorded paths too. Rehearse the presented release; included context is not fresh evidence or proof of model attention. |
| Saved-run recognition, verified locally | “These runs asked the same question. I can inspect which record I am opening before returning to its result.” | Synthetic browser checks verified selection without replacing the current result, exact record/draft restoration, keyboard details, narrow ID-first labels and theme stability. Rehearse the presented release. Session history is not permanent storage; Live connection is not proof of live model execution. |
| Earlier activity, verified locally | “This is one part of the recorded activity. I can open the earlier entries without starting another run.” | Root verified all 98 synthetic entries across three bounded pages and the earliest planner activity in the bundled 52-entry recording. Keyboard, narrow layout and theme geometry passed. Rehearse the presented release; this pass did not deploy it. Activity summaries are not complete raw payloads or internal model reasoning. |
| Request receipt, pending verification | “I can save this run's submitted question, context and requested settings beyond this session.” | First verify the downloaded JSON against the selected saved request, including differing requested/reported questions and all exclusions. Rehearse on the presented release. The receipt is not source-file contents, the full model prompt or a complete reproduction bundle. |
| Evaluation, existing limits | “We measure workflow behavior, failures and resource use separately. These mock checks do not establish biological accuracy.” | Show the actual frozen eval record; absent token usage stays unknown. Do not describe it as an official Terminal-Bench result. |

The strongest closing image is a source-linked limitation and the scientist's next
decision. If time is tight, keep that and remove the second run or voice flourish.
The research basis favors correction and control; it does not establish measured
usability improvement. [Microsoft HAX correction](https://www.microsoft.com/en-us/haxtoolkit/guideline/support-efficient-correction/),
[global controls](https://www.microsoft.com/en-us/haxtoolkit/guideline/provide-global-controls/).

### Twenty-second weak-point beat, verified locally

Action: open a displayed weak point, choose Draft a follow-up, and show the
editable suggestion. Stop before submission unless another run has been rehearsed.

“Here is a gap in the evidence. I can turn it into a follow-up, then edit the
question myself. This uses the evidence we already have; it does not fill the gap.
I decide whether to start another run.”

Allow about 20 seconds and time it during rehearsal. Root verified
the local sequence through an explicit Demo follow-up, then reopened the original
report with the manual and suggested drafts restored. The full local suite passed
192 tests. This pass did not deploy the change: rehearse on the presented release
before using this beat. Keep the selected item visibly an unresolved limitation,
not a solved task; these checks establish interaction behavior, not scientific
or model quality.

### Fifteen-to-twenty-second argument beat, verified locally

Action: open a revision's earlier-argument disclosure and point to the exact
challenge it references. Keep the current reply visible in the same context.

“This revision responds to that specific challenge. I can open the earlier
argument and compare what was said. These are recorded turns, not a score of
scientific truth. I can inspect the assumptions before deciding what to ask next.”

Time this during rehearsal on the presented release; this pass did not deploy the
feature. Root verified exact earlier text, Enter/Space behavior with retained
focus, no disclosure overflow at 390px, and unchanged dimensions/open state across
themes. The full local suite passed 210 tests. If the deployed release lacks the
feature, show the discussion in order and omit the linked-turn action. Do not
describe the revision as more accurate without separate evaluation. Research
motivates reducing inspection effort; it has not measured TRACE's effectiveness.
[Vasconcelos et al., CSCW 2023](https://arxiv.org/abs/2212.06823).

### Fifteen-to-twenty-second evidence beat, verified locally

Action: open a weak point's referenced-finding disclosure. Point to the original
claim, its reported relation to the hypothesis and one attached source record.

“This limitation points to this exact finding. I can inspect the claim and the
source details attached to it, without hunting through the report. That makes it
traceable. Whether the source actually supports the claim still needs checking.”

Time this during rehearsal on the presented release; this pass did not deploy the
feature. Root verified the original CEA claim and supplied file/line/quote in a
fresh mock Demo, lazy loading of the outer References panel, and local toggling of
the inner disclosure. Keyboard focus, 390px layout and theme geometry checks
passed; the full suite passed 227 tests. If the presented release lacks the
shortcut, read its reference records instead. Do not call this lookup a fact check
or evidence of better scientific accuracy. Citation presence and support remain
separate properties. [Liu et al., Findings of EMNLP 2023](https://arxiv.org/abs/2304.09848).

### Ten-to-fifteen-second waiting beat, verified locally

Status: implemented and locally verified in pass 5. Use this during an existing
wait, not as an extra segment or a reason to delay an available result.

Action: point to the local submission clock during a rehearsed
quiet interval, then inspect setup while preserving the next question draft.

“This shows how long it has been since I submitted the run here. It is not an
estimate of when the model will finish. I can keep preparing my next question
while I wait.”

Root verified a quiet fixture advancing from zero to 24 seconds with unchanged
source-event and script-pass counts, terminal freeze, remount/new-run handling,
theme geometry and 390px layout. The main app's mock Demo showed separate local
and measured time; saved Replay showed recording time without a local clock.
The full suite passed 240 tests. No deployment or live-provider check occurred.

Rehearse navigation and draft retention on the exact presented release. Show
recording time separately if switching to Replay, and identify a mock run as such.
Do not call the clock a provider heartbeat, progress percentage, performance win
or proof that computation continues. If the feature is absent or fails validation,
omit the clock line and retain the already verified control/inspection beats.

### Fifteen-second outcome beat, verified locally

Status: implemented and locally verified in pass 6. Replace part of the
existing wait/follow-up sequence with this beat; do not extend the five-minute path.

Action: while a rehearsed run finishes, keep editing a separate
question. Point to the notice, then explicitly open its result or activity.

“The run has ended, and my next question stays exactly where I left it. This notice
tells me the outcome. I decide when to inspect the record, and when to submit my
next question.”

Root verified uncommitted text, DOM identity, caret/focus and selected-section
retention. A first-click issue found in browser testing was fixed; a fresh retest
opened Results on the first click and restored the exact draft on Edit setup.
Cancellation/error presentation, 390px layout and theme bounds passed. Error,
unknown and idea-review abstention verdicts now match the outcome notice. The full
suite passed 264 tests. Polite atomic markup was checked; actual screen-reader
speech was not tested. Polling may continue until the next ordinary interaction
to avoid remounting an active editor.

Rehearse with the actual displayed outcome and release. For abstention, say the
run did not reach a conclusion; for cancellation or failure, identify the partial
record or activity rather than calling it a successful result. This is workflow
control, not evidence of scientific accuracy, durable storage or a completed
deployment. No live-provider validation occurred in this pass.

### Fifteen-to-twenty-second context beat, verified locally

Status: implemented and locally verified in pass 7. Use this in place of
part of the existing follow-up beat, without adding another run to the five-minute path.

Action: prepare a follow-up, point to one actual context limit,
and briefly open the exact prior-context payload. Stop before Run unless rehearsed.

“Before I run this, I can see the previous claims that will accompany my question,
and what this context block leaves out or shortens. These are claims to check,
not new evidence. I can inspect the text before deciding to continue.”

Root's synthetic browser preview showed 8/10 findings, 6/8 weak points, 4/6 turns,
24/32 references on included findings, eight references on omitted findings and
42 shortened fields. Its exact parsed payload matched the captured request, and
the explicit follow-up completed. The eighth weak-point draft preserved that
limitation in the new question while the context kept the first six. Keyboard,
390px layout and theme/open-state checks passed. The full suite passed 272 tests,
including manual, suggested and recorded context equality. No live-provider
inference or deployment was tested.

Only mention an omission or shortening actually visible in the chosen fixture.
This block is separate from the new question and any files reused by the workflow;
it is not the complete provider prompt or evidence that the model attends to every
item. Keep recording limitations visible. Rehearse exact preview/submission
agreement on the presented release. Do not claim improved
model accuracy, saved tokens or deployment from this interface change.

### Ten-to-fifteen-second saved-run beat, verified locally

Status: implemented and locally verified in pass 8. Use this only if
reopening a previous result already belongs in the rehearsed five-minute sequence.

Action: select a saved run with a similar question, inspect its
full question/mode/outcome, and explicitly open that record.

“These runs asked the same question. I can check the saved mode, outcome and exact
question before opening one. My follow-up draft stays attached to the right record.”

Root tested four synthetic records with identical questions. Selection preserved
the current report; explicit Open restored the exact cancelled record and its
draft. Keyboard disclosure, 390px layout and theme geometry/open state passed.
A narrow-menu clipping issue led to ID-first labels; final checks showed distinct
IDs/outcomes and correct keyboard selection of the recorded-abstention preview.
The full suite passed 284 tests. No providers, deployment or real-user study were
part of these checks.

Keep the session-only history limit visible. Do not call Live connection verified live
inference, requested settings confirmed model use, or this history a permanent
archive. If the demo has only one saved run, omit this beat rather than inventing
a comparison. Rehearse on the presented release; no deployment is implied.

### Ten-second live-help beat, verified locally

Status: pass-9 scoped live-help identity is implemented and locally verified.
Use this instead of part of the existing wait beat,
not as another feature tour or a reason to slow a completed result.

Action: focus one live help tip by keyboard while a
rehearsed run waits; keep reading through the next activity refresh, then dismiss it.

“While this run is waiting, I can read what the view means without losing my place.
The clock shows my local wait; the activity changes when recorded events arrive.”

Root verified sustained keyboard focus and a visible network tip across quiet
polls. Escape kept focus and left the tip dismissed through further polls and a
new message; that message appeared and the graph remained visible. Open Agent
details, 390px layout and theme geometry/IDs stayed stable. The synthetic run then
completed into Results. The full suite passed 288 tests; its saved replay reached
nine of nine events with the graph visible and a separate help scope.

Do not convert Python construction timings or automation duration
into a response-time claim. This does not establish faster models, provider health,
field INP, audience capacity or resolution of every long-run stall. Rehearse on
the presented release; no deployment or provider test is implied.

### Ten-to-fifteen-second earlier-activity beat, verified locally

Status: implemented and locally verified in pass 10. This is an optional
replacement within the existing activity inspection, not extra time in the
five-minute presentation.

Action: open the timeline of a rehearsed recorded run that has
more than 40 retained entries. Point to the displayed range, retrieve its oldest
activity, then return to the newest entries using the implemented controls.

“This is one part of the recorded activity. I can check the earlier steps and come
back to the latest entry. I am inspecting this run's record, without asking the
models to run again.”

Root retrieved all 98 entries of a synthetic record in pages of 40, 40 and 18,
without gaps or duplicates. Keyboard controls worked and outside help IDs remained
unchanged through fragment-only page actions. Long identifiers, Unicode and
literal markup passed 390px checks; theme geometry stayed identical. The actual
bundled 52-entry recording exposed its initial planner activity on the oldest
page, then returned to the newest 40 entries without inference. The full suite
passed 303 tests. Rehearse on the presented release; no deployment or live-provider
validation occurred in this pass.

Identify a recording as a recording. Say recorded activity, not complete internal
reasoning: some event text is a shortened tool summary and Raw events holds the
detailed payload. Do not claim better model accuracy, faster inference or permanent
history. If this change is absent from the presented release, omit this beat and
use the already rehearsed claim, argument and evidence inspection.

### Ten-second request-receipt beat, pending verification

Status: pass-11 implementation and automated checks passed (313-test final suite).
Actual downloaded-artifact and selected-owner browser checks remain unverified
after an interrupted download attempt. Keep this beat conditional.
Use this only as a replacement within the existing reproduction handoff; do not
add another feature tour to the five-minute sequence.

Action, after validation: select the rehearsed run and download its request
receipt. Briefly point to the matching local record identity and saved question.

“I can save the submitted question, context and requested settings beyond this
session. This receipt records the request; the source data and executed workflow
are still needed to reproduce the result.”

Before presenting, decode the actual downloaded JSON and compare it with the
selected saved request. Verify that a later draft does not appear in the export,
that requested settings stay separate from reported execution, and that no source
file body or connection credentials are included. A unit test alone is not proof
that the browser downloaded the correct artifact. No deployment, successful
reproduction or improved scientific quality is implied by this proposed feature.

Keep prior generated context labelled as claims, and identify recorded playback
as such. Do not promise receipt import, resumed execution, permanent server
history or the complete provider prompt. If absent from the presented release,
omit this beat and show the existing repository reproduction instructions.
