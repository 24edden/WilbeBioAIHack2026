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
