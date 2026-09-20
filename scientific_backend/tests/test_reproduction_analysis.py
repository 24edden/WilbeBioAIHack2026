"""Source measurement anchors, experimental units and failure boundaries."""
import copy
import hashlib
import json
import shutil

import pytest

from app import analysis_tools as base
from app import reproduction_analysis as replay
from app.cases import SourceIntegrityError


def test_clinical_pairs_preserve_disjoint_assay_membership_and_exact_tests():
    evidence = base.analyze_case("cd19-car-t", "cd19-clinical-paired-endpoints")
    values = evidence["values"]
    retention, ptbp1, ptbp2 = values["endpoints"]
    assert [x["independent_patient_pairs"] for x in values["endpoints"]] == [9, 9, 9]
    assert [x["increased"] for x in values["endpoints"]] == [7, 5, 7]
    assert retention["wilcoxon"]["one_sided_relapse_greater_p"] == 10 / 512
    assert ptbp1["wilcoxon"]["one_sided_relapse_greater_p"] == 77 / 512
    assert ptbp2["wilcoxon"]["one_sided_relapse_greater_p"] == 19 / 512
    assert retention["wilcoxon"]["two_sided_p"] == 20 / 512
    retention_ids = {x["patient_id"] for x in retention["pairs"]}
    expression_ids = {x["patient_id"] for x in ptbp1["pairs"]}
    assert retention_ids - expression_ids == {"13"}
    assert expression_ids - retention_ids == {"16"}
    assert values["all_endpoint_patient_sets_equal"] is False
    assert retention["pairs"][0]["relapse_minus_screening"] == pytest.approx(0.76844372644049497 - 0.43076923076923102)
    assert retention["pairs"][0]["screening_source_cells"] == "Fig. 1b!A2:C2"
    assert values["parameters"]["literature_targets_used"] is False
    assert "0.009" not in json.dumps(values)


def test_surface_replay_uses_paired_intensities_and_biological_replicates():
    evidence = base.analyze_case("cd19-car-t", "cd19-ptbp1-surface-qpcr")
    surface = evidence["values"]["surface_staining"]
    by_key = {(x["cell_line"], x["biological_replicate"]): x for x in surface["replicates"]}
    r = by_key[("MHHCALL4", "replicate 1")]
    assert (r["siSCR"], r["siPTBP1"]) == (11736, 10306)
    assert r["percent_reduction"] == pytest.approx(100 * (1 - 10306 / 11736))
    assert by_key[("P493-6", "replicate 2")]["percent_reduction"] == pytest.approx(100 * (1 - 7663 / 13454))
    assert [x["biological_replicates"] for x in surface["cell_line_summaries"]] == [2, 2]
    assert surface["new_hypothesis_test"] is None
    assert surface["fcs_regating_performed"] is False


def test_qpcr_recomputes_from_wells_preserving_nested_unit_and_all_assays():
    values = base.analyze_case("cd19-car-t", "cd19-ptbp1-surface-qpcr")["values"]
    qpcr = values["qpcr"]
    assert qpcr["technical_wells"] == 169
    assert qpcr["sample_target_groups"] == 64
    assert len(qpcr["sample_ids"]) == 8
    assert len(qpcr["paired_contrasts"]) == 28
    assert qpcr["source_cached_means_used"] is False
    groups = {(x["sample"], x["target"]): x for x in qpcr["technical_group_summaries"]}
    target = ("MHHCALL4_siPTBP1_rep1", "CD19_e2i2")
    assert groups[target]["n_technical_wells"] == 2
    record = next(x for x in qpcr["paired_contrasts"] if (x["sample"], x["target"]) == target)
    assert record["fold_vs_control"] == pytest.approx(1.5676229983925845)
    assert all("Fig. S9c!G" in x["source_cell"] for g in groups.values() for x in g["wells"])
    assert values["wet_lab_executed"] is False
    assert any("amplification efficiencies" in x for x in values["limitations"])


@pytest.mark.parametrize("recipe", [x["id"] for x in replay.CATALOG])
def test_fresh_read_integrity_canonical_hash_and_discovery_source_identity(tmp_path, monkeypatch, recipe):
    root = tmp_path / "casepacks"
    shutil.copytree(base.CASE_ROOT / "sources/cd19-released-endpoints", root / "sources/cd19-released-endpoints")
    shutil.copyfile(base.CASE_ROOT / "MANIFEST.json", root / "MANIFEST.json")
    monkeypatch.setattr(base, "CASE_ROOT", root)
    a = base.analyze_case("cd19-car-t", recipe)
    b = base.analyze_case("cart-discovery", recipe)
    assert b["values"]["source_case_id"] == "cd19-car-t"
    assert b["source"]["sha256"] == base._hash_json(b["values"])
    assert a == base.analyze_case("cd19-car-t", recipe)
    assert a["summary"] == b["summary"]
    source = root / a["values"]["input_sources"][0]["path"]
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(SourceIntegrityError):
        base.analyze_case("cd19-car-t", recipe)
    # Even changing the manifest cannot silently revise an immutable recipe.
    manifest = json.loads((root / "MANIFEST.json").read_text())
    for row in manifest["source_files"]:
        if row["path"] == str(source.relative_to(root)):
            row.update(bytes=source.stat().st_size, sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (root / "MANIFEST.json").write_text(json.dumps(manifest))
    with pytest.raises(SourceIntegrityError, match="recipe pin"):
        base.analyze_case("cd19-car-t", recipe)


def test_invalid_measurements_and_unqualified_exact_test_fail_instead_of_imputing():
    with pytest.raises(base.AnalysisInputError):
        replay._number("NaN", "cell")
    with pytest.raises(base.AnalysisInputError):
        replay._number(None, "cell")
    with pytest.raises(base.AnalysisInputError, match="zero/tie"):
        replay._paired_summary([("1", "Screening", 1, "a"), ("1", "Relapse", 2, "b"), ("2", "Screening", 2, "c"), ("2", "Relapse", 3, "d")], "test", "arbitrary")
    with pytest.raises(base.AnalysisInputError, match="Duplicate patient"):
        replay._paired_summary([("1", "Screening", 1, "a"), ("1", "Screening", 2, "b")], "test", "arbitrary")
    rows, _ = replay._sheet("released_surface_staining", "Fig. 6d-f ")
    rows[2]["B"] = "0"
    with pytest.raises(base.AnalysisInputError, match="denominator"):
        replay._surface(rows)


def test_qpcr_rejects_duplicate_physical_wells_and_missing_references():
    rows, _ = replay._sheet("released_qpcr_wells", "Fig. S9c")
    duplicate = copy.deepcopy(rows)
    duplicate[3]["B"] = duplicate[2]["B"]
    with pytest.raises(base.AnalysisInputError, match="duplicate physical well"):
        replay._qpcr(duplicate)
    missing = {key: value for key, value in rows.items() if value.get("D") != "GAPDH"}
    with pytest.raises(base.AnalysisInputError, match="missing target"):
        replay._qpcr(missing)


def test_new_followups_are_not_eligible_for_old_source_snapshots():
    from app.discovery_planning import planning_options
    from app.followups import approved_catalog
    from app.cases import get_case
    case = get_case("cd19-car-t")
    case["source_manifest"] = [r for r in case["source_manifest"] if "cd19-released-endpoints" not in r["path"]]
    options = planning_options(case, case["evidence"], approved_catalog(case["id"]), "configured")
    selected = [x for x in options if x["id"] in {r["id"] for r in replay.CATALOG}]
    assert len(selected) == 2
    assert all(x["readiness"] == "needs_inputs" for x in selected)
    assert all(len(x["input_sources"]) == 2 for x in selected)
