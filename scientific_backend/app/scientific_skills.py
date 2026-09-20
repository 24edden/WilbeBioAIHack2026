"""Pinned, executable-context skills. Availability never implies model invocation."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills"


def life_sciences_root() -> Path:
    from .config import RUNTIME
    return Path(os.getenv("TEAM_TBD_LIFE_SCIENCES_PLUGIN_ROOT", str(RUNTIME / "life-sciences-databases"))).resolve()


def verify_life_sciences_runtime() -> Path:
    """Verify the user's installed private plugin; never fetch executable code at runtime."""
    root = life_sciences_root()
    manifest = json.loads((SKILL_ROOT / "external-runtime-manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("The pinned OpenAI life-sciences plugin runtime is missing or changed. Install the documented private runtime before sequence discovery.")
    return root


def skill_catalog(role: str | None = None) -> list[dict]:
    records = json.loads((SKILL_ROOT / "manifest.json").read_text())
    return [dict(s) for s in records if role is None or role in s["roles"]]


def load_skill(skill_id: str, role: str | None = None) -> dict:
    matches = [s for s in skill_catalog(role) if s["id"] == skill_id]
    if len(matches) != 1:
        raise ValueError("Skill is not registered for this role.")
    record = matches[0]
    root = verify_life_sciences_runtime() if record.get("external_plugin") == "life-sciences-databases" else SKILL_ROOT.resolve()
    path = (root / record["path"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Skill path escapes the registered skill directory.")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != record["sha256"]:
        raise ValueError("Skill content differs from its pinned release.")
    return {**record, "instructions": content.decode("utf-8")}
