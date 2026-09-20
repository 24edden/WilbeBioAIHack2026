# Brev runbook

The isolated demo directory is `/home/ubuntu/rosalind-hackathon-demo` on the existing `agentic-takeoff-cpu` instance. It uses `/home/ubuntu/.local/bin/python3.12` through a new `.venv`. No GPU or new machine is provisioned. Source datasets and the team workspaces are not modified.

## Private launch

```sh
cd /home/ubuntu/rosalind-hackathon-demo
.venv/bin/python -m app doctor
.venv/bin/python scripts/brev_service.py start
```

The service binds to `127.0.0.1:8080`. From the Mac:

```sh
brev port-forward agentic-takeoff-cpu -p 8081:8080
```

If that command exits without retaining a listener, the existing Brev SSH configuration also supports a persistent private tunnel:

```sh
ssh -o RequestTTY=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -fN -L 127.0.0.1:8081:127.0.0.1:8080 agentic-takeoff-cpu
```

Open http://127.0.0.1:8081. Local development can remain at port 8080. The tunnel must remain running during use; remote localhost is not the browser's localhost.

### Reconnecting local tunnel

For a demo session, the source includes a standard-library Mac/Linux helper that keeps the private SSH tunnel running after the terminal closes and reconnects if SSH drops. Run it **on the Mac, from this source directory**, after the existing SSH alias authenticates successfully:

```sh
python3 scripts/local_tunnel.py start
python3 scripts/local_tunnel.py status
python3 scripts/local_tunnel.py stop
```

It forwards only `127.0.0.1:8081` to Brev's `127.0.0.1:8080`, uses the existing `agentic-takeoff-cpu` SSH configuration, and never starts scientific work. Private state and logs live under ignored `runtime/local-tunnel/`. It does not read or copy API keys. `forwarding` means a local listener exists; confirm the remote application separately at `http://127.0.0.1:8081/api/health`.

The helper refuses to replace an existing listener. Stop an earlier manually launched tunnel using its original owner before transitioning; do not kill an arbitrary process on port 8081. A kernel lock prevents duplicate managed supervisors, and `stop` sends a generation-specific shutdown request. It never signals a PID loaded from a state file. Reconnect attempts back off to 30 seconds; authentication is noninteractive, so expired Brev/SSH access must first be renewed normally. This helper does **not** install an OS startup service or recover automatically after a Mac reboot: run `start` again after reboot. It also cannot restart a stopped remote app.

The remote service launcher writes a PID and log under `runtime/`, survives the SSH command ending, and supports `status` and `stop`. It is a hackathon process launcher, not a boot-time supervisor. Use the container services below or a reviewed system service for automatic machine-reboot recovery.

Configure credentials in `/home/ubuntu/rosalind-hackathon-demo/.env` (0600). Stop and restart after editing. `TEAM_TBD_MODEL=gpt-6-astra` selects the user-authorized high-reasoning placeholder; select `gpt-rosalind-research` only with the corresponding API access. Check the selected model through the UI or `python -m app doctor --live-model`. A normal doctor or health poll performs no inference. Do not put credentials in command arguments or copy them into the source archive.

`TEAM_TBD_DATA_ROOT=/home/ubuntu/rosalind-shared-files` maps the registered CAR-T datasets. `TEAM_TBD_LEON_ROOT` and `TEAM_TBD_HYPOTHESIS_ROOT` can override the prepared BCMA and hypothesis roots. The catalog resolves only registered paths and verifies selected file content before analysis; raw datasets remain read-only. See [the data adapters and limits](DATA_CATALOG.md).

## Reproduce from source

Extract the source release to a new directory, then:

```sh
/home/ubuntu/.local/bin/uv venv --python /home/ubuntu/.local/bin/python3.12 .venv
/home/ubuntu/.local/bin/uv pip install --python .venv/bin/python -r requirements.lock.txt
cp .env.example .env
chmod 600 .env
.venv/bin/python -m pytest -q
.venv/bin/python -m app doctor
```

Never overwrite an existing configured `.env`. The supplied lock was resolved in September 2026. If rebuilding at another date/platform, use the lock and retain installation output; do not silently substitute package versions.

## Optional containers

```sh
mkdir -p runtime
# On Linux, make the bind-mounted runtime writable to the image's scientist UID.
sudo chown 1000:1000 runtime
docker compose -f deploy/compose.cpu.yaml up -d --build
```

This starts separate API and worker containers, keeps the published port on loopback and mounts only runtime state. Case packs ship read-only inside the image. The Docker profile is provided as a reproducible option; the validated Brev deployment uses the isolated Python environment. Check the exact base-image tag/digest before a production deployment.

## Recovery

Stop the service cleanly before updating source; do not run a second server on the same port. Restart with the same runtime directory. Interrupted deterministic work pauses and can be resumed from the UI. An unresolved vendor submission is marked unknown, not automatically repeated. Preserve vendor request IDs and saved job records; there is no automated 202 job reconciler in this release.

Use `python -m app backup runtime/backups/<unique-name>.sqlite` and copy the artifact directory with that backup. Restore into a new runtime directory with `ROSALIND_RUNTIME` and run doctor. Do not copy a live SQLite database without its WAL consistency.

Resource targets: one active investigation, roughly 1–2 GiB application allowance and small pinned case packs. Hosted inference runs at the vendors. Do not start a local NIM on the CPU instance; a separate GPU deployment would need its own model-specific resource and entitlement checks.
