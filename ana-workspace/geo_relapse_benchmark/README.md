# GEO paired leukaemia relapse benchmark

Downloaded and opened on 2026-09-20. The active hypothesis is:

> Leukaemia cells at relapse show reproducible gene-expression changes relative to
> diagnosis that nominate resistance-associated biological processes and interventions
> for experimental testing.

This package supports agent tests of ingestion, paired statistics, replication and
experimental reasoning. Preparation has not established a biological mechanism or
measured agent performance.

## Verified cohorts

| Role | GEO source | Patients | Samples |
|---|---|---:|---:|
| Discovery | GSE28460 | 49 B-ALL | 98 |
| Validation | GSE18497, B-ALL subset | 27 B-ALL | 54 |
| Separate optional comparison | GSE18497, T-ALL subset | 14 T-ALL | 28 |

The primary benchmark has **76 paired B-ALL patients (152 samples)** across two
studies. The full download has 90 paired ALL patients (180 samples). Study-local
identifiers do not independently prove cross-study donor non-overlap. Keep estimates
and processing study-specific. All matrices use GPL570 expression microarrays.

Both source matrices contain 54,675 probes and no missing/non-finite values. Every
patient has one diagnosis and one relapse sample. Numerical read-back of every
exported matrix passed. This is enough for an exploratory computational benchmark;
no prospective power calculation or clinical validation has been performed.

## Open the data

Agent input directory: `ana-workspace/datasets/agent_access/paired_all_relapse/`.
Run this example from the repository root:

```python
from pathlib import Path
import pandas as pd

base = Path("ana-workspace/datasets/agent_access/paired_all_relapse")
group = base / "discovery_B_ALL"
expression = pd.read_csv(group / "expression_log2.tsv.gz", sep="\t", index_col=0)
samples = pd.read_csv(group / "samples.csv")
pairs = pd.read_csv(group / "patient_pairs.csv", index_col=0)
annotation = pd.read_csv(base / "probe_annotation.tsv", sep="\t")
assert expression.shape == (54675, 98)
assert len(pairs) == 49
patient = pairs.index[0]
delta = expression[pairs.loc[patient, "relapse"]] - expression[pairs.loc[patient, "diagnosis"]]
```

Matrices are gzipped tab-separated text, not R-only objects or SRA archives. CSV
manifests and ten-probe previews can be opened directly in a spreadsheet editor.
No account or controlled-access application is required. Raw Affymetrix CEL
archives were not downloaded; original GEO processed matrices were downloaded.

## Processing and evidence limits

- GEO describes the expression as normalized/RMA-derived signal. The actual
  deposited ranges are 15.119–42,313.948 (GSE28460) and 6.63–26,803.99 (GSE18497).
  We supply **log2 of the deposited positive signal**, without a pseudocount,
  additional normalization or imputation. This explicit transformation does not
  reconstruct every original preprocessing step. Original files are preserved;
  consider CEL-based preprocessing for a definitive biological study.
- Patients are paired biological units; probes are not biological replicates.
  These are microarray signals, not RNA-seq read counts. Control multiple testing.
- The GEO GPL570 annotation is dated 2016-08-09: 42,904 single-symbol probes,
  2,214 multi-symbol probes, 9,557 without a symbol. Single-symbol does not mean
  unique gene or current sequence specificity. Document probe-to-gene handling.
- GSE28460 used Ficoll-enriched marrow. GSE18497 sample metadata specify CD19
  enrichment for B-ALL and CD7 enrichment for T-ALL. Purification, cell composition,
  subtype, treatment history and technical differences can affect comparisons.
- GSE28460 metadata label **29 early/20 late** patients; its primary paper reports
  **27 early/22 late** for expression profiling. This discrepancy is unresolved.
  Preserve deposited labels and omit timing subgroups from the primary benchmark.
  p51 and p54 occur in different diagnosis/relapse column positions: pair by ID.
- These are conventional-treatment relapse cohorts, not CAR-T cohorts. All
  included patients eventually relapsed. Diagnosis samples are not cured controls.
  The data cannot establish relapse risk versus cure, causal resistance mechanisms,
  mutations, splice isoforms, surface antigen targetability, or treatment efficacy.
  No patient-specific regimen or blast purity was invented where absent.

## Reproduce and evaluate

Unmodified GEO files are in `source/`. `download_manifest.csv` records exact URLs,
sizes and SHA-256 checksums. From the repository root:

```bash
python3 -m venv .venv-geo-relapse
.venv-geo-relapse/bin/python -m pip install -r ana-workspace/geo_relapse_benchmark/requirements.txt
# Already downloaded; run only to reacquire:
bash ana-workspace/geo_relapse_benchmark/download.sh
.venv-geo-relapse/bin/python ana-workspace/geo_relapse_benchmark/prepare_inputs.py
```

Python 3.11 or later is required. Preparation reads locally, exports the separate
groups, and verifies dimensions, pairing, annotations, positivity, finite values
and every written value. See `evaluator/validation_report.json` and the per-patient
arithmetic references. These are ingestion checks, not biological result labels.
GEO may update files; compare checksums before replacing a benchmark snapshot.

Provide agents with `TASK.md` and the specified inputs. Keep this README, `source/`,
`evaluator/`, archives and prior analyses outside their allowed files. For strict
holdout evaluation, expose validation only after candidates and decision rules
are frozen. This package does not implement an automated runner or access sandbox.
Public datasets may be in model training: evaluate executed calculations and
reasoning rather than claiming discovery on unseen biology.

## Primary sources

- [GSE28460](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE28460) and
  [Hogan et al., Blood 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3217405/),
  DOI 10.1182/blood-2011-04-345595, PMID 21921043.
- [GSE18497](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE18497) and
  [Staal et al., Leukemia 2010](https://pubmed.ncbi.nlm.nih.gov/20072147/),
  DOI 10.1038/leu.2009.286.
- [GPL570 annotation](https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz).

Previous tracked CD19 files are preserved at
`ana-workspace/archive/cd19_car_t_previous/`, outside the active inputs.
