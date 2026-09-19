# Finding-by-finding reproduction status

This table covers 20 finding groups. Acquisition and parsing are complete for the stated released inputs; numerical replay is claimed only where explicitly shown. Full model fitting and full raw-to-figure reproduction remain incomplete. See the [detailed input matrix](DATA-ACCESS.md), [remaining gaps](GAPS.md) and [integration handoff](INTEGRATION-HANDOFF.md).

| Figure group | Finding | Acquired or recomputed | Remaining qualification |
|---|---|---|---|
| F1ab-S1 | Clinical intron retention | Nine released pairs recomputed; all 83 public Orlando RNA FASTQ objects verified. | Stated paired test gives p=.01953125 versus published .009; exact read preprocessing remains incomplete. |
| F1c-F6a-S1-S8a | TARGET splicing and expression | Published correlations replayed; 220 sample-runs mapped to 160 participants. | Historical raw inputs controlled; source-table replay is not a MAJIQ rerun. |
| F1d-S1-S8a | Normal B-cell comparators | Exact 21-sample map/PSI recovered; processed expression qualified. | CPM is not TPM; duplicate immature-B columns and historical raw processing need care. |
| F1fg | Reporter versus endogenous splicing | Measured figure source and construct references acquired. | Assay summary/test replay remains to be implemented. |
| F1hi-S1-table1 | Patient mutations in reporters | Mutation identities and measured figure source acquired. | Construct/control and replicate-aware numerical analysis remains. |
| F2-S2-S3 | Reporter counts and barcodes | All 19,043 SD1/GEO rows reconciled; five artifact columns explain 172,395 counts. | Raw RNA downloads partial; custom reconstruction script absent. |
| F3acde-S4 | 4,255 effects and 193 calls | All 351 flags and 193 identities reproduced from published predictions. | Original model fit, eligibility, weights and optimizer not reproduced. |
| F3b-S4ab | Held-out validation | All released folds/barcodes recovered; correlations recomputed. | 740/737 fitted barcodes missing from CV; one printed value matches pooling rather than mean-fold rounding. |
| S4c | Occurrence reliability calibration | Methods and published curve acquired. | No numerical S4c worksheet or original resampling indices located. |
| F3ef-S5 | Experimental model validation | Numerical means/SD, delta comparisons and model predictions acquired. | Do not infer three individual replicates; baseline-specific comparison still to run. |
| F2b-F4ab | Cryptic isoforms and coding | Released 96-isoform annotation and author code acquired. | Full coordinate/ORF replay still to implement; predicted coding effect is not surface measurement. |
| F4e-S6a | Cryptic associations | Original score matrix yields 38 pairs, 36 isoforms and 31 mutations. | Count-to-score construction not fully matched; app uses a different 30-pair rule. |
| F4cd | Five cryptic validations | Construct identities and measured source acquired. | Band/replicate-aware RT-PCR replay remains. |
| F4fg-S6 | Splice predictors | Full released predictions and historical code acquired. | Upstream historical model/reference execution not performed. |
| F5abcd-S7 | RBP prioritization | 13 historical DeepRiPe weights verified; complete aggregates reproduce 80/73/95 selected RBPs. | Motif/threshold joins still need reconciliation; tensors/inference untested; individual Gu matrices unavailable. |
| F5ef-S8bcd | RBP knockdown splicing | Measured source acquired and inspected. | PTBP1 has four labeled replicates versus n=3 and invalid probability-labeled cells; no forced statistical pass. |
| F6b | Clinical PTBP2 increase | Nine source expression pairs give p=.037109375, matching rounded .037. | Expression cohort differs from retention cohort; logRPKM/FPKM normalization labeling needs reconciliation. |
| F6c | PTBP1 binding | All eight BigWigs parsed; four libraries mapped as 2 replicates × 2 RNase dilutions. | Source profile totals 1,322 versus 484 in plus tracks; raw iCLIP downloads disqualified/partial. |
| F6def-S9-S10 | Surface CD19 and junction qPCR | Per-replicate surface reductions and Ct-based ratios recomputed. | No FCS/event vectors for re-gating; two biological replicates per cell line. |
| COMPLEMENT-GSE197215 | Separate stimulation cohort | Four RDS decoded; raw counts and full cell/library/donor/outcome maps qualified. | 3,345 donor-113 cells unmapped; CAR/cell-type labels absent; no expression contrast run. |
