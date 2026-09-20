"""Provider factory. Nothing above this layer knows which mode it is in."""

from __future__ import annotations

from app.config import Settings, get_settings
from app.providers.base import (
    BioProvider,
    ClaimDraft,
    Plan,
    Providers,
    ReasoningProvider,
    ReasoningStep,
    SubTask,
    SynthesisResult,
    VariantScore,
)

__all__ = [
    "BioProvider",
    "ClaimDraft",
    "Plan",
    "Providers",
    "ReasoningProvider",
    "ReasoningStep",
    "SubTask",
    "SynthesisResult",
    "VariantScore",
    "build_providers",
]


def build_providers(settings: Settings | None = None) -> Providers:
    """`RUN_MODE=mock` -> fixtures, `RUN_MODE=live` -> real endpoints."""
    settings = settings or get_settings()
    if settings.is_mock:
        from app.providers.mock import MockBioProvider, MockReasoningProvider

        scale = settings.mock_latency_scale
        return Providers(
            reasoning=MockReasoningProvider(scale),
            bio=MockBioProvider(scale),
            mode=settings.run_mode,
        )

    # Imported lazily so a mock-mode run never needs the live dependencies or
    # credentials to be present.
    from app.providers.live import LiveBioProvider, LiveReasoningProvider

    return Providers(
        reasoning=LiveReasoningProvider(settings),
        bio=LiveBioProvider(settings),
        mode=settings.run_mode,
    )
