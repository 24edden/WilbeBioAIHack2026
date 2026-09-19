> Historical prototype documentation. The code, runtime, datasets and generated outputs described below are outside this Markdown collection.

# Rosalind BioNeMo integration

Minimum viable, hypothesis-routed BioNeMo integration, built from the supplied **Rosalind Translational Scientist Hackathon Architecture**. It runs a bounded investigation over supplied paired observations and keeps every tool attempt and result in an evidence ledger. This is a deterministic orchestration scaffold that an agent can call, not a complete autonomous scientist.

**Verification status:** offline only, as requested. Synthetic fixtures and HTTP contract tests pass; no NVIDIA inference was performed and no GPU was deployed. Synthetic output must not be presented as a model prediction or biological discovery.

## What is implemented

| Tool | Required question kind | Behavior |
| --- | --- | --- |
| `paired_observations` | `paired_evidence` | Summarizes supplied normalized RNA and variant read counts; checks coverage and batch confounding |
| `evo2_generate` | `connection_check` | Documented hosted/local generation request; validates DNA, probabilities and timings; saves FASTA |
| `evo2_score_snv` | `variant_sequence_plausibility` | Local forward-pass logits, one SNV, explicit reference check and 1-based coordinate; saves NPZ and score |
| `boltz2_compare_complex` | `interface_structure` | Two matched WT/mutant target–binder predictions; requires mapped sequences and interface rationale; saves both CIFs |

Every call requires a hypothesis ID/statement → explicit question → rationale → matching tool, plus dataset version, patient, samples and timepoints. Input/output JSON schemas are exposed by `catalog`; mismatched routing and invalid inputs fail before model execution. The three competing hypotheses are acquired escape, transcriptional loss, and technical/passenger explanation.

The golden path is paired evidence → eligible acquired SNV → Evo 2 → optional interface-gated Boltz-2 → deterministic challenge checklist → unresolved decision and next experiment. Evo score sign does not determine whether Boltz runs. Structure confidence is never used as binding affinity. Failures remain visible and do not turn into supporting evidence.

## Setup and offline demo

From this `rosalind` directory, using Python 3.10 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v

python -m rosalind catalog --offline --output runs/catalog
python -m rosalind smoke --offline --output runs/smoke
python -m rosalind investigate --offline --with-boltz \
  --fixture fixtures/acquired.json --output runs/acquired
python -m rosalind investigate --offline --with-boltz \
  --fixture fixtures/null.json --output runs/null
python -m rosalind investigate --offline --with-boltz \
  --fixture fixtures/confounded.json --output runs/confounded
python -m rosalind investigate --offline --with-boltz \
  --fixture fixtures/contradictory.json --output runs/contradictory
```

The lock records the tested Python 3.13/macOS environment. `pyproject.toml` gives compatible version ranges if another platform cannot resolve that lock. A project-local environment was created during implementation. No global packages or agent plugins were changed.

The CLI prints paths to the decision/result and ledger. Each invocation gets a unique run ID; repeated invocations append rather than overwrite evidence. Exit code 2 means an error or one or more failed tools, including unsupported hosted scoring. The loopback HTTP test binds only to `127.0.0.1`; a sandbox may require permission for that local socket.

Fixtures are fabricated plumbing/routing demonstrations, not patient data, published CD20 sequences, a blinded benchmark, or evidence of scientific accuracy. The acquired fixture uses a deliberately short toy coding sequence with a consistent GAA→AAA/E2K substitution and an unrelated toy binder. Replace these inputs before biological use. The null/technical gates demonstrate restraint, but this scaffold is not a measured false-discovery-control system.

## Live Evo 2 connection test

The hosted call needs an NVIDIA API key with access to the requested NIM. Configure it in your shell or secret manager; do not put the key in code or commit it. `NGC_API_KEY` takes precedence over the accepted `NVIDIA_API_KEY` fallback.

```sh
source .venv/bin/activate
export NIM_API_MODE=hosted
# Configure NGC_API_KEY securely in this shell before running the next command.
python -m rosalind smoke --output runs/live-evo2-smoke
```

This sends an eight-base generation request to `https://health.api.nvidia.com/v1/biology/arc/evo2-40b/generate`, with Bearer authentication. A successful generation smoke test verifies connectivity and response mechanics only. It is not variant scoring.

`.env.example` lists configuration; the CLI does not automatically load `.env`. If you choose a local `.env`, copy the example, enter credentials locally, keep it ignored, and explicitly load it into your shell.

## Local scoring and optional Boltz-2

For the complete implemented sequence-scoring path, use an already running Evo 2 NIM reachable from this computer. For structure prediction also provide a Boltz-2 NIM. Local means self-hosted; it can be on a remote GPU host. The adapters send no Authorization header to local inference. They never fall back to hosted services.

```sh
export NIM_API_MODE=local
export EVO2_NIM_URL=http://YOUR_EVO2_HOST:8000
export BOLTZ2_NIM_URL=http://YOUR_BOLTZ_HOST:8001
export EVO2_MODEL_VERSION=YOUR_ACTUAL_IMAGE_DIGEST_AND_MODEL_VARIANT
export BOLTZ2_MODEL_VERSION=YOUR_ACTUAL_IMAGE_DIGEST
export NIM_TIMEOUT_SECONDS=300

curl --fail "$EVO2_NIM_URL/v1/health/ready"
curl --fail "$BOLTZ2_NIM_URL/v1/health/ready"
python -m rosalind smoke --output runs/local-evo2-smoke
python -m rosalind investigate --fixture YOUR_INPUT.json \
  --with-boltz --output runs/live-investigation
```

Remove `--with-boltz` to run the Evo-only golden path. Base URLs must be origins without an endpoint path, query or embedded credentials. If `NIM_API_MODE` is unset, an explicit local URL selects local mode; otherwise hosted mode is the default. Both services use the selected mode. Local default ports are deliberately different (Evo 8000, Boltz 8001); map the containers accordingly.

For deployment, use the pinned vendor Evo 2 skill (`vendor/bionemo/evo2-nim/SKILL.md`, outside this Markdown collection) and Boltz-2 skill (`vendor/bionemo/boltz2-nim/SKILL.md`, outside this Markdown collection), including their credential/cache preflight. The current documented images are `nvcr.io/nim/arc/evo2:2` and `nvcr.io/nim/mit/boltz2:1.6.0`. Supported local startup requires `NGC_API_KEY` (or the documented `NVIDIA_API_KEY` fallback), an explicitly selected `LOCAL_NIM_CACHE`, Docker with NVIDIA runtime, registry/model entitlement and sufficient hardware/storage. Evo 40B is documented on 2× H100 80 GB or 1× H200 141 GB; Evo 7B has smaller FP8-capable options. A100 is not a supported Evo FP8 shortcut. No local model can execute on this Mac without a reachable GPU service. No Parabricks dependency was added.

## Scientific interpretation and API boundaries

Evo scoring uses the sequence strictly **before** the supplied variant, requests `output_layer` from `/biology/arc/evo2/forward`, validates `[prefix_length, 1, 512]`, and reads the final position's ASCII-indexed A/C/G/T logits. It returns:

`log P(alt | prefix) − log P(ref | prefix) = logit_alt − logit_ref`

This is an exploratory one-strand, single-site conditional score, not full-window likelihood scoring, a standard clinical variant score, or a calibrated resistance predictor. No strand averaging, genomic coordinate lookup, indels, downstream context scoring or p-value is implemented. First-position variants are rejected because there is no prefix; reference mismatches and nonfinite/wrong-shaped tensors fail closed. Inputs are bounded to 4,096 bases for this MVP.

The pinned toolkit's Evo skill covers hosted **40B generation** and **local forward**. NVIDIA also now documents a [hosted 7B forward API](https://docs.api.nvidia.com/nim/reference/arc-evo2-7b-infer). That is a distinct service and is **not implemented or live-validated here**; the code does not guess a hosted 40B forward URL or silently change models. Consequently, this implementation's variant scoring requires a self-hosted Evo endpoint even though hosted 7B forward exists.

Boltz uses documented `polymers`, `recycling_steps`, `sampling_steps`, `diffusion_samples`, `step_scale` and `output_format` fields. It requests no ligand affinity for protein–protein complexes. Predicted structures need actual interface inspection and independent validation; global confidence changes alone do not demonstrate escape. The adapter accepts exactly one amino-acid substitution and requires caller-supplied mapping provenance. It does not independently validate a genomic-to-protein mapping against a reference database.

RNA fold change is descriptive over supplied normalized values, with a pseudocount of 1. Coverage ≥100 at both timepoints, zero baseline alternate reads, and progression VAF ≥0.1 are transparent **demo routing heuristics**, not statistically validated acquisition criteria. A variant below detection at baseline may already exist. The challenge pass is a checklist, not an independent red-team agent. Decisions deliberately remain unresolved pending orthogonal experiments.

## Evidence and agent integration

`evidence.jsonl` stores run IDs, timestamps, hypothesis/question routing, full parameters, source IDs, code hash, toolkit commit, endpoint/model identity, configured model version, elapsed time, status, failures, raw-output artifact references and hashes. Model version is `unknown` unless supplied: a hosted service name does not establish a weights revision. `artifacts/<analysis-id>/` holds requests, full responses, derived summaries, generated FASTA, forward NPZ and paired CIFs. Partial failures preserve already completed calls and artifacts. No Authorization headers are logged; configured keys are redacted if echoed by an error response. Raw-output hashes refer to stored bytes after any credential redaction.

There is one writer per ledger directory; use separate directories for concurrent processes. It is an append-only application convention, not a tamper-proof audit database. A `tool_started`/`http_started` without a terminal event indicates interruption. Data and parameters are stored in full, so put only authorized data into a run directory.

An existing orchestrator can use `Registry.catalog()` to expose the schemas, construct a `Question` for a current hypothesis, and call `Registry.call(name, question, parameters)`. `rosalind.__main__.build(output_directory)` wires the live adapters. For example:

```python
from rosalind.__main__ import build
from rosalind.core import Question

registry = build("runs/agent-investigation")
question = Question(
    hypothesis_id="H1", hypothesis_statement="An acquired coding SNV contributes to escape.",
    question="Is the alternate base less likely under this sequence context?",
    kind="variant_sequence_plausibility", rationale="Paired sequencing identified a candidate SNV.",
    source={"dataset_version":"v1", "patient_id":"P1",
            "sample_ids":["baseline", "progression"], "timepoints":["baseline", "progression"]})
result = registry.call("evo2_score_snv", question, {
    "reference_sequence":"ATGGAACTGCCAGTTGAC", "position_1based":4, "ref":"G", "alt":"A"})
```

Use actual evidence and sequences in place of this synthetic example. No OpenAI model/API credential is required by the deterministic scaffold; adding an LLM orchestrator is separate work. The BioNeMo Agent Toolkit is a skills catalog; this project integrates its verified HTTP contracts rather than inventing a toolkit Python SDK or confusing it with NeMo Agent Toolkit.

## Remaining blockers and explicit limits

- Live success is unverified by user choice. No credential or running endpoint was available in this task's environment.
- Hosted Evo generation and Boltz adapters are ready for credentialed smoke testing. Local Evo scoring additionally requires a running compatible GPU NIM.
- Real paired RNA/variant data, verified target/binder sequences, interface evidence and orthogonal assays must replace the synthetic fixtures before a scientific demo.
- HTTP 202 is recorded as pending and returns a failure/unknown state; asynchronous retrieval is not implemented. HTTP/auth/schema/network failures are logged with no hidden retries or endpoint fallback. Timeout retries must be deliberate to avoid duplicate paid work.
- This is not the full architecture: no real-data ingestion, statistical discovery benchmark, hidden evaluator, autonomous hypothesis generation, dashboard, automated structural comparison or Parabricks deployment.

See [implementation record](docs/IMPLEMENTATION.md) for file changes, verified source links and test results.
