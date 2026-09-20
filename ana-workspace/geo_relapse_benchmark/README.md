# One-cohort GEO leukaemia benchmark

The sole active patient dataset is **GSE28460: 49 paired B-ALL patients, 98 samples,
54,675 expression probes**. GSE18497, its T-ALL subset, and the old CD19/SRA input
copies were removed from the working dataset package. GPL570 annotation is required
metadata for GSE28460, not a second patient dataset.

Start locally at `ana-workspace/hypothesis.txt` and `ana-workspace/input/TASK.md`.
On Brev, use `/home/ubuntu/ana-workspace/hypothesis.txt` and
`/home/ubuntu/ana-workspace/input/`. The input directory is an alias of
`datasets/agent_access/GSE28460/`; it does not duplicate the expression data.

## Hypothesis and test scope

The hypothesis is that cell-cycle and DNA-repair expression increase at relapse
relative to the same patients' diagnosis samples. `hypothesis_gene_sets.json`
contains fixed author-defined panels, not exhaustive or validated pathway signatures.
The agent task specifies scoring and falsifiable decision rules. The hypothesis is
motivated by existing biology and is not an independently preregistered discovery.
No hypothesis result or agent evaluation has been computed by this preparation.

The cohort concerns conventional-treatment relapse, not CAR-T. All patients relapsed;
there are no cured controls. One 49-patient cohort is a moderate, usable exploratory
benchmark, not a large clinical validation study. Removing the second cohort removes
independent replication: resampling within this cohort cannot replace it.

## Opening and reproducing

From the repository root:

```python
import pandas as pd
x = pd.read_csv('ana-workspace/input/expression_log2.tsv.gz', sep='\t', index_col=0)
pairs = pd.read_csv('ana-workspace/input/patient_pairs.csv')
assert x.shape == (54675, 98)
assert len(pairs) == 49
```

Source files are included in `source/`. Exact URLs and SHA-256 checksums are in
`download_manifest.csv`. Rebuild using Python 3.11+ with the pinned numpy/pandas
versions in `requirements.txt`:

```bash
python3 ana-workspace/geo_relapse_benchmark/prepare_inputs.py
```

`download.sh` reacquires only GSE28460 and its GPL570 annotation if needed. It
requires network access and overwrites the source files. Compare checksums against
the recorded snapshot before rebuilding. Source matrices are normalized signals,
not raw CEL files. Prepared values are explicitly log2 of the deposited positive
signals (original range 15.11902536–42313.94755), with no imputation or renormalization.
Raw CEL reprocessing may be appropriate for a definitive biological study.

## Checks and caveats

All 49 pairs are complete, sample IDs are unique, all 54,675 probes match the
platform table, all values are finite, and every exported value passed read-back
comparison. `evaluator/validation_report.json` documents ingestion, not biological
validation. The arithmetic reference is an ingestion sanity check, not an answer key.

GEO labels 29 pairs early and 20 late; the paper reports 27/22 for expression
profiling. This remains unresolved; the primary test uses all pairs. In particular,
p51 and p54 have different diagnosis/relapse column positions: pair by ID.

The 2016-08-09 platform annotation has 42,904 single-symbol, 2,214 multi-symbol and
9,557 symbol-missing probes. Multiple probes can map to one gene. Purification,
cell composition, subtype and treatment history are potential confounders. RNA
alone does not establish mechanism, protein activation, surface accessibility or
benefit from an intervention. Restrict agents to `input/` and their output, keeping
source publication metadata and evaluator material outside the allowed scope.

## Sources

- [GSE28460](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE28460)
- [Hogan et al., Blood 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3217405/),
  DOI 10.1182/blood-2011-04-345595; PMID 21921043.
- [GPL570 annotation](https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz)

Historical analysis results and project code are outside the input directory.
Deleted tracked datasets remain recoverable from Git history; history was not rewritten.
