# Case 02 — ALK residual disease: adaptation or sampling?

Status: open, proposed hypothesis; not analyzed or experimentally validated. Case ID: ROS-HARD-MAYNARD-TH266-001. Dataset: Maynard PRJNA591860. Independent clinical unit: one patient, two biopsies. Difficulty is an expectation to test, not measured agent performance. The public study is known; this packet does not establish a previously unknown mechanism.

## Scientific question

Does the early residual-disease biopsy show a tumor-cell-intrinsic persistence program, or can the apparent change be explained by cell composition, sampling, assay quality, pre-existing clones or unmeasured exposure?

**Primary hypothesis H1:** residual malignant cells show increased stress/adaptive signaling and reduced proliferation relative to the pretreatment malignant cells, consistent with an early persistence state.

This is a prospective analysis hypothesis. These shifts have not been measured for TH266 in this task. Transcriptomic support would establish a within-case association, not reversibility, non-genetic causality or later clinical resistance.

## Verified clinical anchors

The primary clinical worksheet in `Maynard_Table_S1_sample_metadata.xlsx`, rows 49–50, records:

| Field | LT_S75 | LT_S81 |
|---|---|---|
| Patient | TH266 | TH266 |
| Driver | ALK fusion | ALK fusion |
| Treatment state | TN | RD |
| Days from treatment start | NA | 14 |
| Tissue | Liver, metastatic, core | Liver, metastatic, core |
| Treatment context | Alectinib, second line, prior chemotherapy | Alectinib, second line, prior chemotherapy |

Treat TN as the study's pretreatment category. Do not silently convert its missing day to zero or interpret it as no prior therapy. RD is residual disease, not progression. Same organ does not prove the same lesion or equivalent sampled composition. Patient-specific exposure, a validated resistance mutation status and a washout/rechallenge phenotype are not supplied by these metadata.

## Source packet and readiness

Directory: `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19/gap-fill/longitudinal/maynard_prjna591860/`.

- `Maynard_Table_S1_sample_metadata.xlsx`: clinical fields, sample cell-type counts, cancer-cell annotations and analysis inclusion information.
- `PRJNA591860_processed_expression.RDS`: processed expression; verify object structure, feature IDs and measurement scale before analysis.
- `PRJNA591860_sample_cell_names.RDS`: verify cell-to-sample mapping against the original workbook.

Metadata has been inspected; the expression object and retained tumor-cell counts have not. First create a verified LT_S75/LT_S81 slice. Report unmapped cells, duplicate IDs, retained cells and exclusions. Keep a separate reference subset for context, with patient/source namespaces intact. Do not blend EGFR and ALK samples as interchangeable matched replicates.

## Competing predictions

| Hypothesis | Expected evidence | Evidence that weakens it | Best discriminator |
|---|---|---|---|
| H1: tumor-cell persistence state | Prespecified state changes within credible malignant cells, stable to reasonable QC and composition checks | Change exists only in pooled cells or disappears under annotation/QC checks | Tumor-cell-specific analysis; then time course and functional perturbation |
| H2: cell composition or biopsy sampling | Bulk-like changes track immune/stromal proportions or sampled malignant subtypes | Consistent within-malignant-state change after sensitivity analysis | Decompose composition versus within-state expression; pathology review |
| H3: selection of a pre-existing genetic clone | Genotype-linked malignant population becomes enriched | Adequately sensitive orthogonal genotyping fails to support the proposed clone | Paired deep DNA profiling or linked DNA/RNA, with detection limits |
| H4: inadequate or heterogeneous exposure | Persistence follows low tissue exposure or incomplete target inhibition | Measured adequate exposure and sustained target inhibition | Exposure and phospho-target measurements; prescription alone is insufficient |
| H5: technical/annotation effect | Signal tracks library complexity, damaged cells, batch or unstable tumor calls | Signal survives source-aligned QC and orthogonal measurement | QC/annotation sensitivity and independent assay |
| H0: unresolved | Too few comparable malignant cells or no robust directional signal | Reproducible evidence discriminates alternatives | Report insufficiency and choose the missing measurement |

H1–H5 are not mutually exclusive. Two snapshots cannot distinguish induction of a state from selection of a pre-existing non-genetic state.

## Prespecified computational test

1. Validate the sample/cell crosswalk and source inclusion rules. Produce a flow of total, mapped, QC-retained and malignant cells per biopsy. If either biopsy lacks sufficient credible malignant cells for the proposed summaries, report that the tumor-state test is not evaluable.
2. Freeze a small gene-set panel before looking at target differences: proliferation, stress response, and candidate bypass signaling. Record exact genes, species, version and expression-matched control genes. Missing genes remain missing. Do not choose signatures after seeing which distinguish these two samples.
3. Select analysis methods appropriate to the actual RDS scale. Do not feed log-normalized expression or TPM into a raw-count model. Produce within-biopsy malignant-cell summaries and descriptive state-score distributions, plus separate composition summaries.
4. Compare RD-minus-TN direction and magnitude for the frozen panel. Recheck with cell-depth balancing, alternate credible tumor annotations and sensitivity to low-quality cells. Cell resampling quantifies sensitivity to sampled cells only; it is not a confidence interval over patients.
5. Test whether whole-biopsy differences persist within malignant cells or primarily reflect mixture changes. Single-cell ALK expression dropout is not evidence of ALK loss, and inferCNV annotation is not an orthogonal DNA resistance assay.
6. Rank hypotheses by traceable evidence. With one pair, do not report population differential-expression significance or causal discovery. Any expanded donor-level analysis requires a separately frozen eligible cohort and genuine biological replication.

## What would actually test non-genetic persistence?

In a suitable ALK-fusion model, use a treatment time course, washout and rechallenge alongside genotype tracking, target inhibition and viability. Test one candidate pathway only after the case analysis supplies a rationale. Compare ALK inhibitor alone, candidate perturbation alone, combination and matched controls; verify that loss of persistence is not nonspecific toxicity. Use independent biological replicates and an orthogonal readout.

A state that recedes after withdrawal and whose perturbation changes persistence supports a reversible-state explanation within that model. Persistent genotype-linked survival favors genetic selection. Lack of reproducibility or absence of candidate-specific effect weakens the proposed mechanism. Failure to detect a genotype does not prove none exists. Models unrelated to TH266 supply mechanistic context, not patient-specific validation.

## Debate objective and scoring

Bioinformatics and pathology should challenge cell identity/composition; clinical science should stop any substitution of progression for RD; pharmacology should identify missing exposure; statistics should enforce the one-patient boundary; wet lab should distinguish competing mechanisms. A structural tool is warranted only if a specific molecular hypothesis and correct inputs emerge. Absence of a relevant structural call can be the correct decision.

Required output: verified two-sample manifest; QC/readiness result; prespecified state/composition summary if feasible; hypothesis evidence and counterevidence; unresolved distinctions; and one experiment with predicted outcomes for at least two alternatives. A well-supported unresolved conclusion is acceptable. Do not reward agents for guessing H1.

Use the common rubric in STUDY_PRIORITIES.md. Grade evidence fidelity and discrimination, not agreement with a hidden biological answer: no such answer has been established for this case. This case is harder because available observations underdetermine mechanism. A genuinely novel discovery claim would additionally need independent validation and a defined literature/evidence cutoff.

Source: [Maynard et al., Cell 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/), local Table S1 and the acquisition README. Processed reuse source recorded locally: [Zenodo release](https://zenodo.org/records/7860559).
