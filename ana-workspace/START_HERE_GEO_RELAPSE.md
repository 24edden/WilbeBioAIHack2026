# Start here: one leukaemia dataset

Branch: `hypothesis-dataset`. Instance: `agentic-takeoff-cpu`.

- Hypothesis: `/home/ubuntu/ana-workspace/hypothesis.txt`
- Agent input: `/home/ubuntu/ana-workspace/input/`
- Task instructions: `/home/ubuntu/ana-workspace/input/TASK.md`
- Provenance and preparation: `/home/ubuntu/ana-workspace/geo_relapse_benchmark/`

The local workspace has the same layout under `ana-workspace/`.

**GSE28460: 49 B-ALL patients, each sampled at diagnosis and relapse; 98 samples
and 54,675 expression probes.** One complete cohort; no T-ALL or other patient
cohorts are included. `input/` aliases `datasets/agent_access/GSE28460/`.

Read hypothesis.txt, then TASK.md. The agents can test whether cell-cycle and
DNA-repair gene expression rises at relapse within patients and propose experiments.
These are conventional-treatment cases, not CAR-T cases. Expression cannot by
itself establish causal resistance or effective treatment. No independent validation
cohort remains in this simplified package.

```python
import pandas as pd
root = '/home/ubuntu/ana-workspace/input/'
x = pd.read_csv(root + 'expression_log2.tsv.gz', sep='\t', index_col=0)
pairs = pd.read_csv(root + 'patient_pairs.csv')
print(x.shape, len(pairs))  # (54675, 98), 49
```

For an agent test, allow only input/ and its output directory. Source files,
evaluator material and historical analyses are not agent inputs.
