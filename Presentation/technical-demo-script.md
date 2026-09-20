# Technical direction and demo script

Reviewed 19 September 2026 against the working tree and official documentation.
This is a proposal and speaker-note document. It does not record new model calls,
benchmark runs or deployment checks. The final [deployment record](../infra/DEPLOYMENT.md)
must identify the exact release used on stage.

The technical story should be: **scientists can inspect an agent workflow, challenge
its evidence, and compare whether extra computation actually improves its output.**
The [rubric](../Context/judgingCriteria.md) gives equal weight to scientific impact,
meaningful NVIDIA/OpenAI use, execution, originality and reproducibility. A measured
failure case can support four of those criteria. A sponsor logo cannot substitute
for an executed integration.

## What exists and what remains unproven

| Status at review | Evidence and presentation boundary |
|---|---|
| Implemented in source | Async engine, replaceable reasoning/bio providers, input provenance, specialist blackboard, structured idea review, skills and alignments, Weak points, event replay, cancellation, bounded variant workers and duplicate-score reuse. [Architecture](../ARCHITECTURE.md) describes the contracts. |
| Locally measured | The same 60 repeated variant rows require five score calls instead of 60, retaining finding/verdict hashes. Median simulated time is approximately 0.56 seconds before and after. This is a resource improvement, not a demonstrated inference speedup. [Raw trials](../Plan/performance-check.json). |
| Implemented evaluation | The local harness runs cases/configurations with bounded parallelism, repetitions and timeouts. It retains report/events, hashes and provider-reported reasoning usage when available. The bundled suite checks three synthetic behaviors; it does not grade scientific correctness or source entailment. [Evaluation notes](../Plan/model-evaluation.md). |
| Previously deployed and checked | Brev CPU service with mock providers, staged navigation, editable synthetic demo, unsupported-hypothesis abstention and Weak points. Current new voice/skills/review features require the final release's tests and browser rehearsal. [Deployment record](../infra/DEPLOYMENT.md). |
| Implemented, live use unverified | Rosalind Responses transport and error handling have offline HTTP tests. Project entitlement, successful generation, measured latency and actual usage remain unverified. [Integration notes](../Context/rosalind-integration.md). |
| Provisional | BioNeMo adapter paths and scientific output semantics require replacement or validation against the real selected service. A configured model name proves neither working inference nor scientific fit. |
| Proposed | NVIDIA NeMo Agent Toolkit integration, a comparison dashboard, causal-mechanism records, a reviewed external benchmark subset, and a combined downloadable reproduction bundle. |

The current engine uses Python asyncio. NVIDIA Agent Toolkit is not installed in
the workflow. Brev is hosting infrastructure; Codex is build tooling. Neither alone
establishes the rubric's requirement for central in-product NVIDIA/OpenAI technology.
This assessment follows the repo's [tooling analysis](../Context/tooling.md), not a
prediction of the judges' scores.

## Eight ideas ranked by expected value

Estimates are incremental engineer-hours after accounts and data are available.
They exclude queueing for access, large downloads and scientific review. Choose a
small set; do not try to implement the whole table before the presentation.

| Rank | Feature and smallest useful version | Judging payoff | Effort / dependency | Evidence required |
|---|---|---|---|---|
| 1 | **An evaluation view driven by NeMo Agent Toolkit.** Run the same frozen cases through two existing configurations, show outcomes beside latency/usage, and let a scientist inspect one failure. | High: technology, execution, reproducibility. NVIDIA becomes part of a real product capability. | 4–8 h for a bounded adapter, custom verifier and saved-result view; install/version compatibility must be checked first. | Pinned toolkit version, effective config, case manifest, per-case outputs, actual profiler artifacts and a reproducible command. |
| 2 | **One verified Rosalind review with an inspectable challenge and revision.** Use public/synthetic input and the existing bounded review contract. Retain raw usage and model identity. | High: central OpenAI reasoning, execution. Makes the argument graph more than animation. | 1–3 h after approved account access, then scientific review of the chosen example. | Successful generation, complete event transcript, model/API/budget, usage and exact input hash. No hidden fixture fallback. |
| 3 | **Two proposed mechanisms with typed evidence and a discriminating test.** Three to five links each, assumptions visible, one differing prediction and an immutable scientist edit. | High: scientific relevance and originality. Directly addresses the causal-grounding concern. | 4–7 h for authored synthetic records, deterministic checks and a small view. No automatic causal discovery. | Versioned mechanism records, source links, evidence types, context, explicit assumptions, before/after edit and predefined checks. |
| 4 | **A reproducibility bundle attached to every result.** Package report, events, input checksums, effective settings, provider mode and release identity. | High: reproducibility; useful to scientists and judges immediately. | 1–3 h; most ingredients exist, combined export does not. | An exported bundle successfully replayed on a second checkout. No secrets; include source files only when appropriate. |
| 5 | **A measured resource view beside the agent graph.** Display actual phase durations, unique/reused variant calls and active work. Add tokens only where measured. | Medium/high: execution and understandable technical depth. | 1–2 h for existing report metrics; true per-agent token spans need additional instrumentation. | Same-input before/after trials, preserved outputs, clearly labelled clock and counter semantics. |
| 6 | **A small independent scientific benchmark.** Freeze 10–20 reviewed tasks and compare a baseline with the agent workflow under matching budgets. | High potential: relevance and reproducibility, if task fit is defensible. | 3–6 h adapter/reporting plus data access and expert review; no external adapter currently exists. | Dataset version/license, subset selection before results, held-out labels, per-task outputs/errors, repeated trials, raw usage. |
| 7 | **A real BioNeMo scientific tool with a visible consequence.** Choose the model after the teammate's data shape is known; expose a useful model artifact consumed by the next agent. | High potential: central NVIDIA biology; high integration risk. | 4–10 h after access and endpoint readiness; GPU inference is separate from the current CPU host. | Actual service/schema, model/version, valid biological inputs, raw artifact, interpretation method and a disabled-tool ablation. |
| 8 | **A challenge-quality experiment.** Compare an ordinary proposal with a bounded supporter/challenger/revision sequence, using blinded labels for unsupported assumptions and useful revisions. | Medium/high: originality and evidence that the agent interaction helps. | 3–5 h plus independent annotation; runtime sequence already exists. | Frozen prompts, matched compute baseline, reviewed rubric, disagreement records and per-case differences. More agents are not automatically better. |

For the immediate demo, finish and rehearse the current release first. If integration
time remains, ranks 1 and 2 address the largest judging gap. If model access is
blocked, ranks 4 and 5 give concrete value without pretending vendor integration is
complete. Rank 3 is the most distinctive scientific direction, but needs its own
small contract and authored example.

## Make sponsor tooling central through an observable contribution

### NVIDIA NeMo Agent Toolkit: evaluate and explain the workflow

The official toolkit supports custom workflow components and evaluation. Its
evaluation output can include per-case workflow outputs, effective configuration
and profiler artifacts. That is a good match for a scientist-facing comparison
view. [NVIDIA evaluation documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html).

Proposed implementation: register a thin async wrapper around the existing
investigation adapter, preserve its event/report contract, and add explicit
instrumentation around provider/tool calls. Start with a single case, then compare
two configurations. Do not assume wrapping one outer function will automatically
recover all nested HTTP token usage. Check actual traces before claiming detail.
Use the supported plugin surface for the pinned release; current docs expose
registration through `nat.plugin_api`.
[NVIDIA public plugin API](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/plugin-api.html).

The UI should read saved evaluation outputs first. An on-demand comparison can
come later. A useful visible result has four columns: task outcome, unsupported
claims, actual resource use, and execution failures. Until there is an independent
claim verifier, that column must say unassessed. Keep quality separate from a
model's self-reported confidence.

Conditional speaker line, only after this is built and run:

> "NVIDIA's toolkit runs the comparison behind this view. Here are the exact cases,
> settings and traces. This configuration used more computation; this is what it
> changed in the result."

### OpenAI: make a real model responsible for a bounded reasoning step

Official documentation lists `gpt-rosalind-research` through trusted access for
approved internal life-sciences research. Public documentation establishes the
model's existence, not this account's entitlement.
[OpenAI changelog](https://developers.openai.com/api/docs/changelog).

The existing adapter is the right seam. Prove one minimal generation first, then
one complete scientific-input or proposal-review run. Record model identity,
transport, output limit, usage, errors and run ID. A live review should visibly
consume the prior challenge before producing its revision. Compare quality only
after a reviewed rubric exists. Do not claim Workbench tools are inherited by the
API integration.

Conditional speaker line:

> "Rosalind produced these review turns from this input. The challenger received
> the proposal, and the revision received that challenge. You can inspect both
> the argument and the unresolved assumptions."

Current truthful line while live inference is unverified:

> "The Rosalind adapter is implemented and tested offline. This demonstration uses
> simulated providers; we have not yet measured live model quality."

### BioNeMo: correct the scientific interface before decorating the graph

The current generic `/v1/variant-effect` mapping is provisional. Official Evo 2 NIM
documentation describes DNA-sequence generation and forward-pass endpoints,
including `/biology/arc/evo2/generate` and `/biology/arc/evo2/forward`. It does not
establish that the repo's variant-coordinate request returns a calibrated
pathogenicity probability. [Evo 2 endpoint documentation](https://docs.nvidia.com/nim/bionemo/evo2/latest/endpoints.html).

A possible future tool compares reference and alternate sequence likelihoods,
with correct sequence context and a documented scoring procedure. NVIDIA's
illustrated Evo 2 material discusses delta likelihood; that is a model score,
not proof of a patient's disease mechanism.
[NVIDIA's Evo 2 explanation](https://docs.nvidia.com/bionemo-framework/2.6.3/interactives/illustrated-evo2/index.html).

Keep the service on CPU and call an available GPU inference service only after
its exact schema and resource requirements are established. Validate that an
embedding model accepts the scientific input actually supplied; names in settings
are insufficient. A protein/sequence embedding and literature-text retrieval
require different task semantics. The best integration is whichever produces a
real, useful artifact for the teammate's actual dataset.

## Mechanistic discipline that can be demonstrated honestly

The speaker's causal-grounding concern should become an explicit workflow rule:
an agent can suggest a mechanism, but must identify which links are observed,
assumed, predicted or supported by a perturbation study. Agreement between agents
cannot upgrade an association into causal evidence.

For an illustrative pair of mechanisms, store the same observation under two
explanations, then require a proposed measurement with different predictions.
Specify context, controls, readout and what would challenge each explanation.
Removing a cited source should mark a link unsupported; it must not simulate a
biological intervention. See the existing [mechanism proposal](../Plan/feature-direction.md).

Useful deterministic checks for the proposed record:

- Every evidence link resolves to this run or to an explicitly versioned source.
- An assumption is still labelled an assumption after a model revision.
- Competing explanations with identical predictions remain unresolved.
- A scientist's edit records authorship and before/after values.

These checks measure state integrity and explicitness. Scientific correctness
still requires appropriate data and review. Avoid a numerical "causality score."

## Five-minute script using the working product

Rehearse against the final release and cut any scene that does not work there.
This sequence needs no unverified vendor claim. Use a prepared completed evidence
run for inspection, and one fresh, short idea review for interaction. Browser voice
and theme changes are optional polish, not a separate technical scene.

| Time | Screen action | Literal speaker lines |
|---|---|---|
| 0:00–0:35 | Show the editable research question and uploaded synthetic evidence. | "Scientists need to see why an answer was produced and what evidence could change it. TRACE makes the question, sources, agents and unresolved points inspectable. Today's evidence case is synthetic, and the model outputs are simulated. The orchestration itself is running." |
| 0:35–1:15 | Start a prepared short run; briefly show roles, then navigate while it works. | "I choose the task and team. The submitted question is preserved while I prepare the next one. Work runs independently of the page, and cancellation stops the job rather than just hiding its animation." |
| 1:15–2:05 | Open a completed finding and its source, then Weak points. | "This claim points to the evidence used in the run. The critic also exposes gaps, conflicting findings and failed tools. A reference identifies a source; it does not by itself prove that the source supports the claim. Here is the next evidence the system says is needed." |
| 2:05–3:05 | Run the bounded idea review, or open its exact saved transcript. Suggested prompt: `Evaluate this idea: use a shared evidence checklist to improve reproducibility.` | "For an idea, the team changes. A supporter proposes, a challenger responds, and the supporter revises. These are assigned perspectives. We judge the change in the argument, not the number of agents agreeing. This research step inventories supplied evidence; it is not a web search." |
| 3:05–3:45 | Show the same-input performance result and the current evaluation manifest. | "We also measure the machinery. Sixty repeated variant rows now require five score calls while preserving the outputs. Mock elapsed time is effectively unchanged, so we claim reduced work, not a model speedup. Our current evaluation checks synthetic behavior and records failures; it does not establish biological accuracy." |
| 3:45–4:25 | Show a small architecture diagram with solid implemented boxes and clearly labelled proposed integrations. | "The UI, datasets and providers have separate contracts, so new scientific data does not require rebuilding the interface. Brev hosts this CPU demo. Rosalind transport is implemented but live access is unverified. The next integration is NVIDIA's evaluation toolkit, with actual model traces behind the comparison view." |
| 4:25–5:00 | Return to one weak point or unresolved assumption; show repository and release record. | "The useful output is a claim you can inspect and a clear next question. We preserve the run, source identities, configuration and failures so another team can examine what happened. Our next scientific step is comparing competing mechanisms against tests that could distinguish them." |

If ranks 1 or 2 are verified before the presentation, replace the appropriate
conditional scene with the exact measured result. Remove the matching future-tense
line. Do not merely change a diagram box to solid because credentials were added.

## Pre-run and fallback plan

Pre-run slow inference and comparisons using the exact release intended for the
demo. Save input/config hashes, raw report/events, provider model/version, timestamps,
usage and failure records. A cached result is legitimate presentation evidence when
labelled as a previous run. Preparing it does not establish that a new prompt was
processed live.

1. Rehearse the NVIDIA sign-in and permitted viewer access before the session.
   The earlier HTTPS gate was reached, but a full signed-in browser path was not
   established by that deployment record.
2. Keep one successful run, one unsupported-hypothesis abstention, and one review
   transcript available locally. Check the saved artifacts open without network.
3. If a live step exceeds its rehearsed budget, move to the saved run. Say:
   "This run is taking longer than the demo allows. I am opening the recorded
   result for the same prepared example; this is playback."
4. If the service is unavailable, use the local mock engine or a screen recording.
   Say exactly which. A recorded backend error should remain visible in the record.
5. Do not wait for a container pull, run a large benchmark, or discover model access
   on stage. Terminal-Bench integration belongs only after there is a real sandboxed
   terminal agent; the current research workflow has no such executor.

## Artifacts to carry into the final presentation

| Claim | Concrete artifact to show or link |
|---|---|
| Working workflow | Final release identity, deployed browser rehearsal and one complete report/event pair. |
| Less duplicate computation | [Same-input trials](../Plan/performance-check.json), raw counter definitions and matching output hashes. |
| Real model integration | Provider response/model identity, usage, input hash and complete run trace from successful inference. Offline tests alone do not establish this. |
| Effective agent debate | Actual opening, challenge, revision and critic messages; reviewed comparison against a matched baseline before claiming improvement. |
| Useful scientific evaluation | Frozen task manifest, independent labels, per-case outcomes/errors and dataset/version notes. Existing mock suite remains a regression test. |
| Central NVIDIA evaluation | Toolkit config/version and actual output/profiler files consumed by the displayed comparison. |
| Reproducibility | Exact source archive/commit, environment, permitted sample inputs, commands and run artifacts; a dirty Git base alone is insufficient. |

Use [the existing benchmark research](../Plan/model-evaluation.md) to select an
external task set once the dataset/backend is settled. A general terminal score
and a biological mechanism claim answer different questions. Keep unsupported
claims, abstention, tool failures, time and token use separately inspectable.
