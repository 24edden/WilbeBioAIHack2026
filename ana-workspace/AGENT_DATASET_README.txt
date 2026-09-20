Active dataset: paired childhood ALL diagnosis and relapse from GEO

Start with hypothesis/hypothesis.txt and datasets/agent_access/paired_all_relapse/TASK.md.

discovery_B_ALL/: GSE28460, 49 B-ALL patient pairs, 98 samples.
validation_B_ALL/: GSE18497 B-ALL subset, 27 patient pairs, 54 samples.
optional_T_ALL/: GSE18497 T-ALL subset, 14 patient pairs, 28 samples.

Every group has expression_log2.tsv.gz (54,675 probes), samples.csv,
patient_pairs.csv and a small original-signal preview. probe_annotation.tsv
provides the legacy GEO platform mapping and flags ambiguous/missing symbols.

This replaces the previous CD19 CAR-T hypothesis and active nine-patient SRA input.
The previous tracked files are retained under archive/cd19_car_t_previous/.
Older untracked input/, reports and design work are not inputs to this benchmark.

These cohorts concern relapse after conventional ALL treatment, not CAR-T.
There are 76 B-ALL patient pairs across two studies; do not call the full
90-patient download a single B-ALL cohort. All included patients relapsed.

For a closed-book agent evaluation, supply only the designated input directory
and restrict reading to that directory and agent outputs. Do not expose source
publication metadata, archive files, neighbouring reports or evaluator outputs.
For a strict validation holdout, initially withhold validation_B_ALL/ and
optional_T_ALL/ until discovery candidates have been frozen.

Operator documentation and provenance: geo_relapse_benchmark/README.md.
Evaluator checks and scoring rubric: geo_relapse_benchmark/evaluator/.
