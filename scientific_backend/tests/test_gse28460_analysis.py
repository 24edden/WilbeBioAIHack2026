"""Synthetic paired microarrays verify numerical/QC contracts, never biology."""
import copy
import csv
import gzip
import io
import json
from pathlib import Path

import numpy as np
import pytest

from app import gse28460_analysis as g


def _csv(rows, fields, delimiter=","):
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=fields,delimiter=delimiter,lineterminator="\n")
    w.writeheader();w.writerows(rows)
    return out.getvalue().encode()


@pytest.fixture
def input_package(tmp_path,monkeypatch):
    root=tmp_path/"input";root.mkdir()
    patients=["p0","p1","p2","p3"]
    # Pair rows, metadata and expression columns intentionally use different orders.
    columns=["r2","d0","r0","d3","r1","d2","d1","r3"]
    panels={"version":"1.0","cell_cycle":[f"C{i}" for i in range(12)],"dna_repair":[f"D{i}" for i in range(12)]}
    genes=panels["cell_cycle"]+panels["dna_repair"]+["CD19","PTBP1","PTBP2"]
    sample_rows=[{"sample_id":time[0]+str(i),"patient_id":f"p{i}","timepoint":time,"cohort":"GSE28460","lineage":"Precursor-B-ALL"} for i in [1,3,0,2] for time in ["relapse","diagnosis"]]
    pair_rows=[{"patient_id":f"p{i}","diagnosis":f"d{i}","relapse":f"r{i}"} for i in [3,0,2,1]]
    annotation=[]; matrix=[]
    for i,gene in enumerate(genes):
        probe=f"probe{i}"
        annotation.append({"probe_id":probe,"gene_symbol":gene,"mapping_status":"single_symbol"})
        values={sid:5+i*.01+(int(sid[1])+1)*.1*(1 if sid.startswith("r") else 0) for sid in columns}
        matrix.append({"probe_id":probe,**values})
    annotation.extend([{"probe_id":"ambiguous","gene_symbol":"X///Y","mapping_status":"multiple_symbols"},{"probe_id":"missing","gene_symbol":"","mapping_status":"missing"}])
    matrix.extend([{"probe_id":p,**{c:6. for c in columns}} for p in ["ambiguous","missing"]])
    raw={"TASK.md":b"Input metadata; no runtime instructions.\n", "hypothesis.txt":b"Curator panel hypothesis, distinct from scientist question.\n",
         "hypothesis_gene_sets.json":json.dumps(panels).encode(),
         "samples.csv":_csv(sample_rows,sample_rows[0]), "patient_pairs.csv":_csv(pair_rows,pair_rows[0]),
         "probe_annotation.tsv":_csv(annotation,annotation[0],"\t"),
         "expression_log2.tsv.gz":gzip.compress(_csv(matrix,["probe_id",*columns],"\t"),mtime=0),
         "preview_original_signal.csv":_csv([{"probe_id":r["probe_id"],**{c:2**r[c] for c in columns}} for r in matrix[:2]],["probe_id",*columns])}
    for name,data in raw.items():(root/name).write_bytes(data)
    monkeypatch.setattr(g,"PINS",{name:(len(data),g._sha(data)) for name,data in raw.items()})
    monkeypatch.setattr(g,"EXPECTED_PROBES",len(matrix));monkeypatch.setattr(g,"EXPECTED_SAMPLES",8);monkeypatch.setattr(g,"EXPECTED_PATIENTS",4)
    monkeypatch.setattr(g,"BOOTSTRAPS",1000)
    return root,raw


def _repin(root,name,data,monkeypatch):
    (root/name).write_bytes(data)
    monkeypatch.setitem(g.PINS,name,(len(data),g._sha(data)))


def test_exact_patient_pairing_not_column_position_and_curator_scope(input_package):
    root,_=input_package
    record=g.analyze(root)
    values=record["values"]
    assert values["qc"]["pair_order"] == ["p3","p0","p2","p1"]
    panel=values["fixed_panel_results"]["cell_cycle"]
    assert [s["median_gene_difference_log2"] for s in panel["patient_scores"]] == pytest.approx([.4,.1,.3,.2])
    assert panel["median_log2_score"] == pytest.approx(.25)
    assert values["qc"]["excluded_probe_counts"] == {"multiple_symbols":1,"missing":1}
    assert values["qc"]["scale_check"]["second_log_transform_applied"] is False
    assert values["inference_performed"] is True and values["car_t_exposure_established"] is False
    assert values["splicing_measured"] is False and values["independent_validation"] is False
    assert "does not replace" in values["curator_supplied_hypothesis"]["ownership"]
    assert record["source"]["sha256"] == g._sha(values)


def test_source_tamper_is_rejected_before_parsing(input_package):
    root,_=input_package
    path=root/"hypothesis.txt"; path.write_text("changed")
    with pytest.raises(g.PairedExpressionError,match="missing or changed"):
        g.analyze(root)


def test_source_same_size_tamper_is_rejected(input_package):
    root,_=input_package
    path=root/"hypothesis.txt";data=path.read_bytes();path.write_bytes(b"X"+data[1:])
    with pytest.raises(g.PairedExpressionError,match="hash mismatch"):
        g.analyze(root)


@pytest.mark.parametrize("damage",["same_sample","wrong_patient","wrong_timepoint"])
def test_pair_identity_damage_is_rejected(input_package,monkeypatch,damage):
    root,raw=input_package
    _,pairs=g._table(raw["patient_pairs.csv"],",",("patient_id",))
    if damage=="same_sample":pairs[0]["relapse"]=pairs[0]["diagnosis"]
    elif damage=="wrong_patient":pairs[0]["patient_id"]="another"
    else:pairs[0]["diagnosis"],pairs[0]["relapse"]=pairs[0]["relapse"],pairs[0]["diagnosis"]
    _repin(root,"patient_pairs.csv",_csv(pairs,pairs[0]),monkeypatch)
    with pytest.raises(g.PairedExpressionError,match="pairing conflicts"):
        g.analyze(root)


def test_duplicate_metadata_sample_is_rejected(input_package,monkeypatch):
    root,raw=input_package
    _,samples=g._table(raw["samples.csv"],",",("sample_id",))
    samples[0]["sample_id"]=samples[1]["sample_id"]
    _repin(root,"samples.csv",_csv(samples,samples[0]),monkeypatch)
    with pytest.raises(g.PairedExpressionError,match="Duplicate"):
        g.analyze(root)


def test_double_log_transform_is_detected(input_package,monkeypatch):
    root,raw=input_package
    decoded=gzip.decompress(raw["expression_log2.tsv.gz"])
    fields,rows=g._table(decoded,"\t",("probe_id",))
    for r in rows:
        for c in fields[1:]:r[c]=str(np.log2(float(r[c])))
    _repin(root,"expression_log2.tsv.gz",gzip.compress(_csv(rows,fields,"\t")),monkeypatch)
    with pytest.raises(g.PairedExpressionError,match="already-log2"):
        g.analyze(root)


@pytest.mark.parametrize("bad",["nan","inf",""])
def test_nonfinite_or_missing_measurement_has_no_imputation(input_package,monkeypatch,bad):
    root,raw=input_package
    fields,rows=g._table(gzip.decompress(raw["expression_log2.tsv.gz"]),"\t",("probe_id",))
    rows[0][fields[1]]=bad
    _repin(root,"expression_log2.tsv.gz",gzip.compress(_csv(rows,fields,"\t")),monkeypatch)
    with pytest.raises(g.PairedExpressionError,match="intensity"):
        g.analyze(root)


def test_ambiguous_mapping_not_added_to_gene_panel(input_package,monkeypatch):
    root,raw=input_package
    fields,rows=g._table(raw["probe_annotation.tsv"],"\t",("probe_id",))
    for r in rows[:4]:r["mapping_status"]="multiple_symbols";r["gene_symbol"] += "///X"
    _repin(root,"probe_annotation.tsv",_csv(rows,fields,"\t"),monkeypatch)
    panel=g.analyze(root)["values"]["fixed_panel_results"]["cell_cycle"]
    assert panel["status"]=="unevaluable" and panel["coverage"]==8
    assert len(panel["excluded_genes"])==4 and "patient_scores" not in panel


def test_bootstrap_reproducible_and_patients_are_units():
    scores=np.array([1.,2,3,4,5])
    first=g._interval(scores)
    assert first==g._interval(scores)
    assert first[0]<=3<=first[1]
    assert g._interval(np.ones(4)) == [1.,1.]


def test_all_zero_signed_rank_returns_no_change():
    result=g._test([0.,0,0,0])
    assert result["p_two_sided"]==1. and result["method"]=="all_zero_no_change"


def test_ties_and_zeros_use_explicit_approximation():
    result=g._test([0.,1,1,2,-2])
    assert result["method"]=="asymptotic" and result["zero_pairs"]==1
    assert result["zero_method"]=="wilcox" and 0<=result["p_two_sided"]<=1


def test_bh_known_values_and_unsorted_order():
    assert g._bh([.03,.001,.04,.02]) == pytest.approx([.04,.004,.04,.04])
    assert g._bh([1.,1.]) == [1.,1.]


def test_gene_results_use_all_genes_as_exploratory_family(input_package):
    root,_=input_package
    result=g.analyze(root)["values"]
    exploratory=result["exploratory_transcriptome"]
    assert exploratory["tested_genes"]==27
    assert {r["gene"] for r in result["cd19_expression_context"]}=={"CD19","PTBP1","PTBP2"}
    assert all(r["pairs"]==4 for r in result["cd19_expression_context"])
    assert all(r["probes"]==1 for r in result["cd19_expression_context"])


def test_output_artifacts_complete_and_reproducible(input_package,tmp_path):
    root,_=input_package
    before={p.name:p.read_bytes() for p in root.iterdir()}
    out=tmp_path/"outputs"
    result=g.analyze(root,output_dir=out)
    again=g.analyze(root,output_dir=out)
    assert result==again
    assert before=={p.name:p.read_bytes() for p in root.iterdir()}
    for a in result["values"]["artifacts"]:
        assert a["written"] and g._sha((out/a["name"]).read_bytes())==a["sha256"]
    fields,rows=g._table((out/"gene-paired-results.tsv").read_bytes(),"\t",("gene",))
    assert len(rows)==27
    assert len((out/"panel-patient-scores.tsv").read_text().splitlines())==5
    assert (out/"paired-panel-summary.svg").read_text().startswith("<svg")


def test_output_cannot_touch_input_directory(input_package):
    root,_=input_package
    with pytest.raises(g.PairedExpressionError,match="overlap"):
        g.analyze(root,output_dir=root/"new-subdirectory")
    assert not (root/"new-subdirectory").exists()


def test_existing_different_output_is_not_overwritten(input_package,tmp_path):
    root,_=input_package
    out=tmp_path/"outputs";out.mkdir();p=out/"gene-paired-results.tsv";p.write_text("retain this")
    with pytest.raises(g.PairedExpressionError,match="overwrite"):
        g.analyze(root,output_dir=out)
    assert p.read_text()=="retain this"


def test_no_substitution_when_dataset_missing(tmp_path):
    with pytest.raises(g.PairedExpressionError,match="missing"):
        g.analyze(tmp_path/"absent")


def test_default_catalog_has_no_outcome_or_evaluator_path():
    catalog=g.catalog_entry()
    assert catalog["id"]==g.RECIPE_ID
    assert "supported" not in catalog["description"]
    assert len(catalog["input_sources"])==8
    assert not any("evaluator" in s["path"] for s in catalog["input_sources"])
