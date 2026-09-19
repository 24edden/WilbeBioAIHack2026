# Prepare the acquired data for agent workflows

**Recommended next work: implement a versioned data-preparation layer, then run one bounded numerical reproduction end to end.** Additional broad data collection is a lower priority because qualified released counts and measurements already support useful analyses. This document is an implementation recommendation; publishing it does not mean the new adapters or workflows are deployed.

## What was newly downloaded, and what was qualified

New acquisitions include all ten paper supplements and the separate Source Data archive; the complete author code release and history; two verified PacBio library FASTQs; 83 verified public Orlando RNA FASTQ objects; 13 historical DeepRiPe model files; the DepMap 21Q2 expression release; complete released RBP expression aggregates; and additional clinical/sample/method metadata. Original hashes, exact versions, paths and parse scope are recorded in the source inventory. The Orlando reads are targeted gene exports, not whole-transcriptome reads.

The four GSE197215 RDS objects and the original iCLIP archive already existed: they were fully hashed and decoded/parsed rather than redownloaded. Large reporter RNA and iCLIP transfers remain partial and excluded from usable inputs. TARGET historical raw material remains controlled-access. No new patient data, wet-lab experiments or paid model inference are needed for the first preparation and replay work.

## First deliverable: lossless, versioned inputs

| Priority | Derivative | Required behavior | Acceptance check |
|---|---|---|---|
| 1 | Source registry and readiness table | Separate acquired, verified, parsed, mapped and workflow-ready states; pin source/version/hash and physical location; explicitly exclude partial files | A recipe refuses missing, checksum-failed, unmapped or unsupported inputs before running |
| 1 | Reporter counts, mutation and barcode tables | Stable `(replicate, barcode)` keys; preserve all 19,043 rows, readcount denominators, controls, INDELs and discarded/artifact categories; retain source and transformed values | Exact SD1/GEO reconciliation; all 172,395 artifact counts explained; count totals conserved |
| 1 | Published evaluator tables | Put fitted values, CV outputs/folds, 193 calls and 38 cryptic associations in an explicit evaluator partition | Reproduction mode can access references; independent-discovery agents cannot obtain answer keys via joined tables or context |
| 1 | Experimental measurement tables | Typed long tables with figure, source cell, assay, cell line, biological replicate, technical well, construct/control, value and units | Every row traces back to a workbook hash and cell; missing replicates/p-values are flagged, never fabricated |
| 2 | Clinical sample crosswalks | Keep TARGET sample versus participant identity and the two distinct Orlando patient sets; preserve timepoint and normalization labels | 220 TARGET runs map to 160 participants; pair counts match the specific endpoint |
| 2 | Stimulation count/mapping exports | Export raw sparse RNA and ADT separately; preserve species prefixes, feature presence, missingness and library/donor/condition joins | 101,326 cells conserved; 97,981 map to 12 documented donors; 3,345 unresolved cells retained in quarantine; count sums match originals |

Use derived directories, explicit transformation versions and deterministic receipts. Original data remain read-only. A schema should include `source_id`, `source_sha256`, `source_locator`, `sample_id`, `biological_unit`, `units`, `mapping_status`, `qc_flags`, `transform_version` and `intended_use`; assay-specific fields extend it. Stable keys are assay-specific, not a single invented patient/barcode key for every experiment.

## What “cleaning” must preserve

- Do not impute missing ADT as zero or treat all-zero protein profiles as confirmed negative biology. Preserve the BE157 missing and BE167 all-zero exceptions.
- Do not silently discard donor 113, manufacture CD139A or infer CAR negativity from absent h-CAR RNA. Provide full and qualified views with exclusion reasons.
- Do not convert integrated/normalized Seurat assays into raw counts or join feature rows by position. Preserve distinct feature universes and human/mouse identifiers.
- Do not change the published measurements to force the Fig. 1b p-value, CV rounding convention, PTBP1 replicate count or iCLIP profile to agree. Those are scientific discrepancies, not formatting errors.
- Do not treat mean/SD summaries as three individual replicates, technical wells as biological replicates, or cells/libraries as independent patients.
- Do not choose filters to force a 4,255-feature universe or tune model settings against hidden evaluation results without declaring method reconstruction.

## First workflow to wire into the agent

Build an allowlisted `replay_published_variant_calls` reader/recipe first. It reads qualified reporter controls and the explicitly identified published predictions, computes the per-replicate empirical thresholds, and returns the exact variant/isoform flags, disagreement table and source receipts. Its expected result is 351 flags across 193 variants, already independently recomputed in this audit. The agent must label this result **call-layer reproduction conditional on published predictions**, not a new model fit.

Next add a measured-source clinical test recipe. It reproduces the nine-pair retention vector and reports the exact paired signed-rank p=.01953125 alongside the paper's .009 as an unresolved reference discrepancy. This verifies that the workflow can report a mismatch honestly rather than force a pass. Then add the PTBP2 and qPCR/flow endpoint readers that have explicit sample/control maps.

For each recipe, acceptance requires qualified inputs, deterministic output hashes, source-to-result provenance, actual real-data execution, bounded result tables and a new accepted evidence record. Run conservation/missingness tests and a small real-data end-to-end check before registering a new catalog version. Preserve the original hypothesis and past decisions; new source groups require a fresh snapshot/investigation where the current app requires it. No application registration or deployment is performed by this publication task.

## Follow-on scientific analyses

1. Reconstruct the multinomial model after documenting eligibility, solver and weighting assumptions. Use recovered reported fold assignments for the released subset, and explain the 740/737 fitted records absent from CV. Report agreement and sensitivity rather than asserting the absent author implementation has been recovered.
2. Reconstruct count-to-cryptic-association scoring; the released matrix's 38-pair threshold extraction is already verified, while the upstream score construction remains unresolved.
3. Run a separate, donor-paired whole-product CD19-versus-mesothelin response analysis after locking the endpoint, normalization, feature universe, aggregation, exclusions and uncertainty. CAR-positive/subtype claims need additional annotation decisions. This cohort cannot pass the primary paper benchmark.
4. Resume large raw-read downloads only when a planned raw-pipeline comparison needs them; pursue controlled access or author clarification for the precise remaining gaps.

Detailed handling rules are in the reporter and stimulation readiness notes and the complete integration handoff. The publication is a data/method handoff, not a claim that all agent workflows are ready.
