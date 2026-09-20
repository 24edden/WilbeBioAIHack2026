# Start here: paired leukaemia relapse benchmark

Git branch: `hypothesis-dataset`.

Hypothesis: **Leukaemia cells at relapse show reproducible gene-expression changes
relative to diagnosis that nominate resistance-associated biological processes and
interventions for experimental testing.**

Shared Brev instance: `agentic-takeoff-cpu`.

| What | Absolute instance path |
|---|---|
| Hypothesis | `/home/ubuntu/ana-workspace/hypothesis/hypothesis.txt` |
| Agent task | `/home/ubuntu/ana-workspace/datasets/agent_access/paired_all_relapse/TASK.md` |
| Discovery: 49 paired B-ALL patients | `/home/ubuntu/ana-workspace/datasets/agent_access/paired_all_relapse/discovery_B_ALL/` |
| Validation: 27 paired B-ALL patients | `/home/ubuntu/ana-workspace/datasets/agent_access/paired_all_relapse/validation_B_ALL/` |
| Separate optional 14 T-ALL pairs | `/home/ubuntu/ana-workspace/datasets/agent_access/paired_all_relapse/optional_T_ALL/` |
| Data/provenance guide | `/home/ubuntu/ana-workspace/geo_relapse_benchmark/README.md` |
| Original GEO downloads | `/home/ubuntu/ana-workspace/geo_relapse_benchmark/source/` |
| Evaluator rubric and checks | `/home/ubuntu/ana-workspace/geo_relapse_benchmark/evaluator/` |

Each group contains a gzipped TSV expression matrix, sample metadata and explicit
patient pairs. Read with pandas, R or ordinary gzip/TSV tools. No GPU or SRA Toolkit
is needed. The main B-ALL comparison contains 76 paired patients across two studies.

These cohorts are not CAR-T cohorts. All patients eventually relapsed. The supplied
measurements support expression associations and experimental prioritisation,
not proof of resistance causality or an effective new treatment.

For agent testing, start from `TASK.md`; restrict the agent to its input and output
directories. Withhold validation files until discovery candidates are frozen.
Do not expose evaluator files or the prior CD19 analysis. The older remote
`input/` directory is a legacy CD19/SRA package and is not the active input.

From the instance, a minimal loading check is:

```python
import pandas as pd
base = '/home/ubuntu/ana-workspace/datasets/agent_access/paired_all_relapse/discovery_B_ALL/'
x = pd.read_csv(base + 'expression_log2.tsv.gz', sep='\t', index_col=0)
pairs = pd.read_csv(base + 'patient_pairs.csv')
print(x.shape, len(pairs))  # (54675, 98), 49
```

For the full integrity check, Python standard library is sufficient:

```bash
python3 /home/ubuntu/ana-workspace/geo_relapse_benchmark/verify_delivery.py /home/ubuntu/ana-workspace
```
