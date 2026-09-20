"""Editable product/workflow settings; no transport or Streamlit dependencies."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProductProfile:
    name: str = "TRACE"
    page_title: str = "TRACE · Treatment investigation"
    eyebrow: str = "Multi-agent treatment analysis"
    headline: str = "Investigate"
    headline_accent: str = "treatment response"
    description: str = "Add evidence, configure agents and submit a research question. Inspect their findings and source references."
    default_question: str = "Why did this patient's treatment fail?"
    evidence_label: str = "Patient evidence"
    upload_label: str = "Add patient files · VCF, laboratory data, clinical notes"
    input_extensions: tuple[str, ...] = ("vcf", "csv", "txt", "tsv", "json")
    sample_available: bool = True
    sample_label: str = "Use bundled sample patient"
    sample_description: str = "The backend will load the bundled VCF, laboratory results and clinical notes when you start."
    require_files: bool = True
    single_specialist_note: str = "One specialist is useful for inspection. The current evidence gate requires two specialist roles for a conclusion."
    stages: tuple[str, str, str, str] = ("Question", "Investigate", "Cross-examine", "Conclusion")
    review_roles: tuple[str, ...] = ("critic",)
    preview_roles: tuple[str, str, str] = ("genomics", "clinical", "literature")
    role_groups: dict[str, str] = field(default_factory=lambda: {
        "orchestrator": "planner", "genomics": "specialist", "literature": "specialist",
        "clinical": "specialist", "stats": "specialist", "critic": "critic",
    })
    mode_labels: dict[str, str] = field(default_factory=lambda: {
        "Demo": "Try the demo", "Mock": "Explore a recorded case", "Live": "Investigate my data",
    })
    fixture_labels: dict[str, str] = field(default_factory=lambda: {
        "demo_run": "Acquired resistance", "demo_abstain": "Insufficient evidence",
    })
    default_fixture: str = "demo_run"


# Edit this instance or replace it with ProductProfile(...) for another workflow.
PROFILE = ProductProfile()
