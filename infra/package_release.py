"""Package the current working source for deployment, excluding local secrets/data.

Run from any directory: python infra/package_release.py
The archive contains a file-hash manifest, including uncommitted source changes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("app", "frontend", "fixtures", "samples", "eval", "scripts", "infra", "tests", "Presentation")
ROOT_FILES = ("requirements.txt", "pyproject.toml", "README.md", "DeveloperREADME.md",
              "INTEGRATION.md", "ARCHITECTURE.md", "AGENTS.md", ".env.example", ".streamlit/config.toml",
              "Context/rosalind-integration.md", "Context/judgingCriteria.md", "Context/tooling.md",
              "Plan/model-evaluation.md", "Plan/hosting-and-demo.md", "Plan/public-demo-hosting.md",
              "Plan/architecture-review.md", "Plan/performance-check.json")
SUFFIXES = {".py", ".json", ".toml", ".md", ".txt", ".csv", ".tsv", ".vcf", ".yaml", ".yml", ".dockerignore", ".sh", ".js", ".mjs", ".css", ".html", ".svg"}
EXCLUDED = {"__pycache__", ".venv", "venv", "uploads", "results", ".git", ".deploy"}


def git(*args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def package() -> Path:
    candidates = {ROOT / name for name in ROOT_FILES}
    for directory in DIRECTORIES:
        for path in (ROOT / directory).rglob("*"):
            relative = path.relative_to(ROOT)
            if path.is_symlink() or not path.is_file() or EXCLUDED.intersection(relative.parts):
                continue
            if any(part.startswith(".") for part in relative.parts) or path.name == "secrets.toml":
                continue
            if path.suffix in SUFFIXES or path.name == "Dockerfile":
                candidates.add(path)
    files = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in sorted(candidates)}
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    source_hash = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    release = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + source_hash[:12]
    manifest = {"release": release, "source_sha256": source_hash,
                "git_revision": git("rev-parse", "HEAD"),
                "working_tree_dirty": bool(git("status", "--porcelain")), "files": hashes}
    files["release-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    directory = ROOT / ".deploy"
    directory.mkdir(exist_ok=True)
    archive = directory / f"{release}.tar.gz"
    with tarfile.open(archive, "x:gz") as bundle:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(content), 0o644
            bundle.addfile(info, io.BytesIO(content))
    print(json.dumps({"release": release, "archive": str(archive),
                      "files": len(hashes), "bytes": archive.stat().st_size,
                      "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}))
    return archive


if __name__ == "__main__":
    package()
