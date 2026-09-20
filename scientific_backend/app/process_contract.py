"""Pinned, compact process graph. Role authority is explicit application policy."""
import copy

from .store import digest

ROLES = [
    {"id": "clinical_scientist", "name": "Clinical scientist", "recipients": ["translational_scientist", "statistician", "clinical_pharmacologist"],
     "inputs": ["Treatment and response timeline", "Patient/sample/timepoint map"], "work_product": "Population, phenotype, clinical question, timing and competing explanations", "acceptance": "No patient-level inference from a reporter library or functional assay."},
    {"id": "bioinformatician", "name": "Bioinformatician", "recipients": ["statistician", "molecular_scientist"],
     "inputs": ["Assay matrices or variant calls", "Sample mapping and metadata"], "work_product": "Versioned analysis table, feature definitions, exclusions and QC", "acceptance": "Hash-qualified sources; explicit joins, units and exclusions."},
    {"id": "statistician", "name": "Statistician", "recipients": ["clinical_scientist", "translational_scientist"],
     "inputs": ["Bioinformatics work product", "Endpoint and analysis specification"], "work_product": "Estimates, design diagnostics and interpretation limits", "acceptance": "Independent unit and missingness declared; numerical values resolve to deterministic tool results."},
    {"id": "clinical_pharmacologist", "name": "Clinical pharmacologist", "recipients": ["clinical_scientist", "translational_scientist"],
     "inputs": ["Actual dosing", "Sampling times and concentrations"], "work_product": "Supported, weakened or unresolved exposure explanation", "acceptance": "No exposure model without actual dosing/sampling evidence; reference labels are not administered dose."},
    {"id": "molecular_scientist", "name": "Molecular / structural scientist", "recipients": ["translational_scientist", "assay_scientist"],
     "inputs": ["Validated mapping", "Exact sequences/constructs", "Functional evidence"], "work_product": "Qualified prediction, mechanistic limits and discriminators", "acceptance": "Matched binders require exact constructs and target-retained scope; public monomers require their own pinned sequence mapping. Structural confidence is not efficacy."},
    {"id": "translational_scientist", "name": "Translational scientist", "recipients": ["assay_scientist", "coordinator"],
     "inputs": ["Clinical, statistical, molecular and exposure work products"], "work_product": "Evidence matrix, contradictions and ranked discriminating questions", "acceptance": "Preserve alternatives and contrary evidence; do not count repeated analyses as independent evidence."},
    {"id": "assay_scientist", "name": "Assay / wet-lab scientist", "recipients": ["reviewer", "coordinator"],
     "inputs": ["Mechanism and discriminating objective", "Specimen/method/control constraints"], "work_product": "Protocol proposal, matched comparisons, controls and result-to-hypothesis rules", "acceptance": "Protocol proposal is not an executed experiment; returned results require identity and QC qualification."},
]

# These are required incoming work products in the implemented execution order,
# not all possible scientific conversations between the roles. Blocked products
# satisfy the dependency only as an explicit account of missing information.
REQUIRED_UPSTREAM = {
    "bioinformatician": [], "molecular_scientist": ["bioinformatician"],
    "statistician": ["bioinformatician"], "clinical_scientist": ["statistician"],
    "clinical_pharmacologist": ["clinical_scientist"],
    "translational_scientist": ["clinical_scientist", "statistician", "molecular_scientist", "clinical_pharmacologist"],
    "assay_scientist": ["translational_scientist", "molecular_scientist"],
    "coordinator": ["translational_scientist", "assay_scientist"],
    "reviewer": ["coordinator", "assay_scientist"],
}


def get_process_contract():
    body = {"version": "team-tbd-resistance-4", "roles": copy.deepcopy(ROLES),
            "coordinator": "Pins the user hypothesis, integrates accepted work products, and owns the decision.",
            "reviewer": "Independent bounded challenge; failed acceptance returns once to the sender, then blocks.",
            "handoff_required": ["sender", "case_id", "input_versions", "question", "method", "result_status", "result", "limitations", "decision_it_could_change", "recipient", "claims"],
            "additional_routes": {"coordinator": ["reviewer", "scientist"], "reviewer": ["coordinator", "assay_scientist", "scientist"]},
            "loops": {"L1": "Hypothesis testing, specialist correction and reviewed qualified follow-ups within a run", "L2": "Scientist correction to an immutable decision version", "L3": "Exact experiment/candidate-linked new measurements reopen investigation", "L4": "Provisional lesson, scientific review, disjoint evaluation and scoped release"},
            "stage_policy": {"required_upstream": copy.deepcopy(REQUIRED_UPSTREAM),
                             "max_handoff_attempts_per_role": 2,
                             "result_statuses": ["completed", "blocked", "inconclusive"],
                             "blocked_is_scientific_success": False,
                             "evaluation_schema": "team-tbd-stage-evaluation-1"},
            "followup_planning": {"catalog": "Case-bound registered recipes and source readiness",
                                  "proposal_acceptance": "Registered recipe, role, exact hypothesis/evidence/recipe versions; accepted sender handoff",
                                  "execution": "Proposals do not submit work; an independent reviewed governance selection or explicit scientist selection enters the durable follow-up executor"},
            "hypothesis_governance": {"enabled": True, "auto_continue": True,
                "schema": "team-tbd-hypothesis-governance-1",
                "states": ["possible", "probable", "clearly_ruled_out"],
                "state_scope": "Evidence-qualified scientific judgment, not numeric probability or a guarantee of truth",
                "continuation": "One informative, qualified, unperformed registered follow-up selected by the reviewer; reassess all hypotheses after accepted results",
                "stop": "Resolved within scope, no informative executable action, missing input/method, wet-lab requirement, cancellation or execution blocker",
                "replay": "No automatic retry of attempted, failed or unknown same-input work; no arbitrary code or laboratory execution",
                "completion": "A stopped investigation may still contain possible hypotheses; record the reason without fabricating resolution"},
            "loop_contracts": {
                "L1": {"trigger": "Rejected work product, concrete reviewer evidence gap or reviewed informative next hypothesis test", "handoff_repairs": 1,
                       "review_diagnostics": 2, "stop": "Stage repair/diagnostic limits remain bounded; the investigation continues through qualified follow-ups until its explicit governance stopping condition. Aggregate budget thresholds are advisory.",
                       "recovery": "Read-only accepted evidence may be reused; unknown provider submissions are never automatically repeated"},
                "L2": {"trigger": "Scientist correction to the latest immutable decision", "acceptance": "Exact current decision version and idempotency key",
                       "result": "New operation and decision version; same original hypothesis"},
                "L3": {"trigger": "Returned measurement", "acceptance": "Current decision, experiment and candidate IDs; finite value and unit",
                       "result": "Attributed user report, not independently verified biology; a new assessment version"},
                "L4": {"trigger": "Proposed conditional procedure", "acceptance": "Scientist review, matched disjoint baseline/candidate plus excluded-case evaluation, immutable decision hashes",
                       "result": "Scoped procedural release; never evidence or clinical validation"}},
            "reference": "User-supplied role interaction table and outputs/reference-architecture/REFERENCE-ARCHITECTURE.md"}
    return {**body, "sha256": digest(body)}
