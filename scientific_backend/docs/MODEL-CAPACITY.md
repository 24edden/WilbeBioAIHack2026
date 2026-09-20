# Model capacity and reasoning

Team TBD now gives scientific specialists 24,000 generated tokens per response and coordinator/reviewer stages 48,000. These allowances include reasoning and the visible result. The selected model remains **`gpt-6-astra` with `reasoning.effort=high`**; this change does not select a new model or a different effort setting.

## Defaults and explicit overrides

| Setting | Previous default | Current default | Accepted integer range | Applies to |
| --- | ---: | ---: | --- | --- |
| `TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS` | 8,000 | **24,000** | 2,048–64,000 | Each specialist response |
| `TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS` | 24,000 | **48,000** | 8,192–128,000 | Each coordinator/reviewer response |
| `TEAM_TBD_MAX_INPUT_TOKENS` | 400,000 | **2,000,000** | 50,000–10,000,000 | Cumulative observed input across a provider session |
| `TEAM_TBD_MAX_OUTPUT_TOKENS` | 60,000 | **300,000** | 16,000–2,000,000 | Cumulative observed output across a provider session |
| `TEAM_TBD_MAX_MODEL_REQUESTS` | 40 | **120** | 1–1,000 | Requests across a provider session |
| `TEAM_TBD_MAX_TOOL_CALLS` | 60 | **180** | 1–2,000 | Function calls across a provider session |

A provider session is a single investigation/reassessment, synthesis continuation, interpretation operation, or connection probe. Its configuration is snapshotted before calls begin. Run-level usage still accumulates the receipts from all operations. The cumulative input threshold counts repeated context; it is **not** the model's context window or the maximum size of one request.

`TEAM_TBD_BUDGET_MODE=advisory` remains the default. Crossing cumulative thresholds emits an alert and continues, with one warning per category in the session. Explicit `enforced` mode stops the next request when a cumulative threshold is reached; for output it first reserves the full requested allowance. Invalid numeric settings fail before constructing a model transport. Explicit old or smaller operator values remain effective: defaults do not override a nonempty private `.env`.

The per-response output allowance remains an actual API ceiling in either budget mode. At the HTTP boundary, a specialist cannot request coordinator capacity. Every request records its selected allowance, actual model, reasoning effort, provider IDs and returned token usage. Enlarging capacity does not guarantee the model will use it or return a complete result.

## Model and SDK verification

The installed `openai-agents==0.22.3` Responses adapter forwards `ModelSettings.max_tokens` to the API's `max_output_tokens`. The installed `openai==3.16.2` represents that value as an integer and accepts `Reasoning(effort="high")`; transport tests check the actual serialized request. Official [GPT-6 Astra documentation](https://developers.openai.com/api/docs/models/gpt-6-astra) lists a 128,000-token maximum output and support for high reasoning. Both new defaults and the configured synthesis ceiling are within that documented output maximum.

OpenAI's [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning) explains that `max_output_tokens` covers reasoning, visible output and non-visible formatting, and that exhaustion can return `incomplete` before visible text appears. Team TBD does not configure a separate numeric reasoning-token allocation. It leaves the supported effort at high and supplies a larger total output allowance. Visible explanations remain concise scientific rationale; hidden model reasoning is not shown or exported.

The separately selected `gpt-rosalind-research` keeps its existing optional reasoning settings unset. Astra documentation does not establish Rosalind entitlement or its model-specific limits. No model substitution, silent output downgrade, or automatic replay is introduced when a provider rejects an allowance or returns an incomplete response.

## Paths covered and remaining bounds

All seven scientific specialist roles use the specialist setting when they actually call the model. A prerequisite-blocked role still makes no inference call. Coordinator and reviewer paths use the synthesis setting for ordinary investigations, accepted-handoff recovery, research interpretations, visible acceptance corrections, format repair and forced finalization. Research interpretations therefore receive 48,000 tokens for each of their coordinator and reviewer responses. Explicit lower operator settings are honored throughout.

The connection probe deliberately remains at 2,048 generated tokens: it tests a short tool echo and schema round trip, not scientific reasoning. Its separate short timeout and three-turn limit remain. This exception is recorded in its request receipt.

The following are separate execution, input, or scientific-scope guards and were not changed by this capacity release:

- SDK stage turns: initial bioinformatics up to six; ordinary specialists five; coordinator four; reviewer eight; one-turn correction/finalization paths. The research-brief writer and reviewer each have one turn plus at most one explicit acceptance correction.
- Initial bioinformatics exploration: 22 function calls and four distinct analysis reservations; the independent review may request up to two diagnostic cycles. These reserve downstream capacity and limit analysis scope.
- Technical waits: model request 600 seconds and agent stage 1,800 seconds by default, with explicit existing timeout overrides. A timed-out dispatched request remains unknown and is not automatically retried.
- Application context bounds: original hypothesis 24,000 characters; interpretation context 300,000 characters; accepted analysis summary 80,000 characters. These are data-contract bounds, not generated-token allowances.
- Worker-wide elapsed-time and tool thresholds are separately configured through `ROSALIND_MAX_SECONDS` and `ROSALIND_MAX_TOOL_CALLS` and follow the worker's selected budget policy.

The expanded-study evidence bound is now **300,000 serialized characters**, raised from 150,000 and named `EVIDENCE_MAX_INPUT_CHARS` in `app/providers.py`. It allows accepted findings from additional studies to accompany an existing investigation without discarding evidence. It counts the full serialized evidence packet before model transport is constructed; it does not allocate tokens or increase spending limits. Packets above this bound and duplicate or missing evidence IDs still fail before dispatch. The model, reasoning effort, output allowances, timeouts and unknown-request handling remain unchanged by this input-bound adjustment.

## Deployment and validation

Update the private server values to the new defaults if its `.env` contains the old values, then restart the idle service through the normal guarded deployment. `/api/health` exposes `model_limits`; provider metadata pins the values actually used by each new session. Completed investigations retain their historical allowances and receipts.

Focused mocked-transport tests cover the larger default payloads, specialist-versus-synthesis guards, repairs and interpretation calls, explicit smaller overrides, enforced reservations, configurable request/tool thresholds, advisory continuation, unchanged model/effort, invalid values, timeouts and unknown-work protection. Those tests establish integration behavior, not that a live account accepted a new request. Record any subsequent live run separately with its actual request/response receipts.

The expanded-study boundary tests also verify that a combined packet of 156,695 serialized characters and a packet exactly at 300,000 reach mocked transport construction, while 300,001 characters and duplicate evidence IDs are rejected before construction. No live provider calls are required for these input-contract checks.
