---
name: agent-harness-building
description: "Design, build, or improve AI agent harnesses: runtime loops, tool execution, permissions, durable state, interruption recovery, tracing, and integration with OpenAI or NVIDIA tooling. Use for agent infrastructure rather than ordinary prompt editing."
---

# Agent Harness Building

Build the application that makes an agent's actions reliable and verifiable. Preserve the user's requested stack, scope, and existing authorization. Do not treat this skill as permission to deploy, access new systems, or run costly workloads.

## Shape the runtime

Establish the task contract, observable completion condition, tool authority, state lifetime, and resource limits. Inspect an existing implementation before proposing a replacement. Start with one agent when sufficient; add specialists only when separate capabilities, instructions, or ownership measurably help.

Choose who owns the loop and state: a managed runtime, an SDK in the application, or a custom model/tool loop. Keep trusted policy, credentials, and recovery records separate from model-directed code execution. Distinguish conversation memory, execution checkpoints, and sandbox contents; saving one does not automatically save the others.

For detailed runtime choices, failure cases, and official source links, read [the harness playbook](references/harness-playbook.md). Its product notes are dated research, not installed-version guarantees. Verify official API documentation and local dependencies before writing integration code.

## Enforce action contracts

Use explicit tool schemas and server-side argument validation. Supply known identity and resource scope from trusted application context. A model-selected resource identifier is not authorization. Keep tool outputs compact, typed where useful, and linked to their originating calls.

Handle multiple calls, partial/streamed arguments, failures, and actual stopping conditions. Do not execute incomplete streamed arguments or report a requested action as a completed action. Preserve the chosen API's required continuation items and use a deliberate conversation strategy to prevent duplicated history.

Place checks at the side-effect boundary. Apply existing scoped authorization automatically where appropriate; when required review is missing, persist the exact pending action and resume that same run after the decision. Do not create a fresh task that loses the approval or execution context.

## Recover safely

Represent running, paused, completed, failed, cancelled, and budget-exhausted states explicitly. Persist action intent and observed outcome. For state-changing operations, use stable operation IDs and downstream idempotency or reconciliation; an ambiguous timeout does not establish that an operation failed.

Bound retries, model turns, tool calls, elapsed time, spend, and concurrency as appropriate to the workload. Retry transient errors deliberately, not invalid arguments or denied authority. Reset or isolate mutable workspaces between unrelated tasks. Propagate cancellation and record whether in-flight external work actually stopped.

Prevent untrusted source text from becoming trusted instructions. Keep secrets and unrelated data out of execution environments and traces. Treat schema validation and content checks as complementary to authorization, not replacements for it.

## Verify the implementation

Inspect end-to-end traces and test the behaviors introduced by the change: tool errors, cancellation, pause/resume, worker restart, uncertain writes, and limits where relevant. Verify resulting artifacts or external state before declaring completion.

Measure task success, failure classes, cost, and completion latency before adding orchestration complexity. For formal benchmark creation, use a suitable benchmark workflow if available; this skill does not require an additional installed skill.

Deliver the implemented changes or requested design, validation evidence, setup needed to run it, and material limitations. Distinguish tested behavior from a proposed design and a local smoke test from production evidence.
