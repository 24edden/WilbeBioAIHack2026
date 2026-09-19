"""Verify configured model access; optionally make one small inference call.

Run from the repository root: python scripts/check_reasoning.py --env-file .env
No patient files are loaded or sent. Credentials and provider bodies are never
printed. Model visibility is checked separately from successful generation.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.providers.errors import ProviderError
from app.providers.live import LiveReasoningProvider


async def check(smoke: bool) -> None:
    settings = get_settings()
    provider = LiveReasoningProvider(settings)
    print(f"Model: {settings.reasoning_model}; API: {settings.effective_reasoning_api}")
    await provider.transport.check_access()
    print("Model lookup succeeded. Generation has not yet been verified.")
    if smoke:
        result = await provider._chat(
            'Return only the JSON object {"ok": true}.',
            "This is a connection check. No patient data is included.",
        )
        if result != {"ok": True}:
            raise ProviderError("Generation returned an unexpected connection-check result.")
        print("Generation and JSON parsing succeeded. No scientific workflow was exercised.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Optional server .env file; existing environment values take precedence")
    parser.add_argument("--smoke", action="store_true", help="Also make one inference call, which can consume API tokens")
    args = parser.parse_args()
    if args.env_file:
        if not args.env_file.is_file():
            parser.error("The specified environment file does not exist.")
        from dotenv import load_dotenv  # installed by uvicorn[standard]

        load_dotenv(args.env_file, override=False)
    try:
        asyncio.run(check(args.smoke))
    except (ProviderError, ValueError) as exc:
        print(f"Check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
