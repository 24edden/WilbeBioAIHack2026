# Authoritative scientific backend setup

This directory contains the durable Team TBD scientific engine used by the new
frontend. Its `app/` modules, nine-role instructions, model defaults, budgets,
governance and immutable-history rules are preserved from the working scientific
service. The repository-root `app/` is an older, different backend. Run this
backend **from this directory in its own Python environment**; do not install the
two `app` packages into one environment or combine their test discovery.

The new frontend connects to this service's `/api/runs` API. The native browser
at the API root remains available for its complete specialist tools. This is a
private single-team service: bind to loopback and use the existing private tunnel.

## Install source dependencies

Requirements: Python 3.12 or newer; Node for the browser renderer/profile checks.
Use the exact dependency lock rather than replacing the Agents SDK or model.
From the repository root:

```sh
cd scientific_backend
TEAM_TBD_PYTHON=python3.13 ./scripts/setup.sh
```

The script creates an independent `.venv`, installs `requirements.lock.txt`, and
creates `.env` with mode 0600 only if it does not already exist. Set
`TEAM_TBD_PYTHON` to your installed Python 3.12+ executable. No provider check or
scientific run is submitted by setup.

## Install pinned scientific inputs privately

Git contains source, manifests, compact public evidence, source metadata and
authored case descriptions. Six larger scientific input/reference files are
intentionally absent: two GEO minigene tables, the ALK workbook, a prepared BCMA
variant table, the full source article and the author's per-isoform table.
They are listed with exact byte counts, hashes and available URLs in
[`casepacks/EXTERNAL-INPUTS.json`](casepacks/EXTERNAL-INPUTS.json). The unchanged
`casepacks/MANIFEST.json` remains authoritative for **all 25 source files**.
Large Ana/single-cell matrices are separate optional registered inputs and are
never bundled.

For an existing authorized backend installation or external source package:

```sh
.venv/bin/python scripts/install_case_sources.py --from-casepacks /absolute/path/to/existing/backend/casepacks
.venv/bin/python scripts/install_case_sources.py --check
.venv/bin/python casepacks/build_cases.py --check
```

The supplied directory must have the original `sources/...` layout. The installer
checks every required file before writing, copies only matching bytes into ignored
paths, and refuses to overwrite a changed existing source. It never rebuilds pins
to accommodate a changed download.

For a new installation, explicitly download and prepare all six public inputs:

```sh
.venv/bin/python scripts/install_case_sources.py --download-public
```

Downloads are explicit, size bounded, hash checked public data requests only.
Upstream changes or unavailable downloads fail with the original pin intact; use
the original verified source copy. The BCMA table is reproduced by selecting the
original 18 columns from the exact pinned public GEO MAF file, with the same 585
rows and final SHA-256 as the existing scientific service. The recipe and source
hash are included; no large matrix or private source handoff is needed for this
compact preparation. All four case choices share integrity checking
of this compact source set, so source hydration is required before starting any
new investigation. Existing served runs can still be browsed through the frontend
without installing a second backend locally.

## Configure providers and optional scientific capabilities

Set server credentials in this directory's private `.env` or the launching
environment. Never copy that file into Git, the frontend or an output archive.
`.env.example` documents every existing default. The configured scientific model
remains `TEAM_TBD_MODEL=gpt-6-astra`, high reasoning; a task's coding model does not
change this setting. Live starts require the engine's previously verified
capability receipt; a key being present is not verified access. Do not run
`doctor --live-model`, `doctor --live-nim`, or a capability probe merely to test
installation: those deliberately contact paid inference providers.

Optional AI sequence discovery requires an **authorized installed** OpenAI
Life Sciences Databases plugin, pinned at version 0.1.5. Its proprietary code is
not redistributed. Install it through the supported Codex plugin flow, then:

```sh
.venv/bin/python scripts/install_scientific_runtime.py /absolute/path/to/installed/life-sciences-databases/0.1.5
```

Alternatively set `TEAM_TBD_LIFE_SCIENCES_PLUGIN_ROOT` to that existing authorized
installation. Ten expected file hashes are preserved in
`skills/external-runtime-manifest.json`. Missing/changed runtime files fail closed.
Synthesis recovery also verifies the entire registered skill set, so it requires
this installation even when the saved run did not perform sequence discovery.
Ordinary investigation does not silently replace any unavailable method.
The installer only copies verified installed bytes into ignored private runtime.
For Brev, transfer those permitted files through your authorized private deployment
process, then run the same installer there; Git is not the distribution channel.

The included BioNeMo Boltz2 instruction subset is separately attributed under its
Apache-2.0 AND CC-BY-4.0 terms; see [NOTICE.md](NOTICE.md). NVIDIA credentials or an
explicit local NIM URL are still required for actual predictions. Installed skills
and mocked tests are never proof of inference.

Large registered datasets are optional external inputs. Set the existing
`TEAM_TBD_DATA_ROOT`, `TEAM_TBD_LEON_ROOT`, `TEAM_TBD_HYPOTHESIS_ROOT` and
`TEAM_TBD_GSE28460_ROOT` only to qualified source roots as described in
[DATA_CATALOG.md](docs/DATA_CATALOG.md) and
[GSE28460-PAIRED-DATA.md](docs/GSE28460-PAIRED-DATA.md). Keep those inputs read-only;
missing sources remain unavailable in the catalog. Source preparation and hashes
are part of their documented contracts, not arbitrary file-upload support.

## Start a separate local service

```sh
ROSALIND_RUNTIME=/absolute/path/to/new-private-runtime PORT=8083 ./scripts/start.sh
```

Choose a free port/runtime; never point an integration test at a production
database or start two workers over an existing deployment. The native service is
at `http://127.0.0.1:8083`; configure the frontend's `TEAM_TBD_BACKEND_URL` to that
origin for new investigations and their lifecycle. `TEAM_TBD_MAIN_URL` and
`TEAM_TBD_ANA_URL` separately configure saved-study browsing; add the Ana source
only when a genuinely separate Ana backend exists.
The frontend stores neither provider credentials nor runtime databases.

`python -m app doctor` and `GET /api/health` are local/read-only provider checks
and make no inference request. The doctor creates/checks its own SQLite state.
The optional containers use `deploy/compose.cpu.yaml`; hydrate sources privately
before building, retain `.env` and runtime outside the image, and review external
data mounts for the capabilities you intend to enable. The existing production
service is not migrated or restarted by any setup script. See
[BREV.md](docs/BREV.md) for private deployment/backup practice.

## Verify without scientific inference

```sh
.venv/bin/python scripts/check.py
.venv/bin/python casepacks/build_cases.py --check
```

`check.py` uses a new temporary runtime, ignores private `.env`, clears provider
credentials and blocks Python network connections. All vendor transports in the
scientific tests are mocked. It also verifies the nine-agent public profiles
against the actual packaged engine source. With the optional proprietary runtime
available, all registered skill bytes and synthesis-checkpoint eligibility are
verified. The full suite stops with an installation prerequisite if that runtime
is absent. For an explicitly limited public checkout check, use
`.venv/bin/python scripts/check.py --public-only`; this excludes the full-registry
installation check and the three synthesis-checkpoint suites that validate the
proprietary instructions. All public instruction hashes remain tested, and
sequence-client contracts still use fake subprocesses. This subset is not the
complete scientific release gate.
No model probe, sequence search, NVIDIA prediction or production mutation is part
of these commands.

Use the archived source validation documents as historical receipts only. Current
packaging checks are recorded in [RELEASE-VALIDATION.md](RELEASE-VALIDATION.md).

## Make a source archive

```sh
.venv/bin/python scripts/package_source.py /absolute/path/outside-checkout/team-tbd-source.zip
```

The reviewed `PUBLIC-SOURCE-FILES.json` allowlist controls the archive. Even after
local hydration it excludes the six external files, private runtime/plugin code,
credentials, databases and traces. Update that list deliberately when adding public
source files. Historical run databases, the frozen results capsule and live
capability receipts stay external; this checkout contains no copied live run.
