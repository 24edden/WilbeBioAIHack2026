"""Synthetic structures test provenance and numerical contracts, not biology."""
import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest
from Bio.SeqUtils import seq3

from app import molecular_interpretation as m


def cif(sequence, positions, *, metric=True, metric_kind="pLDDT", bad_metric=None):
    from test_structure_preview import cif as base
    header = base().decode().split("ATOM 1")[0]
    rows = [f"ATOM {i} C CA . {seq3(aa).upper()} A 1 {i} ? {p}.0 {p%7}.0 {p%3}.0 1.0 88.0 1"
            for i, (aa, p) in enumerate(zip(sequence, positions), 1)]
    text = header + "\n".join(rows) + "\n#\n"
    if metric:
        text += ("loop_\n_ma_qa_metric.id\n_ma_qa_metric.type\n_ma_qa_metric.mode\n" + f"1 '{metric_kind}' local\n#\n" +
                 "loop_\n_ma_qa_metric_local.model_id\n_ma_qa_metric_local.label_asym_id\n_ma_qa_metric_local.label_seq_id\n_ma_qa_metric_local.label_comp_id\n_ma_qa_metric_local.metric_id\n_ma_qa_metric_local.metric_value\n")
        for i, aa in enumerate(sequence, 1):
            val = bad_metric if bad_metric is not None and i == 1 else .8 if i % 3 else .4
            text += f"1 A {i} {seq3(aa).upper()} 1 {val}\n"
        text += "#\n"
    return text.encode()


@pytest.fixture
def molecular_run(tmp_path):
    root = tmp_path.resolve()
    sequence = "ACDEFGHIKLMNPQR"
    common = list(range(4)) + list(range(8, 15))
    records, artifacts = [], []
    for label, seq, positions in [("reference", sequence, range(15)), ("deletion", sequence[:4]+sequence[8:], common)]:
        directory = root / "artifacts" / "action-fixture" / label
        directory.mkdir(parents=True)
        data = cif(seq, positions)
        (directory / "prediction.cif").write_bytes(data)
        sha = m._hash(data)
        seqsha = m._hash(seq.encode())
        artifact = {"name": label+".cif", "label": label, "sha256": sha, "request_id": "request-"+label,
                    "url": f"/api/runs/run-fixture/artifacts/action-fixture/{label}/prediction.cif"}
        request = {"polymers": [{"id": "A", "molecule_type": "protein", "sequence": seq}],
                   "recycling_steps": 3, "sampling_steps": 50, "diffusion_samples": 1, "step_scale": 1.638, "output_format": "mmcif"}
        job = {"status": "completed", "http_status": 200, "request_id": artifact["request_id"], "model": "mit/boltz2",
               "sequence_sha256": seqsha, "request_sha256": m._hash(request), "artifacts": [artifact]}
        (directory / "request.json").write_text(json.dumps(request))
        (directory / "job.json").write_text(json.dumps(job))
        artifacts.append(artifact)
        records.append({"label": label, "status": "completed", "model": "mit/boltz2", "request_id": artifact["request_id"],
                        "sequence_sha256": seqsha, "sequence_length": len(seq), "confidence_score": .55})
    values = {"scope": "exploratory_public_isoform_structure", "predictions": records,
              "mapping": {"extracellular_residues": [100,114], "deleted_canonical_residues": [104,107]},
              "input_sources": [{"sha256": "a"*64, "name": "synthetic source", "url": "https://example.org/synthetic"}],
              "artifact_hashes": [a["sha256"] for a in artifacts], "limitations": ["Synthetic numerical fixture"]}
    record = {"id": "prediction-fixture", "kind": "prediction", "values": values, "source": {"sha256": m._hash(values)}}
    run = {"id": "run-fixture", "evidence": [record], "followup_operations": [
        {"id": "followup-fixture", "kind": "bionemo_public_structure", "result_status": "completed",
         "evidence_id": record["id"], "artifacts": artifacts}], "decisions": [{"version": 1, "summary": "Original decision"}]}
    return run, root


def mutate_artifact(run, root, data):
    operation = run["followup_operations"][0]
    a = operation["artifacts"][0]
    path = root / "artifacts/action-fixture/reference/prediction.cif"
    path.write_bytes(data)
    a["sha256"] = m._hash(data)
    values = run["evidence"][0]["values"]
    values["artifact_hashes"][0] = a["sha256"]
    run["evidence"][0]["source"]["sha256"] = m._hash(values)


def test_verified_sequences_and_request_settings_preserve_run(molecular_run):
    run, root = molecular_run
    before = copy.deepcopy(run)
    audit = m.audit_molecular_evidence(run, root)
    assert audit["status"] == "completed"
    assert run == before
    assert audit == m.audit_molecular_evidence(run, root)
    inventory = audit["sequence_inventory"]
    assert [s["length"] for s in inventory] == [15,11]
    assert all(s["role"] == "target" and s["verified"] and s["target_retention_established"] is False for s in inventory)
    assert all(s["id"] == "sequence-" + m._hash(s["sequence"].encode())[:20] for s in inventory)
    comparison = audit["comparisons"][0]
    assert comparison["settings_comparison"]["matched"] is True
    assert comparison["predictions"][0]["request_audit"]["settings"]["sampling_steps"] == 50
    assert comparison["predictions"][0]["request_audit"]["model_version"] == "not recorded in this job"
    assert comparison["alignment_sensitivity"]["fits"][0]["rmsd_angstrom"] < 1e-10
    assert audit["audit_sha256"] == m._hash({k:v for k,v in audit.items() if k != "audit_sha256"})


def test_confidence_is_explicit_native_metric_not_b_factor(molecular_run):
    run, root = molecular_run
    result = m.audit_molecular_evidence(run, root)
    confidence = result["comparisons"][0]["predictions"][0]["confidence"]
    assert confidence["source_field"] == "_ma_qa_metric_local.metric_value"
    assert confidence["max"] == .8  # B factor is88 in this fixture, never substituted.
    assert confidence["scale_ambiguous"] is True
    assert confidence["normalization_applied"] is False
    sensitivity = result["comparisons"][0]["alignment_sensitivity"]["fits"][-1]
    assert sensitivity["raw_metric_cutoff"] == .7 and sensitivity["scale_ambiguous"] is True
    assert len(sensitivity["reference_positions_1based"]) == sensitivity["selected_residues"]


def test_explicit_normalized_metric_is_supported(molecular_run):
    run, root = molecular_run
    mutate_artifact(run, root, cif("ACDEFGHIKLMNPQR", range(15), metric_kind="pLDDT in [0,1]"))
    confidence = m.audit_molecular_evidence(run, root)["comparisons"][0]["predictions"][0]["confidence"]
    assert confidence["status"] == "verified" and confidence["scale_ambiguous"] is False


def test_missing_confidence_does_not_infer_from_b_factors(molecular_run):
    run, root = molecular_run
    mutate_artifact(run, root, cif("ACDEFGHIKLMNPQR", range(15), metric=False))
    comparison = m.audit_molecular_evidence(run, root)["comparisons"][0]
    assert comparison["predictions"][0]["confidence"]["status"] == "unavailable"
    assert comparison["alignment_sensitivity"]["fits"][0]["rmsd_angstrom"] < 1e-10
    assert not any("raw_metric_cutoff" in f for f in comparison["alignment_sensitivity"]["fits"])


@pytest.mark.parametrize("bad", ["nan", "inf", "-0.1", "101"])
def test_nonfinite_or_invalid_confidence_is_not_used(molecular_run, bad):
    run, root = molecular_run
    mutate_artifact(run, root, cif("ACDEFGHIKLMNPQR", range(15), bad_metric=bad))
    comparison = m.audit_molecular_evidence(run, root)["comparisons"][0]
    assert comparison["predictions"][0]["confidence"]["status"] == "unavailable"


def test_tampered_structure_cannot_supply_a_sequence(molecular_run):
    run, root = molecular_run
    path = root / "artifacts/action-fixture/reference/prediction.cif"
    path.write_bytes(path.read_bytes() + b"#corruption\n")
    result = m.audit_molecular_evidence(run, root)
    assert result["status"] == "partial"
    assert [s["label"] for s in result["sequence_inventory"]] == ["deletion"]
    assert result["comparisons"][0]["alignment_sensitivity"]["status"] == "unavailable"


def test_wrong_sequence_hash_cannot_supply_a_sequence(molecular_run):
    run, root = molecular_run
    record = run["evidence"][0]
    record["values"]["predictions"][0]["sequence_sha256"] = "b"*64
    record["source"]["sha256"] = m._hash(record["values"])
    result = m.audit_molecular_evidence(run, root)
    assert result["status"] == "partial"
    assert [s["label"] for s in result["sequence_inventory"]] == ["deletion"]


def test_unaccepted_evidence_hash_blocks_every_artifact(molecular_run):
    run, root = molecular_run
    run["evidence"][0]["values"]["scope"] = "altered"
    result = m.audit_molecular_evidence(run, root)
    assert result["status"] == "partial" and result["sequence_inventory"] == []


def test_missing_files_remain_unavailable(molecular_run):
    run, _ = molecular_run
    result = m.audit_molecular_evidence(run)
    assert result["status"] == "partial" and not result["sequence_inventory"]
    assert result["comparisons"][0]["predictions"][0]["reason"] == "Saved artifact files were not supplied"


def test_exported_hash_map_works_without_runtime_paths(molecular_run):
    run, root = molecular_run
    paths = {a["sha256"]: root / "artifacts/action-fixture" / a["label"] / "prediction.cif" for a in run["followup_operations"][0]["artifacts"]}
    result = m.audit_molecular_evidence(run, artifact_paths=paths)
    assert result["status"] == "completed"


@pytest.mark.parametrize("suffix", ["../other", "action-fixture/../reference/prediction.cif", "%2e%2e/private", "action-fixture\\private"])
def test_traversal_locator_is_rejected(molecular_run, suffix):
    run, root = molecular_run
    run["followup_operations"][0]["artifacts"][0]["url"] = "/api/runs/run-fixture/artifacts/"+suffix
    result = m.audit_molecular_evidence(run, root)
    assert [s["label"] for s in result["sequence_inventory"]] == ["deletion"]


def test_other_run_locator_is_not_followed(molecular_run):
    run, root = molecular_run
    run["followup_operations"][0]["artifacts"][0]["url"] = "/api/runs/other/artifacts/action-fixture/reference/prediction.cif"
    result = m.audit_molecular_evidence(run, root)
    assert [s["label"] for s in result["sequence_inventory"]] == ["deletion"]


def test_symlink_artifact_is_rejected(molecular_run):
    run, root = molecular_run
    path = root / "artifacts/action-fixture/reference/prediction.cif"
    target = path.with_suffix(".original")
    path.rename(target)
    path.symlink_to(target)
    result = m.audit_molecular_evidence(run, root)
    assert [s["label"] for s in result["sequence_inventory"]] == ["deletion"]


def test_modified_request_does_not_claim_matched_settings(molecular_run):
    run, root = molecular_run
    path = root / "artifacts/action-fixture/reference/request.json"
    request = json.loads(path.read_text()); request["sampling_steps"] = 100
    path.write_text(json.dumps(request))
    comparison = m.audit_molecular_evidence(run, root)["comparisons"][0]
    assert comparison["status"] == "verified_artifacts"
    assert comparison["settings_comparison"]["status"] == "unavailable"
    assert "hash mismatch" in comparison["predictions"][0]["request_audit"]["reason"]


def test_actual_different_submitted_settings_are_reported(molecular_run):
    run, root = molecular_run
    base = root / "artifacts/action-fixture/reference"
    request = json.loads((base/"request.json").read_text()); request["sampling_steps"] = 100
    (base/"request.json").write_text(json.dumps(request))
    job = json.loads((base/"job.json").read_text()); job["request_sha256"] = m._hash(request)
    (base/"job.json").write_text(json.dumps(job))
    comparison = m.audit_molecular_evidence(run, root)["comparisons"][0]
    assert comparison["settings_comparison"]["status"] == "different_submitted_settings"
    assert comparison["settings_comparison"]["matched"] is False


def test_mismatched_mapping_does_not_align_arbitrary_residues(molecular_run):
    run, root = molecular_run
    record = run["evidence"][0]
    record["values"]["mapping"]["deleted_canonical_residues"] = [105,108]
    record["source"]["sha256"] = m._hash(record["values"])
    comparison = m.audit_molecular_evidence(run, root)["comparisons"][0]
    assert comparison["status"] == "verified_artifacts"
    assert comparison["alignment_sensitivity"]["status"] == "unavailable"


def test_no_biology_in_empty_run():
    result = m.audit_molecular_evidence({"id": "any-other-study", "evidence": [], "followup_operations": []})
    assert result["status"] == "no_molecular_evidence"
    assert result["sequence_inventory"] == result["comparisons"] == []


def test_kabsch_is_rigid_motion_invariant_and_rejects_degeneracy():
    points = np.array([[0.,0,0],[2,0,0],[1,3,0],[1,2,4]])
    rotation = np.array([[0.,-1,0],[1,0,0],[0,0,1]])
    assert m._fit(points, points @ rotation + 15)["rmsd_angstrom"] < 1e-10
    with pytest.raises(ValueError, match="degenerate"):
        m._fit(np.zeros((4,3)),np.zeros((4,3)))


@pytest.mark.parametrize("field, value", [("request_id", "different-request"), ("http_status", 202), ("model", "different-model"), ("sequence_sha256", "c"*64)])
def test_job_identity_mismatch_does_not_verify_request(molecular_run, field, value):
    run, root = molecular_run
    path = root / "artifacts/action-fixture/reference/job.json"
    job = json.loads(path.read_text()); job[field] = value
    path.write_text(json.dumps(job))
    prediction = m.audit_molecular_evidence(run, root)["comparisons"][0]["predictions"][0]
    assert prediction["status"] == "verified"  # Accepted coordinate identity remains independently verified.
    assert prediction["request_audit"]["status"] == "unavailable"


def test_invalid_cif_returns_partial_without_crashing(molecular_run):
    run, root = molecular_run
    mutate_artifact(run, root, b"data_invalid\n_entry.id invalid\n")
    result = m.audit_molecular_evidence(run, root)
    assert result["status"] == "partial"
    assert [s["label"] for s in result["sequence_inventory"]] == ["deletion"]


def test_explicit_normalized_metric_rejects_scores_above_one(molecular_run):
    run, root = molecular_run
    mutate_artifact(run, root, cif("ACDEFGHIKLMNPQR", range(15), metric_kind="pLDDT in [0,1]", bad_metric="80"))
    confidence = m.audit_molecular_evidence(run, root)["comparisons"][0]["predictions"][0]["confidence"]
    assert confidence["status"] == "unavailable"
    assert "declared normalized range" in confidence["reason"]
