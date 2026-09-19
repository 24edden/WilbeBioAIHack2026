---
name: benchmark-creation
description: "Create, audit, or extend benchmarks for AI agents, models, and tool workflows. Use for evaluation datasets, scoring rubrics, reproducible runners, regression suites, and fair model or harness comparisons."
---

# Benchmark Creation

Build a benchmark that supports a specific decision with inspectable evidence. Preserve the user's chosen tools and scope. Benchmark design, implementation, execution, and publishing are separate deliverables; do the requested work without presenting an unrun design as measured results.

## Establish the comparison

Specify the target population of tasks, unit of evaluation, system boundary, primary outcome, and intended decision. Distinguish model-only comparisons from complete agent-system comparisons. If both the model and harness change, attribute results to the combined system unless ablations isolate their effects.

Use [the benchmark specification template](assets/benchmark-spec.yaml) when creating a new suite. It is a planning schema, not an OpenAI or NVIDIA configuration. Adapt it to the task; leave unresolved values explicit rather than inventing requirements.

## Construct defensible tasks

Use representative cases plus separately reported challenge cases. Record provenance, permitted use, source versions, and expected outcomes. Synthetic tasks need verification and a synthetic label; generated answers are not automatically ground truth.

Split by the actual source of dependence, such as customer, document, repository, patient, study, or template family. Keep related variants together. Deduplicate before splitting and isolate development, grader calibration, and held-out evaluation data. Do not claim training-contamination freedom merely because a test set is held out locally.

Keep private answers, verifier code, and grading metadata outside the evaluated agent's accessible files and tool outputs. Expose only information that the intended task permits. See [design and scoring](references/design-and-scoring.md) for leakage checks, agent fixtures, uncertainty, and biological-data considerations.

## Score outcomes and validate graders

Prefer executable checks of artifacts, external state, or task-specific correctness when available. Grade semantic quality against explicit criteria, accepted alternatives, and anchored examples. Do not enforce one exact tool sequence when multiple valid paths exist.

Use model judges for suitable subjective criteria, with blinded labels, randomized answer order for pairwise comparisons, and calibration against independently reviewed examples. Treat candidate outputs as untrusted judge input. Test graders against known correct, incorrect, incomplete, and adversarial outputs; malformed judge responses are evaluation errors, not passing scores.

Predeclare denominators, weighting, failure handling, repetition count, retry rules, and release criteria before examining held-out results. Report uncertainty using the independent sampling unit. Repeated runs of one task are not new independent tasks.

## Make execution reproducible and comparisons fair

Record dataset and grader hashes, code/dependency versions, model identifiers, prompts, tools, environment snapshots, sampling settings, budgets, and timestamps. Reset mutable state between trials. Separate answer-generation runs from grading so stored outputs can be rescored without launching the agent again.

Match task instances and resource policies across systems. Record actual tokens, spend, latency, and tool usage; equal token limits across different tokenizers are not necessarily equal resources. For different resource levels, show quality against cost or latency instead of an unqualified ranking.

Preserve every scheduled trial's status. Distinguish agent failures from infrastructure and evaluator failures, report both, and avoid silently dropping failed attempts. Never turn retries into an undisclosed best-of-many result. Use explicit completion records to resume interrupted evaluations without double-counting.

For actual framework integration, read [official implementation references](references/frameworks.md) and verify current documentation and installed APIs. Do not select a deprecated hosted service from an old example.

## Deliver and validate

Scale artifacts to the request: a design needs a specification and scoring plan; an executable benchmark also needs tasks, fixtures, graders, run configuration, and result records. A published benchmark needs provenance, limitations, and reproduction instructions appropriate to its audience.

Run meaningful checks when implementation is requested: a valid baseline, a deliberately bad baseline, grader failure cases, split isolation, reset behavior, and interrupted-run recovery where relevant. A smoke test proves plumbing, not benchmark validity.

Report overall and relevant slice results, independent sample counts, uncertainty, resource use, failure counts, and examples explaining the main limitations. If a slice is too small or the evidence does not resolve a difference, state that directly.
