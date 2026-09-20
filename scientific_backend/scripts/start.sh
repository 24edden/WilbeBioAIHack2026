#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "Create .venv with Python 3.12 or newer and install requirements.lock.txt first. See README.md."
  exit 1
fi
exec .venv/bin/python -m app serve --port "${PORT:-8080}"
