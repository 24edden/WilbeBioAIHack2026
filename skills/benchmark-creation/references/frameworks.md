# Official implementation references

Reviewed 19 September 2026. Recheck linked documentation and installed package versions before implementation. The core skill's statistical and design recommendations are synthesis, not vendor guarantees.

## OpenAI

OpenAI recommends task-specific evaluations, representative and challenging examples, explicit success criteria, and human calibration of automated graders. Its guidance distinguishes outcome correctness, tool selection, arguments, and handoffs. Use this methodology without copying example thresholds as universal requirements. [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)

The official deprecation notice says existing hosted Evals become read-only on 31 October 2026 and the Evals dashboard and API are scheduled to shut down on 30 November 2026. Graders documented for those workflows are included in the transition. Do not start a new benchmark by assuming these hosted endpoints are a durable default. Consult the current notice and its migration guide; keep datasets and scoring portable. [Evals platform deprecation](https://developers.openai.com/api/docs/deprecations#2026-06-03-evals-platform)

For agents, traces help explain tool and routing failures; repeatable datasets support comparisons. Instrument the chosen runtime and retain exportable execution evidence. Verify which hosted evaluation surfaces remain available. [Agent evaluations](https://developers.openai.com/api/docs/guides/agent-evals)

## NVIDIA

NeMo Agent Toolkit provides dataset-driven workflow evaluation, pluggable graders, repeated runs via `--reps`, controlled concurrency, and scoring of saved answers via `--skip_workflow`. Verify the installed command's options rather than copying configuration across versions. Keep interrupted-run recovery distinct from rerunning failed answers until they pass. [Workflow evaluation](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/evaluate.html)

The custom-evaluator guide documents registration and discovery of evaluator components. Choose a task-specific grader where a general semantic metric cannot establish success. [Custom evaluators](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/custom-components/custom-evaluator.html)

NeMo Agent Toolkit profiling complements quality scores with invocation timings, token usage, bottleneck and concurrency analysis. Instrumentation coverage affects what is visible; a missing span is not proof that no work occurred. [Profiling](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/profiler.html)

## Integration invariants

Own the benchmark's task schema and explicit projection into each runner. Never pass private answer/grader fields into agent inputs just because a dataset loader exposes the entire row. Map output and error states explicitly, preserve source records, and validate the adapter with a correct answer, wrong answer, and evaluation failure.

Export the actual generation and grading configuration separately. A remote evaluator's local configuration does not fully identify the remotely deployed agent. Preserve its model, prompt, tool, code, and environment versions too.
