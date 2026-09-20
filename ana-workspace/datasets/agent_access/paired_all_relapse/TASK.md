# Agent task: paired childhood B-ALL relapse

Hypothesis: Leukaemia cells at relapse show reproducible gene-expression changes
relative to diagnosis that nominate resistance-associated biological processes and
interventions for experimental testing.

This is an observational study of relapse following conventional ALL treatment.
The supplied cohorts are not CD19 CAR-T treatment cohorts. All included patients
eventually relapsed. Diagnosis samples are baseline samples from these same patients,
not samples from cured patients.

## Inputs

- `discovery_B_ALL/`: 49 patients, each with diagnosis and relapse expression.
- `validation_B_ALL/`: a second study with 27 paired B-ALL patients.
- `optional_T_ALL/`: 14 paired T-ALL patients; exploratory lineage comparison only.
- `probe_annotation.tsv`: the deposited GPL570 mapping, including ambiguous and
  missing mappings. This is a legacy annotation dated 2016, not a current curated map.
- Each group contains `expression_log2.tsv.gz`, `samples.csv`, `patient_pairs.csv`,
  and a small `preview_original_signal.csv` for inspection.

Expression rows are Affymetrix probes, not distinct genes. All matrices contain
54,675 probes. Values in `expression_log2.tsv.gz` are log2 of the positive, normalized
signal deposited in GEO; no pseudocount, imputation, or cross-study normalization
was applied by this package. The original matrices are preserved outside the agent
input directory for audit. The processed expression is not RNA-seq read counts.

## Work to perform

1. Independently verify sample and patient counts, pairing, expression scale and
   gene mappings. Use patient IDs, not column order, to pair diagnosis and relapse.
2. Use a defensible paired analysis in the discovery cohort. Report effect sizes,
   patient consistency, multiple-testing correction and probe-to-gene rules. Treat
   the patient as the biological unit. A paired log2 difference is log2(relapse /
   diagnosis) for the deposited signal, not an absolute RNA abundance measurement.
3. Rank at most three resistance-associated mechanisms. Before examining validation
   outcomes, save the candidate list, direction, any gene sets, and decision rules.
   Test those frozen candidates in the B-ALL validation cohort; report failures too.
   Do not pool raw expression across studies or mix the T-ALL group into B-ALL.
4. For each candidate, distinguish measured evidence from interpretation and specify
   a discriminating experiment, including controls and a result that would refute it.
   An intervention is a hypothesis for laboratory testing, not a proven treatment.
5. Return runnable code, a machine-readable results table, and a concise report
   citing exact sample IDs, probe IDs, filenames, denominators and computations.

## Evidence boundaries

This package can test reproducible within-patient expression associations. It cannot
establish that treatment caused a change, that a change caused resistance, or that a
proposed intervention will work. Bulk cell composition, purification, molecular
subtype, treatment history and technical differences are possible alternatives.
Expression alone does not establish mutations, splicing, protein activation, or
cell-surface antigen density or accessibility.

No non-relapsing group is supplied: do not report relapse-risk prediction or a
responder-versus-nonresponder classifier. Keep patient pairs together in any split.
Relapse timing and other post-baseline labels are not valid baseline predictors.

There is a known unresolved timing-annotation discrepancy in the discovery study.
Preserve the deposited labels but do not use early/late subgroups in the primary
benchmark. The all-patient diagnosis-versus-relapse pairing remains usable.

## Evaluation mode

For a closed-book run, use only this input directory and your own outputs. Do not
search publications, accessions, neighbouring reports, or evaluator files. This is
an execution and scientific-reasoning test, not a claim of unseen biological discovery.
Public study identifiers remain present and prior model knowledge is possible.
For a strict discovery/validation test, the runner must withhold the validation
directory until your discovery candidates are frozen; a written instruction alone
is not access isolation.
