"""Numerical anchors and input boundaries for actual runtime scientific analyses."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from app import analysis_tools as analysis
from app.cases import SourceIntegrityError


def test_catalog_is_case_scoped_and_returns_fresh_records():
    catalog = analysis.analysis_catalog("cd19-car-t")
    assert [item["id"] for item in catalog] == ["cd19-barcode-qc", "cd19-isoform-summary", "cd19-variant-splicing-discovery", "cd19-softmax-followup", "cd19-clinical-paired-endpoints", "cd19-ptbp1-surface-qpcr", "gse28460-paired-expression"]
    catalog[0]["title"] = "changed externally"
    assert analysis.analysis_catalog("cd19-car-t")[0]["title"] != "changed externally"
    with pytest.raises(analysis.AnalysisInputError):
        analysis.analyze_case("cd19-car-t", "alk-assay-extraction")
    with pytest.raises(analysis.AnalysisInputError):
        analysis.analyze_case("../../secrets", "cd19-barcode-qc")
    with pytest.raises(analysis.AnalysisInputError):
        analysis.analyze_case("cd19-car-t", "../../secrets")


def test_discovery_catalog_exposes_methods_without_computed_answers_or_alk():
    catalog = analysis.analysis_catalog("cart-discovery")
    assert [item["id"] for item in catalog] == ["cd19-barcode-qc", "cd19-isoform-summary", "bcma-sample-variant-qc", "cd19-variant-splicing-discovery", "cd19-softmax-followup", "cd19-clinical-paired-endpoints", "cd19-ptbp1-surface-qpcr", "gse28460-paired-expression"]
    assert all({"id", "title", "description"} <= set(item) for item in catalog)
    assert next(item for item in catalog if item["id"] == "cd19-softmax-followup")["followup_only"] is True
    assert all(item["input_sources"] for item in catalog[-4:])
    serialized = json.dumps(catalog)
    for answer in ("9527", "9,527", "Q38", "truncating", "10/41", "S5/S6"):
        assert answer not in serialized
    catalog[0]["title"] = "external mutation"
    assert analysis.analysis_catalog("cart-discovery")[0]["title"] != "external mutation"
    with pytest.raises(analysis.AnalysisInputError):
        analysis.analyze_case("cart-discovery", "alk-assay-extraction")


@pytest.mark.parametrize('source_case,recipe', [('cd19-car-t','cd19-barcode-qc'), ('cd19-car-t','cd19-isoform-summary'), ('bcma-gse164551','bcma-sample-variant-qc')])
def test_discovery_recipe_preserves_inputs_measurements_and_source_identity(source_case, recipe):
    original = analysis.analyze_case(source_case, recipe)
    discovered = analysis.analyze_case('cart-discovery', recipe)
    assert discovered['id'] == original['id']
    assert discovered['summary'] == original['summary']
    assert discovered['values']['source_case_id'] == source_case
    assert discovered['values']['case_id'] == 'cart-discovery'
    expected = {**original['values'], 'case_id':'cart-discovery', 'source_case_id':source_case}
    assert discovered['values'] == expected
    assert discovered['source']['sha256'] == analysis._hash_json(expected)
    assert discovered['source']['sha256'] != original['source']['sha256']
    assert discovered['values']['inference_performed'] is False
    for source in discovered['values']['input_sources']:
        assert hashlib.sha256((analysis.CASE_ROOT/source['path']).read_bytes()).hexdigest() == source['sha256']


def test_discovery_recomputes_from_raw_inputs_without_curated_case_answers(tmp_path, monkeypatch):
    root = tmp_path/'casepacks'
    shutil.copytree(analysis.CASE_ROOT/'sources/bcma', root/'sources/bcma')
    shutil.copyfile(analysis.CASE_ROOT/'MANIFEST.json', root/'MANIFEST.json')
    # There is deliberately no bcma-gse164551.json curated case packet.
    monkeypatch.setattr(analysis, 'CASE_ROOT', root)
    evidence = analysis.analyze_case('cart-discovery', 'bcma-sample-variant-qc')
    assert evidence['values']['sample_count'] == 8
    assert evidence['values']['source_case_id'] == 'bcma-gse164551'
    source = root/'sources/bcma/sample_manifest.tsv'
    source.write_bytes(source.read_bytes()+b'changed')
    with pytest.raises(SourceIntegrityError):
        analysis.analyze_case('cart-discovery', 'bcma-sample-variant-qc')


def test_cd19_barcode_join_reproduces_known_source_counts():
    evidence = analysis.analyze_case("cd19-car-t", "cd19-barcode-qc")
    values = evidence["values"]
    assert evidence["id"] == "ANALYSIS-CD19-QC"
    assert values["dna_variant_rows"] == 100135
    assert values["dna_rna_barcodes"] == 10295
    assert values["rna_rows"] == 19043
    assert values["rna_unique_barcodes"] == 9722
    assert values["joined_barcodes"] == 9527
    assert values["unmatched_rna_barcodes"] == 195
    assert values["explicit_unmutated_control_barcodes_without_variant_rows"] == 195
    assert values["unresolved_noncontrol_barcodes_without_variant_rows"] == 0
    assert values["explicit_unmutated_rows_by_replicate"] == {"1":195,"2":194}
    assert values["analysis_version"] == "1.1.0"
    assert values["replicate_rows"] == {"1": 9671, "2": 9372}
    assert values["total_reported_readcount"] == 21866465
    assert values["duplicate_barcode_replicate_keys"] == 0
    assert len(values["unmatched_examples"]) == 10
    assert "patient replicates" in evidence["summary"]


def test_isoform_analysis_retains_unassigned_counts_and_fixed_columns():
    evidence = analysis.analyze_case("cd19-car-t", "cd19-isoform-summary")
    values = evidence["values"]
    assert evidence["id"] == "ANALYSIS-CD19-ISOFORMS"
    assert values["parameters"]["selected_junction_columns"] == list(analysis.CD19_JUNCTION_COLUMNS)
    assert values["parameters"]["statistical_test"] is None
    assert values["parameters"]["variant_effect_estimation"] is False
    first, second = values["replicates"]
    assert first["reported_readcount"] == 10739439
    assert second["reported_readcount"] == 11127026
    assert first["rows_count_coverage_gap"] == 8021
    assert second["rows_count_coverage_gap"] == 7246
    assert first["unassigned_count_difference"] == 95712
    assert second["unassigned_count_difference"] == 76683
    assert first["rows_listed_exceed_readcount"] == second["rows_listed_exceed_readcount"] == 0
    assert [j["count"] for j in first["junctions"]] == [7335688, 1689848, 297594]
    assert [j["count"] for j in second["junctions"]] == [6316523, 3034767, 442146]
    assert first["junctions"][0]["ratio_to_reported_readcount"] == pytest.approx(7335688 / 10739439)
    assert "partial descriptive isoform fractions" in evidence["summary"]
    assert evidence["values"]["analysis_version"] == "1.1.0"


def test_alk_source_key_lookup_preserves_cells_and_precision():
    evidence = analysis.analyze_case("alk-l1196m", "alk-assay-extraction")
    values = evidence["values"]
    assert evidence["id"] == "ANALYSIS-ALK-ASSAY"
    assert values["source_key"] == "ALK_E23_C70A"
    assert values["amino_acid_change"] == "L1196M"
    assert values["source_row"] == 1331
    assert [r["classification"] for r in values["drugs"]] == ["Resistance", "Resistance", "Sensitive"]
    assert [r["resistance_score"] for r in values["drugs"]] == ["7.7445209372741202", "11.4128982028548", "0.23868446278806199"]
    assert [r["score_cell"] for r in values["drugs"]] == ["E1331", "G1331", "I1331"]
    assert values["fitness_score"] == "-0.106903137030655"
    assert values["source_classifications_differ"] is True
    assert "clinical efficacy" in values["limitations"][0]


def test_bcma_identity_timing_and_read_fraction_are_qualified():
    evidence = analysis.analyze_case("bcma-gse164551", "bcma-sample-variant-qc")
    values = evidence["values"]
    assert evidence["id"] == "ANALYSIS-BCMA-QC"
    assert values["independent_patients"] == 1
    assert values["sample_count"] == 8
    assert values["duplicate_sample_ids"] == values["duplicate_gsm_ids"] == 0
    assert values["corrected_aliases"][0]["matrix_alias"] == "S6"
    assert values["corrected_aliases"][1]["matrix_alias"] == "S5"
    assert "depleted" in values["baseline_note"]
    assert "two weeks after the second infusion" in values["genomic_sample_timing"]
    assert values["variant_source_line"] == 438
    assert values["variant"]["HGVSp_Short"] == "p.Q38*"
    assert values["tumor_alt_read_fraction"] == pytest.approx(10 / 41)
    assert all(values["depth_checks"].values())
    assert values["truncating_variant"] is True
    assert values["missense_pair_model_eligible"] is False
    assert values["parameters"]["raw_h5_reconciliation_performed"] is False
    assert values["parameters"]["copy_number_inference_performed"] is False


def test_derived_values_hash_and_input_provenance_reproduce():
    first = analysis.analyze_case("alk-l1196m", "alk-assay-extraction")
    second = analysis.analyze_case("alk-l1196m", "alk-assay-extraction")
    assert first == second
    assert first["kind"] == "derived"
    raw = json.dumps(first["values"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    assert hashlib.sha256(raw).hexdigest() == first["source"]["sha256"]
    for source in first["values"]["input_sources"]:
        assert hashlib.sha256((analysis.CASE_ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
        assert source["locator"]
    assert first["values"]["inference_performed"] is False


def test_changed_source_blocks_before_analysis(tmp_path, monkeypatch):
    root = tmp_path / "casepacks"
    source_dir = root / "sources/bcma"
    source_dir.mkdir(parents=True)
    shutil.copyfile(analysis.CASE_ROOT / "MANIFEST.json", root / "MANIFEST.json")
    source = analysis.CASE_ROOT / "sources/bcma/case.json"
    (source_dir / "case.json").write_bytes(source.read_bytes() + b" ")
    monkeypatch.setattr(analysis, "CASE_ROOT", root)
    with pytest.raises(SourceIntegrityError, match="do not match"):
        analysis.analyze_case("bcma-gse164551", "bcma-sample-variant-qc")


def test_changed_source_is_rechecked_on_next_call(tmp_path, monkeypatch):
    root = tmp_path / "casepacks"
    shutil.copytree(analysis.CASE_ROOT / "sources/bcma", root / "sources/bcma")
    shutil.copyfile(analysis.CASE_ROOT / "MANIFEST.json", root / "MANIFEST.json")
    monkeypatch.setattr(analysis, "CASE_ROOT", root)
    analysis.analyze_case("bcma-gse164551", "bcma-sample-variant-qc")
    source = root / "sources/bcma/sample_manifest.tsv"
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(SourceIntegrityError):
        analysis.analyze_case("bcma-gse164551", "bcma-sample-variant-qc")


def test_file_size_limit_applies_before_read(monkeypatch):
    monkeypatch.setattr(analysis, "MAX_FILE_BYTES", 10)
    with pytest.raises(analysis.AnalysisInputError, match="byte limit"):
        analysis.analyze_case("cd19-car-t", "cd19-barcode-qc")


def test_decompression_and_row_limits_reject_oversized_tables(monkeypatch):
    monkeypatch.setattr(analysis, "MAX_EXPANDED_BYTES", 50)
    with pytest.raises(analysis.AnalysisInputError, match="Expanded table"):
        analysis._tsv(gzip.compress(b"column\n" + b"long-value\n" * 30), compressed=True)
    monkeypatch.setattr(analysis, "MAX_EXPANDED_BYTES", 1000)
    monkeypatch.setattr(analysis, "MAX_TABLE_ROWS", 1)
    with pytest.raises(analysis.AnalysisInputError, match="row limit"):
        analysis._tsv(b"column\na\nb\n")


def test_malformed_rows_and_negative_counts_are_not_silently_skipped():
    with pytest.raises(analysis.AnalysisInputError, match="Malformed"):
        analysis._tsv(b"a\tb\n1\n", required=("a", "b"))
    with pytest.raises(analysis.AnalysisInputError, match="duplicated"):
        analysis._tsv(b"a\ta\n1\t2\n", required=("a",))
    with pytest.raises(analysis.AnalysisInputError, match="nonnegative"):
        analysis._nonnegative_int("-1", "readcount")
