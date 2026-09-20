#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
scientific_python="${TEAM_TBD_PYTHON:-python3}"
"$scientific_python" -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12 or newer is required"'
if [ ! -x .venv/bin/python ]; then
  "$scientific_python" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.lock.txt
if [ ! -e .env ]; then
  cp .env.example .env
  chmod 600 .env
fi
echo "Dependencies installed; existing configuration retained. Hydrate the pinned inputs as documented in SETUP.md before starting."
