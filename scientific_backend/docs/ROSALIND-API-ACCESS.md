# Model access: current Astra selection and Rosalind setup

Checked 19 September 2026 against current official guidance and the exact user-designated Brev configuration.

## Current selected model

The user explicitly authorized **GPT-6 Astra with high reasoning as the temporary model**. The live team therefore defaults to `gpt-6-astra`; it must not be presented as a successful Rosalind run. `TEAM_TBD_MODEL` takes precedence over the legacy `ROSALIND_MODEL`, followed by the code default `gpt-6-astra`. Both local and Brev deployments should put the intended selection in their private `.env`:

```dotenv
TEAM_TBD_MODEL=gpt-6-astra
```

The adapter sends `reasoning.effort=high` for Astra, as documented on the [official GPT-6 Astra page](https://developers.openai.com/api/docs/models/gpt-6-astra). It records the outgoing ID, returned family/snapshot, request ID, actual token usage and role for every request. Only an explicit configuration change selects Rosalind. There is no automatic fallback after denial or failure.

`OPENAI_API_KEY` must be an existing authorized credential supplied by the user or deployment operator. This code does not generate API credentials, infer access from a key's presence, or copy credentials to the browser. `.env.example` has blank credential fields. Nonempty private `.env` values override inherited process values; a blank template entry does not erase a configured value. Restart the service after changing its selection or credentials, then run the live capability check.

## What the credential check established

The key in `/home/ubuntu/rosalind-hackathon-demo/.env` authenticates to the OpenAI API and can list models. Its returned catalog contained no GPT-Rosalind model. A real request for `gpt-rosalind-research` to `/v1/responses` returned HTTP 404 `model_not_found`. This is an observed model-access failure, not a conclusion that the API key itself is invalid. An earlier local environment used a different invalid credential; the Brev configuration is the intended deployment.

The [official model catalog](https://developers.openai.com/api/docs/models) lists GPT-Rosalind under life-sciences models for approved organizations. The catalog currently links GPT-Rosalind to pricing/access information rather than a complete model-specific API card. The Rosalind adapter preserves the plan's exact `gpt-rosalind-research` identifier. Astra is a separately and explicitly authorized temporary selection; the earlier failure remains part of the deployment record.

## Enable the right organization and project

1. Confirm that the organization was approved for **API access**, not only ChatGPT or Codex. OpenAI explicitly distinguishes those surfaces.
2. Sign in to the approved API organization at the platform. Its owner/admin must add the API user under Settings → People, and ensure access to the intended project.
3. Create/use a project key belonging to that approved organization and project. Put that key and `TEAM_TBD_MODEL=gpt-rosalind-research` in the private Brev `.env`; restart the service.
4. Run `.venv/bin/python -m app doctor --live-model`. The probe uses the currently selected model and requires an actual function-tool round trip, a validated result, model identity and usage. Model listing alone is not the gate.
5. If the approved organization still returns 404, ask the organization admin or hackathon OpenAI contact to confirm **GPT-Rosalind API entitlement for that organization/project**. Include the model ID and saved request ID, never the API key. The observed Brev request ID is retained in `runtime/capabilities.json`.

For a new organization, use [OpenAI's Rosalind access request](https://openai.com/form/life-sciences-access/) and explicitly select use in internal tools/applications via the API. Current guidance says new applications require owner/admin approval before final provisioning. The current form redirects through ChatGPT sign-in; this service does not submit an application or modify organization membership.

These steps follow [OpenAI's current GPT-Rosalind setup guidance](https://help.openai.com/en/articles/20001193-gpt-rosalind-for-life-sciences-research), particularly “Add users for API access” and the troubleshooting question for approved users who still cannot see the model. A special string in an ordinary key, a local package name, or an installed life-sciences plugin does not grant the API entitlement. No public documentation found establishes a special header that bypasses that enrollment.

## Standard client configuration

The application uses `AsyncOpenAI` and the Agents SDK `OpenAIResponsesModel`, requesting exactly `gpt-6-astra` or `gpt-rosalind-research` according to explicit configuration. `OPENAI_API_KEY` supplies the server credential; `OPENAI_ORG_ID` and `OPENAI_PROJECT_ID` can explicitly identify an approved organization/project where appropriate, but cannot grant access. Optional `OPENAI_BASE_URL` is trusted server configuration, not a model-controlled value. Astra requests use supported high reasoning. Rosalind optional reasoning/sampling settings remain unset. Capability receipts include the selected model, endpoint, credential fingerprint and organization/project scope; changing scope invalidates old verification. Returned organization/project headers are captured when supplied.

Live access is an external prerequisite. The earlier access failure and scoped transport-mocked tests are not a successful GPT-Rosalind investigation. An Astra tool-roundtrip check proves the selected Astra integration only; BioNeMo requires its own NVIDIA credential or a reachable local NIM and a separately validated prediction.
