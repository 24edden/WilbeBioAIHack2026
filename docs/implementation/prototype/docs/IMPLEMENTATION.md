# Implementation record

Implemented and verified on 19 September 2026.

## Starting point

The provided `/mnt/data/Rosalind_Translational_Scientist_Hackathon_Architecture.docx` path does not correspond to this Mac workspace. The original attachment was recovered through the referenced ChatGPT conversation (`6aae4f00-50e4-83ea-9628-f62b99b4bc34`) and its complete document text, including tool map and object contracts, was read. Its SHA-256 is recorded in `verification.json`.

The current project directory is not a Git checkout. It contains preparation material and an AssayGuard prototype but no existing Rosalind implementation. All implementation files were added under `rosalind/`. Existing preparation material and read-only `sources/` files were not changed. No branch, commit or PR was created.

## Added files and behavior

| File(s) | Change |
| --- | --- |
| `rosalind/core.py` | Question contract, explicit tool registry, JSON schema validation, append-only evidence events and hashed artifacts |
| `rosalind/nim.py` | Hosted/local mode selection; authenticated hosted generation; local SNV scoring; paired Boltz-2 complex prediction; complete HTTP attempt/response/error capture; output validation |
| `rosalind/workflow.py` | Three competing hypotheses; derived RNA/variant observation summary; sequence/interface routing gates; challenge checklist; unresolved decision with next experiment |
| `rosalind/offline.py` | Explicit synthetic transport using documented response shapes; no network calls, credentials or hidden live fallback |
| `rosalind/__main__.py` | `catalog`, `smoke` and `investigate` commands with offline mode and optional Boltz-2 |
| `rosalind/__init__.py` | Package and verified toolkit commit |
| `fixtures/*.json` | Acquired variant, null, batch-confounded and RNA/protein-contradictory synthetic demonstrations |
| `tests/test_integration.py` | Routing, score math, request/auth contracts, output validation, provenance, secret redaction, failures and partial results |
| `tests/test_http.py` | Real Python HTTP transport against a loopback-only fake NIM |
| `pyproject.toml`, `requirements-lock.txt`, `.env.example`, `.gitignore` | Installation, tested dependencies and configuration without credentials |
| `vendor/bionemo/` | Unmodified copies of the two NVIDIA skills and their references, with NVIDIA license/notice files |
| `docs/upstream-lock.json` | Upstream commit and SHA-256 of each retained vendor file |
| `README.md`, `docs/IMPLEMENTATION.md`, `docs/verification.json` | Setup, interpretation limits, file changes and observed verification results |
| `runs/` (ignored) | Executed offline smoke, four investigation demos, schema catalog, ledgers and artifacts |

The only local installed dependencies are in `.venv/`: NumPy for NPZ/logits, requests for HTTP, jsonschema for tool contracts, and their dependencies. No model weights were downloaded; no global toolkit installation was performed.

## API verification sources

The official toolkit was fetched from GitHub at commit **`0e67a612e4045f007e38fa77adc8f3ebfc5616b6`**. Retaining that snapshot avoids silently following a changed schema.

- [Official BioNeMo Agent Toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit)
- [Pinned Evo 2 skill](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit/blob/0e67a612e4045f007e38fa77adc8f3ebfc5616b6/nim-skills/evo2-nim/SKILL.md) and [API schema](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit/blob/0e67a612e4045f007e38fa77adc8f3ebfc5616b6/nim-skills/evo2-nim/references/api.md)
- [Pinned Boltz-2 skill](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit/blob/0e67a612e4045f007e38fa77adc8f3ebfc5616b6/nim-skills/boltz2-nim/SKILL.md) and [API schema](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit/blob/0e67a612e4045f007e38fa77adc8f3ebfc5616b6/nim-skills/boltz2-nim/references/api.md)
- [NVIDIA Evo 2 NIM endpoint reference](https://docs.nvidia.com/nim/bionemo/evo2/latest/endpoints.html): local paths, base64 NPZ, output tensor layout and nucleotide indices
- [NVIDIA hosted Evo 2 7B forward reference](https://docs.api.nvidia.com/nim/reference/arc-evo2-7b-infer): verified as a separate documented endpoint; deliberately outside this MVP adapter

The project consumes the toolkit's HTTP contracts. There is no invented `bionemo-agent-toolkit` Python client package, NeMo Agent Toolkit dependency, or guessed hosted forward endpoint.

## Observed verification

**20 tests passed, 0 failed.** The loopback HTTP test initially could not bind a socket in the filesystem/network sandbox; it passed when run with the local socket permission. The completed suite used no NVIDIA endpoints.

| Executed demo | Result |
| --- | --- |
| Evo 2 generation smoke | Eight valid synthetic bases, response and FASTA saved |
| Acquired SNV + Boltz | Paired observations, one synthetic Evo forward response, two synthetic Boltz responses; NPZ and WT/mutant CIFs saved; no discovery claim |
| Null | Paired observations only; zero model requests; unresolved |
| Batch confounder | Paired observations only; zero model requests; technical alternative preserved |
| Contradictory RNA/protein | Paired observations only; zero model requests; contradiction retained |
| Catalog | Four tools with serializable input/output schemas |

Saved request, response and summary hashes were checked against disk. Repeated calls retain distinct artifact directories. Failure tests covered missing credentials, wrong question/tool routing, missing provenance, invalid input, reference mismatch, wrong tensor shape, nonfinite model output, malformed JSON, 401/403/422/429/500, pending 202, redirects, timeouts and failure of the second Boltz prediction after the first succeeds.

## Live readiness and remaining work

The user explicitly selected offline completion and documented live setup. No live inference success is claimed. The environment exposed no NVIDIA key or NIM URL. To verify hosted generation, supply `NGC_API_KEY` or `NVIDIA_API_KEY` and run the README smoke command. To verify the full implemented path, supply reachable Evo/Boltz NIM origins and actual model versions, then use scientifically appropriate input sequences and evidence. An NVIDIA key needs entitlement to the selected hosted endpoint; key presence alone does not establish access.

The integration does not yet retrieve asynchronous 202 jobs, inspect structures geometrically, ingest public RNA-seq data, validate coordinate/transcript mappings, fit statistical models, or run a blinded false-discovery benchmark. Those are explicit boundaries rather than synthetic successes. Parabricks was omitted to keep the implementation on derived variants.
