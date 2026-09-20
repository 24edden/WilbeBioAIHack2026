"""Read-only capability descriptions, pinned to docs/agent-profiles@7f8e31a.

This registry describes the separate Brev harness. It is never an execution receipt
and must not relabel historical runs or grant tools to the local demo engine.
"""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def registry():
    path=Path(__file__).resolve().parents[2]/'AgentProfiles'/'agent-profiles.json'
    return json.loads(path.read_text(encoding='utf-8-sig'))

def profile_catalog():
    return registry()['skills']

def profiles():
    return registry()['agents']
