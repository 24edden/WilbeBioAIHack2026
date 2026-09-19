"""Runtime configuration.

Everything is read from the environment so that `RUN_MODE=mock` is the only
thing a teammate needs to set to get a full investigation running. Settings are
re-read on each call, which keeps tests free to flip env vars between runs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

MOCK = "mock"
LIVE = "live"


@dataclass(frozen=True)
class Settings:
    run_mode: str
    mock_latency_scale: float

    # live reasoning (OpenAI / GPT-Rosalind, OpenAI-compatible)
    reasoning_base_url: str
    reasoning_api_key: str
    reasoning_model: str

    # live bio (NVIDIA BioNeMo NIMs)
    bionemo_base_url: str
    bionemo_api_key: str
    bionemo_variant_model: str
    bionemo_embed_model: str

    @property
    def is_mock(self) -> bool:
        return self.run_mode == MOCK


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def get_settings() -> Settings:
    run_mode = os.getenv("RUN_MODE", MOCK).strip().lower()
    if run_mode not in (MOCK, LIVE):
        raise ValueError(f"RUN_MODE must be {MOCK!r} or {LIVE!r}, got {run_mode!r}")
    return Settings(
        run_mode=run_mode,
        mock_latency_scale=max(0.0, _float_env("MOCK_LATENCY_SCALE", 1.0)),
        reasoning_base_url=os.getenv("REASONING_BASE_URL", "https://api.openai.com/v1"),
        reasoning_api_key=os.getenv("REASONING_API_KEY", ""),
        reasoning_model=os.getenv("REASONING_MODEL", "gpt-4o-mini"),
        bionemo_base_url=os.getenv("BIONEMO_BASE_URL", "http://localhost:8000"),
        bionemo_api_key=os.getenv("BIONEMO_API_KEY", ""),
        bionemo_variant_model=os.getenv("BIONEMO_VARIANT_MODEL", "evo2"),
        bionemo_embed_model=os.getenv("BIONEMO_EMBED_MODEL", "esm2-650m"),
    )
