"""Evidence integrity and science boundaries that affect the demo's conclusions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from app.cases import CASE_ROOT, SourceIntegrityError, get_case, list_cases, verify_sources


class CasePackTests(unittest.TestCase):
    def test_source_tampering_blocks_analysis(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "packs"
            shutil.copytree(CASE_ROOT / "sources", path / "sources")
            shutil.copyfile(CASE_ROOT / "MANIFEST.json", path / "MANIFEST.json")
            target = path / "sources/cd19/CD19_CAR_T_.txt"
            target.write_bytes(target.read_bytes() + b"changed")
            with self.assertRaises(SourceIntegrityError):
                verify_sources(path)

    def test_brev_hypothesis_preserved_exactly(self):
        case = get_case("cd19-car-t")
        original = (CASE_ROOT / "sources/cd19/CD19_CAR_T_.txt").read_bytes()
        self.assertEqual(case["hypothesis"].encode(), original)
        self.assertEqual(hashlib.sha256(original).hexdigest(), "03918c91a6905f28249ae9d4b5069548e5b18d10e5543a11c6293a8bea395a88")
        self.assertEqual(case["demo_decision"]["rd_handoff"]["modeling"]["status"], "blocked")
        arm = case["demo_decision"]["rd_handoff"]["candidates"][0]
        self.assertEqual(arm["type"], "experimental_arm")
        self.assertEqual(arm["status"], "planned")
        self.assertIn("Not supplied", arm["exact_sequences"])

    def test_cd19_library_does_not_become_patient_evidence(self):
        case = get_case("cd19-car-t")
        self.assertIn("Unresolved", case["demo_decision"]["assessment"])
        values = {e["id"]: e["values"] for e in case["evidence"]}
        self.assertEqual(values["CD19-01"]["rows"], 19043)
        self.assertEqual(values["CD19-01"]["distinct_barcodes"], 9722)
        self.assertEqual(values["CD19-02"]["joined_barcodes"] + values["CD19-02"]["unmatched_rna_barcodes"], 9722)
        self.assertIn("195", case["evidence"][1]["summary"])

    def test_alk_labels_and_precision_match_pinned_source(self):
        case = get_case("alk-l1196m")
        drugs = case["evidence"][1]["values"]["drugs"]
        self.assertEqual([d["classification"] for d in drugs], ["Resistance", "Resistance", "Sensitive"])
        self.assertEqual(drugs[0]["resistance_score"], "7.7445209372741202")
        self.assertEqual(drugs[2]["score_cell"], "I1331")

    def test_bcma_timing_and_truncation_are_retained(self):
        case = get_case("bcma-gse164551")
        values = case["evidence"][2]["values"]
        self.assertEqual(values["HGVSp_Short"], "p.Q38*")
        self.assertEqual(values["t_alt_count"], "10")
        self.assertIn("post-treatment", case["evidence"][2]["summary"])
        self.assertEqual(case["demo_decision"]["rd_handoff"]["modeling"]["status"], "blocked")
        self.assertEqual(case["evidence"][1]["values"]["corrected_samples"][0]["matrix_alias"], "S6")

    def test_all_curated_claims_resolve_and_no_synthetic_measurements(self):
        self.assertEqual(len(list_cases()), 4)
        for card in list_cases():
            case = get_case(card["id"])
            known = {e["id"] for e in case["evidence"]}
            self.assertTrue(all(e["kind"] != "synthetic" for e in case["evidence"]))
            for claim in case["demo_decision"]["claims"]:
                self.assertTrue(set(claim["evidence_ids"]).issubset(known))
                self.assertTrue(claim["evidence_ids"])

    def test_derived_packets_reproduce_from_source_bytes(self):
        spec = importlib.util.spec_from_file_location("case_builder", CASE_ROOT / "build_cases.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, contents in module.generated_files().items():
            self.assertEqual((CASE_ROOT / name).read_text(), contents, name)

    def test_path_input_is_not_a_case(self):
        with self.assertRaises(KeyError):
            get_case("../../private")


if __name__ == "__main__":
    unittest.main()
