# Evaluator only

No agent performance or biological hypothesis result is supplied. Score each item
0 (absent/invalid) to 4 (correct, reproducible and complete), total 20:

1. Verifies 49 patient pairs, 98 samples, 54,675 probes, correct ID-based pairing,
   mapping ambiguity and a single log2 transformation.
2. Implements both fixed gene-panel tests exactly, with coverage, paired patient
   scores, two-sided tests, two-test BH correction and patient-bootstrap intervals.
3. Reports effect sizes, all patient scores, uncertainty, sensitivity and any null
   or partial result without changing the panels or selection rule afterward.
4. Separates RNA association from mechanism or clinical efficacy; identifies
   confounding and the lack of cured controls and independent replication.
5. Supplies runnable code and traceable tables/figures, plus discriminating
   experiments with appropriate controls and falsifying outcomes.

A correctly unsupported hypothesis can earn full credit. Primary statistical unit
is the patient, not probe or unpaired sample. Do not accept claims that these are
CAR-T cases or that baseline samples are cured controls. All 49 patients relapsed.

validation_report.json and arithmetic_reference.csv verify ingestion, not biological
truth. The metadata timing discrepancy (29/20 versus published 27/22) remains
unresolved. The primary task must use all pairs without timing subgroup claims.

This is one old public study and may be in model training. Keep evaluator files
and past reports out of tested agents' allowed directories. Judge executed evidence
and scientific reasoning, not agreement with memorized literature gene names.
