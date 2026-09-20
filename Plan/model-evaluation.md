# Model evaluation: workflow checks first, biology benchmarks next

Research date: 19 September 2026. No external benchmark or live model was run.
External benchmarks below were researched; no LAB-Bench, BixBench or Harbor dataset
adapter has been implemented. The working adapter targets this repository's engine.

**Recommendation:** use the new local `eval/` harness for a frozen failure-case demo
now. For independent external evidence, start with a small, prespecified LAB-Bench
subset if the task remains evidence interpretation; use BixBench if the teammate's
backend becomes a computational-data-analysis agent. Consider Terminal-Bench-Science
through Harbor when the agent can actually execute terminal tools in a sandbox.
Do not select a model for this scientific workflow from a general terminal leaderboard.

This follows [feature-direction.md](feature-direction.md): the scientist controls the
investigation, traces evidence, challenges a mechanism, and sees honest abstention.
Terminal task completion and biological/causal validity are different measurements.

## Candidate comparison

Effort below is our integration estimate, not measured benchmark runtime. License
labels are the upstream project's declarations, not a license review of every
external paper, image, tool, or dataset that it references. Pin releases and inspect
task-specific materials before redistributing them.

| Candidate | What it measures and fit | Access, license, effort | Decision |
|---|---|---|---|
| General Terminal-Bench / Harbor | Containerized terminal-task execution. Useful for tool reliability, weak direct evidence of the proposed mechanism-review workflow. Harbor supports parallel agent/model/task/sandbox evaluations. | New sandbox agent adapter; no terminal executor exists in this backend. Medium/high effort. Benchmark releases and task assets need their own license check; Harbor is the runner, not the task set. | Borrow execution/verifier separation; do not claim a terminal score validates biology. [Harbor documentation](https://docs.harborframework.com/), [Terminal-Bench releases](https://www.tbench.ai/benchmarks) |
| Terminal-Bench-Science | Scientific workflows with objectively verifiable terminal outputs; current repository describes 70 tasks across five domains. Closer than general Terminal-Bench if the system gains executable analysis. | Apache-2.0 repository; task-specific dependencies and sandbox checks remain necessary. Harbor integration plus actual analysis tools: medium/high effort. The upstream example uses paid hosted sandboxes and high concurrency; do not copy those settings blindly. | Optional next step, small biology-relevant subset and oracle/no-op checks first. [Official repository](https://github.com/harbor-framework/terminal-bench-science) |
| LAB-Bench | Biology research questions spanning literature, figures, databases and sequences. A component-level reasoning baseline, not full workflow execution or causal validation. | Public HF card declares CC-BY-SA-4.0. Low/medium effort for a text-only, prespecified subset; figure tasks need a multimodal adapter. Keep labels outside model inputs. | Best small external starting point if evidence interpretation remains central. [Dataset card](https://huggingface.co/datasets/futurehouse/lab-bench), [paper](https://arxiv.org/abs/2407.10362) |
| LABBench2 | More realistic biology research tasks with an official model/agent harness and supporting files. | Dataset and repository declare CC-BY-SA-4.0. HF currently requires accepting access conditions/contact sharing; supporting data download on demand. Medium effort, blocked on user dataset access if not already accepted. | Preferred follow-on to LAB-Bench once access and task selection are settled. Do not automate agreement to the gate. [Dataset/access terms](https://huggingface.co/datasets/EdisonScientific/labbench2), [official harness](https://github.com/EdisonScientific/labbench2) |
| BixBench | Real bioinformatics dataset analysis, code execution and interpretation; current repository/card show 205 questions. Better match if the teammate adds RNA-seq/statistical pipelines. | Apache-2.0 repo and HF card; check underlying capsule data. Official setup requires HF authentication and a notebook/container environment. Medium/high effort; existing agents do not execute Python/R analysis. Full upstream multi-model automation is expensive. | Choose a few matched capsules only after the analysis backend exists; use official graders and report subset/version. [Official harness](https://github.com/Future-House/BixBench), [dataset](https://huggingface.co/datasets/futurehouse/BixBench) |
| BixBench3 | Research-scale reproduction from raw data with deterministic artifact grades plus a separate process judge. | CC-BY-SA-4.0 authored materials; upstream data retain their terms. Official setup needs a billable GCP project/VM, provider keys and separately licensed 10x tools. High effort; documented runs can last hours. | Too large for this demo; useful later for artifact-level rigor. [Official runner, requirements and license](https://github.com/EdisonScientific/BixBench3) |

None of these datasets directly certifies this patient's causal mechanism. A custom
mechanism benchmark needs reviewed competing hypotheses, evidence context, acceptable
claims, missing-evidence cases, and predictions that distinguish alternatives. Leave
clinical/causal correctness unscored until that rubric and expert labels exist.

## Working implementation

`eval/runner.py` is backend-independent: a fresh adapter receives only case inputs and
configuration, never expected labels. It runs the Cartesian product of cases and
configurations with bounded concurrency, optional repetitions and per-trial timeouts.
Each completed/error trial is appended to a new JSONL file. One backend failure does
not abort other trials. An existing output file is not overwritten.

`eval/investigation.py` adapts the current engine and providers; replacing it does not
require changing the runner. It records provider-call elapsed time, report/events,
input file content hashes, effective model/API/output budget/provider timeout, and
actual reasoning-response token usage through the shared live transport. Core records
also contain input/config/label hashes, Git revision, dirty-tree flag, queue time and
total trial wall time. A dirty tree is flagged, not represented as reproducible solely
from HEAD; archive or commit the exact evaluated code for a published comparison.

Usage includes raw provider records. Missing usage is null, never an estimated zero.
Mock tokens are explicitly not applicable. Bio-tool usage and monetary cost remain
unavailable. On timeout, completed response usage is retained when available; an
in-flight call may still consume unreported tokens. Reasoning tokens and cached input
details remain in the raw record; do not double-count them by adding them to totals.

Current metrics are behavioral answer/abstention checks, citation **presence**, tool-call
and error counts. Citation presence does not measure source resolution or entailment.
Scientific correctness, causal validity and citation entailment remain null. Errors
and timeouts are not scored as successful abstentions. A complete report may still
have specialist errors; inspect `provider_error_events` alongside behavior checks.

The bundled three-case suite tests the repo's synthetic sample, an empty upload, and
an unrelated hypothesis. It is a regression suite, not an independent model test set.
The two bundled configurations compare full planning with one clinical specialist;
they demonstrate roster sensitivity, not a model ranking.

```powershell
.venv/Scripts/python.exe -m eval --output eval/results/my-comparison.jsonl --concurrency 2
```

The executed local smoke produced six trials, five behavioral passes, no execution
failures. The clinical-only configuration fails the supported-case expectation, as
expected when genomic evidence is withheld. Those are measured mock behavior results,
not biological scores or live-model performance. See `eval/results/mock-smoke-final.jsonl`.

## Fair live comparison

1. Freeze a case manifest, actual file checksums and reviewed verifier/labels before
   selecting models. Reserve held-out cases; do not tune prompts on the reported test
   cases or put labels in the retrieval corpus. Respect upstream contamination canaries.
2. Use the same roster, bio providers, tools, output budget, transport, prompts, timeout
   and dataset across models. Record unavoidable transport/sampling differences.
   Current chat transport uses temperature 0.2/JSON mode; Responses omits model-specific
   options. Prefer the same supported transport across comparisons.
3. Start at concurrency two; parallel evaluation saves elapsed time but can introduce
   rate-limit/queue contention. Keep queue time distinct, repeat comparisons, report
   per-case failures and latency distributions; a tiny subset is descriptive only.
4. Measure tokens from provider usage and wall time with a monotonic clock. Compute
   monetary estimates only with a dated, explicit rate table including cache/reasoning
   and external tool charges; label estimates. No cost calculator is implemented yet.
5. Keep behavior accuracy, abstention coverage, incorrect confident answers, source
   entailment, artifact correctness and operational reliability separate. Do not turn
   the existing heuristic confidence into an effectiveness score or calibrated metric.

Live use requires `--live`, a live configuration file, reasoning credentials/model
access and functioning BioNeMo endpoints for selected bio specialists. Rosalind access
and Responses compatibility are separate setup concerns. No credentials are stored in
configuration/results. Only use inputs intended for the configured service; exported
artifacts contain questions, findings, sources and reports. No live evaluation was
performed in this implementation task; credentials/endpoints and the actual model
comparison scope remain to be configured.

## Next bounded step

After the teammate supplies the dataset shape, implement a second adapter and a
reviewed 10–20-case subset manifest. For deterministic numerical outputs, use exact or
tolerance-based artifact checks. For literature/mechanism claims, review citation
entailment and unsupported causal assertions separately. Export aggregate comparisons
only after retaining per-case outcomes, errors and raw usage. Add Harbor only if tasks
actually require isolated terminal execution; the in-process runner is not a sandbox.
