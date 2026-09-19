# Local and NVIDIA Brev runbook

This file distinguishes commands that work with the inspected prototype from the deployment interface engineers must implement. No new server, GPU, environment or paid inference was started during planning.

## Observed environment

| Location | Observation |
| --- | --- |
| Local project | `<LOCAL_AI_X_BIO_ROOT>` |
| Local architecture/prototype | `outputs/reference-architecture/`; `rosalind/` |
| Local CPU architecture | ARM64 Mac |
| Brev organization/instance | London-AI-Brev / `agentic-takeoff-cpu`, ID `z484f0h2c` |
| Brev machine | `n2d-highmem-4`; x86_64; 4 cores; 31 GiB reported memory |
| Brev storage | Root filesystem approximately 1.1 TB; 973 GB available at inspection |
| Brev runtime | Python 3.10.12; Docker installed; no running containers shown |
| GPU | Brev inventory shows none; `nvidia-smi` cannot contact a driver |
| Shared reference root | `/home/ubuntu/rosalind-shared-files` |
| Shared datasets | `/home/ubuntu/rosalind-shared-files/datasets/2026-09-19` |
| Team checkout inspected | `/home/ubuntu/ana-workspace/WilbeBioAIHack2026`, main at `ae2d11e` |
| Prepared BCMA case | `/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19` |
| BCMA environment | `/home/ubuntu/leon-workspace/.venvs/gse164551`; preserve it |

The inspected system Python does not contain `openai`, `openai-agents`, FastAPI, NumPy, pandas, Pydantic, h5py or SciPy. This does not describe every virtual environment on the machine. Rscript and uv were not found in the inspected PATH.

## Three supported deployment profiles

| Profile | Application/state | Data | Inference |
| --- | --- | --- | --- |
| local-dev | Local isolated Python environment | Small pinned copies/slices | GPT-Rosalind API; hosted NIM or explicit replay |
| brev-cpu | New isolated application/container on existing CPU instance | Read-only selected case inputs; state under a new runtime directory | GPT-Rosalind API + NVIDIA-hosted NIMs |
| brev-gpu | Same CPU control service | Same qualified case packets | One or more explicitly configured NIM services on a separate supported GPU host |

Recommended first deployment is **brev-cpu**. The browser stays local and connects through Brev's private port forward. CPU analyses stay close to the 63 GB source archive; only compact, policy-approved evidence enters model context.

## Existing commands verified or grounded in the installed CLI

Read-only inventory and connection:

```sh
brev ls
brev exec agentic-takeoff-cpu 'python3 --version'
brev shell agentic-takeoff-cpu
```

From the existing local `rosalind` directory:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m rosalind catalog --offline --output runs/catalog
.venv/bin/python -m rosalind investigate --offline --with-boltz \
  --fixture fixtures/acquired.json --output runs/acquired
```

The test command passed all 20 tests in this review. The demo outputs remain synthetic. Running those commands does not validate GPT-Rosalind or live NIM access.

## New application deployment contract

The following files/commands are **deliverables in W01/W10 of the backlog**, not available startup commands today:

```sh
# From the reviewed application release checkout, after W00-W10:
docker compose -f deploy/compose.cpu.yaml build
docker compose -f deploy/compose.cpu.yaml run --rm worker \
  python -m rosalind_harness doctor --config config/brev-cpu.yaml
docker compose -f deploy/compose.cpu.yaml up -d api worker
```

The doctor performs offline dependency, filesystem, schema and capability-record checks by default. `--live-model` and `--live-nim` are separate explicit probes with tiny inputs and configured budgets. A readiness endpoint must not spend money each time it is polled.

Repository promotion happens first: the current GitHub branch is documentation-only. Bring the reviewed prototype into the code repository, merge or otherwise agree a release commit, and pin that SHA in deployment. Do not clone the documentation branch and expect a runnable agent.

Suggested new directories on Brev:

```text
/home/ubuntu/rosalind-agent/                   reviewed source checkout
/home/ubuntu/rosalind-runtime/
  state/app.sqlite                           authoritative operational state
  state/sessions.sqlite                      SDK conversation state
  artifacts/                                 immutable result files
  logs/                                      structured redacted logs
  exports/                                   selected replay/demo bundles
  backups/                                   consistent DB/artifact backups
/home/ubuntu/rosalind-casepacks/               approved read-only input packets
```

These paths are proposals; create them without modifying Ana's or Leon's working directories. Selectively copy or bind approved input files. An investigator container must not mount the whole shared archive or BCMA `reference/` in a blinded evaluation.

## Container and resource specification

Build an application image from a pinned Python 3.11 base. Install a locked `openai-agents`/`openai` pair, Pydantic 2, FastAPI, Uvicorn, Jinja2, httpx, NumPy, pandas, PyArrow, openpyxl, SciPy and a chosen CIF parser. Add h5py/AnnData for the BCMA extension. Use a separate R preprocessing container only when the Maynard RDS needs it.

Default CPU deployment:

- API: one worker, 0.5 CPU target, 1 GiB memory; listen on container port 8080, publish only host `127.0.0.1:8080`.
- Application worker: one process; one active investigation; one heavy analysis subprocess, up to two CPU threads and 16 GiB for that subprocess.
- Keep total application usage below approximately 20 GiB initially so the 32 GB machine retains headroom.
- Sparse HDF5/AnnData operations must not densify a full feature-by-cell matrix. Stop or subset when the estimated working set exceeds the limit.
- Read-only source mounts; writable runtime mount; run as a non-root user with the runtime directory's matching UID/GID.
- Credentials belong only to the trusted model/NIM gateway. CPU analysis subprocesses inherit a minimal environment with no vendor keys.

The `deploy/compose.cpu.yaml` file must define both services and consistent volume paths. Verify runtime limits in the actual container engine rather than assuming a Compose field was enforced.

## Access from the local computer

The installed CLI supports:

```sh
brev port-forward agentic-takeoff-cpu -p 8080:8080
```

Then open the local browser at `http://127.0.0.1:8080`. Keep the tunnel alive during the demo. A remote worker does not use the local browser's localhost. [Brev connectivity](https://docs.nvidia.com/brev/cli/connectivity)

Use the same approach for a GPU NIM only if the forwarding process terminates on the machine that runs the calling worker. A port forwarded to the Mac is not automatically reachable from the Brev CPU instance. Prefer a private CPU-to-GPU connection, authenticated proxy, or a tunnel established on the CPU host with authorized access. Do not expose unauthenticated NIM ports publicly.

## Credentials and configuration

Configure `OPENAI_API_KEY` and the approved model ID on the trusted worker. For NVIDIA, support the existing `NGC_API_KEY` with `NVIDIA_API_KEY` fallback. Do not print values, commit them, or include them in exports.

The example [runtime configuration](contracts/runtime-config.example.yaml) names the proposed settings and budgets. Backend choices are per tool. Capability flags begin false and become enabled only after the corresponding probe is recorded. Disable hosted SDK trace export by default for data not approved for that destination; retain local event/usage records.

Keep original files under `sources/` and the team's source data read-only. Do not store run state in the shared dataset catalog. It is an input index, not our job database.

## Optional GPU profile

Do not provision a GPU merely to run the agent or CPU analyses. If hosted NIM cannot meet the requirement, select hardware against the **exact image version**.

| NIM | Verified/documented basis | Planning implication |
| --- | --- | --- |
| Boltz-2 1.6.0 | Minimum 12 CPU cores, 64 GB RAM, 80 GB storage, supported NVIDIA GPU with at least 48 GB VRAM; H100 80 GB and L40S 48 GB are listed | Existing 4-core/32 GB CPU machine is unsuitable; choose a separate instance and reserve extra cache/output space |
| Evo 2 40B 2.0.0 | Documented matrix: 2× H100 80 GB or 1× H200, 100 GB disk and 16 GB host RAM | Prefer hosted 7B if appropriate; do not book an A100 as an FP8 shortcut |
| Evo 2 7B self-hosted | Installed toolkit describes a smaller variant | Verify the selected image's current support matrix before provisioning; not required for the CPU-first release |

Sources: [Boltz-2 support matrix](https://docs.nvidia.com/nim/bionemo/boltz2/1.6.0/support-matrix.html), [Evo 2 support matrix](https://docs.nvidia.com/nim/bionemo/evo2/2.0.0/prerequisites.html).

The fetched Boltz 1.6.0 matrix also specifies driver/CUDA prerequisites; check them against the actual selected image and host before pulling weights. The inspected toolkit's approximately 30 GB weight-download note does not replace the support matrix's larger complete storage requirement.

Use the pinned BioNeMo startup instructions for registry entitlement, explicit `LOCAL_NIM_CACHE`, NVIDIA Container Toolkit, cache permissions, and readiness. Pin image digest/model variant. Start with one NIM at a time if sharing a GPU; free VRAM must be measured before co-residency. Record hourly price and a shutdown owner before launch.

## Backup, restart and handoff

Use SQLite's backup API or a quiesced consistent snapshot; do not copy only a live database file while ignoring WAL state. Back up the manifest and all referenced artifact hashes together. Verify a restore to a separate runtime directory.

Rebuildable model weights may use an ephemeral cache. Operational state and source data must not depend on `/ephemeral`. An instance-local directory is not an off-machine backup and may disappear when the instance is deleted.

At release, another engineer must start from the pinned commit and lock, run the replay suite, restore a paused run, inspect a missing/unknown external result, and confirm the browser displays the exact exported decision.
