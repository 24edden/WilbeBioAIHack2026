"""Run deterministic scientific checks in fresh state without credentials/network.

Run from scientific_backend: .venv/bin/python scripts/check.py
The full suite requires the authorized installed proprietary runtime to verify
all current skill bytes, including synthesis-checkpoint eligibility. Use explicit
--public-only to omit installation/synthesis checks when it is unavailable.
"""
from pathlib import Path
import os
import socket
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    import dotenv
    import pytest

    # Tests must never load a configured deployment's private .env.
    dotenv.dotenv_values = lambda *_args, **_kwargs: {}
    for name in ("OPENAI_API_KEY", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID", "OPENAI_BASE_URL",
                 "NGC_API_KEY", "NVIDIA_API_KEY", "BOLTZ2_NIM_URL"):
        os.environ.pop(name, None)
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    os.environ["ROSALIND_EMBEDDED_WORKER"] = "0"
    os.environ["TEAM_TBD_PROFILE_SOURCE"] = str(ROOT)
    os.environ.setdefault("TEAM_TBD_LIFE_SCIENCES_PLUGIN_ROOT", str(ROOT / "runtime/life-sciences-databases"))
    original_connect = socket.socket.connect

    def no_network(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError("Scientific test runner forbids network connections; mock the transport")
        return original_connect(sock, address)

    socket.socket.connect = no_network
    with tempfile.TemporaryDirectory(prefix="team-tbd-check-") as runtime:
        os.environ["ROSALIND_RUNTIME"] = runtime
        os.environ["ROSALIND_CAPABILITIES_FILE"] = str(Path(runtime) / "capabilities.json")
        from app.cases import verify_sources
        from app.scientific_skills import verify_life_sciences_runtime
        verify_sources()
        forwarded = sys.argv[1:]
        public_only = "--public-only" in forwarded
        forwarded = [item for item in forwarded if item != "--public-only"]
        arguments = ["-q", "tests", "static/agent-profiles/test_profiles.py"]
        try:
            verify_life_sciences_runtime()
        except ValueError:
            if not public_only:
                print("Full suite requires the pinned authorized Life Sciences Databases installation. See SETUP.md, or explicitly use --public-only for the documented subset.")
                return 2
        if public_only:
            print("Explicit public-only checks: excluding full-registry installation and three synthesis-checkpoint suites requiring proprietary instruction validation. Public skills and mocked sequence contracts remain checked.")
            arguments.extend(["-k", "not test_every_registered_skill_loads_exact_pinned_bytes_for_its_roles"])
            arguments.extend(["--ignore=tests/test_synthesis_checkpoint.py",
                              "--ignore=tests/test_synthesis_presentation.py",
                              "--ignore=tests/test_synthesis_sdk.py"])
        return pytest.main(arguments + forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
