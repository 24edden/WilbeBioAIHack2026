> Historical prototype documentation. The code, runtime, datasets and generated outputs described below are outside this Markdown collection.

# AssayGuard

A small molecular benchmark audit for London AI × Bio, September 18–20, 2026.

**Status:** measured CPU baseline complete. Optional OpenAI API agent and NVIDIA nvMolKit parity adapter are implemented but not live-tested. No Rosalind access, GPU result, speedup, clinical benefit, or prospective validation is claimed.

## Run the working demo

From this directory on the prepared Mac:

```sh
.venv/bin/python audit.py
.venv/bin/python report.py
open results/report.html
```

The saved report works offline without starting a server. To run on a new machine:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
curl -fL --retry 3 https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/bace.csv -o bace.csv
.venv/bin/python -m unittest -v
.venv/bin/python audit.py
.venv/bin/python report.py
```

The locked environment was tested on Python 3.13.1 / macOS arm64. GPU installations should use their own compatible environment; do not force the Mac lock over nvMolKit's RDKit requirement.

## The actual result

1,513 usable unique molecules; 671 Bemis–Murcko scaffolds; no invalid molecules, exact duplicates, or conflicting exact-molecule labels in the downloaded file. Five molecules have an empty ring scaffold and are grouped together.

| Metric (mean ± sample SD across five seeds) | Random | Scaffold |
|---|---:|---:|
| ROC-AUC | 0.897 ± 0.017 | 0.886 ± 0.036 |
| Average precision | 0.867 ± 0.024 | 0.855 ± 0.058 |
| Fraction of test molecules sharing training scaffold | 0.661 ± 0.027 | 0 |

These are correlated repeated splits, not independent experiments. The difference is descriptive, not a significance claim. Scaffold group holdouts have varying molecule counts and class proportions. This is not the published MoleculeNet split or leaderboard result.

## Live agent at the event

Provide `OPENAI_API_KEY` and `OPENAI_MODEL` through the event's approved credential mechanism. Use the exact model ID granted to the team; the runner does not invent a GPT-Rosalind model ID. A Codex login alone does not prove API access. Do not paste keys into a committed file.

```sh
.venv/bin/python agent.py
```

The agent can inspect the dataset and invoke the fixed audit. Maximum six API requests; fixed seeds; no arbitrary shell execution. It writes an evidence trace and a review under `agent-results/`. The output remains model-generated and needs human checking against the metrics. With `ASSAYGUARD_ENABLE_GPU=1`, it can invoke the NVIDIA parity check after GPU dependencies are installed.

## NVIDIA integration

`gpu_check.py` follows NVIDIA's documented nvMolKit fingerprint/similarity interface. It requires a real NVIDIA CUDA GPU, compatible PyTorch, and nvMolKit. After the smoke test described in `../SETUP.md`, run:

```sh
python gpu_check.py
```

It checks full-matrix Tanimoto parity against RDKit, rejects disagreement above 1e-6, and measures three synchronized CPU/GPU runs after warmup. Fingerprinting, similarity, and host transfer are included; molecule parsing is excluded. A small dataset may favor CPU. The parity path is currently separate from the classifier audit; integrating cached GPU nearest-neighbor results into the audit is a planned weekend task.

## Reproducibility artifacts

- `results/metrics.json`: data hash, versions, all runs, metrics, methods, limitations.
- `results/splits.json`: train/test membership by original row.
- `results/predictions.csv`: every held-out prediction and nearest-training similarity.
- `results/benchmark.png` and `.svg`: measured results, not mock data.
- `test_audit.py`: split disjointness, determinism, conflicting duplicates, invalid inputs, known similarity, tool restrictions.

## Scope and provenance

Dataset: [DeepChem BACE loader](https://raw.githubusercontent.com/deepchem/deepchem/master/deepchem/molnet/load_function/bace_datasets.py). Background: [MoleculeNet](https://pubs.rsc.org/en/content/articlehtml/2018/sc/c7sc02664a). GPU API: [NVIDIA nvMolKit](https://github.com/NVIDIA-BioNeMo/nvMolKit). Agent interface: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).

Only SMILES-derived fingerprints are used. Canonical isomeric SMILES deduplicate exact molecules; this does not harmonize salts, tautomers, or stereoisomer families. BACE assay classification does not establish clinical benefit or toxicity. The data download is excluded from the repository bundle; retrieve it from the original source. Review upstream dataset terms before redistribution.

## Weekend completion criteria

One real, logged OpenAI tool-calling run; one real NVIDIA GPU parity/timing result; an independent assay or meaningful negative control; final human-reviewed claims; one reproducible repository; a five-minute demo. Do not present the prepared integrations as completed work until validated.
