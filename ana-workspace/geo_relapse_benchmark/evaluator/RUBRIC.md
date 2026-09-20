# Evaluator guidance (do not provide to the tested agent)

This package prepares data and a task; no agent performance has yet been measured.
The biological hypothesis has not been tested by the preparation script.

Score five dimensions from 0 to 4 (20 total):

1. Data integrity: reads the supplied matrices; verifies the exact patient counts,
   pair identities, positive deposited scale/log2 transformation and probe annotation.
2. Statistical design: paired patient analysis, effect sizes and multiplicity;
   handles multiple/ambiguous probes explicitly and does not use count-only models
   such as DESeq2 directly on microarray intensities.
3. Replication: freezes discovery candidates before validation; reports every frozen
   candidate and uncertainty; no tuning or gene selection using validation outcomes.
4. Scientific inference: addresses alternative explanations and states measurement
   limits; no causal, CAR-T-specific, surface-protein or clinical efficacy overclaim.
5. Experimental reasoning and reproducibility: proposes discriminating experiments
   with appropriate controls and falsifying outcomes; runnable code reproduces tables.

Rubric anchors: 0 absent/invalid; 1 major errors; 2 partly correct with gaps; 3 correct
with minor omissions; 4 fully correct and documented. A finding that fails to
replicate can earn full credit if analysis and interpretation are sound.

Mark the run scientifically invalid regardless of score if it calls diagnosis
samples non-relapsing controls, claims these are CAR-T-treated cohorts, invents
measurements, or bases its primary comparison on incorrectly paired patients.

`validation_report.json` gives exact ingestion assertions. The three
`*_arithmetic_reference.csv` files give patient-level all-probe sanity checks using
log2(relapse) minus log2(diagnosis). They are arithmetic references, not validated
biological mechanisms or a complete differential-expression answer key.

The source matrices each contain 54,675 probes. GSE28460 contains 49 complete B-ALL
pairs (98 samples). GSE18497 contains 41 complete pairs (82 samples), partitioned
into 27 B-ALL pairs and 14 T-ALL pairs. The primary comparable B-ALL total is
76 patient pairs across two studies. The 90-patient total includes a different
lineage and is not one pooled B-ALL cohort.

GSE28460's deposited metadata has 29 early/20 late patients, while the original
paper reports 27/22 for expression profiling. This discrepancy is unresolved.
No arbitrary correction is acceptable. GSE28460 p51 and p54 also occur in different
column orders at diagnosis and relapse: IDs must determine pairing.

The GPL570 annotation has 42,904 single-symbol probes, 2,214 multi-symbol probes,
and 9,557 probes without a gene symbol. Single-symbol does not mean unique gene,
modern annotation, or demonstrated sequence specificity.

Use a fresh agent run that has not seen this evaluator folder or the research
conversation. For strict holdout evaluation, expose only discovery inputs initially,
then supply validation after saving a timestamped/hash-identified candidate list.
Filesystem folders alone do not enforce a holdout. Old, public datasets may already
be in model training; use deterministic recalculation, code execution and explicit
evidence tracing to evaluate agents rather than scoring remembered gene names.
