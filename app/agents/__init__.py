"""Specialist agents. The orchestrator picks from this registry by role."""

from __future__ import annotations

from app.agents.base import Agent, Blackboard, RunContext
from app.agents.clinical import ClinicalAgent
from app.agents.critic import CriticAgent, evidence_gate
from app.agents.genomics import GenomicsAgent
from app.agents.literature import LiteratureAgent
from app.agents.stats import StatsAgent

AGENT_TYPES: dict[str, type[Agent]] = {
    "genomics": GenomicsAgent,
    "clinical": ClinicalAgent,
    "literature": LiteratureAgent,
    "stats": StatsAgent,
}

__all__ = [
    "AGENT_TYPES",
    "Agent",
    "Blackboard",
    "ClinicalAgent",
    "CriticAgent",
    "GenomicsAgent",
    "LiteratureAgent",
    "RunContext",
    "StatsAgent",
    "evidence_gate",
]
