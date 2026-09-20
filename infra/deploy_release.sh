#!/usr/bin/env bash
# Run on the Brev CPU: bash deploy_release.sh ARCHIVE EXPECTED_SHA256
set -euo pipefail

archive=$(realpath "${1:?Pass the release archive}")
expected=${2:?Pass its SHA-256}
release=$(basename "$archive" .tar.gz)
[[ "$release" =~ ^[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}$ ]] || { echo 'Invalid release name' >&2; exit 1; }
[[ "$expected" =~ ^[a-f0-9]{64}$ ]] || { echo 'Invalid checksum' >&2; exit 1; }
actual=$(sha256sum "$archive" | cut -d ' ' -f 1)
[[ "$actual" == "$expected" ]] || { echo 'Archive checksum does not match' >&2; exit 1; }

deploy_root=/home/ubuntu/trace-service
target="$deploy_root/releases/$release"
mkdir -p "$deploy_root/releases"
# A release is immutable; an existing directory must not be overwritten.
mkdir "$target"
tar -xzf "$archive" -C "$target"
cd "$target"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
manifest = json.loads(Path('release-manifest.json').read_text())
for name, expected in manifest['files'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
print('Verified source manifest:', manifest['release'])
PY

# Secure Links reach the host through its private NetBird interface. Keep the
# loopback mapping for SSH access and add only that specific private interface.
TRACE_BREV_IP=$(ip -j address show dev wt0 | python3 -c 'import json,sys; print(next(a["local"] for i in json.load(sys.stdin) for a in i["addr_info"] if a["family"] == "inet"))')
export TRACE_BREV_IP
python3 - <<'PY'
import ipaddress, os
assert ipaddress.ip_address(os.environ['TRACE_BREV_IP']) in ipaddress.ip_network('100.64.0.0/10'), 'Unexpected Brev mesh address'
PY
printf 'TRACE_BREV_IP=%s\n' "$TRACE_BREV_IP" > deployment.env
compose=(docker compose --env-file deployment.env -p trace-demo -f infra/compose.yaml -f infra/compose.brev.yaml)
"${compose[@]}" config --quiet
"${compose[@]}" build
docker run --rm --read-only --tmpfs /tmp \
    --mount "type=bind,source=$target/tests,target=/srv/trace/tests,readonly" \
    --mount "type=bind,source=$target/pyproject.toml,target=/srv/trace/pyproject.toml,readonly" \
    trace-demo-ui:latest python -m pytest -q -p no:cacheprovider --basetemp /tmp/trace-tests
"${compose[@]}" up -d --wait --wait-timeout 120
"${compose[@]}" exec -T ui python infra/check_deployment.py
curl --fail --silent --show-error "http://$TRACE_BREV_IP:8501/_stcore/health"
"${compose[@]}" exec -T api python -m pip freeze > deployed-requirements.txt
docker image inspect trace-demo-api:latest trace-demo-ui:latest \
    --format '{{.RepoTags}} {{.Id}}' > deployed-images.txt
docker image tag trace-demo-api:latest "trace-demo-api:$release"
docker image tag trace-demo-ui:latest "trace-demo-ui:$release"
# Only advance the convenience pointer after the connected workflow passes.
ln -sfn "$target" "$deploy_root/current"
"${compose[@]}" ps
printf 'Release ready: %s\n' "$release"
