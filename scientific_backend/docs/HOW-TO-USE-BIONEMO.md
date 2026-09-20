# How to use BioNeMo for our CAR-T project

Saved: 19 September 2026. Scope: Rosalind / Team TBD, with CD19 CAR-T as the primary investigation and BCMA and ALK as supporting cases. This is a planning reference; it does not register new runtime skills, enable providers, or record completed inference.

## What BioNeMo contributes

Use BioNeMo to connect a qualified molecular question to a prediction or candidate design that can be tested experimentally. For our CAR-T project, the useful progression is:

**Why recognition failed → a candidate recognition domain → a discriminating experiment.**

Expression, cell-state, exposure, clinical timing and statistical analyses remain necessary alongside molecular modeling. See [Scientific evidence and R&D handoff](SCIENCE.md) for the case-specific evidence boundaries.

## Relevant skills

All names below belong to the `bionemo-agent-toolkit` plugin.

| Skill | Use in our CAR-T project | Priority |
| --- | --- | --- |
| `boltz2-nim` | Compare the antigen bound to the reference CAR recognition domain versus a candidate; inspect epitope contacts and possible effects of a precisely mapped antigen change. | First molecular comparison |
| `complexa-binder-design` | Generate new protein binders against a defined, accessible epitope; assess predicted complexes with Boltz2 or OpenFold3. | Main design extension after target qualification |
| `protein-binder-design` | Alternative workflow composing `rfdiffusion-nim` for backbones, `proteinmpnn-nim` for sequences, and Boltz2/OpenFold3 for complex assessment. | Alternative to Complexa |
| `complexa-evaluate-pdbs` | Evaluate an existing batch of candidate structures for interface metrics and consistency after refolding. | Once candidate structures exist |
| `uniprot-database` | Retrieve reference sequences, isoforms and annotations to establish the correct antigen identity and construct. Therapeutic binder sequences need their own source. | Input preparation |
| `msa-search-nim` | Provide evolutionary alignments where appropriate, particularly for the target protein. An MSA for an engineered binder may have limited useful homologous information. | Supporting structure prediction |
| `openfold3-nim` | Cross-check a selected complex with another structure-prediction model. | Optional computational check |
| `evo2-nim` | Explore precisely mapped nucleotide hypotheses and benchmark sequence-based scores against measured variant or minigene outcomes. | Secondary, question-dependent branch |

The `msa-structure-prediction-pipeline` packages MSA Search followed by OpenFold3 when that complete alternative workflow is required. `alphafold-database-fetch-and-analyze` can help inspect an existing target prediction and its confidence; it does not establish the structure of the therapeutic complex.

## Start with the CAR-T failure mechanism

Ask whether failure is more consistent with loss of functional surface antigen recognition or inadequate antigen-specific CAR-T activity, persistence or expansion.

| Evidence state | Appropriate next action |
| --- | --- |
| Relevant surface epitope is retained and accessible | Qualify the molecular constructs, then consider reference/candidate interaction modeling. |
| Relevant epitope is absent | Investigate antigen selection, another accessible epitope, or a multi-target research strategy. A stronger binder to an absent epitope does not establish rescue. |
| Target retention or accessibility is unknown | Obtain the necessary surface-recognition evidence before interpreting a binder comparison as relevant to the failure. |
| Recognition is retained but CAR-T function or persistence is inadequate | Prioritize cell-state and functional evidence. Binder design alone does not resolve these mechanisms. |

The CD19 minigene and stimulation datasets address distinct questions and must not be presented as patient-matched observations. Sequence plausibility is not a direct measurement of splicing, surface expression or patient causality.

For the BCMA case, the recorded Q38* truncation is not a qualified missense comparison or evidence that a modeled intact target remains available. A separate target-retained construct packet is required for binder modeling.

## Recommended workflow

1. **Establish the failure mechanism.** Preserve alternative explanations and identify which evidence can distinguish them.
2. **Qualify the inputs.** Obtain the exact antigen sequence and construct boundaries; reference and candidate binding-domain sequences; molecular format, domain order and linker definitions; mutation/isoform mapping; and source provenance. Record target-retention evidence and material glycosylation or membrane-context omissions.
3. **Inspect the reference interaction with Boltz2.** Use matched conditions for comparisons. Check the returned chain sequences, structural confidence, relevant contacts and consistency across samples. Use suitable experimental structures as references when available.
4. **Design only against a justified epitope.** Use `complexa-binder-design`, or the alternative RFdiffusion–ProteinMPNN workflow, to propose candidates. Choose a bounded campaign and retain its settings and provenance.
5. **Evaluate candidates.** Refold selected candidates, inspect interfaces and epitope contacts, and compare structural consistency. A different folding model provides another computational assessment; it is not an experimental validation or guaranteed independent evidence.
6. **Test the biological claim.** Propose appropriate measurements of surface binding, specificity, expression and antigen-dependent killing, with matched reference controls. Assess signaling and tonic activation, and persistence where relevant to the hypothesis.
7. **Return measurements to the investigation.** Link results to the exact candidate, construct, experiment and decision version. Preserve negative, failed and inconclusive results alongside positive ones.

## What these predictions do not establish

- A generated protein binder is a candidate recognition domain, not a complete validated CAR or automatically a validated antibody/scFv design.
- Protein-interface confidence does not measure affinity, specificity, cytotoxicity or clinical efficacy.
- Boltz2's small-molecule affinity option is not a protein-binder affinity estimator.
- Evo2 sequence scores are not calibrated resistance or splicing probabilities without a suitable validation study.
- These skills do not by themselves establish CAR signaling, exhaustion, persistence, trafficking or clinical benefit.

## Current project readiness

The app implements a Boltz2 protein-binder comparison path and loads a pinned Boltz2 skill for the molecular role. The bundled case packs do not themselves supply a qualified target/reference/candidate sequence set. Exact constructs and the relevant target-retention evidence are the immediate prerequisites.

The earlier `rosalind` prototype also contains an Evo2 SNV-scoring route. That does not mean Evo2 is already registered or live-validated in the current `rosalind-demo` app. Complexa, DiffDock and other catalog skills likewise require explicit integration and provider qualification before they are described as app capabilities.

Hosted prediction requires appropriate NVIDIA API access; local prediction requires a compatible running service. Check the current skill and service contract at execution time. A configured credential, loaded skill or pending job is not successful inference. No fresh BioNeMo inference was completed while preparing this reference.

For accepted runs, preserve request parameters, provider/model identity, every returned structure, validation results, raw response artifacts and source hashes. Keep predictions separate from measurements. See [runtime skills](SKILLS.md) and [provider contracts](PROVIDERS.md).

## Example requests

After the required inputs are available:

> Use the BioNeMo Boltz2 skill to compare these exact reference and candidate CAR recognition-domain sequences against this verified CD19 construct. Keep settings matched, preserve all returned structures, inspect epitope contacts, and distinguish structural confidence from measured binding.

> Use the BioNeMo Complexa binder-design skill to propose a bounded set of binders against this experimentally supported, retained CD19 epitope. Assess selected candidates with another folding model and report them as computational candidates for experimental testing.

> Use complexa-evaluate-pdbs to evaluate this existing candidate directory. Preserve per-candidate metrics, failures and provenance, and identify which candidates merit a discriminating experiment.

## Other project branches

For **ALK**, `boltz2-nim` and `diffdock-nim` can address a defined small-molecule binding question. The existing protein-binder adapter does not automatically support a validated ALK–inhibitor workflow. Docking pose confidence is not measured affinity or clinical resistance.

Use **Parabricks / genomics-workflow-acceleration** when a selected case genuinely requires raw sequencing processing. Suitable processed matrices do not require reprocessing just to use a GPU.

Defer **GenMol, MolMIM, the drug-discovery pipeline and KERMT** until the project explicitly includes small-molecule generation or property modeling. They are not the immediate tools for the CD19 CAR-T investigation.

## References

- [Project scientific scope](SCIENCE.md)
- [Scientific skills used at runtime](SKILLS.md)
- [NVIDIA Boltz2 overview](https://docs.nvidia.com/nim/bionemo/boltz2/latest/overview.html)
- [NVIDIA Evo2 endpoints](https://docs.nvidia.com/nim/bionemo/evo2/latest/endpoints.html)
- [NVIDIA DiffDock documentation](https://docs.nvidia.com/nim/bionemo/diffdock/latest/index.html)
- [NVIDIA Proteina-Complexa project](https://research.nvidia.com/labs/genair/proteina-complexa/)

At execution time, read the installed skill version and verify the relevant model service. The saved recommendation is not a substitute for current schemas or live readiness checks.
