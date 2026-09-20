# Explicit recovery from a known incomplete synthesis

An initial investigation can now reuse its seven accepted specialist handoffs when the coordinator returns HTTP 200 with `status: incomplete` and `incomplete_details.reason: max_output_tokens`. This is a new, explicitly selected operation on the same investigation. It does not retry the old request, rewrite its failure or treat its partial text as an accepted answer.

## Acceptance and lineage

- The latest operation must have no issued decision or accepted coordinator/reviewer product. Its research action must have a known failed outcome, with request and response IDs. Unknown, submitting, cancelled or otherwise unqualified work is rejected.
- Exactly one accepted product from each of the seven specialist roles is required. Original hypothesis/source, case snapshot, evidence, source versions, process contract, skills, routes, dependencies and acceptance receipts are verified. Blocked and inconclusive products keep those meanings.
- The server builds and freezes the checkpoint; the caller supplies only the source operation ID and an idempotency key. Its content is checked again before execution and before accepting fresh synthesis/review handoffs.
- Original handoffs, skill receipts, failed actions and usage remain unchanged. New operation records name the checkpoint, original operation/action and reused handoff IDs. No duplicate specialist product or model call is manufactured.
- Only the verified old upstream IDs become eligible inputs to the new coordinator/reviewer acceptance checks. This is a narrow evaluation allowance, not permission to reuse arbitrary old work across operations.

Coordinator and reviewer run afresh with their own skill receipts, evidence reads, tools and acceptance checks. Partial coordinator output, unaccepted proposals and unfinished governance are discarded. Only proposals attached to accepted specialist products survive.

## Scientific scope

Checkpoint synthesis reads the exact preserved evidence. It cannot execute new analysis, diagnostic or NVIDIA work while skipping the specialists. If a new test is needed, the reviewer can select a qualified registered follow-up through the existing hypothesis-governance contract. After publication, that action follows the normal durable executor and full specialist/reviewer cycle. The original hypothesis remains unchanged.

This path is limited to initial synthesis and a later known incomplete coordinator attempt against the same checkpoint. It is not a general checkpoint engine for partial specialist stages, revisions, follow-ups, reviewer failures, timeouts or unknown provider responses. The ordinary `/resume` protections remain in place.

## UI and API

`GET /api/runs/{id}/synthesis-checkpoint` inspects eligibility without changing state or making model calls. Eligible stopped investigations show **Continue synthesis**. `POST /api/runs/{id}/continue-synthesis` accepts exactly `source_operation_id` and `idempotency_key`, rechecks eligibility and queues a new operation. Selection is explicit; the application never automatically starts this recovery because it notices a failure.

The role view labels reused accepted, inconclusive and blocked work. It distinguishes those records from current coordinator/reviewer activity. Exports include the operation lineage; model metadata separates `actual_model_roles` from `reused_role_ids`.

## Output capacity and validation

`TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS` sets the coordinator/reviewer allowance, including reasoning: default 24,000, integer range 8,192–32,000. Specialists retain `TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS` (default 8,000). The HTTP boundary and format repairs use the role's allowance. Aggregate budgets remain advisory by default; configured technical limits and zero automatic retries still apply. Higher capacity does not guarantee a complete or correct answer.

See [VALIDATION.md](VALIDATION.md) for software, deployment and live-run evidence; mocked SDK tests are not proof of live scientific success. See [HYPOTHESIS-GOVERNANCE.md](HYPOTHESIS-GOVERNANCE.md) for the subsequent test/review loop.
