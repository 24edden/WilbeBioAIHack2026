# Live provider contract and handoff

The live research team uses **`gpt-6-astra` with high reasoning**, explicitly selected as the temporary model while GPT-Rosalind API entitlement is unavailable. Set `TEAM_TBD_MODEL=gpt-rosalind-research` when that project has access. Selection order is `TEAM_TBD_MODEL`, then the compatible legacy `ROSALIND_MODEL`, then `gpt-6-astra`. Only these two exact request IDs are allowed. A failed request never triggers a different model or a recorded answer; returned model identities must match the selected family.

Seven scoped scientific roles exchange durable work products before coordinator synthesis and independent review. Analysis selection and review follow-ups are model-directed; computations and source validation run in bounded tools. The prepared walkthrough is separate and does not claim live research.
The molecular branch submits actual NVIDIA BioNeMo Boltz-2 jobs for a fixed target with a reference and candidate binder. An incomplete pair stays incomplete. Confidence and deterministic contact counts are structural outputs, not measured affinity, CAR-T efficacy, or proof of antigen escape.

## Configuration

The application loads the repository `.env` through `app.config`; nonempty private-file values take precedence over inherited process values, while blank template values do not erase existing values. Keep keys on the server. Never enter keys into the browser or a hypothesis.

| Setting | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | API credential for the selected model/project |
| `TEAM_TBD_MODEL` | `gpt-6-astra` (default, high reasoning) or `gpt-rosalind-research` |
| `TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS` | Model HTTP wait, default 600 seconds; 15-second connect timeout |
| `TEAM_TBD_AGENT_TIMEOUT_SECONDS` | Enclosing role wait, default 1800 seconds; must exceed request wait by at least 30 seconds |
| `ROSALIND_MODEL` | Legacy selection alias; `TEAM_TBD_MODEL` takes precedence |
| `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID` | Optional explicit API organization/project scope |
| `OPENAI_BASE_URL` | Optional trusted server configuration for an approved OpenAI-compatible endpoint; no model-selected destinations |
| `NGC_API_KEY` or `NVIDIA_API_KEY` | NVIDIA hosted inference credential; `NGC_API_KEY` takes precedence |
| `BOLTZ2_NIM_URL` | Optional local NIM origin, such as `http://127.0.0.1:8001`; omit for NVIDIA hosted inference |
| `BOLTZ2_MODEL_VERSION` | Optional observed deployment version; otherwise recorded as not supplied |
| `NIM_TIMEOUT_SECONDS` | Per prediction wait, default 300 seconds, allowed 1–900 |
| `ROSALIND_CAPABILITIES_FILE` | Capability receipts; application defaults inside its runtime directory |

A credential means **configured**, not authorized or working. Verification is linked to a fingerprint of the configured model, credential, endpoint, organization and project; changing any of these invalidates the cached proof. No credential value is written to that file. Checked timestamps remain visible because a historical success cannot promise the next call will succeed.

## What the check verifies

`await probe("rosalind")` (the retained API provider key) sends a non-sensitive nonce to the selected model, requires a real `echo_evidence_id` tool call, and validates the model's subsequent answer. It records requested and returned model identities, HTTP request IDs, response IDs, returned organization/project headers, actual reported token usage and installed SDK versions. Typed output is tested explicitly. When the API explicitly rejects structured output as unsupported, the check attempts strict locally validated JSON without changing models. Other errors are surfaced rather than retried.

`await probe("bionemo")` checks local readiness when a local NIM is configured. Hosted Boltz-2 has no documented health endpoint in the inspected contract, so the hosted check reports configured and asks for an explicit qualified comparison. Only a returned, validated prediction sets `prediction_verified=true`. A readiness check is never called a prediction test.

The Astra request explicitly sets supported `reasoning.effort=high`; the probe allows 2,048 output tokens including reasoning. Rosalind optional reasoning/sampling settings are unset. Streaming and remote cancellation are not claimed as verified by these checks. Model response events, scoped function calls, and the reviewer handoff are displayed in the local run timeline. Trace export to the OpenAI tracing service is disabled globally and per run.

## Agent boundary

```python
await investigate(case, hypothesis, evidence, emit, cancelled,
                  accept_evidence=accept_evidence,
                  request_molecular=request_molecular,
                  accept_handoff=accept_handoff,
                  accept_skill=accept_skill)
```

| Role | Actual work and handoff |
| --- | --- |
| Bioinformatician | Chooses source-data analyses; accepted derived evidence and QC → statistician |
| Statistician | Reviews computed values, experimental units, denominators and confounding → clinical/translational |
| Clinical scientist | Frames population and endpoint from source evidence → translational/statistics/pharmacology; missing qualified timelines block patient-specific timing claims |
| Clinical pharmacologist | Interprets qualified exposure inputs → clinical/translational; missing exposure produces a blocked product without model inference |
| Molecular scientist | Qualifies exact constructs; requests relevant BioNeMo comparison through the durable executor → translational/assay |
| Translational scientist | Integrates clinical, statistical, molecular and pharmacology evidence → coordinator/assay |
| Assay scientist | Proposes controls, readouts and interpretation rules → coordinator/reviewer; no lab execution |
| Coordinator | Synthesizes accepted products against the original hypothesis → independent reviewer |
| Reviewer | Checks sources and gaps; may request up to two additional approved diagnostics, then reassesses → scientist |

Each role's versioned scientific skill is loaded and recorded before its work. The skill's instructions enter the agent's prompt. The molecular role also automatically loads `bionemo-boltz2`. `load_scientific_skill(skill_id)` can load an additional applicable skill; it cannot choose arbitrary files or expand tool authority. Skill receipts identify version, content hash and role. Blocked prerequisites still produce a recorded work product and skill receipt, with `model_called=false`.

Scientific synthesis release 1.1.0 updates the coordinator, translational, reviewer and assay skills with new pinned hashes. It requires scoped study-versus-patient answers, coverage of every supplied alternative (including published evidence), numerical comparators, review of both overclaiming and underclaiming, and evidence-based continuity of the parent experiment after a narrow follow-up. Assay guidance separates total effects from effects conditional on matched mediators; prediction priority depends on confidence and decision relevance. These are model review obligations, not claims of automated scientific validation. Schemas and tool authority are unchanged; historical skill receipts remain immutable. Transport and integrity tests verify instruction/context delivery, while a fresh live answer still requires scientific review.

`get_case_readiness()` returns accepted IDs, pinned process contract, scientist revision context and input availability. `read_evidence(evidence_ids)` resolves only accepted run evidence. Both discovery and fixed cases expose applicable curated source analyses through `analysis_catalog()` and `run_case_analysis(analysis_id)`. For the Brev discovery case it has `list_datasets()`, `get_dataset(dataset_id)`, `inspect_data_file(file_id)` and `analyze_data_file(file_id, analysis_kind, parameters_json)`. Analysis adapters allow only registered file IDs, documented parameter keys and bounded table/gene/sparse-matrix operations. Unsupported formats or missing files are reported; the agent may choose another qualified source. A dataset inventory or schema preview is not a completed analysis. The final answer must distinguish inventoried data from data actually analyzed.

Computed evidence passes `accept_evidence` and is persisted **before** its ID becomes visible for citation. Work products include original hypothesis hash, evidence IDs/content versions, upstream accepted handoff IDs, methods, limitations, recipients and skill receipts. A rejected work product gets one bounded repair. Source text, peer findings and scientist reports are data; they cannot authorize arbitrary code, files, URLs or jobs.

Reviewers use `request_followup_analysis(analysis_id,gap)` or discovery's `request_data_followup(file_id,analysis_kind,parameters_json,gap)`. A concrete gap and each returned diagnostic receipt are recorded in `metadata.review_cycles`. The same model must reassess after the tool response. Repeated source/parameter combinations return the prior result labeled reused; repetition is not independent evidence. Two diagnostic requests are allowed, after which unresolved gaps must remain limitations. These are real tool/reassessment cycles, not scripted alternate answers.

`qualify_molecular_inputs()` checks the trusted case's exact target/reference/candidate sequences, source note and target-retention attestation. `request_molecular_comparison(rationale)` can only request those inputs through the application's durable action callback. At most one comparison is requested in an investigation. No callback means a deferred proposal and no vendor call. Pending or incomplete comparisons cannot become accepted paired evidence.

Every published factual claim must cite an accepted evidence ID; application code attaches source links. Alternatives stay separate from the exact user hypothesis. Procedural memory releases may guide method selection but are never scientific evidence or expanded authority. A provisional evaluation-only lesson is explicitly unapproved.

The structured result contains `summary`, `assessment`, `claims`, `alternatives`, `limitations`, `next_experiment`, `rd_handoff`, and `metadata`. The experiment defines positive, negative and inconclusive outcomes. Only the executor may attach molecular artifacts; a language-model response claiming completed artifacts is rejected.

`TEAM_TBD_BUDGET_MODE=advisory` is the default. Cumulative thresholds for 40 model requests, 60 shared tool calls, input tokens and output tokens produce one durable warning per category and allow the investigation to continue. Usage keeps accumulating; a threshold warning is not a completed scientific result. Users can cancel the run. `enforced` mode restores cumulative budget stops. The selected mode and threshold values are frozen when the provider session starts and recorded under `metadata.budgets`; emitted warnings are also retained under `metadata.budget_alerts`.

`TEAM_TBD_MAX_INPUT_TOKENS` sets the shared observed input threshold, including repeated context: default 2,000,000, allowed integer range 50,000–10,000,000. `TEAM_TBD_MAX_OUTPUT_TOKENS` sets the shared observed output threshold: default 300,000, allowed integer range 16,000–2,000,000. Advisory mode warns as actual returned usage reaches either threshold, including on a final response. Enforced mode checks observed input before the next dispatch and requires observed output plus the full next request allowance to fit the output budget. Invalid modes or numeric settings fail before any model request.

`TEAM_TBD_AGENT_MAX_OUTPUT_TOKENS` is a distinct technical API allowance for each specialist response, including high-reasoning tokens: default 24,000, integer range 2,048–64,000. Coordinator and reviewer use `TEAM_TBD_SYNTHESIS_MAX_OUTPUT_TOKENS`: default 48,000, integer range 8,192–128,000. The role-specific allowance is passed as the API's `max_output_tokens` in both modes, including finalization and repair. It is not a cumulative spending threshold. The capability probe remains capped at 2,048. An incomplete provider response, timeout or API failure remains an actual error; advisory mode does not manufacture a complete output or retry an uncertain call.

Role scope remains bounded: initial bioinformatics has 22 function calls and four analyses, reviewer diagnostics have two cycles, and SDK turns and repair attempts retain their contracts. `TEAM_TBD_MODEL_REQUEST_TIMEOUT_SECONDS` sets the HTTP response wait (default 600 seconds, integer range 60–1800; connection establishment remains 15 seconds). `TEAM_TBD_AGENT_TIMEOUT_SECONDS` sets the enclosing role wait (default 1800 seconds, range 120–7200 and at least request wait plus 30 seconds); molecular science retains a minimum 900-second role allowance. These settings are frozen in each provider session and shown in health/receipt limits. Finalization and JSON repair allow request wait plus 30 seconds; the small capability probe retains its existing shorter bounds (150 seconds for its SDK run, 120 seconds at the web endpoint). These technical waits apply in both advisory and enforced modes and do not permit extra model turns, tool actions or retries.

A timed-out model request with no complete response remains an unknown external outcome. The app records `model_request_timeout`, preserves dispatched-request receipts and accepted work, and does not automatically resubmit it. If no response ID was returned, the current app has no provider retrieval path. Accepted handoffs are audit artifacts, not resumable model checkpoints: an unknown timed-out investigation cannot use `/resume`. A distinct [explicit synthesis recovery](SYNTHESIS-RECOVERY.md) applies only to a known terminal coordinator output-limit response and seven verified accepted specialist products. Preserve it and explicitly create a new run after correcting the cause. This does not relabel or resolve the historical unknown request. Independent tools can be batched in a turn. OpenAI retries and trace export remain disabled. Numerical results come from executable tools, not model arithmetic.

## Molecular interface

```python
await predict_complex(target_sequence, binder_sequence, output_dir)
await compare_binders(target_sequence, reference_binder, candidate_binder, output_dir)
await paired_compare(target_wt, target_mutant, binder_sequence, output_dir)
```

`compare_binders` is the CAR-T R&D route: exact fixed target, exact reference binder and exact candidate binder. The sequences must be explicitly supplied and qualified by the scientist. Standard uppercase amino acids only, maximum 4,096 residues per chain; the adapter does not normalize away unknown residues, choose constructs, or invent sequences. `paired_compare` instead requires one target amino-acid substitution at matched construct boundaries.

Both members use the same declared settings: three recycling steps, 50 sampling steps, one diffusion sample, step scale 1.638 and mmCIF output. Each child has its own durable request/response files and job record. Both chains must parse, match the submitted sequences and complete residue numbering, and contain finite coordinates. The actual returned confidence score must be finite and in [0,1]. CIFs are SHA-256 hashed. A deterministic parser reports unique target/binder residue pairs with any non-hydrogen atom separation at most 5 Å. No affinity head is requested for protein binders.

Raw responses and any returned CIF are retained even if validation fails, but failed artifacts are never accepted as completed prediction evidence. Model-version omission is explicit. Artifacts are not silently overwritten or reused across jobs.

## Interrupted and ambiguous jobs

The transport writes intent and the exact request before dispatch. HTTP 202 is `pending` with the vendor request ID preserved. Timeout or cancellation after dispatch is `unknown`; ending a local wait does not stop remote inference. The inspected Boltz-specific asynchronous reconciliation contract is not implemented, so the client does not invent a polling endpoint or repeat the POST. An operator must inspect the saved request ID and reconcile with the actual endpoint before deliberately starting another job.

If the first member succeeds and the second fails or remains pending, the comparison returns `incomplete` and preserves the first artifact. The worker publishes an incomplete modeling handoff, blocks the operation, and adds no paired-prediction evidence. Usage receipts prevent the earlier model decision being charged again when a molecular update is published.

## BioNeMo scope and extension handoff

Boltz-2 is implemented here. Evo 2 generation/forward references were reviewed, but this release does not call Evo 2: generating DNA would not test the CD19 protein-binder question. The earlier prototype contains a local forward adapter. A later nucleotide-scoring extension must first freeze accession/version, sequence context, orientation, position/ref/alt and tensor shape. Do not present a generation smoke test as splice, resistance or variant-effect evidence; do not reuse a hosted generation URL as a forward endpoint. Other BioNeMo toolkit skills are not automatically executable tools inside this app.

## Validation and provenance

Transport-mocked tests exercise the real installed Agents SDK and function-tool loop, strict evidence validation, exact-model enforcement, metadata capture, cancellation, partial jobs, timeouts, and real mmCIF parsing. They do not establish live entitlement or successful vendor inference. Run the explicit capability check and a qualified molecular job for that proof. Locally inspected versions: `openai-agents 0.22.3`, `openai 3.16.2`, `httpx 0.28.1`, `pydantic 2.13.5`, `biopython 1.88` on Python 3.13. Use the repository lock and supported runtime for deployment.

Checked 19 September 2026 against [OpenAI's GPT-6 Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra), which documents high reasoning and tool/structured-output support; [OpenAI's Rosalind release entry](https://developers.openai.com/api/docs/changelog); [Agents SDK definitions](https://developers.openai.com/api/docs/guides/agents/define-agents); [SDK observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability); and [NVIDIA's Boltz-2 API reference](https://docs.nvidia.com/nim/bionemo/boltz2/latest/api-reference.html). The exact Rosalind request identifier is `gpt-rosalind-research`; access depends on the configured API organization/project. Payloads also follow the installed BioNeMo `boltz2-nim` skill and its API/validation references. The [NVIDIA healthcare catalog](https://docs.api.nvidia.com/nim/reference/healthcare-apis) lists Evo 2 and Boltz-2 separately.

## Exploration and review capacity

Discovery bioinformatics selects at most two studies by instruction and can reserve at most four initial analyses (enforced before execution, including parallel calls). Its function-call limit is 22, reserving work for downstream specialists and reviewer diagnostics. The separate 60-call shared threshold warns in advisory mode and rejects additional calls in enforced mode. Dataset lists use 12-file pages and schema previews are bounded. Durable products retain exact source and skill versions; peer model context omits repeated provenance fields. After six exploration turns, one tools-disabled synthesis may finalize accepted evidence; it cannot acquire new data and still passes the normal handoff gates. The reviewer retains up to two concrete follow-up diagnostics, including curated CD19/BCMA analyses. Unresolved gaps remain explicit.
