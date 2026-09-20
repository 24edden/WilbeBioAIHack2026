#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
exec "${TRACE_UI_PYTHON:-$ROOT_DIR/.venv/bin/python}" -m streamlit run frontend/app.py \
  --server.address 127.0.0.1 --server.port "${TRACE_UI_PORT:-8505}" \
  --browser.gatherUsageStats false --theme.base dark --theme.primaryColor '#d6fb73' \
  --theme.backgroundColor '#080b09' --theme.secondaryBackgroundColor '#101612' \
  --theme.textColor '#f0f5ee' "$@"
