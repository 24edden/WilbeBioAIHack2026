"""The provider interface — the first seam of the design (ARCHITECTURE.md).

Every model call in the system goes through one of these two protocols. Above
this layer nothing knows whether it is talking to a GPU or to a fixture file,
which is what makes `RUN_MODE=mock` a full-fidelity rehearsal rather than a
separate code path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.models import AgentRole, PatientBundle, Stance, Variant


# --- reasoning results ---------------------------------------------------

@dataclass
class SubTask:
    role: AgentRole
    task: str
    rationale: str = ""


@dataclass
class Plan:
    restated_question: str
    hypothesis: str | None
    tasks: list[SubTask]
    notes: str = ""


@dataclass
class ClaimDraft:
    claim: str
    stance: Stance = "neutral"
    confidence: float = 0.5
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningStep:
    """One specialist's turn: something to say, plus zero or more claims."""

    message: str
    claims: list[ClaimDraft] = field(default_factory=list)


@dataclass
class SynthesisResult:
    answer: str
    rationale: str
    confidence: float
    abstained: bool = False
    abstain_reason: str | None = None
    caveats: list[str] = field(default_factory=list)


# --- bio results ---------------------------------------------------------

@dataclass
class VariantScore:
    variant_label: str
    pathogenicity: float          # 0 = benign, 1 = pathogenic
    call: str                     # pathogenic | likely_pathogenic | uncertain | benign
    model: str
    output_id: str                # provenance handle for the NIM response
    notes: str = ""
    therapy_implication: str = ""  # what, if anything, the result changes clinically


@runtime_checkable
class ReasoningProvider(Protocol):
    """Live: GPT-Rosalind / OpenAI. Mock: fixtures."""

    name: str

    async def plan(self, question: str, bundle: PatientBundle) -> Plan: ...

    async def step(
        self, role: AgentRole, task: str, context: dict[str, Any]
    ) -> ReasoningStep: ...

    async def synthesize(
        self, question: str, claims: list[dict[str, Any]], context: dict[str, Any]
    ) -> SynthesisResult: ...


@runtime_checkable
class BioProvider(Protocol):
    """Live: NVIDIA BioNeMo NIMs. Mock: fixtures."""

    name: str

    async def score_variant(self, variant: Variant) -> VariantScore: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class Providers:
    """What gets handed to the engine. One object, so a test can inject its own."""

    reasoning: ReasoningProvider
    bio: BioProvider
    mode: str
