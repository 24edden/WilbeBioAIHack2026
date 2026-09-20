"""Public profile contract checks; no vendor calls or third-party dependencies.

Run: python3 -m unittest discover -s /path/to/AgentProfiles -p test_profiles.py
Set TEAM_TBD_PROFILE_SOURCE to the audited application directory to enable source
checks. A nearby local rosalind-demo directory is detected for development only.
The public GitHub checkout intentionally lacks this separate private application.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
PROFILE_PATH = HERE / "agent-profiles.json"
LOCK_PATH = HERE / "source-lock.json"
PROFILE = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
LOCK = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
SPEC = importlib.util.spec_from_file_location("public_profile_builder", HERE / "build_profiles.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

ROLES = {
    "clinical_scientist", "bioinformatician", "statistician", "clinical_pharmacologist",
    "molecular_scientist", "translational_scientist", "assay_scientist", "coordinator", "reviewer",
}
MOLECULAR_INTERPRETERS = {
    "bioinformatician", "statistician", "molecular_scientist", "translational_scientist",
    "coordinator", "reviewer",
}
COMMON_TOOLS = {
    "get_case_readiness", "read_evidence", "load_scientific_skill",
    "list_available_followups", "propose_followup",
}
LOCKED_FILES = {
    "app/providers.py", "app/process_contract.py", "app/scientific_skills.py",
    "app/sequence_discovery.py", "app/research_brief.py", "app/worker.py", "skills/manifest.json",
}


def objects(value):
    """Walk structured objects without examining any private application state."""
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from objects(item)


class PublicProfileContract(unittest.TestCase):
    def setUp(self):
        self.agents = {item["id"]: item for item in PROFILE["agents"]}
        self.skills = {item["id"]: item for item in PROFILE["skills"]}

    def test_exact_scientific_team_and_unique_skill_catalog(self):
        self.assertEqual(len(PROFILE["agents"]), 9)
        self.assertEqual(set(self.agents), ROLES)
        self.assertTrue(all(item["kind"] == "model_agent" for item in self.agents.values()))
        self.assertEqual(len(PROFILE["skills"]), len(self.skills))
        self.assertEqual(len(self.skills), 16)
        for skill in self.skills.values():
            self.assertTrue(set(skill["eligible_roles"]) <= ROLES)
            self.assertRegex(skill["sha256"], r"^[a-f0-9]{64}$")

    def test_automatic_and_optional_skills_partition_eligibility(self):
        for role, agent in self.agents.items():
            with self.subTest(role=role):
                main = agent["main_investigation"]
                automatic = set(main["automatic_skills"])
                optional = set(main["optional_skills"])
                eligible = {key for key, skill in self.skills.items() if role in skill["eligible_roles"]}
                self.assertEqual(len(automatic), len(main["automatic_skills"]))
                self.assertEqual(len(optional), len(main["optional_skills"]))
                self.assertFalse(automatic & optional)
                self.assertEqual(automatic | optional, eligible)
                expected = {role, "discovery-planning", "rosalind-informed-workflow", "research-interpretation"}
                if role in MOLECULAR_INTERPRETERS:
                    expected.add("molecular-interpretation")
                if role == "molecular_scientist":
                    expected.add("bionemo-boltz2")
                self.assertEqual(automatic, expected)

    def test_skill_origins_are_not_model_or_tool_authority(self):
        self.assertEqual(self.skills["rosalind-informed-workflow"]["category"], "rosalind_informed")
        self.assertIn("not a proprietary", self.skills["rosalind-informed-workflow"]["origin"])
        self.assertEqual(self.skills["bionemo-boltz2"]["category"], "nvidia_bionemo")
        self.assertEqual(set(self.skills["bionemo-boltz2"]["eligible_roles"]), ROLES - {
            "clinical_scientist", "clinical_pharmacologist"})
        for key in ("uniprot-skill", "rcsb-pdb-skill"):
            self.assertEqual(self.skills[key]["category"], "openai_life_sciences")
            self.assertEqual(set(self.skills[key]["eligible_roles"]), {
                "bioinformatician", "molecular_scientist", "translational_scientist", "coordinator", "reviewer"})
        for role in ROLES:
            self.assertEqual(self.skills[role]["category"], "custom")
            self.assertEqual(self.skills[role]["eligible_roles"], [role])

    def test_direct_nvidia_request_is_molecular_only(self):
        requesters = set()
        for role, agent in self.agents.items():
            main = agent["main_investigation"]
            tools = set(main["tools"])
            tools.update(tool for condition in main["conditional_tools"] for tool in condition["tools"])
            if "request_molecular_comparison" in tools:
                requesters.add(role)
            self.assertEqual(agent["nvidia"]["can_request_matched_comparison"], role == "molecular_scientist")
            self.assertTrue(agent["nvidia"]["can_propose_registered_followup"])
            self.assertIn("propose_followup", tools)
            self.assertEqual(agent["nvidia"]["submission_owner"], "Trusted durable application executor")
        self.assertEqual(requesters, {"molecular_scientist"})

    def test_main_tool_routes_and_case_restrictions(self):
        extras = {
            "bioinformatician": {"analysis_catalog", "run_case_analysis"},
            "reviewer": {"analysis_catalog", "request_followup_analysis"},
            "molecular_scientist": {"qualify_molecular_inputs", "request_molecular_comparison"},
        }
        for role, agent in self.agents.items():
            with self.subTest(role=role):
                main = agent["main_investigation"]
                self.assertEqual(set(main["tools"]), COMMON_TOOLS | extras.get(role, set()))
                if role in {"bioinformatician", "reviewer"}:
                    self.assertEqual(len(main["conditional_tools"]), 1)
                    conditional = main["conditional_tools"][0]
                    self.assertIn("cart-discovery", conditional["when"])
                    expected = {"list_datasets", "get_dataset", "inspect_data_file"}
                    expected.add("analyze_data_file" if role == "bioinformatician" else "request_data_followup")
                    self.assertEqual(set(conditional["tools"]), expected)
                    if role == "reviewer":
                        self.assertIn("no synthesis checkpoint", conditional["when"])
                else:
                    self.assertEqual(main["conditional_tools"], [])

    def test_separate_workflows_do_not_inherit_main_permissions(self):
        sequence_roles, brief_roles = set(), set()
        sequence_tools = {"search_uniprot", "fetch_uniprot", "search_structures", "fetch_structure"}
        for role, agent in self.agents.items():
            self.assertFalse(set(agent["main_investigation"]["tools"]) & sequence_tools)
            workflows = agent["additional_workflows"]
            self.assertEqual(len(workflows), len({item["id"] for item in workflows}))
            for workflow in workflows:
                skills = set(workflow["automatic_skills"])
                self.assertTrue(all(role in self.skills[key]["eligible_roles"] for key in skills))
                if workflow["id"] == "public_sequence_discovery":
                    sequence_roles.add(role)
                    self.assertEqual(skills, {role, "rosalind-informed-workflow", "research-interpretation",
                                             "molecular-interpretation", "bionemo-boltz2", "uniprot-skill", "rcsb-pdb-skill"})
                    self.assertEqual(set(workflow["tools"]), sequence_tools)
                    self.assertNotIn("discovery-planning", skills)
                elif workflow["id"] == "research_brief":
                    brief_roles.add(role)
                    self.assertEqual(skills, {role, "research-interpretation", "molecular-interpretation", "bionemo-boltz2"})
                    self.assertEqual(workflow["tools"], [])
                    self.assertNotIn("rosalind-informed-workflow", skills)
                else:
                    self.fail("Unreviewed workflow: " + workflow["id"])
        self.assertEqual(sequence_roles, {"molecular_scientist", "reviewer"})
        self.assertEqual(brief_roles, {"coordinator", "reviewer"})

    def test_exceptions_and_evidence_levels_remain_visible(self):
        notes = " ".join(PROFILE["interpretation_notes"])
        for fragment in ("no model call", "only its role skill", "only common tools",
                         "Repair passes have no tools", "must never be applied retrospectively"):
            self.assertIn(fragment, notes)
        self.assertEqual(set(PROFILE["execution_evidence"]), {
            "skill_loaded", "model_called", "nvidia_completed", "historical_run_data"})
        self.assertFalse(PROFILE["model_policy"]["live_configuration_checked"])
        self.assertIn("No model was called", PROFILE["model_policy"]["identity_note"])

    def test_human_jev_and_executor_are_separate_participants(self):
        participants = {item["id"]: item for item in PROFILE["participants"]}
        self.assertEqual(set(participants), {"scientist", "executor", "jev"})
        self.assertFalse(set(participants) & set(self.agents))
        self.assertEqual(participants["scientist"]["kind"], "human")
        self.assertEqual(participants["executor"]["kind"], "deterministic_application")
        self.assertEqual(participants["jev"]["kind"], "external_pilot")
        self.assertIn("None of the above", participants["jev"]["note"])
        self.assertIn("No registered harness skills, tool authority or automatic decision override", participants["jev"]["note"])

    def test_public_artifact_excludes_private_execution_material(self):
        self.assertFalse(PROFILE["source"]["instructions_embedded"])
        self.assertFalse(PROFILE["source"]["private_run_data_embedded"])
        self.assertEqual(set(PROFILE), {
            "schema_version", "profile_version", "snapshot_date", "scope", "source", "model_policy",
            "skill_categories", "skills", "agents", "participants", "interpretation_notes", "execution_evidence",
        })
        forbidden = {
            "api_key", "access_token", "refresh_token", "authorization", "headers", "password", "secret",
            "run", "run_id", "decisions", "case_snapshot", "hypothesis", "evidence", "artifacts",
            "source_records", "source_receipts", "request_body", "response_body", "provider_metadata",
            "patient_id", "patient_name", "sequence", "sequence_data", "instructions",
        }
        for item in objects(PROFILE):
            if isinstance(item, dict):
                self.assertFalse(set(key.lower() for key in item) & forbidden)
            elif isinstance(item, str):
                self.assertNotRegex(item, r"(?:sk-proj-|nvapi-|apikey_)[A-Za-z0-9_-]{12,}")
                self.assertNotRegex(item, r"(?:/Users/|/home/|127\.0\.0\.1|localhost:|BEGIN PRIVATE KEY)")
                if item.startswith(("http://", "https://")):
                    self.assertEqual(urlparse(item).hostname, "openai.com")
        for skill in PROFILE["skills"]:
            self.assertEqual(set(skill) - {"source_url", "external_plugin"}, {
                "id", "name", "version", "sha256", "origin", "description", "category", "eligible_roles", "instruction_path"})

    def test_source_provenance_matches_review_lock(self):
        self.assertEqual(set(LOCK["files"]), LOCKED_FILES)
        self.assertEqual({item["path"]: item["sha256"] for item in PROFILE["source"]["files"]}, LOCK["files"])
        for path, digest in LOCK["files"].items():
            self.assertFalse(Path(path).is_absolute())
            self.assertNotIn("..", Path(path).parts)
            self.assertRegex(digest, r"^[a-f0-9]{64}$")


class AuditedSourceRegeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("TEAM_TBD_PROFILE_SOURCE")
        candidate = Path(configured).expanduser() if configured else HERE.parent.parent / "rosalind-demo"
        if not candidate.is_dir():
            raise unittest.SkipTest(
                "Separate audited application source unavailable; set TEAM_TBD_PROFILE_SOURCE to enable source-lock and regeneration checks."
            )
        cls.source = candidate.resolve()

    def copy_locked_sources(self, target):
        for relative in LOCK["files"]:
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.source / relative, destination)

    def test_cli_regeneration_matches_published_bytes_and_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(HERE / "build_profiles.py"), "--source", str(self.source), "--output", temporary],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = Path(temporary) / "agent-profiles.json"
            self.assertEqual(json.loads(generated.read_text(encoding="utf-8")), PROFILE)
            self.assertEqual(generated.read_bytes(), PROFILE_PATH.read_bytes())

    def test_only_locked_sources_needed_and_environment_is_not_exported(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            self.copy_locked_sources(source)
            self.assertEqual({str(path.relative_to(source)) for path in source.rglob("*") if path.is_file()}, LOCKED_FILES)
            sentinels = {key: "test-only-private-sentinel-do-not-export" for key in (
                "OPENAI_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY", "JEV_API_KEY", "TEAM_TBD_MODEL",
            )}
            with patch.dict(os.environ, sentinels):
                generated = BUILDER.build(source, LOCK)
            self.assertEqual(generated, PROFILE)
            self.assertNotIn("test-only-private-sentinel", json.dumps(generated))

    def test_every_changed_locked_file_requires_review_even_prose_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            self.copy_locked_sources(source)
            for relative in LOCK["files"]:
                with self.subTest(source_file=relative):
                    path = source / relative
                    original = path.read_bytes()
                    # A Python comment or JSON whitespace changes no runtime policy.
                    # It must still invalidate the exact audited source snapshot.
                    suffix = b"\n# Documentation-only audit change.\n" if path.suffix == ".py" else b"\n "
                    path.write_bytes(original + suffix)
                    try:
                        with self.assertRaisesRegex(ValueError, "Source changed:"):
                            BUILDER.build(source, LOCK)
                    finally:
                        path.write_bytes(original)
            self.assertEqual(BUILDER.build(source, LOCK), PROFILE)


if __name__ == "__main__":
    unittest.main()
