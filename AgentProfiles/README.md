# Agent profiles

[Browse source profiles](https://github.com/24edden/WilbeBioAIHack2026/blob/7f8e31a/AgentProfiles/index.html) · [Machine-readable profiles](agent-profiles.json)

Imported for the pet UI from `docs/agent-profiles` at `7f8e31a`. The JSON and source lock retain that snapshot unchanged. This repository's local demo harness is a separate implementation; these profiles are reference metadata and do not reconfigure its runtime.

Source snapshot: 20 September 2026. These profiles describe the configured harness. They do not claim that every agent, skill or provider ran in a particular investigation.

The harness has **nine scientific agents**, a separate **human scientist/customer**, and a trusted application executor for registered work. Skills supply instructions; tool permissions and accepted execution receipts determine what an agent can do and what actually happened.

## Scientific team

Every main-investigation role that reaches model execution automatically receives its own role skill plus `discovery-planning`, `research-interpretation` and `rosalind-informed-workflow`. “Additional skills” below are in addition to that shared set. Optional skills must be explicitly loaded and pass their pinned-content checks.

| Agent | Responsibility | Additional automatic skills | Optional eligible skills | Main-investigation tool authority beyond shared tools |
|---|---|---|---|---|
| Clinical scientist (`clinical_scientist`) | Frame population, endpoints and timeline; identify missing clinical links. | None | None | No additional tools |
| Bioinformatician (`bioinformatician`) | Qualify sources and sample mappings; execute registered quantitative analyses. | `molecular-interpretation` | NVIDIA Boltz2 guidance; UniProt and RCSB PDB guidance | `analysis_catalog`, `run_case_analysis`; discovery-case data tools described below |
| Statistician (`statistician`) | Review design, denominators, replication, confounding and uncertainty. | `molecular-interpretation` | NVIDIA Boltz2 guidance | No additional tools; reviews accepted computed results |
| Clinical pharmacologist (`clinical_pharmacologist`) | Qualify dose, measured exposure and sampling times before exposure-dependent conclusions. | None | None | No additional tools; blocked without qualified exposure inputs |
| Molecular scientist (`molecular_scientist`) | Qualify exact molecular inputs and interpret scoped structure predictions. | `molecular-interpretation`, NVIDIA Boltz2 guidance | UniProt and RCSB PDB guidance | `qualify_molecular_inputs`, `request_molecular_comparison` |
| Translational scientist (`translational_scientist`) | Integrate competing mechanisms and propose discriminating experiments. | `molecular-interpretation` | NVIDIA Boltz2 guidance; UniProt and RCSB PDB guidance | No additional tools |
| Assay scientist (`assay_scientist`) | Specify fit-for-purpose assays, controls, endpoints and experimental handoffs. | None | NVIDIA Boltz2 guidance | No additional tools |
| Coordinator (`coordinator`) | Integrate accepted evidence while preserving the scientist’s original hypothesis. | `molecular-interpretation` | NVIDIA Boltz2 guidance; UniProt and RCSB PDB guidance | No additional tools |
| Independent reviewer (`reviewer`) | Challenge evidence, numerical support, causal claims and experiment fitness. | `molecular-interpretation` | NVIDIA Boltz2 guidance; UniProt and RCSB PDB guidance | `analysis_catalog`, `request_followup_analysis`; discovery-case review tools described below |

Shared tools are `get_case_readiness`, `read_evidence`, `load_scientific_skill`, `list_available_followups` and `propose_followup`. All nine roles can propose a registered follow-up when their model stage runs. Proposing work does not execute it.

For the `cart-discovery` case, the bioinformatician also receives `list_datasets`, `get_dataset`, `inspect_data_file` and `analyze_data_file`. The reviewer receives the first three plus `request_data_followup`.

## Where skills come from

| Category | Skill IDs | Provenance and meaning |
|---|---|---|
| Custom project skills | The nine role IDs; `discovery-planning`; `research-interpretation`; `molecular-interpretation` | Team TBD-authored scientific instructions and harness contracts. “Custom” describes authorship, not the human customer. |
| Rosalind-informed guidance | `rosalind-informed-workflow` | Team TBD-authored guidance informed by public OpenAI workflow documentation. It is not a proprietary Rosalind skill or proof of Rosalind model access. |
| NVIDIA BioNeMo guidance | `bionemo-boltz2` | Pinned NVIDIA BioNeMo agent-toolkit instructions for Boltz2 input qualification and prediction interpretation; original attribution retained. Loading it grants no new execution permission. |
| External OpenAI Life Sciences guidance | `uniprot-skill`, `rcsb-pdb-skill` | Pinned installed Life Sciences Databases plugin instructions. Availability depends on the verified external runtime. Eligible main-investigation roles may load the guidance; the corresponding lookup tools are exposed in the separate sequence workflow. |

The authoritative versions, role eligibility and content hashes are in `skills/manifest.json`; loading and integrity checks are in `app/scientific_skills.py`. Historical runs retain their recorded skill versions and must not be relabeled with today’s registry.

## Who can make NVIDIA calls

**Only the molecular scientist receives the direct comparison-request tool in the main investigation.** It supplies a rationale after input qualification. The application’s `Worker.agent_molecular` validates trusted inputs, records durable action intent and owns provider submission. The agent cannot supply arbitrary provider commands or treat its own proposal as approval.

Separately, all roles may propose registered follow-ups. An eligible follow-up selected through the harness’s scientist or agent-governance process is executed by `Worker.execute_followup`. A molecular ownership label on a follow-up does not prove that the molecular agent initiated it. Execution attribution should preserve the proposing role, selection origin and trusted executor separately.

Boltz2 is configured as `mit/boltz2`; endpoint configuration is not a vendor-returned version receipt. A key, available skill, tool attempt, queued job or pending response is not a completed prediction. Completion requires successful execution and validated, accepted output artifacts. Prediction confidence is not measured binding affinity, clinical benefit or proof of a hypothesis.

## Separate workflows and exceptions

| Workflow | Participating roles and skill loading | Execution boundary |
|---|---|---|
| Public sequence discovery | Molecular scientist and reviewer each load their role skill plus Rosalind-informed workflow, research interpretation, molecular interpretation, Boltz2, UniProt and RCSB PDB guidance. Discovery planning is not automatically loaded here. | Both can search/fetch UniProt and RCSB structures. This produces reviewed candidate inputs, not human approval or a new NVIDIA prediction. |
| Research interpretation addendum | Coordinator and reviewer each load their role skill plus research interpretation, molecular interpretation and Boltz2 guidance. | Model interpretation calls use existing accepted evidence; agents receive no tools and do not launch new NVIDIA inference. |
| Synthesis checkpoint recovery | Coordinator and reviewer make fresh model calls; accepted specialist products may be reused. | Reviewer has shared tools only; no fresh diagnostic or molecular execution within recovery. Reused work must retain its original operation attribution. |
| Missing exposure data | Clinical pharmacologist loads only its own role skill and produces a deterministic blocked product. | No model inference for that role. |
| Repair passes | An agent corrects a rejected or malformed product using supplied context. | Repair agent calls have no tools; their tool authority must not be inferred from the normal-stage table. |

Sequence discovery and research interpretation prepare both roles’ skill receipts before dispatch. A reviewer load receipt therefore does not, by itself, establish that the reviewer model was called.

## Model identity, human authority and Jev

The nine roles share the model explicitly selected for their session. The source default is `gpt-6-astra`; configuration also permits `gpt-rosalind-research`. Record the requested model and the actual returned model from each provider receipt. The internal capability name `rosalind` and Rosalind-informed instructions do not establish the model used. No historical run is identified here as having used either model.

The **human scientist/customer** supplies the hypothesis, inputs, scientific context and explicit review or selection decisions. This is a human participant, not a tenth model agent. Public source retrieval, model review and a high option score cannot manufacture human approval.

**Jev is a separate advisory pilot**, not one of the nine runtime agents and not a built-in governance authority in this harness. Any Jev ranking must identify the evidence and options it assessed, include **“None of the above”** under the requested pilot policy, and label its scores as model assessments. A highest-ranked option is not automatically the scientifically true answer or an authorization to execute work.

## Read the metadata correctly

| State | Evidence required | What it does not establish |
|---|---|---|
| Eligible | Role appears in the pinned skill registry or tool-routing contract. | Skill loaded or work performed |
| Loaded | Role-specific skill receipt with version and content hash. | Model dispatch or provider inference |
| Model called | Provider request/response receipt for the role and operation, including status and actual returned identity when available. | Accepted scientific conclusion or successful NVIDIA work |
| Tool attempted | Tool observation or call count tied to the role. | Successful provider submission; the result can be blocked or deferred |
| Output completed and accepted | Successful execution receipt, validated artifacts and accepted evidence identifiers. | Measured laboratory outcome, causal truth or human approval |

Implementation references: `app/providers.py` (roles, prompts, tools and model receipts), `app/worker.py` (durable execution and acceptance), `app/sequence_discovery.py`, `app/research_brief.py`, `app/scientific_skills.py` and `skills/manifest.json`. These paths identify files in the separately audited Brev application, whose source is not included in this GitHub repository. This document contains no private run results, credentials or deployment addresses.
