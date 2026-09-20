# Case 01 — ALK L1196M: known functional phenotype

Status: proposed analysis; not executed. Case ID: ROS-EASY-ALK-L1196M-001. Source study: 2026 ALK functional atlas, DOI 10.1186/s13059-026-03977-4. Difficulty: low relative to the open patient case. This is an assay adjudication task, not a patient treatment recommendation.

## Question and hypotheses

**Primary hypothesis:** ALK L1196M has a drug-specific resistance phenotype in the source assay, rather than equal resistance to every tested ALK inhibitor.

**Alternative A:** apparent differences reflect drug concentration, model background, assay definition or baseline growth rather than a transferable mutation-specific effect.

**Alternative B:** guide/editing artifacts or unequal expression account for the screen result.

**Mechanistic hypothesis, separate from the phenotype:** L1196M alters inhibitor interaction or kinase conformation. Neither the screen label nor a predicted structure alone establishes this mechanism.

## Exact source inputs

Data directory: `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/alk-atlas/`.

| File/table | Use |
|---|---|
| `13059_2026_3977_MOESM2_ESM.xlsx`, Table S2, row 1331 | Target ID `ALK_E23_C70A`, amino-acid change L1196M, three classifications/scores and fitness |
| Same workbook, Table S1 | Guide/edit identity; repeated guides are not independent variants |
| Same workbook, Tables S6 and S7 | Locate individual validation and dose-response evidence; interpret layouts before extracting |
| Same workbook, Table S11 | Construct sequence identity, including EML4–ALK context |
| `13059_2026_3977_MOESM1_ESM.docx` | Assay/figure context and units cross-check |

Pin the original file hashes before execution. Preserve source field names, precision and units. The workbook is public experimental evidence, not a matched clinical cohort. The easy task can be open-book; if predicting hidden labels, the evaluator must supply a sanitized packet with target outcome cells and equivalent answer-bearing material removed.

## Analysis plan

1. Confirm variant ID, amino-acid label, construct and reference mapping. Preserve nucleotide identity rather than using only the protein substitution.
2. Extract each drug's classification and continuous resistance score separately. Report fitness as a different endpoint. Resistance scores are not IC50s or resistance probabilities, and magnitudes need not be comparable across drugs.
3. Locate matched wild-type/control and individual validation data. Check replicate unit, duration, measurement type and usable concentration range. Do not infer that every selected validation table supplies independent clones or clinical exposures.
4. Compare screen and individual assays. If raw dose-response values are suitable, estimate mutant/WT IC50 ratios within each matched assay and confidence intervals across independent experimental replicates. Report an unidentifiable curve as such; do not manufacture estimates from categorical labels.
5. Review concentration discrepancies before quantitative cross-assay comparisons. The S5 header/legend conflict documented in STUDY_PRIORITIES.md blocks absolute exposure conclusions, not extraction of S2 categorical outcomes.
6. Return supported, contradicted or unresolved for each hypothesis, with precise source references and the remaining limitation.

## Falsification and next experiment

The narrow source-label hypothesis is contradicted if the source labels do not differ across drugs. The stronger causal phenotype is weakened if it fails matched independent edited models, disappears after correcting expression/editing artifacts, or does not revert when the variant is reverted.

Propose WT, L1196M and revertant comparisons with verified edit identity, matched expression, vehicle controls and independent biological replicates. Measure drug-response and pathway inhibition together. Predefine assay dynamic range and a minimum effect based on assay variability before seeing new results. Binding/kinase assays can then separate interaction effects from downstream context. A cellular phenotype need not imply clinically attainable rescue.

## Agent responsibilities

Bioinformatics returns the exact extracted record and identity checks. Statistics challenges endpoints, independent replicates and uncertainty. Pharmacology checks concentration meaning and forbids invented patient exposure. Structural biology makes a testable prediction only if exact sequence/ligand inputs are supplied. Wet lab chooses the smallest orthogonal experiment. The integrator preserves disagreement and states whether it affects the narrow assay conclusion or only its transfer.

## Required output

Return a drug-by-endpoint table with source cells; a ranked hypothesis list; at least one concrete counterexplanation; the interpretation boundary; and one next experiment with positive, negative and inconclusive interpretations. Mark missing evidence explicitly.

Success means correct assay-specific interpretation and a defensible validation plan. Published phenotype recall alone is not evidence that multi-agent debate improves reasoning. For evaluation, keep the expected drug labels in the evaluator-only store, not in this hypothesis prompt. The surrounding source archive is not currently access-isolated.

Source: [primary ALK study](https://link.springer.com/article/10.1186/s13059-026-03977-4); original local workbook as above. No new assay result is asserted here.
