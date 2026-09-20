# Test the hypothesis in hypothesis.txt

One cohort: GEO GSE28460, 49 children with precursor B-ALL, 98 matched diagnosis
and relapse samples, 54,675 Affymetrix GPL570 probes. All patients eventually
relapsed after conventional ALL treatment. This is not a CAR-T cohort.

## Files

- hypothesis.txt: the hypothesis to test, not an established conclusion.
- expression_log2.tsv.gz: all 54,675 probes by 98 samples.
- samples.csv and patient_pairs.csv: original sample IDs and explicit pairings.
- probe_annotation.tsv: legacy GPL570 probe-to-gene mapping, with ambiguity flags.
- hypothesis_gene_sets.json: two fixed, author-defined operational gene panels.
- preview_original_signal.csv: ten original-scale rows for a quick opening check.

The expression is log2 of the positive normalized signal deposited in GEO. Do not
log-transform it again. No imputation or additional normalization was performed.
This is not raw RNA-seq count data. Original source downloads are kept outside the
agent input for reproducibility.

## Primary test

1. Verify counts, pairing, expression scale and mappings. Pair by patient ID; the
   diagnosis and relapse column orders differ. Patients are biological replicates.
2. Use only single-symbol probe mappings for the fixed panels. For each gene and
   sample, take the median log2 intensity of its mapped probes. Report panel
   coverage and exclusions; never substitute genes after looking at effects.
3. Within each patient calculate relapse minus diagnosis for each mapped gene.
   For each panel, take the median of these gene differences as the patient's score.
   Require at least 9 of the 12 panel genes to be mapped; otherwise mark that panel
   unevaluable. Report all 49 patient scores, the median score, fraction positive,
   and a patient-bootstrap 95% confidence interval with a fixed random seed.
4. Test each panel score against zero with a two-sided Wilcoxon signed-rank test;
   specify zero handling and adjust the two p-values with Benjamini-Hochberg.
   If all differences are zero, report no change rather than a software error.
   Operational support requires a positive median, adjusted p < 0.05, and a
   bootstrap interval entirely above zero. This decision rule is a benchmark
   convention, not a clinical threshold. The joint hypothesis requires both panels
   to pass. Report partial support, no support, or inability to evaluate honestly.
5. As secondary analysis, explore the whole transcriptome with paired tests and
   multiple-testing correction. Keep this exploratory work separate from the two
   fixed tests. Perform sensitivity checks for influential patient pairs and probe
   aggregation. Internal resampling is not independent cohort validation.
6. If warranted, nominate up to three mechanisms and discriminating experiments,
   with controls and outcomes that would refute them. Return runnable code, a
   machine-readable result table, a figure and a short evidence-based report.

## Limits and alternative explanations

Do not confuse diagnosis samples with non-relapsing controls. This cohort cannot
estimate relapse risk versus cure or establish clinical treatment efficacy. Bulk
composition, prior treatment, subtype and technical effects may explain expression
changes. Increased pathway-related RNA does not prove pathway activity, causal
resistance, mutations, splicing, or a cell-surface therapeutic target.

Early/late relapse labels disagree between deposited metadata and the paper;
keep them as supplied and do not use those subgroups for the primary analysis.
There is no independent validation cohort in this cleaned package. Follow-up
validation and functional perturbation are required for mechanistic conclusions.

For a closed-book agent test, use only this input directory and your own output.
Do not consult publications, neighbouring reports or evaluator files. Public study
identifiers remain visible; this tests executed analysis and reasoning, not unseen
biological discovery. A null result can be a correct agent result.
