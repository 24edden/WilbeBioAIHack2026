# GPT-Rosalind integration

Verified against official OpenAI documentation on 19 September 2026.

## What is available

GPT-Rosalind is an API model, with ID `gpt-rosalind-research`. OpenAI lists it
for organizations approved through its trusted-access program for internal
life-sciences research. The team's project entitlement still needs to be checked.
See the [OpenAI API changelog](https://developers.openai.com/api/docs/changelog)
and [pricing/access notes](https://developers.openai.com/api/docs/pricing).

Rosalind Workbench is a separate scientific interface in the ChatGPT app, built
on the model. This integration calls the model; it does not automate Workbench or
inherit Workbench's tools. See the
[Workbench announcement](https://developers.openai.com/blog/rosalind-workbench).

## Backend setup

Copy `.env.example` to `.env` and set these server variables:

```dotenv
RUN_MODE=live
REASONING_BASE_URL=https://api.openai.com/v1
REASONING_MODEL=gpt-rosalind-research
REASONING_API=auto
REASONING_API_KEY=<key from the approved API project>
REASONING_TIMEOUT_SECONDS=180
REASONING_MAX_OUTPUT_TOKENS=16000
```

The placeholder must be replaced in the local server environment. Keep the key
out of browser fields, source control and screenshots. `.env` is ignored by Git.
This application reads `REASONING_API_KEY`; it does not reuse a ChatGPT login or
implicitly copy `OPENAI_API_KEY` to another configured endpoint.

Run the read-only model lookup first:

```powershell
.venv/Scripts/python.exe scripts/check_reasoning.py --env-file .env
```

Once that passes, this separate command makes one minimal inference request
with no patient data. It can consume API tokens:

```powershell
.venv/Scripts/python.exe scripts/check_reasoning.py --env-file .env --smoke
```

Start the API with explicit environment loading:

```powershell
.venv/Scripts/python.exe -m uvicorn app.main:app --env-file .env
```

Existing process environment variables take precedence over `.env` in both
commands. Restart the server after changing them. In the frontend select the
backend source. The existing reasoning-model field can select
`gpt-rosalind-research` per run if another server default is configured.

For an initial model-only investigation, select **Clinical** as the sole
specialist. It uses parsed labs/notes, Rosalind interpretation and the critic,
without calling BioNeMo. A single-specialist run intentionally abstains under
the corroboration gate. Genomics and Literature additionally require working
BioNeMo endpoints; their provisional adapters have not been live-verified.

## Implementation boundary

`app/providers/reasoning_http.py` contains the HTTP mapping. `REASONING_API=auto`
selects `/responses` for the Rosalind model and its dated snapshots. Other model
names retain the existing `/chat/completions` behavior. Set `responses` or
`chat_completions` explicitly for a gateway with a known contract. Selecting a
different model does not silently substitute credentials, providers or fixtures.

The Responses request supplies `model`, `instructions`, user `input`,
`max_output_tokens` and `store: false`. It requests JSON through the scientific
prompts and validates returned JSON. It does not assume Rosalind supports a
particular temperature, reasoning-effort option, JSON-schema mode or built-in
tool. The public Rosalind catalog does not document those model-specific
parameters. The transport follows OpenAI's
[Responses guide](https://developers.openai.com/api/docs/guides/migrate-to-responses);
successful generation with this project's account remains to be verified.

The chat path sends the same configured budget as `max_completion_tokens`.
Both APIs count internal and visible generation toward their limit, per
[OpenAI's token-counting guide](https://developers.openai.com/api/docs/guides/token-counting).
The legacy chat path also retains `temperature: 0.2` and JSON-object mode;
comparisons must report this difference or explicitly use Responses for every
model that supports it. Gateways must support these request parameters.

The parser reads assistant output messages, skips reasoning items, and rejects
refusals, missing text and incomplete results. The token budget includes internal
reasoning and visible output. Provider errors are shown without echoing upstream
bodies that could contain uploaded data or credentials. No retry or fallback is
automatic. Existing grounding checks and the critic's abstention gate still run.

`LiveReasoningProvider.usage` exposes actual per-call API usage for evaluation:
`model`, `api`, `response_id` and the provider's `usage` object. Missing usage is
`null`, never an estimated zero. Calls rejected before an API body is received
have no usage record. HTTP-successful incomplete/refused responses can still
have measured usage and are retained in that list.

`GET /capabilities` and report configuration expose the effective `reasoning_api`.
This means configured transport, not confirmed account access. The frontend's
request format and the event schema are unchanged.

## Verification status

Offline tests cover Responses request mapping, automatic selection after a
per-run model override, legacy chat compatibility, access failures, refusal,
incomplete output, timeouts, safe error messages and the end-to-end clinical
run/abstention path. They use intercepted HTTP responses, not real Rosalind
outputs, and make no scientific quality claim.

No local `REASONING_API_KEY`, `OPENAI_API_KEY` or `.env` was present during setup.
The connection check correctly stopped before network access. Model entitlement,
generation, latency and real token usage have therefore **not** been measured.
The remaining live setup input is a server API key belonging to an approved
project. Public service deployment should follow that project's approved use;
the documented access category is internal research.

Troubleshooting: 401 means check the server key; 403/404 means check the exact
model ID, base URL and project model permission; 429 means check rate/usage
limits. A successful model lookup proves visibility only; use `--smoke` to
verify generation and then test a representative scientific workflow.
