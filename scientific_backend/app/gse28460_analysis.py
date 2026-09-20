"""Pinned paired microarray analysis of Ana's GSE28460 agent-input package.

Conventional-treatment childhood B-ALL is contextual evidence for a CAR-T case,
not a CAR-T replication cohort. Data-curator panels are separate from the user's
original hypothesis. No source/evaluator/neighboring result files are consulted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import warnings

import numpy as np
from scipy.stats import wilcoxon

RECIPE_ID = "gse28460-paired-expression"
VERSION = "1.0.0"
GEO_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE28460"
DEFAULT_ROOT = "/home/ubuntu/ana-workspace/datasets/agent_access/GSE28460"
EXPECTED_PROBES, EXPECTED_SAMPLES, EXPECTED_PATIENTS = 54675, 98, 49
BOOTSTRAPS, BOOTSTRAP_SEED = 10000, 28460
CONTEXT_GENES = ("CD19", "PTBP1", "PTBP2")
PINS = {
    "TASK.md": (4024, "3b94daac4b3b84436497540dc90d56923218b2b1eb4dc46f89e3b607f9ce84f2"),
    "expression_log2.tsv.gz": (27110984, "cc5751784aed33a0ccf018fcc3e297f75f9a55ca0f75cf679e8dfd56e5128de5"),
    "hypothesis.txt": (300, "d15fd3808365deabeb7e9f3beffc49c51327412b8da96a295df7201632a85788"),
    "hypothesis_gene_sets.json": (553, "ceba9079fa126feb59fc4206491f12afe2a13bf303bfbb673be9099d98514558"),
    "patient_pairs.csv": (1646, "89440a01306c1557434fd0b25025fc2fb7bbe7a6cf0bdc6aaed6d5f220a94ec1"),
    "preview_original_signal.csv": (12720, "6cc5887554d72c046123e7f33ba67bc88dbf60158cd1c5c66368e2559dbd39a7"),
    "probe_annotation.tsv": (3622845, "a81e3e5d2b1114fd2797e82331cd93eaf1e1257acf425d57393d06245d04bc0a"),
    "samples.csv": (10737, "3a02e5f5f784d022b121585b397ece0cc5624266c8112dc41aa722c90075067f"),
}
LIMITATIONS = [
    "GSE28460 contains diagnosis/relapse samples after conventional ALL treatment, not CAR-T exposure; it cannot establish a CAR-T resistance mechanism or validate the separate CD19 CAR-T patient cohort.",
    "All 49 patients relapsed. Diagnosis is a within-patient baseline, not a cured/non-relapsing control; this design does not estimate relapse risk or treatment efficacy.",
    "Already-normalized deposited microarray signal was log2-transformed upstream. No raw array processing, re-normalization, imputation or RNA-seq count modeling is performed here.",
    "Bulk probe/gene expression does not measure exon skipping, intron retention, pathway activity, mutation, surface antigen availability or CAR binding/killing.",
    "The two fixed 12-gene panels are data-curator operational definitions, not exhaustive pathways or externally validated clinical signatures. Their support thresholds are benchmark conventions.",
    "Cell composition, prior treatment, subtype and technical effects can explain expression differences. Early/late-relapse metadata disagreements are not resolved or used for primary subgrouping.",
    "Patient bootstrap, leave-one-pair-out and probe-aggregation sensitivity are internal checks, not independent biological validation. Wilcoxon location interpretation assumes symmetric paired differences.",
    "Only unambiguous single-symbol legacy probe mappings are used. Alternative mappings, isoforms and probe-specific biology are not inferred.",
]


class PairedExpressionError(ValueError):
    pass


def _sha(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(value).hexdigest()


def source_manifest():
    return [{"name": name, "path": "ana-agent-access/GSE28460/" + name,
             "root": "ana_agent", "relative_path": "GSE28460/" + name,
             "sha256": digest, "bytes": size, "url": GEO_URL,
             "provenance": "Locally prepared agent-input derivative of public GEO GSE28460; hash pins this prepared file, not an original GEO download"}
            for name, (size, digest) in PINS.items()]


def catalog_entry():
    return {"id": RECIPE_ID, "title": "GSE28460: 49 historical B-ALL diagnosis/relapse pairs",
            "description": "Verify all 98 log2 microarrays and 49 patient pairings; test fixed curator cell-cycle/DNA-repair panels, summarize CD19/PTBP1/PTBP2 expression, and explore paired gene expression with multiplicity correction. Conventional-treatment context only; not CAR-T, splicing or target-retention evidence.",
            "input_sources": source_manifest(),
            "prerequisites": ["All eight prepared public inputs match frozen byte counts and SHA256 pins.",
                              "Complete identity-matched pairs, single-symbol probe mapping, finite existing-log2 measurements; no model-supplied paths or parameters."]}


def _load(root):
    root = Path(root or os.getenv("TEAM_TBD_GSE28460_ROOT", DEFAULT_ROOT)).resolve()
    data = {}
    for name, (size, expected) in PINS.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size or size > 32_000_000:
            raise PairedExpressionError("Pinned paired-expression source is missing or changed: " + name)
        raw = path.read_bytes()
        if len(raw) != size or _sha(raw) != expected:
            raise PairedExpressionError("Paired-expression source hash mismatch: " + name)
        data[name] = raw
    return data


def _table(raw, delimiter, required):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter=delimiter)
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or not set(required).issubset(fields):
        raise PairedExpressionError("Missing or duplicate metadata columns")
    rows = []
    for row in reader:
        if len(rows) >= 60000 or None in row or any(v is None for v in row.values()):
            raise PairedExpressionError("Malformed or oversized metadata table")
        rows.append(row)
    return fields, rows


def _matrix(raw):
    ids, rows = [], []
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as handle:
        header = handle.readline(30000).decode().rstrip("\r\n").split("\t")
        samples = header[1:]
        if header[0] != "probe_id" or len(samples) != EXPECTED_SAMPLES or len(set(samples)) != len(samples):
            raise PairedExpressionError("Microarray sample columns are missing, duplicated or unexpected")
        consumed = 0
        for line in handle:
            consumed += len(line)
            if consumed > 96_000_000 or len(line) > 30000 or len(rows) >= EXPECTED_PROBES:
                raise PairedExpressionError("Microarray input exceeds the fixed analysis bounds")
            cells = line.decode().rstrip("\r\n").split("\t")
            if len(cells) != len(samples)+1 or not cells[0]:
                raise PairedExpressionError("Malformed expression row")
            try:
                values = np.asarray(cells[1:], dtype=np.float64)
            except ValueError as exc:
                raise PairedExpressionError("Nonnumeric microarray intensity") from exc
            if not np.isfinite(values).all():
                raise PairedExpressionError("Missing or nonfinite microarray intensity; no imputation")
            ids.append(cells[0]); rows.append(values)
    if len(rows) != EXPECTED_PROBES or len(set(ids)) != len(ids):
        raise PairedExpressionError("Probe rows are missing, duplicated or unexpected")
    return ids, samples, np.stack(rows)


def _qualified(data):
    probes, columns, matrix = _matrix(data["expression_log2.tsv.gz"])
    _, samples = _table(data["samples.csv"], ",", ("sample_id", "patient_id", "timepoint", "cohort", "lineage"))
    _, pairs = _table(data["patient_pairs.csv"], ",", ("patient_id", "diagnosis", "relapse"))
    if len(samples) != EXPECTED_SAMPLES or len({s["sample_id"] for s in samples}) != len(samples):
        raise PairedExpressionError("Duplicate or unexpected sample metadata count")
    sample_map = {s["sample_id"]: s for s in samples}
    if set(sample_map) != set(columns):
        raise PairedExpressionError("Expression columns do not exactly match sample metadata")
    if len(pairs) != EXPECTED_PATIENTS or len({p["patient_id"] for p in pairs}) != len(pairs):
        raise PairedExpressionError("Duplicate or unexpected patient pair count")
    paired_samples = []
    for pair in pairs:
        for time in ("diagnosis", "relapse"):
            sid = pair[time]
            sample = sample_map.get(sid)
            if not sample or sample["patient_id"] != pair["patient_id"] or sample["timepoint"] != time:
                raise PairedExpressionError("Explicit patient pairing conflicts with sample identity or timepoint")
            if sample["cohort"] != "GSE28460" or sample["lineage"] != "Precursor-B-ALL":
                raise PairedExpressionError("Unexpected cohort or lineage")
            paired_samples.append(sid)
    if len(set(paired_samples)) != EXPECTED_SAMPLES or set(paired_samples) != set(columns):
        raise PairedExpressionError("A sample is reused, unpaired or absent from the matrix")
    _, annotation = _table(data["probe_annotation.tsv"], "\t", ("probe_id", "gene_symbol", "mapping_status"))
    if len(annotation) != len(probes) or len({a["probe_id"] for a in annotation}) != len(annotation) or {a["probe_id"] for a in annotation} != set(probes):
        raise PairedExpressionError("Probe annotation must uniquely match every measured probe")
    index = {probe: n for n, probe in enumerate(probes)}
    gene_rows = defaultdict(list)
    excluded = Counter()
    for row in annotation:
        symbol = row["gene_symbol"].strip()
        if row["mapping_status"] == "single_symbol" and symbol and "///" not in symbol and ";" not in symbol and " " not in symbol:
            gene_rows[symbol].append(index[row["probe_id"]])
        else:
            excluded[row["mapping_status"] or "unlabelled"] += 1
    fields, preview = _table(data["preview_original_signal.csv"], ",", ("probe_id", *columns))
    if set(fields) != {"probe_id", *columns} or not preview:
        raise PairedExpressionError("Original-scale preview sample columns differ")
    preview_ids = []
    max_error = 0.
    for row in preview:
        if row["probe_id"] not in index or row["probe_id"] in preview_ids:
            raise PairedExpressionError("Original-scale preview has missing/duplicate probes")
        preview_ids.append(row["probe_id"])
        try:
            original = np.array([float(row[c]) for c in columns])
        except ValueError as exc:
            raise PairedExpressionError("Invalid original-scale preview") from exc
        if not np.isfinite(original).all() or np.any(original <= 0):
            raise PairedExpressionError("Original-scale preview must be positive and finite")
        error = float(np.max(np.abs(np.log2(original)-matrix[index[row["probe_id"]]])))
        max_error = max(max_error, error)
        if error > 1e-6:
            raise PairedExpressionError("Expression does not match the already-log2 source preview")
    panels = json.loads(data["hypothesis_gene_sets.json"])
    if panels.get("version") != "1.0":
        raise PairedExpressionError("Unexpected fixed-panel definition version")
    definitions = {name: panels.get(name) for name in ("cell_cycle", "dna_repair")}
    if any(not isinstance(genes, list) or len(genes) != 12 or len(set(genes)) != 12 or any(not isinstance(g, str) or not g for g in genes) for genes in definitions.values()):
        raise PairedExpressionError("Expected two fixed panels with 12 unique gene symbols each")
    column_index = {sid: i for i, sid in enumerate(columns)}
    diagnosis = np.array([column_index[p["diagnosis"]] for p in pairs])
    relapse = np.array([column_index[p["relapse"]] for p in pairs])
    qc = {"patients": len(pairs), "samples": len(columns), "probes": len(probes),
          "complete_pairs": True, "pairing_method": "Explicit patient ID and sample ID; never positional column order",
          "diagnosis_column_indices_0based": diagnosis.tolist(), "relapse_column_indices_0based": relapse.tolist(),
          "single_symbol_probes": sum(len(v) for v in gene_rows.values()), "single_symbol_genes": len(gene_rows),
          "excluded_probe_counts": dict(excluded), "missing_values": 0,
          "matrix_log2_min": float(matrix.min()), "matrix_log2_max": float(matrix.max()),
          "scale_check": {"original_scale_preview_probes": len(preview), "sample_values": len(preview)*len(columns),
                          "maximum_absolute_log2_error": max_error, "second_log_transform_applied": False},
          "pair_order": [p["patient_id"] for p in pairs], "pair_map": pairs,
          "covariates_not_adjusted": ["cell composition", "prior treatment", "subtype", "batch"],
          "early_late_subgrouping_performed": False}
    return probes, matrix, gene_rows, diagnosis, relapse, definitions, qc


def _bh(pvalues):
    values = np.asarray(pvalues, dtype=float)
    if not len(values):
        return []
    order = np.argsort(values, kind="stable")
    ranked = values[order] * len(values) / np.arange(1,len(values)+1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1].clip(0,1)
    result = np.empty(len(values)); result[order] = adjusted
    return [float(v) for v in result]


def _test(differences):
    differences = np.asarray(differences, dtype=float)
    nonzero = differences[differences != 0]
    if not len(nonzero):
        return {"statistic": 0., "p_two_sided": 1., "method": "all_zero_no_change", "zero_method": "wilcox", "zero_pairs": len(differences)}
    exact = len(nonzero) == len(differences) and len(np.unique(np.abs(nonzero))) == len(nonzero)
    method = "exact" if exact else "asymptotic"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        result = wilcoxon(differences, alternative="two-sided", zero_method="wilcox", method=method, correction=False)
    if not math.isfinite(result.pvalue):
        raise PairedExpressionError("Nonfinite paired test")
    return {"statistic": float(result.statistic), "p_two_sided": float(result.pvalue), "method": method,
            "zero_method": "wilcox", "zero_pairs": int(np.sum(differences == 0)), "continuity_correction": False}


def _interval(scores):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    medians = np.median(scores[rng.integers(0,len(scores),(BOOTSTRAPS,len(scores)))],axis=1)
    return [float(x) for x in np.quantile(medians,[.025,.975])]


def _panel_results(definitions, genes, differences, pair_ids):
    lookup = {g:i for i,g in enumerate(genes)}
    results, all_scores = {}, {}
    for name, requested in definitions.items():
        included = [g for g in requested if g in lookup]
        base = {"requested_genes": requested, "included_genes": included,
                "excluded_genes": [g for g in requested if g not in lookup], "coverage": len(included),
                "minimum_required": 9, "biological_replicates": len(pair_ids)}
        results[name] = base
        if len(included) < 9:
            base.update(status="unevaluable", reason="Fewer than 9 fixed panel genes have qualified single-symbol probes")
            continue
        scores = np.median(differences[[lookup[g] for g in included]],axis=0)
        all_scores[name] = scores
        base.update(status="computed", median_log2_score=float(np.median(scores)),
                    fraction_positive=float(np.mean(scores>0)), increased_patients=int(np.sum(scores>0)),
                    decreased_patients=int(np.sum(scores<0)), zero_patients=int(np.sum(scores==0)),
                    bootstrap_95_percent_ci=_interval(scores), wilcoxon=_test(scores),
                    patient_scores=[{"patient_id": p, "median_gene_difference_log2": float(s)} for p,s in zip(pair_ids,scores)])
    tested = [name for name,value in results.items() if value["status"] == "computed"]
    # Preserve the planned family of two tests: an unevaluable panel contributes p=1.
    adjusted = _bh([results[name].get("wilcoxon", {}).get("p_two_sided", 1.) for name in definitions])
    for name, q in zip(definitions,adjusted):
        if name not in tested:
            continue
        r = results[name]
        r.update(bh_adjusted_p=q, bh_family_size=2,
                 operational_support=bool(r["median_log2_score"]>0 and q<.05 and r["bootstrap_95_percent_ci"][0]>0))
    supported = sum(bool(r.get("operational_support")) for r in results.values())
    joint = "supported" if supported==2 else "partial_support" if supported else "unable_to_evaluate" if len(tested)<2 else "no_support"
    return results, all_scores, joint


def _gene_statistics(genes, differences, gene_rows, probes):
    active = np.any(differences != 0,axis=1)
    pvalues = np.ones(len(genes)); stats = np.zeros(len(genes))
    if active.any():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            test = wilcoxon(differences[active], axis=1, alternative="two-sided", zero_method="wilcox", method="asymptotic", correction=False)
        if not np.isfinite(test.pvalue).all():
            raise PairedExpressionError("Nonfinite exploratory paired-gene test")
        pvalues[active], stats[active] = test.pvalue, test.statistic
    qvalues = _bh(pvalues)
    records = []
    for i,gene in enumerate(genes):
        d = differences[i]
        records.append({"gene": gene, "probe_ids": [probes[j] for j in gene_rows[gene]], "probes": len(gene_rows[gene]),
                        "pairs": len(d), "median_log2_difference": float(np.median(d)), "mean_log2_difference": float(np.mean(d)),
                        "fraction_positive": float(np.mean(d>0)), "wilcoxon_statistic": float(stats[i]),
                        "p_two_sided": float(pvalues[i]), "bh_adjusted_p": qvalues[i]})
    return records


def _tsv_bytes(rows, fields):
    buffer = io.StringIO(); writer = csv.DictWriter(buffer,fieldnames=fields,delimiter="\t",lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({k:",".join(r[k]) if isinstance(r[k],list) else r[k] for k in fields})
    return buffer.getvalue().encode()


def _svg(panels):
    # Pure SVG: source IDs and captions are fixed recipe text, no raw HTML input.
    width, height = 860,420
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#fff"/><g font-family="Arial,sans-serif" fill="#173322">',
           '<text x="32" y="32" font-size="21">Diagnosis to relapse: fixed-panel expression changes</text>',
           '<text x="32" y="56" font-size="13">GSE28460 · conventional-treatment B-ALL · each dot is one patient pair</text>']
    scores=[s["median_gene_difference_log2"] for p in panels.values() for s in p.get("patient_scores",[])]
    limit=max(.25,max([abs(v) for v in scores] or [.25])*1.1)
    x=lambda v: 450+float(v)/limit*345
    parts.append('<line x1="450" y1="85" x2="450" y2="330" stroke="#adb8ab" stroke-dasharray="4 4"/>')
    for i,(name,panel) in enumerate(panels.items()):
        y=140+130*i
        parts.append(f'<text x="32" y="{y-32}" font-size="18">{name.replace("_"," ").title()}</text>')
        if panel["status"]!="computed":continue
        for j,row in enumerate(panel["patient_scores"]):
            parts.append(f'<circle cx="{x(row["median_gene_difference_log2"]):.2f}" cy="{y+(j%7-3)*4}" r="3" fill="#43985a" fill-opacity=".7"/>')
        lo,hi=panel["bootstrap_95_percent_ci"]; median=panel["median_log2_score"]
        parts.append(f'<line x1="{x(lo):.2f}" y1="{y+28}" x2="{x(hi):.2f}" y2="{y+28}" stroke="#173322" stroke-width="4"/>')
        parts.append(f'<circle cx="{x(median):.2f}" cy="{y+28}" r="5" fill="#173322"/>')
        parts.append(f'<text x="32" y="{y+58}" font-size="12">Median {median:.3f};95% patient-bootstrap CI [{lo:.3f},{hi:.3f}];BH q={panel["bh_adjusted_p"]:.3g}</text>')
    for tick in np.linspace(-limit,limit,5):
        parts.append(f'<line x1="{x(tick):.2f}" y1="337" x2="{x(tick):.2f}" y2="343" stroke="#173322"/>')
        parts.append(f'<text x="{x(tick):.2f}" y="357" font-size="11" text-anchor="middle">{tick:.2f}</text>')
    parts.append('<text x="270" y="378" font-size="14">Relapse minus diagnosis (panel log2-expression score)</text>')
    parts.append('<text x="32" y="407" font-size="12">Expression association only: not pathway activity, clinical benefit, splicing or CAR-T resistance.</text></g></svg>')
    return "".join(parts).encode()


def analyze(dataset_root=None, *, case_id="cd19-car-t", output_dir=None):
    data = _load(dataset_root)
    probes, matrix, gene_rows, diagnosis, relapse, definitions, qc = _qualified(data)
    genes = sorted(gene_rows)
    median_expression = np.stack([np.median(matrix[gene_rows[g]],axis=0) for g in genes])
    mean_expression = np.stack([np.mean(matrix[gene_rows[g]],axis=0) for g in genes])
    differences = median_expression[:,relapse]-median_expression[:,diagnosis]
    alternate = mean_expression[:,relapse]-mean_expression[:,diagnosis]
    panels,scores,joint = _panel_results(definitions,genes,differences,qc["pair_order"])
    sensitivity_panels,_,sensitivity_joint = _panel_results(definitions,genes,alternate,qc["pair_order"])
    leave_out={}
    for name,score in scores.items():
        medians=[float(np.median(np.delete(score,i))) for i in range(len(score))]
        leave_out[name]={"omitted_patient_count":len(score), "minimum_median_log2_score":min(medians),
                         "maximum_median_log2_score":max(medians), "all_leave_one_out_medians_positive":all(x>0 for x in medians),
                         "largest_median_change_patient": qc["pair_order"][int(np.argmax(np.abs(np.array(medians)-np.median(score))))],
                         "scope":"Median sign/influence only; does not repeat the full bootstrap/BH support rule."}
    gene_records = _gene_statistics(genes,differences,gene_rows,probes)
    table_fields=("gene","probe_ids","probes","pairs","median_log2_difference","mean_log2_difference","fraction_positive","wilcoxon_statistic","p_two_sided","bh_adjusted_p")
    table = _tsv_bytes(gene_records,table_fields)
    record_map={r["gene"]:r for r in gene_records}
    context=[]
    for gene in CONTEXT_GENES:
        if gene not in record_map:
            context.append({"gene":gene,"status":"unmapped"});continue
        i=genes.index(gene); record=record_map[gene]
        context.append({**record,"status":"computed", "bootstrap_95_percent_ci":_interval(differences[i]),
                        "patient_differences":[{"patient_id":p,"relapse_minus_diagnosis_log2":float(v)} for p,v in zip(qc["pair_order"],differences[i])],
                        "scope":"Secondary expression context only; multiplicity-adjusted within the complete exploratory mapped-gene family, not a splice or CAR-T endpoint."})
    up=sorted((r for r in gene_records if r["median_log2_difference"]>0),key=lambda r:(r["bh_adjusted_p"],-r["median_log2_difference"],r["gene"]))[:12]
    down=sorted((r for r in gene_records if r["median_log2_difference"]<0),key=lambda r:(r["bh_adjusted_p"],r["median_log2_difference"],r["gene"]))[:12]
    score_rows=[{"patient_id":pid,**{name:float(score[i]) for name,score in scores.items()}} for i,pid in enumerate(qc["pair_order"])]
    score_table = _tsv_bytes(score_rows,("patient_id",*scores))
    svg=_svg(panels)
    outputs={"gene-paired-results.tsv":table,"panel-patient-scores.tsv":score_table,"paired-panel-summary.svg":svg}
    output_records=[{"name":name,"sha256":_sha(raw),"bytes":len(raw),"written":output_dir is not None} for name,raw in outputs.items()]
    if output_dir is not None:
        out=Path(output_dir).resolve()
        source=Path(dataset_root or os.getenv("TEAM_TBD_GSE28460_ROOT",DEFAULT_ROOT)).resolve()
        if out.is_relative_to(source) or source.is_relative_to(out):
            raise PairedExpressionError("Output directory must not overlap the read-only input directory")
        out.mkdir(parents=True,exist_ok=True)
        for name,raw in outputs.items():
            dest=out/name
            if dest.is_symlink() or (dest.exists() and dest.read_bytes()!=raw):
                raise PairedExpressionError("Refusing to overwrite different or linked output artifact")
            if not dest.exists():dest.write_bytes(raw)
    values={"analysis_id":RECIPE_ID,"analysis_version":VERSION,"case_id":case_id,"study_accession":"GSE28460",
            "clinical_context":"Childhood precursor B-ALL after conventional ALL treatment; no CAR-T exposure established",
            "assay":"Affymetrix GPL570 bulk expression microarray; deposited normalized signal already log2-transformed",
            "input_sources":source_manifest(),"qc":qc,
            "curator_supplied_hypothesis":{"wording":data["hypothesis.txt"].decode(),"source":"hypothesis.txt","sha256":PINS["hypothesis.txt"][1],
                                          "ownership":"Data-curator supplied companion hypothesis; does not replace the user's original hypothesis"},
            "fixed_panel_results":panels,"joint_panel_result":joint,
            "support_rule":"Each panel: >=9/12 mapped genes, positive median score, BH-adjusted two-sided p<0.05, patient-bootstrap 95% interval entirely above zero. Both panels required for joint support; an unevaluable panel is counted as p=1 in the planned two-test family.",
            "parameters":{"contrast":"relapse minus diagnosis within each explicit patient pair", "gene_aggregation":"median log2 intensity across single-symbol probes per gene/sample",
                          "panel_score":"median of within-patient gene-level differences across fixed panel genes", "second_log_transform":False,"imputation":False,"new_normalization":False,
                          "bootstrap":{"unit":"patient pair","replicates":BOOTSTRAPS,"seed":BOOTSTRAP_SEED,"interval":"percentile95%;numpy quantile linear interpolation"},
                          "panel_tests":"two-sided Wilcoxon;exact if no zero/tied absolute differences, otherwise asymptotic tie-corrected;wilcox zero handling;no continuity correction;BH family 2"},
            "sensitivity":{"mean_probe_aggregation":{"panels":sensitivity_panels,"joint_result":sensitivity_joint},"leave_one_patient_out":leave_out},
            "cd19_expression_context":context,
            "exploratory_transcriptome":{"tested_genes":len(genes),"unit":"unambiguous legacy symbol, all mapped genes; median probe aggregation",
                                         "test":"paired two-sided Wilcoxon asymptotic, tie-corrected, wilcox zero handling;all-zero genes p=1;BH over all tested genes",
                                         "q_below_0_05":sum(r["bh_adjusted_p"]<.05 for r in gene_records),"top_increased":up,"top_decreased":down,
                                         "complete_table_sha256":_sha(table),"selection_note":"Top 12 in each median-effect direction, ranked by BH q then effect; exploratory, not primary panel tests."},
            "artifacts":output_records,"limitations":LIMITATIONS,"inference_performed":True,"independent_validation":False,
            "splicing_measured":False,"car_t_exposure_established":False,"raw_pipeline_reproduced":False}
    summary=f"New paired-expression analysis of {EXPECTED_PATIENTS} conventional-treatment B-ALL patients ({EXPECTED_SAMPLES} arrays). Fixed curator panels: {joint.replace('_',' ')}. CD19/PTBP1/PTBP2 are secondary expression context only; this cohort does not test CAR-T exposure, splicing or recognition."
    return {"id":"ANALYSIS-GSE28460-PAIRED","title":"Historical B-ALL paired expression: 49 patients, conventional treatment", "kind":"derived", "summary":summary,
            "source":{"name":"Runtime paired analysis of Ana's prepared public GSE28460 inputs","url":GEO_URL,
                      "locator":"All 98 sample columns paired by explicit patient IDs; frozen prepared-input hashes and method in values","sha256":_sha(values)},"values":values}
