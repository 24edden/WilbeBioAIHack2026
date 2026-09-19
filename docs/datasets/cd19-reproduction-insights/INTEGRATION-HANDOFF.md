# Study-specific integration possibilities

**Current scope:** [general skill guidance](NEXT-STEPS.md) and [data references](DATA-REFERENCES.md). The study-specific possibilities below preserve the earlier audit; they are not a required sequence or reusable skill instructions. No new analysis adapters are implemented by the skill update.

This is a concrete proposal for the application/analysis agents. All original sources remain read-only. Develop readers in a separate checkout and review source-catalog changes before deployment. Do not edit accepted evidence or either saved decision; new computations require new versioned recipes and evidence records.

## Priority 0 — register and qualify the inputs

Use the branch manifests referenced by `inventory-index.json`. Every registered file must carry the exact source URL/accession/version, full-file SHA-256, physical path, format, access/license status and sample role. Reference existing files without copying them. New Brev staging is separate from `/home/ubuntu/rosalind-shared-files` and `/home/ubuntu/rosalind-hackathon-demo`. A manifest record whose status is partial, expected-only, available-not-acquired or metadata-only is not an analysis input.

Proposed new catalog groups are `CD19-PAPER-SOURCE-DATA`, `CD19-AUTHOR-RELEASE-1.0`, `CD19-PUBLISHED-EVALUATOR`, `CD19-PTBP1-QUALIFIED`, `CD19-CLINICAL-RELEASED`, and `GSE197215-QUALIFIED-MAPS`. These names are handoff suggestions, not existing registered IDs. The paper supplement manifest, recovered archive and exact mapping files make each proposed entry reviewable. Keep the current historical source group versions unchanged.

Required reader contracts:

- Workbook cells: retain workbook hash, sheet, exact cell/range, original units, cached value/formula provenance, construct/sample/replicate/control identities. Do not treat formatting dimensions as data counts. Do not execute embedded formulas or external links during intake.
- Reporter: retain the 19,043 rows, two replicates, 195/194 explicit controls, exact barcode orientations, INDELs, original `readcount`, discarded/other category and five artifact-junction columns. Validate G748T as the assay baseline without rewriting the original FASTA.
- iCLIP: hash the original archive, verify members, preserve strand, hg38 coordinates, BigWig source units and all four replicate/RNase-library identities (no IgG/input controls deposited); perform an explicit genomic-to-minigene coordinate transformation.
- RDS: decode the two gzip layers explicitly; use `RNA@counts` and a bounded sparse reader/export. `ADT@counts` is the raw protein assay, while `ADT_renorm@counts` is noninteger and `integrated` values are not raw counts. Preserve the documented missing/all-zero bead ADT measurements. Validate every cell-to-library-to-donor-to-condition join. Quarantine 113; retain the CD139 library discrepancy. Never add modalities, cells or A/B libraries as independent donors.

Qualification scripts and compact source extractions live with their branch reports. Rerun them in isolated environments with versions recorded, then turn the proven behavior into allowlisted app readers. The final package checksums verify delivery; they do not replace each original-source checksum before analysis.

## Priority 1 — reproduce the measured endpoints already released

Start with Source Data Fig. 1b/c/d/g/i, Fig. 3 validation, Fig. 4 RT-PCR, Fig. 5 RBP knockdowns and Fig. 6/S9 measurements. Use each figure's original controls and biological replicate identities. Recompute means, sample SD, per-replicate ratios and stated tests. Record directions/effect sizes and exact source locators, including negative controls and nonsignificant RBP results. For Fig. 3 validation, the numerical release supplies means/SD and delta comparisons; do not invent individual triplicates. Reading a workbook is not a successful numerical reproduction.

For TARGET Fig. 6a, the released 220-sample correlations have been recomputed; preserve the map to 160 participants and distinguish numerical replay of the paper from inference treating repeated participant samples as independent. For Fig. 1b, make the reproduced measurement vector and the p-value discrepancy separate records. The released nine pairs give an exact paired one-sided Wilcoxon p = 0.01953125, not 0.009. The test mismatch must remain visible even though the direction of the effect is supported. Use the clinical report's distinct sample sets for CD19 retention and PTBP expression; the Orlando gene table's all-zero CD19 column is not an intron-retention input.

For surface CD19, distinguish any released fluorescence vectors/histogram bins/MFI from original FCS event data and gating. Recompute only the layers supported by the inspected file. P493-6 and MHHCALL4 are separate cell lines with two biological replicates; tens of thousands of events are not biological n. These do not become NALM-6 surface measurements.

## Priority 2 — reproduce the model, with the evaluator held apart

The complete published predictions and call set allow genuine numerical scoring. They must not be used as training labels or a shortcut to generate an apparent refit.

1. Produce a canonical barcode-by-mutation design and six-output response with explicit eligibility reasons. Compare the exact retained feature identities against 4,255 published variants, including all 656 INDELs. Diagnose discrepancies; do not force the feature count.
2. Implement the documented multinomial/L1 model with independent replicate fits. Lock software, weighting normalization, solver, intercept, stopping rule and random seed. The missing author choices require declared reconstruction/sensitivity variants. A chosen setting that resembles the Methods is not proof of equivalence.
3. Use the recovered reported barcode/fold mapping in `reporter/recovered-model-barcode-fold-map.tsv.gz` for the corresponding published validation subset; all category-expanded records for a barcode stay together. Reconcile the 740/737 fitted records absent from the held-out table before claiming full-coverage tenfold validation. Preserve a newly generated split only as a separately labeled sensitivity run. Use the compound key (replicate, fold, mutation number): the displayed mutation number is reused and is not a global identifier. Persist folds and out-of-fold predictions. Separate training correlations, held-out correlations and the C-selection process. Preserve mean-fold versus pooled reporting: replicate-2 skipping rounds to .92 under the former and .93 under the latter, with .93 printed in Fig. 3b. The released reference has C=10; a synthetic optimizer test does not validate this experiment.
4. Compare both replicate predictions across six outputs with the acquired SD3 table, whose frequency fields are percentages. Its average-delta field is a fraction; the 19-validation delta fields are percentage points. Compare within the published rounding resolution, report full residuals, MAE and correlations, and preserve exact feature identities.
5. Recompute controls/thresholds and compare all 351 flag identities and all 193 unique mutation identities. Matching 193 as a count is insufficient. The package has already reproduced this downstream threshold layer using the published predictions, with zero disagreements.
6. Reproduce the seven-mutation occurrence calibration and 19-validation-construct comparisons separately. HEK293 validation has the G742C background and the G748C* exception; it is not the NALM-6 screen baseline.

If numerical differences persist, report partly reproduced with the unresolved choice and its sensitivity. Do not tune to the answer key without disclosing that this is method reconstruction. Do not silently replace the original held-out validation with a different split/test and call it exact reproduction.

## Priority 3 — binding, cryptic isoforms and prediction dependencies

Recompute the 38 exact cryptic associations from original counts and compare the full released matrix; the already successful extraction/thresholding of that matrix is only the downstream layer. The app's 30-pair stricter criterion remains its own recipe. Replay isoform coding/coordinate analyses for the 96 cryptic isoforms and 71 splice sites, including the 78 noncoding predictions. Do not convert predicted coding disruption into measured surface loss.

For RBP prioritization, use the archived motif/prediction tables and exact effective-site joins. DeepRiPe exports and SD6 have differing row universes and isoform expansion; the methods' threshold wording must be reconciled with actual tables/code. Required historical model-weight identity was investigated and is documented in the reporter report. Public predictions allow figure-level reproduction without new paid inference.

For iCLIP, start from fully qualified processed tracks and independently recompute the CD19 profile and replicate/RNase comparisons. Raw preprocessing remains a separate benchmark with its own software/reference and read-integrity requirements. Additional raw downloads should use the resumable acquisition manifests; partial reads cannot enter analysis.

## Priority 4 — complementary donor-paired stimulation analysis

This is a separate dataset and cannot pass the primary-paper benchmark. The study's released donor outcomes and a full cell inventory are now available, with qualified mappings for the 12 documented donors and explicit unmapped-113 flags. A product-wide paired CD19-versus-mesothelin analysis can be designed for the 12 documented donors after excluding the unresolved 113 cells and declaring technical-library coverage. Aggregate raw counts within donor/condition; combine A/B libraries within donor. Preserve h-/m- feature prefixes, align differing feature lists by identity and declare absent-feature handling. Bead RNA retains 18,504 mouse-feature UMIs, so specify human-feature filtering before normalization. This paired estimand is a complementary reanalysis, not automatically an exact replay of the Bai paper's statistical tests. Beads are an optional general activation comparator. Use donor-level uncertainty, not cell-level pseudo-replication.

CAR-positive and cell-subtype-specific claims additionally require qualified annotations. An h-CAR count is a raw feature, not an established positivity gate. Declare clinical grouping exactly as the source defines it; durable-response classifications can coexist with a later CD19-negative relapse and must not be relabeled. The mapping and outcome conflicts documented in `stimulation/README.md` must remain visible.

## Priority 5 — exact raw-pipeline and access gaps

TARGET raw inputs remain under controlled access. Do not bypass access controls or substitute current open gene-expression files for inaccessible splice-junction/read evidence. Released author PSI/TPM/source tables support a narrower numerical endpoint reconstruction. Original missing fitting/isoform scripts, unexplained validation-set coverage and historical sample manifests are author-request candidates only if the user later explicitly authorizes contact; no contact was made here. Raw Ct/well records are acquired; FCS and gated-event exports were not located. Record each gap at the exact level actually absent.

## Benchmark contract

Score each row of `finding-input-matrix.tsv`, not one undifferentiated “paper passed” status:

- **Reproduced:** recomputed the specified numerical layer from its qualified inputs, with exact sample/variant identities, original units, denominators and declared tolerance; expected results reconcile. State whether this is measured-source, processed-input or raw-pipeline reproduction.
- **Partly reproduced:** some layers or endpoints reproduce, while the model, mapping, assay reader or upstream raw pipeline remains unresolved. The 193-call threshold replay is the canonical example.
- **Not reproduced:** only source acquisition, literature summary, plotting an answer table, synthetic tests, training correlations substituted for held-out testing, or an analysis with a materially different estimand.
- **Reference discrepancy:** qualified released values and the stated calculation disagree with the publication. Preserve both the recomputed value and the published claim; do not score a faithful computation as fabricated or force a false exact match.

Exact identifiers and integer counts require exact agreement. For rounded numeric references, tolerance must derive from the actual rounding (for example 0.01 percentage point display), not an invented permissive threshold. For stochastic reconstructions with missing seeds, report distributions/residuals and partial status rather than retrospectively choosing the best seed. All 20 finding groups must have an explicit disposition before any whole-publication completeness claim.

The previous eight-criterion reasoning pass for the saved demo run remains valid at its original scope. It is not evidence that these numerical criteria passed. No new patients, wet-lab work, app restart, model calls or structure predictions are required to execute the available-data reproduction work.
