# GPT-Rosalind, OpenAI SDK and BioNeMo contracts

Checked 19 September 2026. Documentation-supported capability is different from account entitlement or a successful live test. This review did not invoke either vendor's inference API.

## GPT-Rosalind: verified facts and engineering use

| Feature | What is established | Implementation consequence |
| --- | --- | --- |
| Model identity | Official model catalog lists `gpt-rosalind-research` | Use this explicit configurable ID; record the returned model identifier |
| Scientific specialization | Official life-sciences guidance describes biology, drug discovery, translational medicine, chemistry, protein engineering and genomics, with improved tool use | Use for hypothesis framing, choosing discriminating analyses, interpretation and critique |
| Access | API access is limited to approved organizations through trusted access | Check the team's actual API project; Workbench or Codex availability alone does not establish API entitlement |
| Pricing | Listed standard rates are $5/M input, $0.50/M cached input, $25/M output; billing begins October 5, 2026 | Keep a dated rate card and report estimated future-rate cost separately from actual billed/credited cost |
| Model evolution | Eligible organizations receive newer Rosalind releases | Pin a snapshot if offered; otherwise record alias, response identity, date and capability fingerprint and re-evaluate changes |
| Model-specific limits | No complete Rosalind API model card was recovered in this review | Do not invent context limits, image support, reasoning-effort values, temperature controls or a snapshot ID |

Sources: [OpenAI model catalog](https://developers.openai.com/api/docs/models), [life-sciences guidance](https://learn.chatgpt.com/use-cases/collections/life-sciences), [pricing and access terms](https://developers.openai.com/api/docs/pricing). The life-sciences landing page still uses research-preview wording; the architecture relies on verified account access rather than that label.

Do not attribute features of GPT-6, Codex, or Rosalind Workbench to the Rosalind API model without verification. Workbench plugins, file viewers, connectors, persistent memory and desktop tools are application capabilities. Installing `openai-agents` does not automatically expose the Codex tools available in this conversation.

## OpenAI SDK features we will use

| SDK feature | Project use |
| --- | --- |
| Agent + Runner | Coordinator and bounded reviewer loops |
| Function tools | Validated analysis gateway with small typed inputs/outputs |
| RunContextWrapper | Trusted IDs, permissions, DB handles and budgets that stay out of model context |
| output_type | Typed step/decision objects if the selected model supports the required schema |
| SQLiteSession | Persist conversation history in an explicit file; operational DB remains separate |
| Streaming | Show model/run progress; only completed tool outcomes become evidence |
| Agents as tools | Later specialist consultation while coordinator retains final ownership |
| Guardrails | Additional input/output checks; action-boundary enforcement remains in our code |
| Tracing | Inspect model calls, tool spans and review; redact/disable sensitive-data export as appropriate |
| SDK-managed MCP | Later private retrieval integration; local Python functions are simpler for the initial tools |

These are SDK capabilities, not a guarantee that every feature works with every Rosalind account/transport. [Agent definitions](https://developers.openai.com/api/docs/guides/agents/define-agents), [orchestration](https://developers.openai.com/api/docs/guides/agents/orchestration), [observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)

## Mandatory compatibility probe

Implement `doctor --live-model` as a deliberately small, non-sensitive test. It is an implementation task; it was not run during planning.

1. Verify credential presence without printing it and resolve the approved model ID.
2. Make a minimal text response through the selected OpenAI transport.
3. Invoke a deterministic `echo_evidence_id` function; verify parsed arguments, tool execution and a second response using that result.
4. Try the small typed output schema used by the harness. If unsupported, record validated-JSON mode with one repair attempt; do not disable server validation.
5. Check usage reporting, stop/incomplete/error handling, cancellation behavior, and streaming separately.
6. Test supported optional settings one at a time. Leave reasoning effort, temperature and similar settings unset until established.
7. Save model/SDK versions, API path, observed capabilities, request IDs and non-sensitive responses in `capabilities.json`.

Target the SDK's standard Responses path. If the entitled Rosalind endpoint does not support that transport, verify the documented SDK provider for the supported API and rerun the same tests. Do not fabricate a Responses compatibility layer or silently change models. If tool calling cannot be established, live release is blocked; replay development can continue.

Public source packets may be sent to the model only according to the case policy. Large matrices remain on disk. Model answers and confidence statements are not calibrated scientific probabilities.

## Initial CPU tool surface

All functions receive trusted run context outside model arguments. Request IDs refer only to a case's approved manifest.

| Tool | Model-visible inputs | Output and validation |
| --- | --- | --- |
| `get_case_readiness` | No identity arguments | Missing prerequisites, QC state, allowed tool families, current evidence IDs |
| `read_source_excerpt` | source ID, locator, bounded row/character limit | Text/table slice plus source hash and exact locator; no arbitrary path or SQL |
| `extract_alk_assay` | variant source key, allowed table/endpoint selection | Drug/score/classification/fitness rows, preserved units, worksheet cells and exclusions |
| `summarize_variant` | variant-table ID, normalized variant key | Build/alleles/read counts/sample timing; no inferred pretreatment absence |
| `summarize_expression` | accepted matrix/annotation IDs, sample IDs, gene-set ID, analysis-spec ID | Sparse summaries, composition/QC results, sample counts and limits; no automatic population p-values |
| `qualify_molecular_inputs` | sequence/ligand/reference IDs and mutation mapping ID | Mapping/construct/ref-allele/chemistry checks or a precise block |
| `request_analysis` | hypothesis, question kind, allowed tool, input IDs, parameters, expected discriminator | Durable receipt; policy rechecks capability, scope, budget and prerequisites |
| `read_analysis_result` | action ID | Accepted evidence IDs and compact summary, or an explicit pending/failed/unknown state |
| `get_process_contract` | allowed process ID | Versioned relevant checks from the graph extract |

No general-purpose shell or arbitrary Python execution is exposed in the first release. Expanding analysis means adding a reviewed adapter with a contract. A user-designated hypothesis prompt or Markdown file supplies the investigation objective through validated intake. Ordinary source files and downloaded pages remain evidence; they cannot redefine that objective or expand tool authority.

## BioNeMo tool selection

The BioNeMo Agent Toolkit is a catalog of skills and reference contracts. It is distinct from the BioNeMo model framework and from **NeMo Agent Toolkit**, an optional agent workflow/profiling framework. Use the inspected toolkit pin `0e67a612e4045f007e38fa77adc8f3ebfc5616b6` as the prototype provenance baseline. Record deliberate updates.

| Capability | Release | Role in this project | Gate |
| --- | --- | --- | --- |
| Boltz-2 | P0 molecular branch | Matched WT/mutant ALK–ligand structures; optional later model affinity | Exact construct/residue mapping and ligand identity; paired validated artifacts |
| Boltz-2 protein-complex comparison | P1 R&D loop | Compare reference/candidate CAR binding-domain structures against a fixed target and return predictions to R&D | Qualified target-retained question, exact constructs, matched settings, controls and a new candidate-comparison adapter |
| Evo 2 7B hosted forward | P1, or first NIM route if ready sooner | Exploratory conditional nucleotide score | Exact DNA context/ref/alt/orientation; new backend contract passes |
| Evo 2 40B generation | Existing diagnostic | Connection test only | Never count generation smoke output as variant-scoring evidence |
| Evo 2 self-hosted forward | Optional GPU profile | Existing score adapter route | Compatible NIM/GPU; observed version and tensor contract |
| DiffDock | P2 | A distinct small-molecule pose hypothesis | Prepared receptor/ligand, validated adapter; not antibody docking |
| MSA Search + OpenFold2/3 | P2 | A folding question not already answered by Boltz | Exact biological inputs and endpoint-specific contracts |
| RFDiffusion + ProteinMPNN; optional Complexa workflow | Later R&D generation extension | Generate binder backbones/sequences before independent structural comparison | Scaffold/epitope constraints and evaluation; a generated binder is not automatically a CAR-compatible scFv |
| GenMol/MolMIM | Separate medicinal-chemistry case | Molecule generation/optimization | Appropriate property/chemistry constraints and experimental validation |
| Parabricks | Separate raw-read pipeline | GPU alignment/variant processing when FASTQs are actually required | Compatible workflow/reference/compute; no raw reprocessing for suitable processed tables |

The later rows identify available toolkit directions, not installed production adapters or validated endpoints in this project. The [CAR-T R&D process](07-RD-FEEDBACK-LOOP.md) starts with expert-provided reference/candidate constructs, making a useful modeling handoff possible before adding de novo generation.

The planned `compare_binder_candidates(design_brief_id, target_id, candidate_ids, control_ids, prediction_spec_id)` tool resolves all sequences from qualified artifacts. It uses the existing durable NIM transport, but requires its own action schema and scientific validators: the current target WT/mutant adapter assumes a different comparison. Return structural artifacts, actual available metrics and limitations. Prediction confidence is not measured affinity or cell-therapy performance, and the ligand-affinity option is not enabled for a protein binder. Candidate-linked laboratory measurements return through W18 to update the next design round.

## Evo 2 forward adapter

Verified hosted route:

```text
POST https://health.api.nvidia.com/v1/biology/arc/evo2-7b/forward
Authorization: Bearer <NVIDIA credential>
Content-Type: application/json
{"sequence": "<validated DNA prefix>", "output_layers": ["output_layer"]}
```

The endpoint documents `output_layer` as [sequence length, batch size, 512], with A/C/T/G at ASCII indices 65/67/84/71. [NVIDIA forward reference](https://docs.api.nvidia.com/nim/reference/arc-evo2-7b-infer)

Add `evo2_7b_hosted` as a named backend. Do not make the existing hosted-40B generation URL accept a fictional forward operation, and do not label 7B results 40B. Confirm the response envelope using the live endpoint contract before reusing the existing NPZ decoder.

For continuity with the prototype, the first scoring implementation is:

```text
prefix = reference_sequence[:position_1based - 1]
score = logits[last_prefix_position, 0, ALT] - logits[last_prefix_position, 0, REF]
```

Reject first-position variants, reference mismatch, unsupported bases, nonfinite tensors and unexpected shapes. Bound inputs to 4,096 bases initially. The score is single-site, one-orientation conditional sequence plausibility. It is not full-window likelihood, a splice-effect predictor, a functional assay or a resistance probability.

Record whether the context is genomic or a construct, its accession/version, strand/orientation, coordinate mapping and sequence hash. A future reverse-complement/window scoring method needs its own contract/version and evaluation. Evo score sign must not gate structural modeling or exclude known functional evidence.

## Boltz-2 ALK ligand adapter

Verified prototype/toolkit hosted route:

```text
POST https://health.api.nvidia.com/v1/biology/mit/boltz2/predict
```

Proposed minimum paired request:

```json
{
  "polymers": [{"id": "A", "molecule_type": "protein", "sequence": "<verified ALK construct>"}],
  "ligands": [{"id": "L1", "smiles": "<verified alectinib structure>"}],
  "recycling_steps": 3,
  "sampling_steps": 50,
  "diffusion_samples": 1,
  "step_scale": 1.638,
  "output_format": "mmcif"
}
```

This is an input template, not a scientific sequence or a request that has been run. The molecular-input task must freeze the actual construct, canonical residue numbering and ligand identifier/SMILES from an authoritative chemical source. L1196 is a canonical residue number, not automatically index 1196 in a cropped kinase domain.

Submit WT and L1196M as distinct child actions of one pair, with identical ligand, settings and construct boundaries. Require exactly the intended amino-acid change and a mapping table. Store both requests, responses, model identity and CIFs. If only WT completes, preserve it and mark the pair incomplete; do not invent a mutant result.

Validate parseable CIF, chain and ligand identity, residue coverage, finite confidence values and mapped mutation position. Inspect aligned pocket geometry and contacts using a deterministic structure parser. Persist chain selection, alignment selection and contact definition so another engineer can reproduce the comparison. Avoid claiming a confidence-score delta is an affinity change.

Start without affinity prediction. If the later ligand-affinity capability is enabled, request it for exactly one ligand, retain the returned affinity field definitions and distinguish prediction from measurement. The existing protein-binder adapter must not request small-molecule affinity for an antibody/protein complex.

Source of payload contract: the pinned [BioNeMo toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit/tree/0e67a612e4045f007e38fa77adc8f3ebfc5616b6) and locally inspected `boltz2-nim/references/api.md`. Check the deployed NIM contract at first live use.

## Common NIM job behavior

HTTP 202 means accepted/pending. The current client raises an error and lacks asynchronous retrieval. The new executor must persist the vendor request ID and use the documented polling route supplied by that service contract. Do not invent a universal NVIDIA status endpoint. An endpoint with no implemented reconciliation path returns unknown/pending and requires an explicit operational resolution.

Transport timeout is not proof of failed inference. Default to no automatic repeated POST after an ambiguous response. Bound polling with wall time and backoff; release the agent worker while waiting. Validate downloaded assets before accepting evidence.

Set backend independently per tool. A run may use hosted Boltz plus self-hosted Evo, but each selection is frozen in the manifest. Backend/model/mode changes create a new action identity and are visible to the scientist. No silent live-to-synthetic fallback.

## Budgets

Initial policy targets: 12 total model requests across coordinator/reviewer, 80,000 accumulated input tokens, 16,000 accumulated output tokens, 24 gateway actions, four external NIM requests, one heavy CPU job, and 15 minutes to a settled result or explicit wait. Reserve budget before dispatch, including nested specialist work.

At the published future standard Rosalind rates, 80k uncached input plus 16k output is **$0.80** before other services; actual reasoning/output usage and any extra requests must be counted. Use a $2 OpenAI ceiling as headroom, subject to the account's configured limits. NVIDIA endpoint pricing, credits, rate limits and GPU rental rates were not verified; record them before live operation, cap call count, and keep GPU provisioning disabled in the default profile.
