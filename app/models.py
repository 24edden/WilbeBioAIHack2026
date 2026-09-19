"""Domain models: what gets uploaded, what agents produce, what the UI reads."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentRole = Literal[
    "orchestrator",
    "genomics",
    "literature",
    "clinical",
    "stats",
    "critic",
]

Stance = Literal["supports", "contradicts", "neutral"]


# --- uploaded data -------------------------------------------------------

class Variant(BaseModel):
    """One row of a VCF, kept deliberately thin."""

    chrom: str
    pos: int
    ref: str
    alt: str
    gene: str | None = None
    rsid: str | None = None
    consequence: str | None = None
    zygosity: str | None = None
    source_line: int | None = None

    @property
    def protein_change(self) -> str | None:
        """`p.Gly12Asp` / `c.1905+1G>A` out of the consequence annotation."""
        if not self.consequence:
            return None
        match = re.search(r"(p[.][A-Za-z0-9*=_]+|c[.][0-9+*>A-Za-z-]+)", self.consequence)
        return match.group(1) if match else None

    @property
    def label(self) -> str:
        """How this variant is named everywhere downstream, so a finding, an
        event payload and the report all say the same thing."""
        gene = self.gene or f"chr{self.chrom}:{self.pos}"
        return f"{gene} {self.protein_change or f'{self.ref}>{self.alt}'}"


class LabResult(BaseModel):
    name: str
    value: float | None = None
    raw_value: str | None = None
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    date: str | None = None
    source_line: int | None = None

    @property
    def flag(self) -> str:
        """`high` / `low` / `normal` / `unknown` against the reference range."""
        if self.value is None:
            return "unknown"
        if self.ref_high is not None and self.value > self.ref_high:
            return "high"
        if self.ref_low is not None and self.value < self.ref_low:
            return "low"
        if self.ref_low is None and self.ref_high is None:
            return "unknown"
        return "normal"


class NoteSection(BaseModel):
    heading: str | None = None
    text: str
    source_line: int | None = None


class SourceFile(BaseModel):
    file_id: str
    filename: str
    kind: Literal["vcf", "labs", "notes", "unknown"]
    n_records: int = 0


class PatientBundle(BaseModel):
    """Normalized view of everything uploaded for one patient."""

    patient_id: str = "patient-0"
    files: list[SourceFile] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)
    labs: list[LabResult] = Field(default_factory=list)
    notes: list[NoteSection] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.variants or self.labs or self.notes)

    def summary(self) -> str:
        return (
            f"{len(self.variants)} variant(s), {len(self.labs)} lab value(s), "
            f"{len(self.notes)} note section(s)"
        )

    def notes_text(self) -> str:
        return "\n".join(n.text for n in self.notes)


# --- what agents produce -------------------------------------------------

class Provenance(BaseModel):
    """Where a claim came from. Every finding carries at least one."""

    kind: Literal["file", "pmid", "nim", "derived"]
    ref: str                      # filename, PMID, NIM output id
    locator: str | None = None    # line number, sentence, field
    quote: str | None = None


class Finding(BaseModel):
    finding_id: str
    agent_id: str
    agent_role: AgentRole
    claim: str
    stance: Stance = "neutral"     # relative to the user's hypothesis
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: list[Provenance] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)


class AgentSummary(BaseModel):
    agent_id: str
    agent_role: AgentRole
    parent_id: str | None = None
    task: str
    status: Literal["spawned", "running", "done", "error"] = "spawned"
    n_findings: int = 0


class Verdict(BaseModel):
    answer: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    abstained: bool = False
    abstain_reason: str | None = None
    caveats: list[str] = Field(default_factory=list)


class Report(BaseModel):
    run_id: str
    question: str
    status: Literal["running", "complete", "error"] = "running"
    verdict: Verdict | None = None
    findings: list[Finding] = Field(default_factory=list)
    agents: list[AgentSummary] = Field(default_factory=list)
    bundle_summary: str = ""
    run_mode: str = "mock"
    started_ts: int = 0
    finished_ts: int | None = None
    error: str | None = None


# --- HTTP request/response ----------------------------------------------

class InvestigateRequest(BaseModel):
    question: str
    file_ids: list[str] = Field(default_factory=list)


class InvestigateResponse(BaseModel):
    run_id: str


class UploadedFileInfo(BaseModel):
    file_id: str
    filename: str
    kind: Literal["vcf", "labs", "notes", "unknown"]
    n_records: int


class UploadResponse(BaseModel):
    files: list[UploadedFileInfo]
