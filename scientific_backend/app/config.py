from pathlib import Path
import os
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
# An explicitly populated private file wins over inherited stale credentials.
# Blank template values never erase a key supplied by the launching environment.
for name, value in dotenv_values(ROOT / ".env").items():
    if value:
        os.environ[name] = value
RUNTIME = Path(os.getenv("ROSALIND_RUNTIME", str(ROOT / "runtime"))).resolve()
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("ROSALIND_CAPABILITIES_FILE", str(RUNTIME / "capabilities.json"))
os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")
DB_PATH = RUNTIME / "app.sqlite"
MAX_SECONDS = int(os.getenv("ROSALIND_MAX_SECONDS", "1200"))
DEMO_DELAY = float(os.getenv("ROSALIND_DEMO_DELAY", "0.7"))
MAX_TOOL_CALLS = int(os.getenv("ROSALIND_MAX_TOOL_CALLS", "80"))
