# Proposed process and simulation harnesses

Prepared 19 September 2026. Design recommendations, not implemented simulation results.

The shared project process is: define a scientific question, qualify the available evidence, register competing explanations, select and execute a discriminating analysis, revise the evidence-linked decision, obtain scientist review, and feed new measurements back into the case. A second loop turns corrections into bounded lessons and tests their usefulness on other cases before release.

Two local proposals instantiate this process differently. The revised PRINCE proposal concerns baseline immune features and survival; the subsequent translational documents concern ALK resistance and learning from scientist feedback. This design uses the shared process, ALK for the main walkthrough, and a separate PRINCE scenario pack. It does not assume these are one biological analysis.

**Recommendation:** one durable runner, one event store, and several independently scored harnesses. Build contract replay and a small hidden-world scenario pack first. Add experiment choice and feedback transfer next. Test failures throughout. Defer a company-wide process simulator until there are measured operating times and capacities.

## What the local graph actually contributes

The application at `http://127.0.0.1:8773` exposed its API specification. Its health query returned HTTP 503 and a workspace read timed out. The analysis therefore uses the saved local export at `<REFERENCE_MODEL_WORKSPACE>/graph/model/graph.json`, not a successful live database read. No graph writes or service changes were made.

The export identifies reference model `0.3.0-draft`, schema `1.2.0`, as-of `2026-09-10`, with 2,259 nodes and 17,374 edges. Its source hash and the exact selected nodes/edges are in graph-reference-extract.json (`graph-reference-extract.json`, outside this Markdown collection). These are authored reference contracts. They do not establish measured biology, completed work, actual delegations, or validated company procedures.

| Project stage | Existing reference anchor | How the harness should use it |
| --- | --- | --- |
| Define scope and permissible claims | `proc.clinical_interpretation`, activity `.1`; `proc.sap` | Pin question, population, evidence cutoff, exploratory status and analysis budget. Adapt the contract to research; do not require a full regulated SAP for every exploratory run. |
| Qualify evidence | `proc.data_review` → `analysis.data_quality` / `analysis.reconciliation`; `proc.biomarker` → `analysis.assay` | Validate identities, timepoints, assay context, source versions and applicability. Missing applicable evidence remains unknown. |
| Check exposure alternatives | `proc.pharmacometrics` → `analysis.pkpd` | Require dosing/time joins and units for an exposure claim. Unknown exposure does not mean adequate exposure. |
| Execute and verify | `analysis.output_qc` | Reconcile outputs and narrative to exact inputs, denominators, numerical results and uncertainty. This analysis is a useful adapter contract; it is not asserted to be a direct edge from every process. |
| Challenge and integrate | `proc.clinical_interpretation` → `analysis.evidence`, activities `.2` and `.3` | Keep counterevidence, claim-source mappings, interpretation limits and unresolved alternatives. |
| Review a version | `decision.clinical_interpretation`, activity `.4`, `artifact.clinical_interpretation` | Review the exact memo version and scope. The reference proposes `role.clinical_dev_head` as authority; actual reviewer assignment must be configured. |
| Learn across cases | New project-specific extension | Decision episodes, feedback, lesson candidates, evaluations, releases and use events. These are proposed records, not verified existing graph types. |

The existing interpretation contract is especially useful: it already specifies scope → integrated outcomes → challenge alternatives → qualified interpretation. Its exception route returns unsupported claims for correction and preserves scientific disagreement. Build on this four-step structure.

Keep three distinct kinds of knowledge: reference work definitions, observations from actual or simulated cases, and approved procedural lessons. Also keep the simulator's hidden truth outside all agent-visible stores. A company/process graph is not a causal biological model. `CONSUMES` points from a consumer to required information; it is neither temporal sequence nor causation. `DECIDES` describes proposed authority, not an actual approval.

## Harness 1: contracts, evidence and replay — build first

**Question:** Can a run complete the proposed investigation with every consequential claim traceable to a valid result, and can we reconstruct it later?

Input is a pinned reference-contract subset, scenario manifest, versioned evidence package and bounded action menu. The runner maintains explicit states: framed, evidence checked, analysis planned, running, results checked, decision drafted, awaiting review, completed, blocked, failed, cancelled or budget exhausted. A case can complete with an unresolved scientific conclusion; execution failure is a different state.

Use one coordinator with sequential specialist contracts initially. A specialist returns claims, supporting/contradicting evidence IDs, unknowns and proposed discriminators. More model instances are an experimental condition, not a prerequisite or a source of independent evidence.

Persist action intent before execution, an immutable result after validation, and a new decision version after interpretation. Enforce output schemas, artifact hashes, stable IDs, typed links, release pinning and declared numerical tolerances. A failed or pending tool call cannot become completed evidence. Record an exception when a contract is inapplicable instead of silently requiring every dataset in the company graph.

**Pass evidence:** no orphan consequential claims; all referenced results resolve to exact input versions and specifications; deterministic replays match within declared tolerances; failures and superseded interpretations remain visible; reviewer disposition binds to the intended version. These are proposed hard checks, not measured pass rates.

**Reuse:** `rosalind/core.py` already supplies question/tool schemas, evidence events and hashed artifacts. Its current workflow is explicitly deterministic, not an LLM team. Extend around it rather than replacing it with a new orchestration framework.

## Harness 2: hidden scientific scenarios — build alongside replay

**Question:** Does the investigator behave appropriately when plausible explanations generate overlapping observations?

Each scenario separates a hidden state, an observation process and the evidence released to the agent. The evaluator holds the generator parameters and labels. The agent receives only the current evidence and may request permitted analyses. Do not include the answer in case filenames, graph neighbors, lesson text, tool descriptions or trace metadata visible to the agent.

Start with small deterministic fixtures to verify behavior, then parameterized stochastic families to challenge generalization. For ALK, use deliberately abstract synthetic worlds covering: variant-driven functional change, inadequate exposure, bypass biology, passenger variant, measurement artifact, and unresolved mixtures. Vary coverage, temporal sampling, assay noise, missing exposure, correlated evidence and contradictory measurements. These are mechanism-neutral stress tests, not calibrated digital patients or claims about a named ALK mutation.

For PRINCE-style work, use a separate generator with a known endpoint model: general prognostic association, a regimen interaction, measured/unmeasured confounding, missingness, null effects and assumption violations. Vary event availability, censoring and assay availability. Enforce patient-level joins and baseline rules before fitting. Do not infer population facts from the proposal without checking the actual trial release.

An important test pair has identical initial observations under two different hidden mechanisms. The correct initial behavior must be the same under both: preserve ambiguity and request a discriminator. Marking one confidently guessed mechanism “correct” solely because it matches hidden truth would reward unjustified reasoning.

**Pass evidence:** appropriate use or omission of tools, detection of relevant confounding, preservation of counterevidence, justified abstention, and calibrated predictions only when the task defines probabilistic labels. Report unsupported causal claims separately from ordinary mistakes. Include cases where sufficient evidence exists so that indiscriminate abstention does not win.

Use ADEMP—aims, data-generating mechanisms, estimands, methods and performance measures—to specify the statistical simulations, and report Monte Carlo uncertainty. This is established simulation-study guidance; the scenario choices here are our proposed design. [Morris, White and Crowther (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/).

## Harness 3: experiment choice and sequential evidence

**Question:** Does the chosen next action reduce the uncertainty that matters for the decision?

The simulated laboratory supplies delayed or noisy observations only after a permitted request. Define a finite assay/analysis menu with required specimens or inputs, controls, observable outputs, cost and time assumptions. Reserve the hidden outcome model for the evaluator. Include failed assays, uninterpretable measurements and experiments that do not discriminate the competing hypotheses.

For the resistance pack, candidate actions might include orthogonal variant confirmation, an exposure check, a matched functional comparison, a pathway readout, or a mechanistic biochemical assay. Specify what each can and cannot resolve. A structural prediction adds mechanistic plausibility; it must not automatically settle a functional or clinical causal claim. For the PRINCE pack, the menu differs: interaction, prespecified covariate adjustment, stability/influence analysis, or an available second modality.

Score the complete trajectory rather than the persuasiveness of the experiment rationale. Compare against a fixed checklist, a random feasible action policy, and an oracle with access only to the simulator's known generative model and the same initial observations/action budget. Where likelihoods and utilities are explicit, estimate expected information gain or expected decision utility. Otherwise use predefined expert-acceptable action sets; do not invent a numerical information-gain score from an LLM's opinion.

**Pass evidence:** benefit over the fixed policy at matched budget; low selection of infeasible or nondiscriminating actions; appropriate stopping; and actual revision after disconfirming results. Report regret relative to the oracle only within the synthetic model. Model-based optimality is not optimality in a real laboratory.

A useful demonstration begins with a credible progression-enriched variant, reveals an exposure ambiguity or bypass signal, and shows the next test change. Include another case where the original hypothesis survives. A reversal-only script would not evaluate reasoning.

## Harness 4: scientist feedback and transfer

**Question:** Does a correction improve later decisions within its scope without damaging unrelated cases?

Implement the documented learning loop as immutable decision → feedback → candidate lesson → reviewed/evaluated release → recorded application. A correction can revise the present case immediately; promotion into shared memory is a separate event. A simulated reviewer can test these transitions but cannot provide independent scientific validation.

Use four controlled conditions: frozen baseline; retrieval of raw past cases; retrieval of approved bounded lessons; approved lessons plus a structured challenge step. Keep model, tools, input evidence and total resource budget comparable. Record memory retrieval costs as well as model/tool costs.

Split by case family, patient or experimental series as applicable before lesson generation. Add a mechanism-family holdout for transfer claims and a temporal cutoff where relevant. Reworded copies and replicate assays do not count as independent cases. Fix the memory release during each run; future feedback and outcomes must not leak into earlier decisions.

The first useful lesson is procedural: if the causal claim rests mainly on structure, preserve it as provisional and seek a functional discriminator. Its negative control is a case where matched functional evidence already answers the narrow question; the lesson should not demand redundant validation automatically.

**Pass evidence:** paired improvements on blinded scientist ratings and/or verified actions, acceptable prespecified regression margins, fewer consequential unsupported claims, reasonable correction burden, and limited out-of-scope lesson use. Define thresholds and sample-size rationale before opening the holdout. Report uncertainty; a handful of demonstrations cannot validate learning. Inject contradictory feedback, suspend a lesson, and replay affected decisions under the preceding release. Curators cannot approve their own candidate simply because it passes schema validation.

## Harness 5: tool failures, interruptions and recovery

**Question:** Does the process remain truthful and recoverable when execution goes wrong?

Build fault injection into the first harness, not after the scientific demo. Cover invalid coordinates or assay mappings, contradictory metadata, malformed output, partial WT/mutant results, asynchronous jobs, transient errors, missing credentials, lost responses, worker restarts, duplicate feedback, cancellation and exhausted budgets. Inject untrusted instructions into retrieved scientific text and verify that they cannot alter tool authority or evaluation rules.

Persist an operation ID and action intent. When a write or remote job may have succeeded before a timeout, reconcile it before resubmission. Resume the same pending review/run after restart. Preserve failed attempts and partial artifacts without promoting them into validated findings. Bound retries and report whether in-flight work actually stopped.

**Pass evidence:** no duplicate effects in the tested cases; no false completion claims; state and artifact consistency after restart; and no new work after cancellation or budget exhaustion. “No failures observed” describes the test set, not a universal guarantee.

The prototype implementation record reports 20 offline/loopback tests, but this task did not rerun them. It also explicitly lacks live inference verification, asynchronous-job retrieval and several scientific ingestion/analysis capabilities. Its present synthetic target-escape workflow is not an implemented ALK kinase or PRINCE survival pipeline; both require dedicated adapters and cases.

## Later: human handoff and capacity simulation

A discrete-event simulator could ask how reviewer availability, evidence delays and rework affect time to a reviewed decision. Use the graph's role, dependency, exception and handoff contracts to constrain valid routes. Sample separate processing time, queue delay and evidence lag; allow concurrent work and multiple roles held by one person.

Do not make this the first build. The inspected `proc.clinical_interpretation.behavior` fields for latency distribution, capacity consumption, cadence and evidence lag are all null. The graph defines work but does not contain calibrated operating dynamics. Initial sliders would be explicit what-if assumptions; collect timestamps from real runs before making throughput or staffing claims.

## Shared implementation contract

Use a small transactional event store plus immutable artifact files initially, and render a graph projection from those records. Keep the existing reference graph read-only. Its observed HTTP API is read-only; do not invent an analysis-write endpoint. A later adapter can publish validated operational records after its schema and semantics are tested.

The minimum new record types are `ScenarioManifest`, `EvidenceSnapshot`, `AnalysisSpec`, `ActionAttempt`, `AnalysisResult`, `HypothesisRevision`, `DecisionVersion`, `ReviewEvent`, `LessonVersion`, `MemoryRelease` and `EvaluationRun`. Their exact types are proposals. Every case pins the graph snapshot hash, case inputs, evidence cutoff, code/tool/model/prompt versions, memory release, action budget and scenario seed. The evaluator additionally records hidden-generator versions in a separate inaccessible store.

Keep scientific states (supported, weakened, contested, unresolved) separate from execution states (pending, running, succeeded, failed) and review states (draft, accepted within scope, returned, held). A successful analysis can weaken a hypothesis; an accepted exploratory memo is not authorization for a clinical action. Every delayed outcome attaches to the original prediction without overwriting it.

Illustrative event sequence:

```text
case opened → evidence qualified → hypotheses registered
→ action intent recorded → tool result validated → evidence appended
→ decision v1 → scientist correction → decision v2
→ candidate lesson → review + disjoint evaluation → memory release
```

## Evaluation that identifies the source of benefit

Compare ordinary tool-enabled instructions, a structured investigation stored as flat records, and the same structured investigation with graph-based retrieval/navigation. Keep the accessible information, model, tools and budget matched. The first contrast measures the package of structure and evidence discipline. The second tests whether graph access itself adds value. If equivalent retrieval differs in practice, report that difference explicitly; storage topology alone is not a scientific intervention.

Only then compare one coordinator against multiple specialists and add learned memory. Changing graph, prompting, tools, model and team size at once cannot identify which helped.

Use deterministic checks for numerical/execution correctness and blinded domain review for experiment discrimination and interpretation. Model judges can assist triage, but should not be the sole scientific arbiter. Report successes and failures by scenario family, paired differences, uncertainty, latency, cost, manual interventions and over-abstention. Audit the generator and graders independently of the agent's output; agent consensus does not establish ground truth.

## Concrete first build

1. Freeze a small graph subset and translate its four interpretation activities into executable, typed checks. Configure reviewer assignments separately.
2. Add immutable case/decision/review records around the existing evidence ledger, plus fault injection and replay.
3. Author a proposed 12-case development pack spanning clean evidence, confounding, contradictions, insufficient information, invalid inputs and interrupted execution. This number is an implementation target, not a statistically powered benchmark.
4. Run one complete ALK-style synthetic investigation: initial evidence → chosen discriminator → released result → revised decision → scientist correction. Preserve uncertainty and identify all simulated evidence.
5. Run the same cases with a fixed checklist baseline and a tool-enabled unstructured baseline. Inspect whether the graph-based contract prevented an observable mistake.
6. Add a separate frozen holdout and the smallest bounded lesson plus an out-of-scope control. Show transfer and rollback behavior without claiming validated biological discovery.

The first release should demonstrate that the team asks a better next question and preserves the evidence needed to check its answer. Large-scale discovery, live model performance, calibrated biological simulation and company-wide automation remain subsequent empirical questions.

## Local source trail

- `WilbeBioAIHack2026/Context/TRANSLATIONAL_SCIENCE_HYPOTHESES.md`: case loop, roles, competing hypotheses and selective computation.
- `WilbeBioAIHack2026/Context/AGENTIC_SCIENTIFIC_LEARNING_LOOP.md`: feedback, memory governance and transfer evaluation.
- `revised-proposal/revise_proposal.py`: source text of the revised PRINCE proposal and its A/B evaluation plan.
- `rosalind/rosalind/workflow.py`, `rosalind/docs/IMPLEMENTATION.md`: inspected current behavior and documented implementation limits.
- Local biotech graph export and `docs/PROCESS_CONTRACTS.md`: stable IDs, relationship directions, work/review contracts and explicit reference-model limits.

The interactive walkthrough is an illustrative design view. It performs no biological analysis, model inference, live graph query or harness evaluation.
