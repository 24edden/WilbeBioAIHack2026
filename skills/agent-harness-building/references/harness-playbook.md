# Agent harness playbook

Reviewed against official OpenAI and NVIDIA documentation on 18 September 2026.

Purpose: a reusable implementation reference for future agent work in this project. This is researched guidance, not an implemented or benchmarked harness. Product details must be checked again against the installed versions when building. Sections marked “Engineering recommendation” are my synthesis rather than promises made by either vendor.

## What the harness owns

The harness is the application around the model: it runs the loop, routes tools, manages state, applies permissions, records execution, and handles recovery. The execution environment is a separate concern: it provides files, commands, packages, and compute. Keep credentials, policy decisions, and recovery records in the trusted application; give execution environments only the access needed for their task. OpenAI's sandbox-agent APIs are currently beta. [OpenAI: sandbox agents](https://developers.openai.com/api/docs/guides/agents/sandboxes)

Engineering recommendation: judge a harness by whether it completes real tasks correctly, recovers from interruption, and stays within its authority and resource budget. A convincing final answer is insufficient evidence of a completed action.

## Choose the smallest appropriate stack

| Requirement | Starting point | Design consequence |
| --- | --- | --- |
| Managed, long-running agent sessions | OpenAI Agents API | OpenAI operates the harness; check its state, retention, and environment constraints before choosing it. |
| Custom application with tools and explicit runtime ownership | OpenAI Agents SDK | The SDK provides the loop; the application owns deployment, tool implementations, storage, and permissions. |
| Direct model calls or a deliberately custom loop | OpenAI Responses API | The application must implement the orchestration it needs. |
| Compose, evaluate, and profile workflows across frameworks | NVIDIA NeMo Agent Toolkit | Integrate the required functions and instrumentation into the existing workflow. |
| Additional input, retrieval, tool, or output checks | NVIDIA NeMo Guardrails | Verify the selected engine and API format support each configured check. |

OpenAI distinguishes the Agents API, Agents SDK, and Responses API as separate runtime choices. An SDK session, API session, conversation, and sandbox are also distinct resources. [OpenAI: agent runtimes](https://developers.openai.com/api/docs/guides/agents)

NVIDIA positions NeMo Agent Toolkit as a framework-flexible composition, observation, evaluation, and profiling library. It can complement existing agent software. [NVIDIA: toolkit overview](https://docs.nvidia.com/nemo/agent-toolkit/latest/)

Engineering recommendation: default to one agent with a small tool set and a measured task contract. Add another framework only to solve a demonstrated need. Do not assume that every provider, transport, and instrumentation adapter is interchangeable.

## Define success before implementation

Engineering recommendation: record this contract for each workflow:

| Contract field | What to specify |
| --- | --- |
| Task | Exact user outcome and explicit exclusions |
| Inputs | Accepted formats, required context, and trusted identity |
| Tools | Allowed operations and resource scope |
| Result | Output schema, artifacts, and supporting evidence |
| Completion check | Observable condition establishing success |
| Budgets | Time, model turns, tool calls, tokens or spend, and concurrency |
| Interruptions | Cancellation, missing information, and review behavior |
| Recovery | Durable state, replay rules, and reconciliation of uncertain writes |

For this AI × Bio project, an example is “produce a cited evidence table from specified public sources.” Validate identifiers and citations and preserve distinctions between source findings and inference. File analysis should record input hashes, dataset/reference versions, parameters, and output locations. These are proposed project conventions, not a biological analysis protocol.

## Implement the loop and its stopping conditions

The SDK runner calls the model, executes requested tools, follows handoffs, and continues until a final result or interruption. A final response, an approval pause, and a runtime failure require different handling. Streaming does not change those semantics; settle the stream before treating the result as complete. [OpenAI: running agents](https://developers.openai.com/api/docs/guides/agents/running-agents)

Engineering recommendation: use explicit run statuses such as `running`, `waiting_for_input`, `waiting_for_approval`, `completed`, `failed`, `cancelled`, and `budget_exhausted`. A worker crash should leave a recoverable record, not a misleading completed status.

Conceptual control flow—not an SDK code example:

```text
Load the task, identity, policy, budgets, and durable state.
If cancellation or a budget limit applies, stop with an explicit status.
Call the model with the relevant context and allowed capabilities.
For each requested action:
    Validate its name, arguments, resource scope, and authorization.
    Pause and persist if a required decision is missing.
    Record the intent; execute with timeout and duplicate protection.
    Record the observed result and return it to the model.
Checkpoint progress and repeat while work remains.
Validate final artifacts and completion evidence before reporting success.
```

## Make tool contracts precise

Use descriptive names, parameter schemas, and clear usage guidance. Prefer enums and structured arguments over ambiguous strings. Supply known values from application state instead of asking the model to invent them. Keep the initially exposed tool set small; defer tools when supported and useful. With strict function schemas, set `additionalProperties: false` on objects and require every property; represent optional values with nullable types. [OpenAI: function calling](https://developers.openai.com/api/docs/guides/function-calling)

Handle zero, one, or multiple function calls. In Responses, match results using `call_id`; preserve the required model output items, including reasoning items when replaying a reasoning-model interaction. Do not mistake a function-call item for successful execution. [OpenAI: function calling](https://developers.openai.com/api/docs/guides/function-calling)

Engineering recommendation: validate arguments again on the server. Bind tenant and user permissions to authenticated application context. Return compact, typed results with status, evidence references, and recoverable error details. Keep large artifacts in storage and return references. Streamed argument fragments are not executable requests.

## Separate conversation memory from execution state

Choose one conversation strategy: local history, SDK sessions, a server-managed conversation, or response chaining. Mixing history replay and server-managed context can duplicate content. Approval interruptions should resume the same saved run rather than start a fresh user turn. [OpenAI: running agents](https://developers.openai.com/api/docs/guides/agents/running-agents)

Engineering recommendation: store conversation context separately from task checkpoints, tool execution records, and artifact manifests. Conversation history alone does not establish whether an external write happened. An in-memory session is not durable storage.

Persist the original goal, accepted constraints, completed steps, unresolved questions, artifact references, and remaining budget. Keep source evidence accessible after summarization. Use per-session locking or version checks when workers can update the same state.

## Recover without duplicating actions

Engineering recommendation:

- Give state-changing operations stable operation IDs and use downstream idempotency mechanisms where available.
- Persist action intent before executing and observed outcome afterward. A crash between those events requires reconciliation.
- After an uncertain timeout, check the external system before retrying a write. A missing response does not prove failure.
- Retry transient read failures with bounded backoff and jitter. Do not repeatedly retry invalid arguments, denied permissions, or permanent errors.
- Limit both model turns and tool operations: a single turn may produce multiple actions.
- Apply deadlines and cancellation to child work as well as the parent. Report whether already-started external operations actually stopped.
- Detect repeated unsuccessful actions and route them to a clearer failure or information request.

## Put checks beside the actions they protect

OpenAI distinguishes automatic guardrails from approval interruptions. Agent input guardrails apply at the initial agent boundary; output guardrails apply to the final-producing agent. Tool guardrails cover the function tools to which they are attached. Consequently, an outer input check does not replace validation at an internal tool boundary. [OpenAI: guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)

Engineering recommendation: encode standing authorization and operation scope in policy so routine authorized work proceeds automatically. Request review only when required by that policy or missing user authority, and bind approval to the exact proposed operation. Approval is not a substitute for authorization checks.

Keep retrieved documents and tool outputs separate from trusted instructions. Structured interfaces reduce opportunities for malicious external content to influence later steps, but do not eliminate prompt injection. [OpenAI: agent safety](https://developers.openai.com/api/docs/guides/agent-builder-safety)

## NVIDIA compatibility details to remember

NeMo Agent Toolkit uses YAML to connect named functions, models, and workflows, with optional memory, retrieval, and evaluation configuration. Component configuration uses Pydantic models and typed references. [NVIDIA: workflow configuration](https://docs.nvidia.com/nemo/agent-toolkit/latest/build-workflows/workflow-configuration.html)

The NeMo Guardrails tool-calling guide currently describes experimental, opt-in IORails validators for the OpenAI Chat Completions wire format. It explicitly excludes Responses API support. The harness still executes tools. Result validation checks structural consistency, not content safety, output-schema correctness, or independently verified provenance. The guide also documents silent engine fallback on some invalid configurations and recommends `require_iorails=True` when IORails is required. [NVIDIA: tool calling](https://docs.nvidia.com/nemo/guardrails/configure-guardrails/guardrail-catalog/tool-calling)

Engineering recommendation: build compatibility tests for the exact model, API format, SDK version, and guardrail engine. Use application-side validation when the chosen integration lacks the required coverage. Verify actual engine selection at startup; do not treat a configuration file as proof that a check ran.

## Add specialists only when useful

OpenAI recommends beginning with one agent. Handoffs transfer ownership to a specialist; agents-as-tools keep the manager responsible for the final answer. Specialization is useful when instructions, capabilities, or policy boundaries materially differ. [OpenAI: orchestration](https://developers.openai.com/api/docs/guides/agents/orchestration)

Engineering recommendation: each specialist needs a bounded input, output contract, budget, cancellation path, and merge owner. Parallelize independent work, serialize dependencies and conflicting writes, and include delegation cost in the baseline comparison.

## Observe and evaluate real outcomes

OpenAI SDK tracing records model calls, tools, handoffs, and guardrails and is enabled by default in the normal server-side path. Use traces to diagnose failures, then build repeatable evaluations. [OpenAI: observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)

OpenAI recommends trace grading for workflow diagnosis and datasets/evaluation runs for comparisons and regression tracking. [OpenAI: agent evaluations](https://developers.openai.com/api/docs/guides/agent-evals)

Update checked 19 September 2026: OpenAI's hosted Evals platform is deprecated. Existing evals are scheduled to become read-only on 31 October 2026, with dashboard/API shutdown on 30 November 2026. Keep benchmark tasks, graders, and records portable, and check the migration guidance before choosing a hosted evaluation implementation. [OpenAI: Evals deprecation](https://developers.openai.com/api/docs/deprecations#2026-06-03-evals-platform)

NVIDIA's `nat eval` executes configured datasets and evaluators. It saves individual workflow results and original/effective configuration. For remote evaluations, that saved configuration does not capture the remote application's own workflow configuration; preserve that separately. [NVIDIA: evaluation](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/evaluate.html)

NVIDIA's profiler captures invocation timing and token usage and can analyze bottlenecks, concurrency spikes, and reusable prompt prefixes through the evaluation workflow. Supported wrappers or explicit instrumentation are needed for useful coverage. [NVIDIA: profiling](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/profiler.html)

Engineering recommendation: track verified task completion, tool success, permission violations, duplicate writes, recovery success, cost per successful task, and median/tail latency. Redact secrets and sensitive data before exporting traces. Log observable actions and results; do not depend on hidden model reasoning.

## A minimum evaluation set

These are proposed test cases, not measured results:

| Scenario | Expected evidence |
| --- | --- |
| Ordinary task | Correct result and valid artifact/source references |
| Ambiguous input | Focused clarification instead of guessed critical values |
| Unknown tool or malformed arguments | Rejected before execution |
| Unauthorized resource | Denied regardless of model-generated arguments |
| Malicious instructions in retrieved text | No escalation of tool authority |
| Transient read timeout | Bounded recovery or accurate failure status |
| Write succeeds but response is lost | Reconciliation without duplicate effect |
| Approval pause and process restart | Same pending operation resumes correctly |
| Cancellation and exhausted budget | No new work launched; honest final status |
| Large context and multiple sessions | Goal preserved and sessions isolated |
| Tool error followed by confident prose | Completion validator detects the mismatch |

Engineering recommendation: maintain held-out cases and repeat stochastic runs. Prefer deterministic checks of artifacts and external state where possible; calibrate model-based judges against human assessment. Define release thresholds before tuning. A small test suite can detect regressions but cannot prove universal reliability.

## Build order for the next project

1. Define the task contract and representative success/failure examples.
2. Select the runtime and pin compatible dependencies.
3. Build one agent with the minimum necessary tools.
4. Add argument validation, authorization, deadlines, and execution records.
5. Add durable state, pause/resume, cancellation, and write reconciliation.
6. Inspect complete traces and run the evaluation set.
7. Profile the measured bottleneck and change one variable at a time.
8. Add specialists, richer memory, or additional frameworks only when the measured benefit justifies them.

Before implementation, revisit the linked official pages for changed APIs, supported engines, model compatibility, retention controls, and experimental features. This file preserves the research; it does not change the model's underlying training or guarantee recall in unrelated tasks.
