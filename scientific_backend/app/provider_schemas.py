"""Strict model outputs; identifiers and artifacts are checked again by the server."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Claim(StrictModel):
    text: str
    evidence_ids: list[str]
    kind: Literal["observation", "interpretation", "prediction", "limitation"]


class Alternative(StrictModel):
    title: str
    reason: str


class NextExperiment(StrictModel):
    title: str
    design: str
    positive: str
    negative: str
    inconclusive: str


class Candidate(StrictModel):
    id: str
    name: str
    rationale: str


class Modeling(StrictModel):
    status: Literal["blocked", "proposed", "completed", "incomplete"]
    reason: str
    artifacts: list[str]


class RDHandoff(StrictModel):
    objective: str
    status: str
    reference: str
    candidates: list[Candidate]
    modeling: Modeling
    experiment_id: str
    return_requirements: list[str]


class Insight(StrictModel):
    title: str
    finding: str
    why_it_matters: str
    evidence_ids: list[str]
    next_step: str


class FollowupRecommendation(StrictModel):
    kind: Literal["data_analysis", "bionemo_public_structure"]
    analysis_id: str
    title: str
    rationale: str
    decision_it_could_change: str
    prerequisites: list[str]
    evidence_ids: list[str]
    status: Literal["ready", "needs_inputs"]


class HypothesisAssessment(StrictModel):
    """A scoped reviewer interpretation, never an estimated probability."""
    hypothesis_id: str
    statement: str
    origin: Literal["user", "agent_generated"]
    source_quote: str
    scope: str
    status: Literal["possible", "probable", "clearly_ruled_out"]
    rationale: str
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    test_evidence_ids: list[str]
    falsification_test: str
    falsification_result: str
    next_analysis_ids: list[str]
    blocker: str
    scope_type: Literal["biological", "computational"] = "biological"


class HypothesisGovernance(StrictModel):
    hypotheses: list[HypothesisAssessment] = Field(min_length=1, max_length=16)
    next_action_id: str | None
    target_hypothesis_ids: list[str]
    continuation_reason: str
    stop_reason: Literal["continue", "resolved_within_scope", "needs_data", "needs_method",
                         "wet_lab_required", "no_informative_action", "provider_unresolved"]


class Investigation(StrictModel):
    summary: str
    assessment: Literal["supported", "weakened", "inconclusive", "blocked"]
    claims: list[Claim]
    alternatives: list[Alternative]
    limitations: list[str]
    next_experiment: NextExperiment
    rd_handoff: RDHandoff
    insights: list[Insight]
    followups: list[FollowupRecommendation]
    governance: HypothesisGovernance | None = None


class ProbeOutput(StrictModel):
    evidence_id: str
    tool_observation: str


class SpecialistBrief(StrictModel):
    """The server supplies role, case, recipient and input-version identities."""
    question: str
    method: str
    result_status: Literal["completed", "blocked", "inconclusive"]
    result: str
    limitations: list[str]
    decision_it_could_change: str
    claims: list[Claim]
