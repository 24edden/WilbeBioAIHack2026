# Benchmark design and scoring

These methodological conventions are practical recommendations. Choose a design that matches the intended claim rather than treating one metric or split as universal.

## Dataset construction

Define what each task represents and why the collection represents the target workload. A balanced challenge set and a production-frequency sample answer different questions; report them separately or use prespecified, justified weights.

Each task should identify its source, source date/version, split, dependence group, category, difficulty if defensible, input, required fixtures, and scoring contract. Private grading material should be stored separately from agent-visible inputs. Stable task IDs are useful for joins; content hashes detect accidental changes. Do not let a task-ID update conceal a changed question.

Review ambiguous questions and reference errors before the held-out run. Record exclusions and adjudication rules. A task may allow multiple answers or an appropriate clarification; encode that explicitly. Preserve cases where the right result is that available evidence is insufficient.

Check exact duplicates, near-duplicates, shared source fragments, and generated variants. Keep development examples and grader calibration separate from final evaluation where feasible. Once a test has influenced tuning, disclose that use and obtain new held-out evidence for strong generalization claims.

For biological applications, choose grouping to match the generalization claim: patient or study for clinical observations, sequence-similarity groups for related proteins, or scaffold/temporal splits for molecular tasks when appropriate. Random row splitting alone does not establish independence. Define clustering and similarity criteria explicitly and validate them with domain expertise. Record database releases and reference assemblies where relevant. Computational scores do not by themselves demonstrate clinical or experimental efficacy.

## Agent environments

Package a reproducible initial state: files, tool schemas, service fixtures, clock assumptions, allowed actions, and resource budget. Reset or recreate this state for each task and repetition. An agent should not see prior candidates' artifacts or private grading files.

Use deterministic tools or recorded responses for controlled comparison. Label such evaluation as simulated or replayed. Use live services only when live variability is part of the intended measurement, recording timestamps and external failures. Execute state-changing tests in scoped test environments, consistent with the user's authorization.

Compare both final outcomes and relevant behavioral constraints. A tool call can be correctly formatted but unauthorized, or successfully executed without achieving the goal. Verify resulting state. Inspect recovery, unnecessary actions, and permission boundaries separately from answer quality.

## Grading contracts

For each metric specify: measured property, admissible evidence, score range, aggregation, missing/error handling, threshold, and examples at the decision boundary. Numerical tolerance, units, citation validity, partial credit, and alternative correct solutions belong in the contract where applicable.

Do not average away critical violations through a high fluency score. Report hard requirements independently or define an explicit gated success metric. Choose exact-match scoring only where exact identity matters; choose executable tests for behavior and structured rubrics for semantics.

For model judges, pin the available model identifier, prompt, rubric, parameters, and output schema. Remove candidate identity where possible, randomize pairwise order, allow ties, and test position/verbosity bias. Assess agreement and false acceptance/rejection against adjudicated examples. Calibrating a judge against itself provides little independent evidence. Give judges enough source evidence to check factual claims.

Challenge graders with an empty output, a polished wrong answer, an incomplete answer, a valid alternate solution, and text trying to instruct the judge to award a perfect score. Keep parsing/transport failures distinct from a legitimate low score. Cache results only under a key that includes the candidate output, reference material, rubric, and judge configuration.

## Comparisons and uncertainty

Choose sample size using the effect or precision that matters and pilot variability when available. Do not prescribe a universal number of examples. If only a small smoke set is feasible, label conclusions accordingly.

For system A versus B, use paired task instances. Estimate uncertainty on paired differences, clustering by the independent source unit when tasks share a source. A cluster bootstrap may be appropriate with enough independent clusters; an ordinary row bootstrap does not repair dependence. Report the resampling unit, repetition policy, method, and limitations. For tiny samples or zero/all successes, avoid a bootstrap interval that spuriously implies certainty; use a method appropriate to the design.

Keep sampling uncertainty across tasks separate from variability across repeated executions of the same task. Report both counts. Success on a single attempt, success on at least one of several attempts, and consistent success across attempts measure different properties. Name the estimator, attempt budget, and selection procedure. Include selection/judge costs in best-of-many comparisons.

Define an operational completion rate over scheduled trials and, if useful, a conditional quality score over valid trials. Always show excluded/invalid counts and reasons. An infrastructure exclusion policy must be fixed and applied consistently; outage-heavy systems should not receive an artificially strong headline score.

Report total evaluation expense, per-task resources, and cost per verified successful task with clear numerators and denominators. Zero verified successes makes cost per success undefined. Distinguish time to first output from completion latency; disclose concurrency, retries, warm-up, and cache conditions. Include failed and timed-out work in operational accounting.

Avoid declaring a winner just from overlapping or nonoverlapping individual intervals; analyze the comparison itself. Distinguish statistical evidence from practically meaningful improvement. For many candidates or exploratory slices, disclose selection and multiplicity; confirm important findings on fresh held-out data when needed.

## Suggested result record

Keep task ID, group ID, system/config hash, repetition, attempt, generation status, grading status, candidate output or artifact reference, score components, verifier evidence, latency, resource use, and error classification. Store sensitive payloads only where authorized. Preserve original outputs when recomputing metrics.

A useful report states the evaluated claim, dataset coverage, excluded cases, comparison controls, metrics and uncertainty, cost/latency, error analysis, known contamination risks, and reproduction steps. Mark every value as observed, estimated, or proposed as appropriate.
