# Ana's paired tumour-expression input: source assessment and handoff

## Inclusion finding

The active dataset on Brev is
`/home/ubuntu/ana-workspace/datasets/agent_access/GSE28460/`.
`/home/ubuntu/ana-workspace/input/` is a symlink to that directory.
A name-only inventory found exactly one immediate `agent_access` dataset:
`GSE28460`. Ana's `AGENT_DATASET_README.txt` and `START_HERE_GEO_RELAPSE.md`
identify it as the sole active cohort and say older patient datasets were removed.
Historical CD19 analysis/header files remain in a different output directory;
those are not treated as source measurements here. Evaluator files and neighboring
scientific reports were not read.

The completed CD19 investigation `b5898d6c3b3940ee9eac90f01b8b8e19` did **not**
include GSE28460: its exported case/evidence/analysis records contain no such
accession or dataset path, and the old file registry included Ana's hypothesis
folder but not this agent-input root. Its nine-patient CD19 clinical endpoints
are different measurements from a different cohort. No cross-cohort patient join
or historical-result overwrite is permitted.

This inclusion finding is source-specific. It does not mean the earlier CD19
analyses were invalid; it means this additional cohort must receive its own
qualified analysis and explicit scientific scope.

## Starting-point assessment

- **Objective:** include the available paired patient measurements in a new
  investigation, preserving the original scientist's hypothesis. Assess the
  supplied expression panels and relevant CD19 expression context.
- **Observed input:** 54,675 Affymetrix GPL570 probes by 98 sample columns, with
  49 uniquely mapped diagnosis/relapse patient pairs. Metadata and matrix use
  different orders, so pairing uses exact identifiers.
- **Source identity:** prepared derivatives of public GEO GSE28460, pinned by
  exact byte counts and SHA256 in `app/gse28460_analysis.py`. These pins identify
  the local prepared files; they do not claim the prepared matrix is an untouched
  original GEO download.
- **Clinical scope supplied by the package:** childhood precursor B-ALL after
  conventional treatment, all patients eventually relapsing. No CAR-T exposure is
  established. Diagnosis samples are not non-relapsing/cured controls.
- **Measurement scale:** existing log2-transformed deposited normalized microarray
  signal. The ten original-scale preview probes provide 980 arithmetic checks
  against the matrix. No second logarithm, imputation, new normalization or
  count-based RNA-seq model is appropriate.
- **Relationships:** samples and patient pairs match every expression column
  exactly once. Probe annotation matches every measured probe. Only explicitly
  single-symbol mappings contribute to gene expression.
- **Companion hypothesis:** `hypothesis.txt` and its two fixed gene panels were
  supplied by the data curator. They concern cell-cycle/DNA-repair expression at
  relapse and do not silently replace the user's CD19 CAR-T hypothesis.
- **Supportable analyses:** paired expression effects, fixed operational-panel
  tests, within-patient context for CD19/PTBP1/PTBP2 expression, transcriptome-wide
  exploratory paired tests, and internal sensitivity checks.
- **Unresolved inputs:** raw-array preprocessing, cell composition, subtype,
  treatment history/batch qualification and independent validation. Deposited
  early/late relapse labels reportedly disagree with the paper and are not used
  for primary subgrouping. This gene-expression platform does not supply a
  qualified CD19 splice endpoint or CAR binding/killing measurement.
- **Handoff:** root registers the additional source root and recipe, then starts
  a new versioned agent investigation. Historical cases/results stay unchanged.

Public accession: [GEO GSE28460](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE28460).
No publication-derived expected answer or evaluator result is used in the recipe.

## Runtime interface

```python
from app.gse28460_analysis import catalog_entry, analyze, source_manifest

# Recipe metadata has source pins and methods, never source outcomes.
recipe = catalog_entry()

# Server-selected, fixed recipe. No model-supplied path or parameter.
evidence = analyze(case_id="cd19-car-t")

# Optional caller-owned artifact directory for human inspection/download.
evidence = analyze(dataset_root="/qualified/input/GSE28460",
                   case_id="cd19-car-t",
                   output_dir="/run-owned/output/gse28460")
```

`TEAM_TBD_GSE28460_ROOT` is the server-side root override. The default is the
exact Brev directory above. Missing/changed sources fail instead of substituting
synthetic data. All eight input files are checked on every execution.

`source_manifest()` returns the eight prepared-input pins and logical paths.
`catalog_entry()` uses recipe ID `gse28460-paired-expression`. `analyze()` returns
one accepted-evidence-shaped object with ID `ANALYSIS-GSE28460-PAIRED`, canonical
content hash, actual statistical methods, independent units, complete patient
panel scores, sensitivity checks, and explicit limits.

Only these new files implement this work: `app/gse28460_analysis.py`,
`tests/test_gse28460_analysis.py`, and this handoff. Shared file-catalog, case
registration, mandatory new-run inclusion and deployment are owned by root.

## Analysis specification

1. Validate all source hashes, expected dimensions, unique probe/sample IDs,
   cohort/lineage metadata and explicit patient/timepoint relationships. Compare
   log2 matrix values with the positive original-scale preview to tolerance 1e-6.
2. Exclude missing/ambiguous probe-to-symbol mappings. For every gene/sample,
   take the median log2 intensity across its qualified probes. Do not choose
   probes based on their effects.
3. Compute relapse minus diagnosis within each patient, then each panel's median
   gene difference within the patient. At least 9 of the fixed 12 genes are
   required. No post-result substitutions are allowed.
4. Return all 49 patient scores, median and positive fraction, plus a percentile
   95% CI for the median from 10,000 patient-pair bootstrap draws (seed 28460).
5. Use two-sided Wilcoxon signed-rank tests. No zero or tied absolute differences
   permits the exact method; otherwise use the asymptotic tie-corrected method,
   `zero_method=wilcox`, no continuity correction. All-zero scores yield p=1.
   Apply BH over the planned two-panel family (unevaluable panel contributes
   p=1). A panel's operational support requires positive median, BH q<0.05 and
   CI entirely above zero. Both must pass for joint support. These are benchmark
   criteria, not clinical thresholds or proof of pathway activation.
6. Repeat with mean rather than median probe aggregation. Leave one patient out
   in turn to assess median-sign/influence sensitivity; this latter check does
   not rerun the full CI/BH support rule.
7. Separately test every qualified mapped gene using paired asymptotic Wilcoxon
   tests, with all-zero genes retained at p=1 and BH over the entire gene family.
   CD19/PTBP1/PTBP2 are prespecified contextual displays from that same family;
   they do not receive a smaller, favorable multiplicity correction.

The optional artifacts are a complete gene-level TSV, a complete patient-panel
TSV and an SVG figure. Their hashes are retained even when no output directory
is supplied. Model-facing evidence contains bounded top-gene summaries rather
than the entire 20,848-row result table. Existing different output files are not
overwritten, and output directories cannot overlap the input directory.

## Local real-input verification, 2026-09-20

A source-preserving copy of only the eight permitted inputs was analyzed locally.
This is deterministic computational verification, not a new model-led run,
independent cohort replication, raw preprocessing or laboratory experiment.

QC verified 49 pairs, 98 arrays and 54,675 probes. Of the probes, 42,904 have a
qualified single-symbol mapping; 2,214 multi-symbol and 9,557 missing mappings
were excluded, yielding 20,848 analyzed genes. Both fixed panels cover 12/12 genes.

| Fixed curator panel | Median paired score (log2) | Positive patients | Bootstrap 95% CI | Two-panel BH q | Operational support |
|---|---:|---:|---:|---:|---|
| Cell cycle |0.367548|34/49|0.089651 to 0.635518|0.001898|Yes|
| DNA repair |0.181595|32/49|0.023662 to 0.282578|0.024943|Yes|

Mean-probe aggregation also passes both panel criteria. This supports the
curator's paired-expression hypothesis within this cohort; functional dependencies
remain proposals for experiments.

| Contextual gene | Median relapse−diagnosis (log2) | Genome-wide BH q |
|---|---:|---:|
| CD19 |−0.032164|0.855896|
| PTBP1 |0.007299|0.990902|
| PTBP2 |−0.038596|0.551011|

The contextual expression results do not show clear cohort-wide changes under
these tests. They do **not** rule out altered CD19 splicing, patient-specific
mechanisms, target accessibility changes or CAR-T failure in another cohort.

Complete local outputs are in
`../outputs/gse28460-integration-20260920/analysis/` relative to the app root.
That directory is a development verification artifact, not a replacement for
acceptance of the newly executed result in the new live investigation.
