"""Bounded numerical replay of released clinical and PTBP1 assay measurements.

Inputs are lossless, cell-addressed Source Data extracts, not literature
conclusions or evaluator outputs. These recipes neither refit the reporter
model nor reconstruct fluorescence events, RNA alignments or clinical causes.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
import re
import statistics

VERSION = "1.0.0"
PINS = {
    "released_clinical_retention": ("clinical-retention.json", "411264188340ad2503d5fa7805b33c8fae562b190cd431a7e98f0c73b36008b8"),
    "released_clinical_expression": ("clinical-rbp-expression.json", "05622439704937f2ef701a2bac4597440db62d200989efeb9c517c2b9d8b5cc6"),
    "released_surface_staining": ("surface-staining.json", "7924e11909edbe2013836b378ba60d7f5d14bdb82bdc68774753b4e9c2c46945"),
    "released_qpcr_wells": ("qpcr-wells.json", "5cba914d84bb21f782f947027fb55f62e88eef9749336f9ef201eedc2409eebd"),
}
CATALOG = [
    {"id": "cd19-clinical-paired-endpoints", "title": "Released paired clinical endpoints", "description": "Recompute screening/relapse CD19 intron-retention and PTBP1/PTBP2 expression contrasts from cell-addressed released measurements. Qualify complete patient pairs separately for each assay; report all differences and exact paired tests without substituting gene expression for splicing."},
    {"id": "cd19-ptbp1-surface-qpcr", "title": "PTBP1 perturbation: surface staining and junction qPCR", "description": "Recompute surface-CD19 intensity ratios and junction-specific ΔΔCt from released individual wells in two cell lines. Retain biological versus technical replicates, source cells, reference-gene assumptions, negative controls and measured-versus-inferred boundaries."},
]
for _recipe, _keys in zip(CATALOG, [("released_clinical_retention", "released_clinical_expression"), ("released_surface_staining", "released_qpcr_wells")]):
    _recipe["input_sources"] = [{"path": "sources/cd19-released-endpoints/" + PINS[key][0], "sha256": PINS[key][1]} for key in _keys]


def _error(message):
    from .analysis_tools import AnalysisInputError
    return AnalysisInputError(message)


def _sheet(key, expected_name):
    from .analysis_tools import _load_source
    raw, source = _load_source(key)
    if source["sha256"] != PINS[key][1]:
        from .cases import SourceIntegrityError
        raise SourceIntegrityError("Released endpoint source differs from immutable recipe pin")
    doc = json.loads(raw)
    if doc.get("format_version") != "1.0.0" or doc.get("sheet") != expected_name:
        raise _error("Released worksheet identity/version does not match the recipe")
    if not re.fullmatch(r"[0-9a-f]{64}", doc.get("original_workbook_sha256", "")):
        raise _error("Released worksheet has no valid original-workbook digest")
    cells = doc.get("cells", [])
    if not cells or len(cells) > 5000:
        raise _error("Released worksheet cell limit exceeded or sheet is empty")
    rows = defaultdict(dict)
    for item in cells:
        match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,4})", item.get("cell", ""))
        if not match:
            raise _error("Malformed worksheet cell address")
        col, row = match[1], int(match[2])
        if col in rows[row]:
            raise _error("Duplicate worksheet cell address")
        # A formula's cached output is not silently accepted as a measurement.
        if item.get("formula") is not None:
            raise _error("Formula-bearing source cells require separate qualification")
        rows[row][col] = item.get("value")
    source.update({"locator": expected_name + "; exact source cells retained in results", "original_workbook": doc["original_workbook"], "original_workbook_sha256": doc["original_workbook_sha256"], "measurement_layer": "released source cells; upstream instrument/read preprocessing not rerun"})
    return dict(rows), source


def _number(value, label, minimum=None, maximum=None):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise _error("Nonnumeric measurement at " + label) from exc
    if not math.isfinite(number) or (minimum is not None and number < minimum) or (maximum is not None and number > maximum):
        raise _error("Out-of-range measurement at " + label)
    return number


def _headers(rows, expected):
    if rows.get(1) != expected:
        raise _error("Released worksheet headers differ from the qualified recipe")


def _paired_summary(records, endpoint, units):
    from scipy.stats import wilcoxon
    patients = defaultdict(dict)
    omitted = []
    for patient, stage, value, locator in records:
        if stage not in {"Screening", "Relapse"}:
            omitted.append({"patient": patient, "stage": stage, "source_cells": locator, "reason": "outside prespecified screening/relapse contrast"})
            continue
        if stage in patients[patient]:
            raise _error("Duplicate patient/stage measurement in " + endpoint)
        patients[patient][stage] = (value, locator)
    pairs = []
    for patient, measurements in sorted(patients.items()):
        if set(measurements) != {"Screening", "Relapse"}:
            omitted.append({"patient": patient, "stages": sorted(measurements), "reason": "incomplete pair"})
            continue
        before, after = measurements["Screening"], measurements["Relapse"]
        pairs.append({"patient_id": patient, "screening": before[0], "relapse": after[0], "relapse_minus_screening": after[0] - before[0], "screening_source_cells": before[1], "relapse_source_cells": after[1]})
    if len(pairs) < 2:
        raise _error("Fewer than two complete patient pairs")
    differences = [x["relapse_minus_screening"] for x in pairs]
    if any(x == 0 for x in differences) or len({abs(x) for x in differences}) != len(differences):
        raise _error("Exact no-tie signed-rank recipe requires separate zero/tie handling")
    test = wilcoxon([-x for x in differences], alternative="less", method="exact")
    two_sided = wilcoxon([-x for x in differences], alternative="two-sided", method="exact")
    return {"endpoint": endpoint, "units": units, "independent_patient_pairs": len(pairs), "pairs": pairs, "omitted_records": omitted, "increased": sum(x > 0 for x in differences), "decreased": sum(x < 0 for x in differences), "mean_paired_difference": statistics.mean(differences), "median_paired_difference": statistics.median(differences), "screening_mean": statistics.mean(x["screening"] for x in pairs), "relapse_mean": statistics.mean(x["relapse"] for x in pairs), "wilcoxon": {"statistic": float(test.statistic), "one_sided_relapse_greater_p": float(test.pvalue), "two_sided_p": float(two_sided.pvalue), "method": "exact", "alternative": "screening < relapse", "multiplicity_adjusted": False}}


def clinical_paired():
    from .analysis_tools import _result
    retention, src1 = _sheet("released_clinical_retention", "Fig. 1b")
    expression, src2 = _sheet("released_clinical_expression", "Fig. 6b")
    _headers(retention, {"A": "intron_retention_ratio", "B": "group", "C": "patient_number"})
    _headers(expression, {"A": "RBP", "B": "Patient", "C": "Stage", "D": "logRPKM"})
    values = []
    for row, cells in retention.items():
        if row == 1:
            continue
        if set(cells) != {"A", "B", "C"}:
            raise _error("Malformed clinical retention row")
        values.append((str(cells["C"]), cells["B"], _number(cells["A"], f"Fig. 1b!A{row}", 0, 1), f"Fig. 1b!A{row}:C{row}"))
    endpoints = [_paired_summary(values, "CD19 intron-retention ratio", "fraction")]
    for gene in ("PTBP1", "PTBP2"):
        records = []
        for row, cells in expression.items():
            if row == 1:
                continue
            if set(cells) != {"A", "B", "C", "D"} or cells["A"] not in {"PTBP1", "PTBP2"}:
                raise _error("Malformed clinical expression row")
            if cells["A"] == gene:
                records.append((str(cells["B"]), cells["C"], _number(cells["D"], f"Fig. 6b!D{row}"), f"Fig. 6b!A{row}:D{row}"))
        endpoints.append(_paired_summary(records, gene, "logRPKM as labeled in Source Data; article caption labels FPKM"))
    sets = {item["endpoint"]: sorted(x["patient_id"] for x in item["pairs"]) for item in endpoints}
    limits = ["Recomputed from released patient-level processed measurements, not from raw RNA reads or realigned junctions.", "The retention and expression endpoint patient sets differ and must not be fused into a complete matched mediation analysis.", "Within-patient temporal association does not establish that PTBP1/PTBP2 or CD19 splicing caused relapse; treatment selection and other mechanisms remain possible.", "One-sided directions follow the source analysis convention; both one-sided and two-sided exact tests are reported without multiplicity adjustment.", "The Source Data expression unit is logRPKM while the article caption says FPKM; values are preserved without conversion.", "No published target p-value is an input to this computation; evaluation against the publication is a separate step."]
    summary = "; ".join(f"{x['endpoint']}: {x['increased']}/{x['independent_patient_pairs']} paired increases, median relapse−screening {x['median_paired_difference']:.4g}, exact one-sided p={x['wilcoxon']['one_sided_relapse_greater_p']:.8g}" for x in endpoints)
    return _result("cd19-car-t", "cd19-clinical-paired-endpoints", "ANALYSIS-CD19-CLINICAL-PAIRED", "Released paired clinical endpoint replay", summary + ". Separate assay cohorts retained; association is not causal adjudication.", [src1, src2], {"endpoints": endpoints, "paired_patient_sets": sets, "all_endpoint_patient_sets_equal": len({tuple(v) for v in sets.values()}) == 1, "raw_pipeline_reproduced": False}, {"unit": "patient pair within endpoint", "difference": "relapse minus screening", "missing_pair_policy": "report and exclude incomplete pairs; no imputation", "test": "exact paired Wilcoxon with no zero/tied absolute differences", "literature_targets_used": False}, "Fig. 1b and Fig. 6b; complete source rows; exact endpoint-specific patient join", limits, analysis_version=VERSION)


def _surface(rows):
    _headers(rows, {"B": "MHHCALL4_siSCR", "C": "MHHCALL4_siPTBP1", "D": "P493-6_siSCR", "E": "P493-6_siPTBP1"})
    results = []
    seen = set()
    for row, cells in rows.items():
        if row == 1:
            continue
        if set(cells) != {"A", "B", "C", "D", "E"} or not re.fullmatch(r"replicate [1-9][0-9]*", cells["A"]):
            raise _error("Malformed surface-staining biological replicate")
        if cells["A"] in seen:
            raise _error("Duplicate surface-staining biological replicate")
        seen.add(cells["A"])
        for line, a, b in (("MHHCALL4", "B", "C"), ("P493-6", "D", "E")):
            control = _number(cells[a], f"Fig. 6d-f !{a}{row}", 0)
            treated = _number(cells[b], f"Fig. 6d-f !{b}{row}", 0)
            if control == 0:
                raise _error("Surface-staining control denominator is zero")
            results.append({"cell_line": line, "biological_replicate": cells["A"], "siSCR": control, "siPTBP1": treated, "treated_to_control_ratio": treated / control, "percent_reduction": 100 * (1 - treated / control), "source_cells": f"Fig. 6d-f !A{row},{a}{row},{b}{row}"})
    groups = []
    for line in sorted({x["cell_line"] for x in results}):
        values = [x["percent_reduction"] for x in results if x["cell_line"] == line]
        groups.append({"cell_line": line, "biological_replicates": len(values), "mean_percent_reduction": statistics.mean(values), "sample_sd_percent_reduction": statistics.stdev(values) if len(values) > 1 else None})
    return {"unit": "released surface-staining fluorescence intensity; arbitrary instrument units", "replicates": results, "cell_line_summaries": groups, "new_hypothesis_test": None, "fcs_regating_performed": False}


def _qpcr(rows):
    _headers(rows, {"A": "Well", "B": "Well Position", "C": "Sample Name", "D": "Target Name", "E": "Reporter", "F": "Quencher", "G": "CT", "H": "Ct Mean", "I": "Ct SD"})
    wells = defaultdict(list)
    seen = set()
    for row, cells in rows.items():
        if row == 1:
            continue
        if not {"A", "B", "C", "D", "G"}.issubset(cells):
            raise _error("Incomplete qPCR well row")
        match = re.fullmatch(r"(MHHCALL4|P493)_(siPTBP1|siSCR)_rep([1-9][0-9]*)", cells["C"])
        if not match or cells["B"] in seen:
            raise _error("Invalid qPCR sample identity or duplicate physical well")
        seen.add(cells["B"])
        # The acquired source contains measured numerical CTs; no nondetect
        # imputation or post-hoc outlier trimming is permitted by this recipe.
        ct = _number(cells["G"], f"Fig. S9c!G{row}", 0, 50)
        wells[(cells["C"], cells["D"])].append({"well": cells["B"], "ct": ct, "source_cell": f"Fig. S9c!G{row}"})
    means = {key: statistics.mean(x["ct"] for x in values) for key, values in wells.items()}
    groups = [{"sample": key[0], "target": key[1], "n_technical_wells": len(values), "mean_ct": means[key], "sample_sd_ct": statistics.stdev(x["ct"] for x in values) if len(values) > 1 else None, "wells": values} for key, values in sorted(wells.items())]
    contrasts = []
    for (sample, target), ct in sorted(means.items()):
        if "_siPTBP1_" not in sample or target == "GAPDH":
            continue
        control = sample.replace("_siPTBP1_", "_siSCR_")
        if any(key not in means for key in ((sample, "GAPDH"), (control, target), (control, "GAPDH"))):
            raise _error("qPCR contrast missing target or paired GAPDH reference")
        delta = ct - means[(sample, "GAPDH")]
        ctrl_delta = means[(control, target)] - means[(control, "GAPDH")]
        dd = delta - ctrl_delta
        contrasts.append({"sample": sample, "paired_control": control, "target": target, "treated_delta_ct": delta, "control_delta_ct": ctrl_delta, "delta_delta_ct": dd, "fold_vs_control": 2 ** (-dd)})
    return {"reference_target": "GAPDH", "formula": "2^-((mean_CT_target - mean_CT_GAPDH)_siPTBP1 - (mean_CT_target - mean_CT_GAPDH)_paired_siSCR)", "technical_wells": len(seen), "sample_target_groups": len(groups), "sample_ids": sorted({key[0] for key in wells}), "technical_group_summaries": groups, "paired_contrasts": contrasts, "source_cached_means_used": False, "source_cached_sd_used": False, "technical_replicates_used_as_independent_biology": False}


def surface_qpcr():
    from .analysis_tools import _result
    surface_rows, src1 = _sheet("released_surface_staining", "Fig. 6d-f ")
    qpcr_rows, src2 = _sheet("released_qpcr_wells", "Fig. S9c")
    surface, qpcr = _surface(surface_rows), _qpcr(qpcr_rows)
    limitations = ["Released surface intensities and individual Ct wells are measured inputs; this is an independent arithmetic replay of processed endpoints, not new wet-lab work.", "Surface staining has two biological replicates per cell line. Technical qPCR wells and flow-cytometry events are not independent biological or patient replicates.", "P493 in qPCR sample labels is the source shorthand for P493-6; retain original labels. These surface/qPCR assays are not NALM-6 or patient experiments.", "No original FCS event/gating files are included, so gating and instrument-level processing cannot be independently reconstructed.", "ΔΔCt assumes comparable target/reference amplification efficiencies and a stable GAPDH reference; source CT values alone do not validate these assumptions.", "The two E2E3 primer assays interrogate the same junction and are not independent biological endpoints. Intron-boundary primer signals are not a calibrated percent-spliced-in measurement.", "A PTBP1-perturbation association with junction abundance and surface staining does not demonstrate CAR binding/killing, trafficking mechanism, rescue specificity, or the cause of clinical relapse.", "No inference of exon-2 deletion is made from intron-retention primer signals; no new significance test is calculated from two biological replicates."]
    findings = "; ".join(f"{x['cell_line']}: mean surface-intensity reduction {x['mean_percent_reduction']:.2f}% across {x['biological_replicates']} biological replicates" for x in surface["cell_line_summaries"])
    return _result("cd19-car-t", "cd19-ptbp1-surface-qpcr", "ANALYSIS-CD19-PTBP1-ENDPOINTS", "PTBP1 perturbation endpoint replay", findings + f". Recomputed {len(qpcr['paired_contrasts'])} GAPDH-normalized assay contrasts from {qpcr['technical_wells']} original released Ct wells; technical wells remain nested within source samples.", [src1, src2], {"surface_staining": surface, "qpcr": qpcr, "raw_pipeline_reproduced": False, "wet_lab_executed": False}, {"unit": "cell line × biological replicate × treatment; qPCR technical wells averaged first", "surface_change": "100*(1-siPTBP1/paired siSCR)", "qpcr_reference": "GAPDH", "qpcr_exclusions": "none; malformed/missing measurements fail explicitly", "statistical_test": None, "literature_targets_used": False}, "Fig. 6d-f !A1:E3 and Fig. S9c all released wells; exact source addresses retained", limitations, analysis_version=VERSION)
