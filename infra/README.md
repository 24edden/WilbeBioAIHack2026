# Single-host demo deployment

Deployment configuration for the Streamlit and FastAPI services. It uses an existing
host; it does not enable live models or make application state durable.
The service recommendation and presentation plan are in
[Plan/hosting-and-demo.md](../Plan/hosting-and-demo.md).

## Start and inspect

Requirements: Docker Engine with Compose 2.24 or newer, Linux containers, access to
the Python image/package registries, and a repository checkout. Run from the repo root:

```bash
docker compose -f infra/compose.yaml config --quiet
docker compose -f infra/compose.yaml up --build -d --wait --wait-timeout 120
docker compose -f infra/compose.yaml ps
docker compose -f infra/compose.yaml logs --tail 60 api ui
```

Open <http://127.0.0.1:8501>. To avoid colliding with the local development preview,
set `TRACE_UI_PORT=8502` in the shell before these commands. On PowerShell that is
`$env:TRACE_UI_PORT = '8502'`; on Linux use `export TRACE_UI_PORT=8502`.

The UI starts with an editable demo using simulated models; recorded playback is
also available. Choose **Investigate my data**, keep
the default `http://api:8000` server address, select the bundled sample and start an
investigation to exercise the connected mock backend. `api` resolves inside the
Compose network; requests originate from Streamlit's Python server.

One API process owns uploads, runs and streams. Do not add replicas or workers until
the stores are replaced. Restarting the API loses all its current files and runs.
No volume can fix that without changing the in-memory stores. The UI's temporary
session state is also lost on restart.

The image includes bundled `samples/`, `fixtures/` and frontend recordings. Only
keep public/synthetic demo data in those directories when building a distributable
image. The Dockerfile-specific ignore file excludes credentials and local uploads.
The 10 MB Streamlit setting limits each uploaded file, not total session memory or
the API's upload endpoint; use the trusted demo audience until backend limits exist.

## Brev access

The current app uses the existing `agentic-takeoff-cpu` instance in a separate
`/home/ubuntu/trace-service` directory and the `trace-demo` Compose project.
Teammates' existing workspaces and services are separate. In Windows PowerShell,
a presenter can forward the remote UI:

```powershell
wsl -d Ubuntu -- bash -lc 'brev port-forward agentic-takeoff-cpu --port 18501:8501'
# Direct SSH alternative using the same Brev-managed configuration:
wsl -d Ubuntu -- ssh -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -N -L 127.0.0.1:18501:127.0.0.1:8501 agentic-takeoff-cpu
```

Then open <http://localhost:18501>. Keep the forwarding process running. The alternate
local port avoids the development app on 8501. Windows-to-WSL forwarding was checked
on this machine; the direct SSH alternative stayed available during verification.

The authenticated link is <https://trace-z484f0h2c.gobrev.dev>. It requires NVIDIA
sign-in and currently authorizes only the deploying user's Brev account. It is not
an anonymous audience link. Keep FastAPI unpublished and Streamlit's XSRF protection
enabled. Another viewer needs an explicit access-policy update, not a shared login.

The base Compose file maps the UI to loopback. `compose.brev.yaml` adds a listener
on the host's specific private `wt0` mesh address so the Brev HTTPS gateway can reach
it, without binding the public network interface. `deploy_release.sh` discovers and
validates that address and saves it in `deployment.env`. Never replace it with
`0.0.0.0`. This follows the [NetBird listener guidance](https://docs.netbird.io/manage/reverse-proxy/troubleshooting).

The link was created with the installed CLI:

```bash
brev ports create agentic-takeoff-cpu 8501 --protocol http --hostname trace --json
```

Do not repeat that command on every release; the existing link continues routing
port 8501. `brev ports ls agentic-takeoff-cpu --json` shows its current policy.

## Packaging and updating the CPU deployment

```powershell
.venv/Scripts/python.exe infra/package_release.py
```

This packages a whitelist of source files and bundled synthetic samples from the
current working tree into `.deploy/`. It excludes local credentials, uploads, caches
and evaluation outputs, and prints the archive's SHA-256. Each release contains a
per-file checksum manifest, Git revision and dirty-tree flag, so uncommitted UI work
is included explicitly rather than lost in a remote clone.

Copy the printed archive into `/home/ubuntu/trace-service/incoming/` with `brev copy`
or Brev-configured `scp`, and copy `infra/deploy_release.sh` to the same directory.
Then run on the instance:

```bash
bash /home/ubuntu/trace-service/incoming/deploy_release.sh /home/ubuntu/trace-service/incoming/RELEASE.tar.gz ARCHIVE_SHA256
```

The script verifies the archive and all source hashes, builds the images, runs the
test suite in the Linux image, starts the stack, checks health, uploads three
synthetic files and verifies a complete connected mock
investigation. It records exact installed dependencies and image IDs, tags both images
with the release ID, and advances `/home/ubuntu/trace-service/current` only after the
checks pass. An existing release directory is never overwritten. Restarting the API
still loses its in-memory runs, so do updates between demonstrations.

Operational commands from the active release:

```bash
cd /home/ubuntu/trace-service/current
docker compose --env-file deployment.env -p trace-demo -f infra/compose.yaml -f infra/compose.brev.yaml ps
docker compose --env-file deployment.env -p trace-demo -f infra/compose.yaml -f infra/compose.brev.yaml logs --tail 60 api ui
docker compose --env-file deployment.env -p trace-demo -f infra/compose.yaml -f infra/compose.brev.yaml exec -T ui python infra/check_deployment.py
```

## Verified live models later

Create the root `.env` from `.env.example` locally on the host, then set the actual
provider endpoints, keys and model IDs. Only the API receives this file. Override
`TRACE_RUN_MODE=live` explicitly and recreate the API container after a successful
provider smoke test. Never print the resolved Compose configuration with secrets
loaded; use `config --quiet`.

`localhost` inside an API container means that container. The sample
`BIONEMO_BASE_URL=http://localhost:8000` is a placeholder, not a usable separate NIM
endpoint here. A later NIM service needs a real reachable URL and a matching adapter.
The current CPU instance is not a GPU inference deployment.

## Repeatability and validation status

The current requirements use lower bounds and the Python base uses a tag. After
the successful rehearsal, save exact dependency versions and the built image digest
with the commit ID. Reuse that image for the presentation rather than rebuilding.

Containers built and reached healthy status on the Brev CPU on 19 September 2026.
The HTTPS address reached NVIDIA authentication. The release deployment check also
tests the connected mock workflow; neither that nor HTTP readiness validates live
scientific models. See [the deployment record](DEPLOYMENT.md) for the final released
version and browser verification status.
