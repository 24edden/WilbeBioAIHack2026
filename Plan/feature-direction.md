# Feature direction: a scientist controls the investigation

Research date: 19 September 2026. Recommendation, not an implementation commitment. Code observations are a snapshot while frontend/backend work proceeds. Effort and judging scores below are estimates, not measured outcomes.

**Updated recommendation after the user's causal-grounding input:** “Compare possible mechanisms, challenge the weakest link, and identify what evidence would distinguish them.” Make the scientist's choices central. An editable mechanism comparison now supersedes source-selection reruns as the leading feature; source exclusion becomes a way to inspect which proposed mechanism links lose evidential support. Keep the executable failure cases and downloadable run record. This is a mechanism-review workspace, not an automated causal-discovery claim.

## What already exists

The repository already contains file ingestion, questions/hypothesis handling, concurrent specialists, agent messages, supporting/contradicting findings, source provenance, a deterministic abstention gate, SSE, report/event-log endpoints, recorded demos and a headless CLI. These are implementation assets, not new feature proposals. See `app/main.py`, `app/engine.py`, `app/models.py`, `app/agents/critic.py`, `app/cli.py`, `frontend/ui/stream.py` and the grounding/critic tests.

Important distinctions:

- Frontend recorded playback is a saved investigation. Backend `RUN_MODE=mock` executes the actual orchestration with simulated provider outputs. A live connection to the backend does not establish live model inference.
- `app/engine.py` explicitly uses the plain asyncio fallback, not the NVIDIA toolkit spine described in `ARCHITECTURE.md`. Live provider API mappings in `app/providers/live.py` are assumptions requiring verification. Existing code is not proof that the hosted models work.
- Brev access was established in this session, but the instance is CPU-only. GPU models must use an available hosted endpoint or await separate GPU allocation. Do not promise local BioNeMo inference.
- Confidence values and gate thresholds are heuristics/model outputs, not calibrated probabilities. Distinct specialist roles are not necessarily independent evidence: agents may reuse the same source. A citation that resolves is not proof that the cited text supports a biological claim.
- These are research workflow demonstrations. Neither existing unit tests nor the proposed small suite validate patient-level causal conclusions.

## Ranked additions

Scores indicate expected contribution to the five **equally weighted** event criteria on a 1–10 scale: Scientific relevance / NVIDIA+OpenAI application / Execution / Originality / Presentation+reproducibility. They are prioritization judgments, not forecasts of judges' marks. Integration scores are low where a feature adds no meaningful vendor use.

| Rank | Addition and visible proof | Scores | Effort; dependencies and risk |
|---|---|---|---|
| 1 | **Compare and challenge mechanisms.** Two small candidate mechanisms, editable assumptions/links, evidence types and competing predictions. Exclude a source to reveal unsupported links; export the revision and a proposed discriminating test. | 9/3/7/9/9 | 5–8 engineer-hours for bounded cards and persistence; add 2–3 for source-rerun comparison. New structured mechanism state is needed; existing findings/provenance and `file_ids` help. No GPU needed for display/checks. Main risk: a plausible diagram being mistaken for established causality. |
| 2 | **Executable failure-case panel.** Run a small frozen suite and display pass/fail by case, with one click opening its evidence trace. Show both success and informative refusal. | 8/4/9/8/10 | 4–6 hours. Reuse engine, fixtures and tests; new case manifest/verifiers/reporting. Low compute demand; medium scientific-label risk. Mock checks demonstrate software behavior only. |
| 3 | **Evidence ledger and conflict view.** Expand a finding into exact file/line or corpus excerpt; group support and contradiction; surface gate checks and flag reuse of a source across agents. Judge follows a report claim to its origin and sees disagreement. | 9/2/9/7/9 | 2–4 hours for presentation over existing provenance/stance/check events. Source independence requires a separate provenance grouping design; do not label roles “independent evidence.” |
| 4 | **Download the investigation.** Export report, event log, selected source manifest/checksums, question, run mode, model/provider/config identifiers and code revision. Judge receives the record corresponding to the displayed run. | 6/2/9/6/10 | 1–3 hours; reuse report/log endpoints. Distinguish exact playback from rerunning nondeterministic model calls. Include demo inputs when redistributable; otherwise document required input files. |
| 5 | **Real control checkpoints.** Preview/edit a plan before dispatch; cancel an active run with explicit backend acknowledgement; preserve partial evidence. Judge stops execution and sees it cease. | 8/4/6/8/8 | 5–8 hours; new run state/API semantics and cancellation handling. Stretch. A paused animation is not a paused investigation; a chat box cannot redirect agents without actual backend support. |

**Ship order:** protect the basic upload → prompt → agents → report path first. Then ledger/export, two editable mechanism cards, a compact failure suite, and source-selection comparison if time remains. Do not add a fourth specialist, a universal terminal, autonomous experiments, model training, or a new large dataset before these work. Estimates are incremental and should not be blindly summed into the remaining event schedule.

The mechanism cards include a simple missing-evidence checklist. Genuine information-gain ranking remains stretch work requiring a defensible uncertainty model; do not invent numerical value-of-information scores.

## Causal grounding: what the new direction means

The user's recollection is useful motivation, not a verified quotation or a general result that agents reason well. Do not assign it to a speaker. Anna Gogleva is a coauthor of the relevant **Tiny Moves** paper: it reports improved recovery of deliberately corrupted pathway hypotheses through localized edits, with comparable performance to its strongest baseline in reconstruction. That is evidence for a bounded refinement method, not proof that generated mechanisms are true. [Dobrowolska et al., 10 February 2026](https://arxiv.org/abs/2602.09801).

Keep these distinctions visible in the product:

| Layer | What it establishes | What it does not establish |
|---|---|---|
| Citation/provenance | Where a statement or observation came from. | Whether the source supports the statement, or whether the relationship is causal. |
| Evidence sensitivity | Whether an output changes after a source is removed. | The result of intervening on a biological variable. |
| Mechanism hypothesis | An explicit proposed sequence of biological processes, with assumptions and expected observations. | That those processes caused this patient's outcome. |
| Causal identification | Whether a specified causal effect is recoverable from available data under stated assumptions. | Automatic validity of those assumptions or applicability to an individual. |
| Experimental validation | Results of a performed perturbation/test, within its controls and biological context. | Universal transfer to other contexts; a proposed experiment is not a performed one. |

Observation and intervention are mathematically different operations; identification depends on the causal model and assumptions. [Pearl, 1995; PMLR reissue 2022](https://proceedings.mlr.press/r0/pearl95a.html). A recent agent-methodology paper argues that causal claims should rest on data, formal methods, diagnostics and expert decisions, and specifically cautions against treating LLM-supplied edge directions as causal evidence. This is the authors' proposed approach, not a settled ban on hypothesis generation. [Zheng et al., preprint, 22 June 2026](https://arxiv.org/abs/2606.23608).

**Minimum feature:** two mechanism cards with 3–5 links each. Each link stores source/target/process, direction/sign, species/tissue/time context, supporting and conflicting finding IDs, evidence type (observation, association, perturbation, model prediction, or assumption), source status, author and revision. Scientists can edit a link, reject it, or mark it unresolved. Agent suggestions remain labelled proposals; accepting an edit records a user's decision, not scientific validation. Use an edge table first; a graph is optional and must not imply a fitted structural causal model.

The critic checks missing links, context mismatches and whether both explanations fit the observations. Present one discriminating-test card: proposed perturbation or measurement, controls, readout, different predictions under A/B, and an outcome that would challenge each explanation. Start with a clearly synthetic curated pair, such as inadequate target engagement versus downstream bypass, with predefined illustrative predictions. No medical recommendation, patient intervention, wet-lab execution or numerical causal effect is produced. A literature-supported biological demo needs domain review and explicit transfer assumptions.

**Implementation boundary:** existing findings/stance/provenance can populate references, but mechanism records, edit persistence, evidence-type annotations and comparison checks are new backend/UI work. Coordinate additive report fields or a separate versioned artifact; do not silently change the shared event contract. Save immutable revisions and show which links lose support when a source is excluded; unsupported does not mean disproven. LLM extraction is optional and requires live endpoint/schema validation. CPU-only deterministic checks and manually authored synthetic fixtures suffice for the first demo. Automatic pathway-database integration, formal causal discovery and mechanistic simulation are stretch dependencies, not hidden prerequisites.

**Judging consequence:** this raises the originality/scientific-workflow opportunity and makes scientist control concrete, but increases execution risk. It adds no automatic NVIDIA/OpenAI technology credit. If two editable cards cannot work end to end within the timebox, keep a read-only mechanism checklist alongside the working evidence ledger and label it honestly.

As an adjacent direction, EvoSCM studies competing causal models and discriminating interventions in simulated physics. It is explicitly preliminary and is not evidence of biomedical performance. Its relevance is the design idea of committing to different predictions before observing a test result. [Zhao et al., preliminary preprint, 1 September 2026](https://arxiv.org/abs/2609.01526).

The outstanding technology criterion is a separate release gate: demonstrate an actually available NVIDIA component doing necessary work and an OpenAI reasoning call, with identifiable tool input/output in the trace. Verify one real end-to-end call before investing in an integration. CPU hosting and build-time Codex use alone do not establish this. The event's exact “BioNeMo Agent Toolkit” naming remains an on-site clarification, as already recorded in `Context/tooling.md`; do not silently treat different NVIDIA products as interchangeable.

## Terminal-Bench: credible precedent, different target

Terminal-Bench measures agents performing terminal tasks. Its January 2026 paper describes version 2.0 as 89 realistic tasks with dedicated environments, human-written solutions and executable verification. That supports borrowing its evaluation structure, not transferring its scores to biomedical reasoning. [Paper, submitted 17 January 2026](https://arxiv.org/abs/2601.11868).

There is concrete evidence behind its reputation: the official site identifies Stanford/Harbor/Laude hosting, and Anthropic publicly reports using Terminal-Bench in evaluations. “Established and used by major labs” is defensible; “the best benchmark” is not established by these sources. At this research date the homepage labels its featured benchmark **4.0**; 2.0 should therefore be referred to as the version discussed in the cited paper, not the latest. The retrieved homepage contained no usable numeric leaderboard entries, so no current rankings are asserted. [Official homepage, accessed 19 September 2026](https://www.tbench.ai/); [Anthropic engineering, 5 February 2026](https://www.anthropic.com/engineering/infrastructure-noise).

The original announcement even describes a Raman-spectrum task where wavelength/wavenumber confusion produces a successful-looking but meaningless fit: a useful analogy for checking scientific inputs and outputs. Its reusable lesson is to verify artifacts and environment state, rather than reward fluent explanations. [Original announcement, publication date not exposed in retrieved page; accessed 19 September 2026](https://www.tbench.ai/news/announcement).

**Recommendation:** build our own small research-workflow evaluation inspired by these principles. Do not run the full Terminal-Bench suite as the hackathon deliverable, claim its endorsement, call our suite an official extension, or claim Terminal-Bench performance without running the official versioned benchmark. A later terminal-based bioinformatics task collection could be packaged for Harbor; that is future work, not necessary for this UI/API project.

Anthropic's controlled study also found scores sensitive to runtime resource configuration. Record CPU/RAM, timeouts, model settings and per-run failures when comparing systems; small differences are not automatically meaningful. [Infrastructure analysis, 5 February 2026](https://www.anthropic.com/engineering/infrastructure-noise).

## Small evaluation that can actually be finished

Start with six authored cases and an explicit expected **software behavior** per case: valid sourced input; empty/unparseable data; a claim pointing to nonexistent evidence; balanced support/contradiction; an irrelevant hypothesis; and two agents repeating one source. The last case probes a known current limitation rather than assuming the implementation passes. Add a unit-mismatch case only after defining the supported units and expected handling. Do not infer scientific gold labels from provider fixtures.

For the mechanism feature, add at most four adversarial synthetic cases: a deleted source leaves a link unresolved; an association is not relabelled as an intervention; two mechanisms with identical predictions remain unresolved; and a scientist's link edit persists with an auditable before/after diff. Check that proposed tests include readout, controls and contrasting predictions. These verifiers assess state integrity and explicitness, not biological truth. A synthetic simulator with known equations could test intervention predictions later, but would validate only that toy world.

For each case store the input files and hashes, question, permitted outputs, verifier, reference artifact, versioned configuration and captured trace. Keep reference answers/verifiers outside model context. Report counts with denominators: unresolved citations, required abstentions achieved, answer coverage, unexpected errors/timeouts and latency. Keep infra failures distinct from incorrect answers. Prefer simple executable assertions; biologically substantive labels need domain review, and no such review is assumed available.

Compare the same frozen cases and source context against a single-agent baseline using the same model and budget, then optionally ablate the critic. Publish all cases, not only wins. Mock mode is a control-flow regression suite; live mode measures these limited tasks. Small live samples are descriptive and cannot establish calibration or clinical validity. Do not reuse old plan statements predicting that the baseline will fail or that scaffolding will necessarily win.

## Five-minute demo arc

| Time | Action | Proof and criterion |
|---|---|---|
| 0:00–0:30 | State a research question and why uninspectable answers are insufficient. | Scientific relevance; no invented efficiency numbers. |
| 0:30–1:15 | Upload bundled synthetic files, select sources, type a hypothesis and start. | Scientist control and execution; visible mode/provider status. |
| 1:15–2:00 | Follow a specialist exchange; open two candidate mechanism cards and inspect the weakest link's source and evidence type. | Originality and execution; genuine tool output establishes technology use if available. |
| 2:00–3:00 | Scientist edits or marks a link unresolved; show the revision. If implemented, exclude its source and show which links lose support. | Control over explicit assumptions; source ablation is labelled evidence sensitivity. |
| 3:00–4:00 | Show the proposed test with different A/B predictions, then an unresolved case and the measured small-suite results. | Mechanistic discipline and honest limitations; no claimed experiment or causal proof. |
| 4:00–4:40 | Export the run and point to the documented reproduction entry point. | Presentation/reproducibility; show the repository submission artifact. |
| 4:40–5:00 | Explain which validated integrations ran, current limits and one next step. | Accurate technology claim; finish within the event limit. |

If external endpoints remain unavailable, demo the real orchestrator in explicitly labelled mock mode and retain the working product story. Do not imply that this satisfies live NVIDIA/OpenAI integration or scientific performance evidence. Keep a labelled captured run available for connectivity failure.

Local basis: `Context/judgingCriteria.md`, `Context/challengeWeb.md`, `Context/tooling.md`, `Plan/README.md`, `Plan/00-decision-framework.md`, `Plan/finalists/F1-failure-benchmark.md`, `Plan/finalists/F2-variant-triage.md`, and `ARCHITECTURE.md`. Pre-event predictions in those plans are scaffolding, not results.
