# TRACE: a demonstration the judges can inspect

Drafted 19 September 2026 against the current source. This is a presentation and
feature proposal, not a record of new implementation or deployment. Rehearse the
exact release before promoting any source feature to a demonstrated claim.

The strongest story is: **a scientist asks a question, watches an argument change,
then sees the evidence that would be needed to go further.** The memorable moment
is a useful challenge, not the number of agents on screen.

This builds on [Visual storytelling](../Plan/visual-storytelling.md), with a
different priority: use the working team, discussion and weak-point interfaces
first. Add a scientific scene only if it can expose real source data. The event's
[five equally weighted criteria](../Context/judgingCriteria.md) reward scientific
impact, meaningful NVIDIA/OpenAI use, execution, originality and reproducibility.
Visual polish helps delivery; it does not substitute for the other four.

## What we can honestly show

| Status | Current evidence |
|---|---|
| Implemented in current source | Four stages, persistent question draft, question-only idea review, task-mode selection, role skills and SVG icons, explicit supporting/challenging perspectives, directed agent-message graph, revised discussion, source-linked investigation findings, weak points, abstention, execution metrics, optional browser voice, background event rendering and cancellation. See [architecture](../ARCHITECTURE.md). |
| Previously checked on the hosted release | Editable synthetic demo, navigation, unsupported BRCA2 question, weak points and an uploaded-file API run. [Deployment record](../infra/DEPLOYMENT.md) identifies the checked release. New skills/voice/review features need verification on whichever release is presented. |
| Proposed, not implemented | Clickable source nodes in the graph, a comparison of original/revised text, one-click use of a weak point as the next question, treatment/lab timeline, source-removal experiments, molecular viewer and complete run-bundle export. |
| Not established | Scientific accuracy, calibrated confidence, improved scientist productivity, causal discovery, live Rosalind entitlement/inference, actual BioNeMo inference or NVIDIA Agent Toolkit integration. |

Three distinctions should remain visible throughout the demo:

- **Demo** runs the actual orchestration with simulated provider outputs.
- **Recorded** replays saved events and outputs. It does not process a new prompt.
- **Connected/Live UI mode** describes the connection. The backend's provider mode
  still determines whether model outputs are simulated or real.

Review perspectives are assignments, not measures of truth. A research role
inventories supplied records; it does not currently search the web or independently
validate papers. Its proposal discussion is kept separate from scientific findings.

## Ranked concepts

Ranks express presentation priorities, not predicted judging scores. Effort is a
rough engineering estimate for the stated increment, excluding new datasets,
scientific validation and provider access.

### 1. Show an argument changing because another agent challenged it

**Immediate beat:** start an idea review. Point to the supporter, then the
challenger's message edge, then the revision. Open the revision's response ID and
assumptions. Give the audience one change to track: adding held-out evaluation
and a baseline after the challenge raises leakage and unclear success criteria.

**Spoken line:** “The challenger gets the proposal the supporter actually wrote.
The next turn responds to that challenge. You can inspect the exchange.”

**Rubric fit:** originality, execution, presentation. Scientific value depends on
testing the resulting proposal; debate alone does not validate it.

**Available now:** a bounded sequence of real provider calls, or their labelled
mock equivalents, with directed messages and a final critic. The graph shows real
message counts; discussion entries retain phases and `reply_to` identifiers.

**Small upgrade:** a two-column “Original proposal / Revised proposal” view,
linked by the real response IDs. Highlight changed constraints only when those
changes can be extracted faithfully; otherwise display full text side by side.
No win/loss meter, consensus percentage or simulated attack animation.

**Assets/data:** one prepared question, discussion entries, role metadata and
event log. Existing SVG icons are sufficient. **Effort:** 20–40 minutes of
rehearsal now; 2–3 hours for the comparison view. **Status:** core implemented in
source; comparison view proposed.

### 2. Turn “weak points” into the next useful question

**Immediate beat:** open Results → Weak points after the evidence investigation.
Read one specific limitation, expand its linked references, then place its next
evidence suggestion into the persistent question draft. Explain that a new run
requires an explicit start and does not rewrite the completed report.

**Spoken line:** “Here is what this run cannot support, and what we would need to
check next. The scientist decides whether that is worth pursuing.”

**Rubric fit:** scientific impact, originality and execution. This changes the
output from an answer to an inspectable research decision.

**Available now:** backend-generated limitations, rationale, linked findings,
sources and next evidence. Copying a next question is manual. An item can have no
source references; the UI says so instead of inventing a citation.

**Small upgrade:** “Use as next question” fills a draft and records the originating
run/weak-point ID. It must not submit a run, change evidence or imply the requested
evidence has been obtained. Frontend can own the draft interaction; an eventual
saved lineage field needs a coordinated additive backend contract.

**Assets/data:** actual `weak_points.items` from a completed sample run. Do not
promise a conflict if that run only has scope limits. **Effort:** 20 minutes to
rehearse now; 1–2 hours for a draft-only button. **Status:** assessment implemented;
next-question button proposed.

### 3. Invite a question the evidence cannot answer

**Immediate beat:** change the draft to “Did the patient fail because of BRCA2?”
with the same synthetic sample. Start a new evidence investigation. Show the
withheld conclusion and the missing-evidence explanation. Keep the first run's
captured report beside it only if a comparison has actually been prepared.

**Spoken line:** “I have named a plausible-sounding cause that this sample does
not establish. Watch whether the system follows my suggestion or asks for evidence.”

**Rubric fit:** execution, scientific relevance and reproducibility. A bounded
failure demonstration is more credible than an unsupported accuracy claim.

**Available now:** editable mock investigation and an abstention gate. This exact
question is recorded in the prior hosted browser checks. Confirm its behavior on
the final release; do not present a scripted mock outcome as a live model test.

**Small upgrade:** a saved two-run comparison containing question, provider mode,
evidence hashes, verdict and weak points. It should not subtract uncalibrated
confidence numbers and call the difference scientific improvement.

**Assets/data:** the bundled files, two run records and a clearly labelled backup
capture. **Effort:** 30–45 minutes of preparation; 2–4 hours for comparison UI.
**Status:** underlying runs implemented; comparison UI proposed.

### 4. Make the team visibly fit the work

**Immediate beat:** show “Review an idea” and its fixed team of planner, research,
supporter, challenger and critic. Contrast it briefly with Evidence investigation,
where the scientist selects genomics, clinical and literature specialists. Open
one skills card, then start the chosen task. The effective plan appears in the run.

**Spoken line:** “The team has a job description. For an idea, it develops and
challenges a proposal. For uploaded evidence, I choose the specialists.”

**Rubric fit:** execution and usability, with a clear route to scientific value.
It makes configuration understandable without exposing the whole system at once.

**Available now:** role skills/icons, task selection, explicit effective mode and
routing reason. Auto selection uses conservative text rules, not a learned
planning policy. Idea review uses a fixed five-role roster. Model choice selects
configured backend identifiers; it does not provision arbitrary models.

**Small upgrade:** a compact preview of the effective team before a run, using
the same backend planning contract. Avoid a frontend guess that might differ
from the submitted plan. **Assets/data:** capability catalog and actual plan.
**Effort:** 15–30 minutes rehearsal; 2–3 hours for a preview endpoint and view.
**Status:** selection/catalog implemented; exact pre-run plan preview proposed.

### 5. Reveal the difference between two agents and two sources

**Immediate beat:** find two findings that cite the same source, expand their
references and point to the shared identifier. Explain that duplicate agreement
is not independent corroboration. Only use this beat if the prepared run actually
contains source reuse.

**Spoken line:** “Two agents can agree because they read the same thing. This
reference lets us check whether we have independent evidence.”

**Rubric fit:** scientific relevance and originality. It gives the graph a
scientific purpose beyond showing activity.

**Small upgrade:** an evidence view with agent → finding → canonical source nodes.
Clicking a node opens its source locator; two agents sharing a source visibly
converge. Keep communication edges separate from evidence edges. Preserve finding
IDs and define canonical source identity at the adapter boundary first.

**Assets/data:** actual finding IDs, provenance kind/ref/locator and source metadata.
No source-entailment claim follows merely from matching IDs. **Effort:** 30 minutes
to find a truthful manual example; 3–5 hours for the linked graph. **Status:**
reference inspection implemented; source-node graph proposed.

### 6. Let a scientific observation take over the screen

**Immediate beat, if implemented:** select a dated CEA observation. A timeline
shows that measurement alongside treatment-note markers, and a click opens the
exact row. Ask which missing observation would separate alternative explanations.

**Spoken line:** “This dot is a supplied measurement. This marker is a note.
Their sequence gives us a question to investigate; it does not prove the cause.”

**Rubric fit:** scientific relevance and presentation. This is the best visual
upgrade if the teammate's dataset has stable dates, values and provenance.

**Assets/data:** full normalized rows, units, dates and source locators. Current
tool-event timestamps describe agent activity and cannot serve as patient dates.
Keep units on separate scales and label the case synthetic. The previous visual
plan specifies the data/renderer boundary. **Effort:** 3–5 hours after data
agreement. **Status:** proposed. Use current cited findings as the fallback.

A molecule or organism image is optional contextual material. It is lower
priority than this interaction, and must retain the reference/sample distinction
described in [Visual storytelling](../Plan/visual-storytelling.md).

### 7. End with a receipt for the demonstration

**Immediate beat:** open Run details, the effective plan, measured execution
fields and event records. Point to the repository's release manifest and prepared
run artifacts. Close on one reproduction command verified by the technical team.

**Spoken line:** “These are the inputs, settings and events behind what you just
saw. Another team can run this workflow and inspect where it succeeds or stops.”

**Rubric fit:** execution and presentation/reproducibility; use the receipt to
identify any verified in-product NVIDIA/OpenAI calls, if present.

**Available now:** run details, raw events, backend report/log routes, release
hashes and a local performance artifact. No complete downloadable run bundle is
currently exposed in the UI. Runs are in memory, so save the artifacts before a
server restart.

**Small upgrade:** a downloadable manifest/report/event package, including source
hashes, provider mode and code version. Exporting uploaded contents should be an
explicit choice. **Assets/data:** real report/log and final release identity.
**Effort:** 30–60 minutes to prepare the handoff; 2–4 hours for a bundle export.
**Status:** inspection/artifacts implemented; one-click bundle proposed.

## Five-minute script using the working core

This sequence uses two explicit modes on one theme: investigating an explanation
and evaluating a proposed way to test it. Prepare the evidence run and unsupported
case beforehand. Start the review run on stage only after timing it on the demo
machine. A precomputed result remains inspectable but must keep its label.

| Time | Screen/action | Spoken draft |
|---|---|---|
| 0:00–0:25 | Evidence screen, three synthetic files already visible | “A scientist can get a fluent explanation in seconds. The hard part is deciding what in that explanation is supported, what was assumed, and what to test next. TRACE puts that decision in the scientist's hands.” |
| 0:25–0:50 | Persistent question; task and skill cards | “Our sample combines variants, laboratory records and notes. I choose the question and the team. This demonstration runs real orchestration with simulated model outputs, so you can inspect the workflow without mistaking it for validated clinical reasoning.” |
| 0:50–1:30 | Completed evidence result, one finding and its reference | “Here is one claim. Here is the source the agent attached to it. The evidence investigation and the final review stay inspectable. We do not equate a confident sentence or agreement among agents with a demonstrated causal mechanism.” |
| 1:30–2:00 | Weak points; expand one actual item | “The most useful part can be the limitation. This item explains what is missing and what evidence would help. I can turn that into a new question without changing the completed run.” |
| 2:00–2:25 | Type the prepared proposal; select Review an idea; start | “Let's evaluate the next research idea. I am asking for a baseline, a falsifiable comparison and a way to challenge the explanation. The system uses a review team with supporting and challenging perspectives.” |
| 2:25–3:15 | Actual graph/messages, then review discussion | “The supporter develops a proposal. The challenger receives that argument and questions the assumptions. The supporter then revises it. These arrows represent recorded messages, and this response points back to the turn it addresses. The critic receives the discussion. None of these roles can manufacture experimental evidence.” |
| 3:15–3:50 | Prepared unsupported BRCA2 run; abstention and weak points | “Now I ask about a cause these files do not establish. In this prepared mock run, the system withholds that conclusion. We include this failure case because knowing where to stop is part of a useful research workflow.” |
| 3:50–4:30 | Architecture slide with verified components; Run details | “The interface streams events while work runs in the background. Specialists share findings through the backend. We preserve the plan, provider mode, references and execution record. This CPU deployment runs on Brev. The provider adapters are separate, so model services can change without rebuilding the scientist's workflow.” |
| 4:30–5:00 | Repository/reproduction slide; return to weak-point card | “The repository contains the runnable workflow, synthetic case, tests and release instructions. Our next evaluation is whether researchers can identify unsupported claims and choose better follow-up tests. TRACE makes the argument, its evidence and its weak points available for that decision.” |

Prepared idea-review question:

> Evaluate this research idea: compare the target-pathway explanation with a
> treatment-exposure explanation for the supplied synthetic case. Propose a
> falsifiable comparison, a simple baseline and the evidence that would challenge
> each explanation. Separate assumptions from observations.

In current mock mode, the response is a deterministic review template. It
demonstrates data flow, reference separation and turn-taking, not model-specific
biomedical reasoning. If a verified live model replaces it, capture that run and
its provider metadata before using a live-inference claim in the script.

## Technical-tooling sentence variants

Use exactly the version that the final run artifacts support. Ask the technical
workstream to populate verified provider/model IDs and retained outputs.

- **Current CPU/mock state:** “We host TRACE on Brev and have a Rosalind Responses
  adapter. This run uses simulated providers; live model validation is still open.”
- **If live Rosalind is verified:** “This recorded run used [actual model ID] for
  [actual role]. Here is its output and provider record.” A saved API response is
  evidence of that invocation, not a general accuracy result.
- **If a real NVIDIA scientific tool is integrated:** “This [named, versioned
  service] produced this output from these inputs, and the downstream agent used
  it here.” Only use this sentence after showing the retained call and output.
- **If NVIDIA Agent Toolkit is integrated:** name the actual orchestration,
  profiling or evaluation function it executes. Do not relabel the existing
  Python asyncio engine as Agent Toolkit.

Criterion 2 is currently a gap. Brev hosting and Codex development alone do not
demonstrate central in-product use of both vendors. A small working scientific
tool integration is more persuasive than extra logos; the independent technical
brainstorm owns that choice. See the explicit team-analysis caveats in
[Tooling](../Context/tooling.md).

## Backup beats and stage discipline

- **Slow live run:** after five seconds without a new visible event, say “This
  step is still running. Here is a saved run from the same setup.” Open the
  labelled capture or prepared result. Never silently replace live outputs.
- **Older replay:** older fixture logs may lack weak points or review discussion.
  Prepare a capture of the final release; do not assume the existing replay picker
  contains the new review scenario.
- **Graph too quick:** use the completed Agent activity tab. It preserves the
  network and messages, so the audience can inspect the exchange at a readable
  pace. Do not add pretend processing delay to claim model work is happening.
- **Voice:** optional ten-second opening, only after checking microphone permission
  and the chosen voice on the presentation machine. Speak the question, inspect
  its transcript, then apply it. Use one short agent status cue. Keep typed input
  ready and disable speech while presenting scientific interpretation.
- **Network/auth problem:** use the pre-authenticated session or local deployment
  prepared by infra. A video or event capture carries a visible “Recorded” label.
- **Time overrun:** cut the skill-card explanation and voice. Preserve one source,
  one challenge/revision, one weak point and the reproduction evidence.

Do not promise that graph nodes are clickable: the present Graphviz view is a
rendered graph. Inspect the adjacent message/discussion panels. Do not promise
mid-run steering: editing the persistent question drafts a later run.

## Material to prepare for the submission

Save all actual presentation artifacts alongside this script or in a clearly
linked, versioned demo-artifact directory; this document does not create them.

1. One screenshot of the skills/team selection and one of the completed review
   graph, with readable text at projector scale.
2. A short recorded review run, preserving the provider-mode label and directed
   exchange. Keep the complete event log separately.
3. Reports and event logs for the evidence and unsupported-question cases, plus
   source hashes, release identity and exact reproduction commands.
4. One weak-point reference opened before recording, so the backup demonstrates
   inspection rather than merely a list of limitations.
5. A small architecture slide containing only implemented components. Mark live
   integrations and planned work separately; do not include proposed imagery as
   if it were shipped.
6. The official Google Slides submission template and a repository link. The
   event requires both; this script is preparation for that deliverable.

If a number is spoken, retain its source. The current local mock performance
artifact shows 60 repeated variant-score requests coalesced into five calls with
unchanged finding/verdict hashes in that experiment. It does **not** show a 12×
latency gain: measured mock wall time was approximately unchanged. Token-cost,
scientific-accuracy and productivity claims require their own measurements.
See [performance-check.json](../Plan/performance-check.json).
