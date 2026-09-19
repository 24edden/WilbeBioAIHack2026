# How to use Rosalind for our project

Saved: 19 September 2026. Project: Rosalind / Team TBD scientific investigation workbench, with CD19 CAR-T as the primary investigation and BCMA and ALK as supporting cases.

This is a reference for selecting relevant services and skills. It does not install integrations, enable model access, or record completed scientific analyses.

## What Rosalind contributes

Rosalind Workbench is a hub for guided life-science workflows, connecting evidence synthesis, sequencing analysis, molecular design, structure and sequence analysis, and experimental validation. It is distinct from our Team TBD application and from access to the GPT-Rosalind model.

Our application follows this research loop:

**Scientist's hypothesis → scoped analysis → specialist handoffs → independent review → proposed experiment → returned measurement → versioned decision.**

Use the available services to answer a specific question within that loop. Keep the original hypothesis, competing explanations, input provenance, tool results, and unresolved gaps visible.

## Most relevant services and skills

| Capability and skills | Application to our project | Priority |
| --- | --- | --- |
| Life Sciences Literature: PubMed/NCBI Entrez, PMC, bioRxiv | Gather evidence for competing explanations, inspect experimental methods, and support reviewer challenges with traceable sources. | Core |
| Life Sciences Databases: UniProt, Ensembl, RCSB PDB, ClinVar, CIViC | Verify antigen sequences, isoforms, mutation mappings, existing structures, and published variant interpretations. | Core |
| NGS Analysis Workbench: `understand-ngs-data`, `design-ngs-analysis`, `run-ngs-analysis`, `understand-ngs-results` | Translate the hypothesis into an appropriate sequencing or expression-data analysis, with explicit inputs, compute requirements, and interpretation. Execution depends on compatible workflows and compute readiness. | Core when analyzing datasets |
| Biological Sequence & Alignment Viewer | Inspect exact target and binder sequences, compare variants or isoforms, and check sequence differences before modeling. | High |
| BioNeMo `boltz2-nim` plus Molecular Structure Viewer | Compare qualified reference and candidate complexes; inspect contacts, clashes, interfaces, and actual model-confidence metrics. | First molecular branch |
| BioNeMo `complexa-binder-design` or `protein-binder-design` | Propose candidate recognition domains against a justified, accessible target epitope. The alternative workflow combines RFdiffusion, ProteinMPNN, and structure prediction. | Later design branch |
| BioNeMo `evo2-nim` | Explore a precisely mapped nucleotide hypothesis. Validate sequence-based scores against relevant measurements before treating them as predictors. | Question-dependent |
| Slide Viewer | Inspect tissue imaging or spatial datasets when these become part of the investigation. | Conditional |
| BioNeMo `diffdock-nim` and small-molecule tools | Support a defined ALK–inhibitor question or a future small-molecule discovery branch. | Supporting case |
| BioNeMo `parabricks` and `genomics-workflow-acceleration` | Accelerate raw sequencing processing when it is actually needed. Suitable processed matrices do not automatically require reprocessing. | Infrastructure-dependent |

For the application itself, `agent-harness-building` supports reliable handoffs, durable work, and evidence handling. `benchmark-creation` supports evaluation of defensible conclusions, failure handling, and appropriate uncertainty. These engineering skills are separate from biological evidence.

## Recommended workflow

1. **Frame the investigation.** Preserve the scientist's question and specify which observations could distinguish competing mechanisms.
2. **Gather evidence.** Use literature and reference databases, recording exact source identifiers, versions, and relevant passages or records.
3. **Analyze the appropriate data.** Inspect sample metadata, assay scope, confounding, and data quality before selecting an analysis. Do not treat unrelated datasets as patient-matched observations.
4. **Verify molecular inputs.** Establish exact antigen and binder sequences, construct boundaries, mutation/isoform mapping, and provenance. Obtain relevant evidence that the target epitope is retained and accessible.
5. **Compare structures when justified.** Run matched Boltz2 comparisons and inspect returned structures. Structural confidence is not measured affinity, specificity, CAR-T efficacy, or proof of resistance.
6. **Design only when the evidence supports it.** Use a bounded binder-design campaign against a justified epitope. A generated binder is a candidate recognition domain, not a complete validated CAR.
7. **Test and return measurements.** Link experimental results to the exact candidate, construct, experiment, and decision version. Preserve negative, failed, and inconclusive results.

If antigen recognition is absent or uncertain, establish that mechanism before claiming binder redesign can rescue it. If recognition is retained but CAR-T activity or persistence is inadequate, prioritize the corresponding functional and cell-state evidence.

## Current implementation and access boundaries

- The project documentation records an implemented Boltz2 protein-binder comparison path and versioned scientific role instructions. Exact qualified constructs and provider readiness are still required for each live comparison.
- The earlier `rosalind` prototype contains an Evo2 scoring route. This does not establish Evo2 integration or live validation in the current `rosalind-demo` app.
- Catalog skills such as Complexa, DiffDock, and NGS workflows require explicit integration and service qualification before they can be described as app capabilities.
- During preparation of this reference, Rosalind Workbench's local package was found, but its own tools were not exposed in the active session. Other installed science plugins had separately available skills or tools. Recheck availability when starting work.
- An installed workbench or skill does not grant GPT-Rosalind API entitlement. The project documents GPT-6 Astra with high reasoning as the explicitly selected temporary model; report the model that actually returned each result.
- A configured credential, loaded skill, pending job, or mocked test is not a successful scientific inference. Preserve provider receipts and validated artifacts separately from skill-load records.

## Example requests

> Use literature and reference databases to build an evidence table for the competing CD19 CAR-T failure mechanisms. Separate measured findings from interpretations and identify the next discriminating experiment.

> Inspect this registered expression dataset and its sample metadata. Propose an analysis that can distinguish the stated mechanisms, with explicit confounders and limits.

> Verify these exact antigen and CAR recognition-domain sequences and their provenance. If the molecular question is qualified, compare reference and candidate complexes with Boltz2 and inspect the interfaces.

> Evaluate whether our workbench preserves evidence provenance, exposes blocked branches, and remains uncertain when the available evidence cannot distinguish the hypotheses.

## Project references

- Companion molecular guide: `HOW-TO-USE-BIONEMO.md` in the same documentation collection.
- Application overview: `rosalind-demo/README.md` locally; `/home/ubuntu/rosalind-hackathon-demo/README.md` on Brev.
- Application details on Brev: `/home/ubuntu/rosalind-hackathon-demo/docs/SKILLS.md`, `SCIENCE.md`, `DATA_CATALOG.md`, `PROVIDERS.md`, `ROSALIND-API-ACCESS.md`, and `BREV.md` (all under that same `docs/` directory).
- GitHub project knowledge library: <https://github.com/24edden/WilbeBioAIHack2026/tree/docs/project-knowledge-library/docs>.

Application documents named above may be outside the GitHub documentation collection. This guide records project recommendations and documented implementation boundaries as of its saved date; verify current service contracts and access at execution time.
