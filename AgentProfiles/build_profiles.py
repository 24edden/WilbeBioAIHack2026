"""Export an audited, public-safe profile snapshot. Standard library; no app imports.

Usage: python3 build_profiles.py --source /path/to/rosalind-demo --output .
The source lock forces a fresh policy review if the audited harness changes.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMON_TOOLS = ["get_case_readiness", "read_evidence", "load_scientific_skill",
                "list_available_followups", "propose_followup"]
SHARED_SKILLS = ["discovery-planning", "rosalind-informed-workflow", "research-interpretation"]
MOLECULAR_ROLES = {"bioinformatician", "statistician", "molecular_scientist",
                   "translational_scientist", "coordinator", "reviewer"}
SEQUENCE_SKILLS = ["rosalind-informed-workflow", "research-interpretation", "molecular-interpretation",
                   "bionemo-boltz2", "uniprot-skill", "rcsb-pdb-skill"]


def read_constant(source: Path, name: str):
    for node in ast.parse(source.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"Missing source constant: {name}")


def build(source: Path, lock: dict) -> dict:
    """Read only the explicitly locked source files, never .env or runtime state."""
    source = source.resolve()
    for relative, expected in lock["files"].items():
        path = (source / relative).resolve()
        if not path.is_relative_to(source) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source changed: {relative}. Review role/skill/tool policy before updating source-lock.json.")
    manifest = json.loads((source / "skills/manifest.json").read_text())
    role_details = read_constant(source / "app/process_contract.py", "ROLES")
    role_details += [
        {"id": "coordinator", "name": "Coordinator", "inputs": ["Accepted specialist work products", "Original scientist hypothesis"],
         "work_product": "Integrated evidence assessment, decision and proposed next steps", "recipients": ["reviewer", "scientist"],
         "acceptance": "Preserve the original hypothesis; integrate accepted evidence; decisions pass independent review and application validation."},
        {"id": "reviewer", "name": "Independent reviewer", "inputs": ["Coordinator decision", "Specialist products and accepted evidence"],
         "work_product": "Challenge, corrections and qualified governance follow-up selection", "recipients": ["coordinator", "assay_scientist", "scientist"],
         "acceptance": "Challenge source identity, causality, evidence independence and readiness; only registered qualified follow-ups may enter execution."},
    ]
    catalog = []
    for item in manifest:
        category = ("rosalind_informed" if item["id"] == "rosalind-informed-workflow" else
                    "nvidia_bionemo" if item["id"] == "bionemo-boltz2" else
                    "openai_life_sciences" if item.get("external_plugin") else "custom")
        catalog.append({**{k: item[k] for k in ("id", "name", "version", "sha256", "origin", "description")},
                        "category": category, "eligible_roles": item["roles"],
                        "instruction_path": item["path"],
                        **{k: item[k] for k in ("source_url", "external_plugin") if k in item}})
    agents = []
    for detail in role_details:
        role = detail["id"]
        own = next(s for s in catalog if s["id"] == role)
        automatic = [role, *SHARED_SKILLS]
        if role in MOLECULAR_ROLES:
            automatic.append("molecular-interpretation")
        if role == "molecular_scientist":
            automatic.append("bionemo-boltz2")
        tools = list(COMMON_TOOLS)
        conditional = []
        if role == "bioinformatician":
            tools += ["analysis_catalog", "run_case_analysis"]
            conditional = [{"when": "case_id == cart-discovery", "tools": ["list_datasets", "get_dataset", "inspect_data_file", "analyze_data_file"]}]
        elif role == "reviewer":
            tools += ["analysis_catalog", "request_followup_analysis"]
            conditional = [{"when": "case_id == cart-discovery and no synthesis checkpoint", "tools": ["list_datasets", "get_dataset", "inspect_data_file", "request_data_followup"]}]
        elif role == "molecular_scientist":
            tools += ["qualify_molecular_inputs", "request_molecular_comparison"]
        workflows = []
        if role in {"molecular_scientist", "reviewer"}:
            workflows.append({"id": "public_sequence_discovery", "name": "Public sequence discovery",
                              "automatic_skills": [role, *SEQUENCE_SKILLS],
                              "tools": ["search_uniprot", "fetch_uniprot", "search_structures", "fetch_structure"],
                              "note": "Separate workflow. Finds public sequence/construct candidates; no NVIDIA submission or assertion of target retention. A loaded reviewer skill does not prove the reviewer model ran."})
        if role in {"coordinator", "reviewer"}:
            workflows.append({"id": "research_brief", "name": "Research interpretation addendum",
                              "automatic_skills": [role, "research-interpretation", "molecular-interpretation", "bionemo-boltz2"],
                              "tools": [],
                              "note": "Separate synthesis and review of accepted outputs; no new NVIDIA prediction or raw-data analysis. This is an addendum to the preserved decision."})
        agents.append({**detail, "kind": "model_agent", "purpose": own["description"], "model_policy_ref": "model_policy",
                       "main_investigation": {"automatic_skills": automatic,
                           "optional_skills": [s["id"] for s in catalog if role in s["eligible_roles"] and s["id"] not in automatic],
                           "tools": tools, "conditional_tools": conditional},
                       "additional_workflows": workflows,
                       "nvidia": {"can_request_matched_comparison": role == "molecular_scientist",
                                  "can_propose_registered_followup": True,
                                  "submission_owner": "Trusted durable application executor",
                                  "note": ("Can request a qualified matched comparison through the application. Exact inputs, provenance and readiness gates still apply."
                                           if role == "molecular_scientist" else "Can propose a registered follow-up; has no direct NVIDIA comparison request tool. NVIDIA skill access supports planning or interpretation.")}})
    return {
        "schema_version": "team-tbd-agent-profiles-1", "profile_version": "1.0.0", "snapshot_date": "2026-09-20",
        "scope": "Audited configured capabilities in the separate Brev application. This snapshot is descriptive metadata, not an authorization policy or a record of executed work.",
        "source": {"application": "Team TBD research workbench", "deployment_type": "Source directory; no Git branch recorded",
                   "files": [{"path": path, "sha256": value} for path, value in lock["files"].items()],
                   "instructions_embedded": False, "private_run_data_embedded": False},
        "model_policy": {"provider": "OpenAI", "default_model": read_constant(source / "app/providers.py", "MODEL"),
                         "selection": "TEAM_TBD_MODEL, then ROSALIND_MODEL, then the source default. All nine main roles share the selected model within a session.",
                         "identity_note": "Rosalind-informed guidance is Team TBD-authored instruction content, not proof of GPT-Rosalind access. Requested and provider-returned model identities belong in the run's call receipts. No model was called to generate these profiles.",
                         "gpt_6_astra_reasoning_effort": "high", "live_configuration_checked": False},
        "skill_categories": [
            {"id": "custom", "label": "Custom project skills", "description": "Team TBD-authored scientific role and workflow instructions."},
            {"id": "rosalind_informed", "label": "Rosalind-informed guidance", "description": "Team TBD-authored workflow informed by public OpenAI documentation; not a proprietary model skill."},
            {"id": "nvidia_bionemo", "label": "NVIDIA BioNeMo", "description": "Pinned Boltz2 NIM guidance from the installed NVIDIA toolkit. Loading it does not grant submission authority."},
            {"id": "openai_life_sciences", "label": "OpenAI Life Sciences", "description": "Registered UniProt and RCSB PDB plugin skills. Use requires the separately installed, verified private runtime."},
        ],
        "skills": catalog, "agents": agents,
        "participants": [
            {"id": "scientist", "name": "Scientist / customer", "kind": "human", "role": "Supplies the hypothesis, feedback, exact inputs and returned measurements; can select a registered follow-up.", "note": "A human participant with no model or automatic skill grants. Scientist review and feedback must be recorded, not inferred from agent consensus."},
            {"id": "executor", "name": "Application executor", "kind": "deterministic_application", "role": "Validates inputs, journals intent, submits authorized provider work and accepts validated outputs.", "note": "Executes qualified molecular requests or reviewed governance/scientist-selected registered follow-ups. No automatic repeat of unknown same-input external work. NVIDIA prediction model: mit/boltz2; Brev hosts the harness and is not itself evidence of inference."},
            {"id": "jev", "name": "Jev advisory pilot", "kind": "external_pilot", "role": "Separate review/scoring of saved outputs; not an agent in the deployed nine-role harness.", "note": "No registered harness skills, tool authority or automatic decision override. Multiple-choice hypothesis assessments must include None of the above. Pilot scores do not establish biological truth or replace the existing review process."},
        ],
        "interpretation_notes": [
            "Automatic skills are loaded when that role's model execution is attempted. Optional skills are eligible for explicit loading; eligibility alone is not usage.",
            "If exposure inputs are missing, the clinical pharmacologist can return a deterministic blocked work product with only its role skill loaded and no model call.",
            "Synthesis checkpoint recovery reuses specialist work; only coordinator/reviewer make fresh synthesis calls. The reviewer then receives only common tools. Repair passes have no tools.",
            "UniProt/PDB skill eligibility in the main investigation does not expose public sequence tools there; those tools belong to the separate sequence-discovery workflow.",
            "Current skill versions must never be applied retrospectively to a saved run. Its own version/hash/role/operation load receipts are authoritative for instruction use.",
            "Tool counts and model requests include attempts or blocked outcomes. A completed NVIDIA call requires its provider receipt and validated output artifact; a configured key, loaded skill or proposal is insufficient.",
            "Governance judgment is evidence-qualified and scope-limited. This profile snapshot neither asserts scientific truth nor changes the decision rules.",
        ],
        "execution_evidence": {
            "skill_loaded": "Stored skill_receipts with skill_id, version, sha256, role and operation/purpose.",
            "model_called": "Operation-specific provider request receipts with agent, requested_model, returned_model and status; reused handoffs do not prove a fresh call.",
            "nvidia_completed": "Molecular/follow-up provider receipt plus accepted, validated returned artifact; retain requesting context, operation, model and input/output hashes.",
            "historical_run_data": "Intentionally excluded from this public profile snapshot. Inspect the selected investigation's own receipts in the private workbench.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    payload = build(args.source, json.loads((HERE / "source-lock.json").read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "agent-profiles.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Exported {len(payload['agents'])} agent profiles and {len(payload['skills'])} skill definitions.")


if __name__ == "__main__":
    main()
