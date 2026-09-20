"""Build and validate agent inputs from the three unmodified GEO downloads.

Run with Python 3, numpy and pandas. No network access or biological result lookup.
"""
from pathlib import Path
from collections import defaultdict, Counter
import csv
import gzip
import hashlib
import json
import re
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
INPUT = ROOT.parent / "datasets" / "agent_access" / "paired_all_relapse"
EVAL = ROOT / "evaluator"
URLS = {
    "GSE28460_series_matrix.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE28nnn/GSE28460/matrix/GSE28460_series_matrix.txt.gz",
    "GSE18497_series_matrix.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE18nnn/GSE18497/matrix/GSE18497_series_matrix.txt.gz",
    "GPL570.annot.gz": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz",
}


def read_matrix(path):
    meta = defaultdict(list)
    with gzip.open(path, "rt") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if not row:
                continue
            if row[0] == "!series_matrix_table_begin":
                break
            meta[row[0]].append(row[1:])
        header = next(reader)
        ids, values = [], []
        for row in reader:
            if row[0] == "!series_matrix_table_end":
                break
            assert len(row) == len(header), (path, row[0], len(row))
            ids.append(row[0])
            values.append([float(v) for v in row[1:]])
        else:
            raise ValueError(f"Missing matrix end marker: {path}")
        # Drain the gzip stream to verify its footer/CRC.
        for _ in reader:
            pass
    frame = pd.DataFrame(values, index=ids, columns=header[1:])
    frame.index.name = "probe_id"
    assert frame.index.is_unique and frame.columns.is_unique
    assert header[1:] == meta["!Sample_geo_accession"][0]
    assert np.isfinite(frame.to_numpy()).all() and (frame.to_numpy() > 0).all()
    assert set(meta["!Sample_platform_id"][0]) == {"GPL570"}
    assert set(meta["!Sample_organism_ch1"][0]) == {"Homo sapiens"}
    return meta, frame


def manifest(acc, meta):
    rows = []
    for i, gsm in enumerate(meta["!Sample_geo_accession"][0]):
        title = meta["!Sample_title"][0][i]
        traits = {}
        for line in meta["!Sample_characteristics_ch1"]:
            key, value = line[i].split(": ", 1)
            traits[key] = value
        if acc == "GSE28460":
            match = re.fullmatch(r"(p\d+)-([DR])-([EL])", title)
            assert match, title
            patient, time, subgroup = match.groups()
            time = {"D": "diagnosis", "R": "relapse"}[time]
            assert meta["!Sample_source_name_ch1"][0][i] == time
            lineage = "Precursor-B-ALL"
        else:
            match = re.fullmatch(r"Patient_(\d+)_(diagnosis|relapse)", title)
            assert match, title
            patient, time = match.groups()
            subgroup = ""
            lineage = traits["all type"]
        rows.append({
            "sample_id": gsm, "patient_id": f"{acc}_{patient}",
            "timepoint": time, "lineage": lineage, "original_title": title,
            "cohort": acc, "source_description": meta["!Sample_source_name_ch1"][0][i],
            "relapse_group_deposited": subgroup,
            "relapse_time_deposited": traits.get("relapse time", ""),
            "months_to_relapse": traits.get("months to relapse", ""),
            "all_subtype": traits.get("all subtype", ""),
            "sex_deposited": traits.get("gender", ""),
        })
    samples = pd.DataFrame(rows)
    for patient, group in samples.groupby("patient_id"):
        assert len(group) == 2 and set(group.timepoint) == {"diagnosis", "relapse"}, patient
        assert group.lineage.nunique() == 1
        assert group.relapse_group_deposited.nunique() == 1
    return samples


def export_group(name, frame, samples):
    folder = INPUT / name
    folder.mkdir(parents=True, exist_ok=True)
    columns = list(samples.sample_id)
    original = frame.loc[:, columns]
    log_signal = np.log2(original)
    # Record this explicit transformation; do not silently claim raw RNA counts.
    log_signal.to_csv(folder / "expression_log2.tsv.gz", sep="\t", float_format="%.8f",
                      compression={"method": "gzip", "mtime": 0})
    samples.to_csv(folder / "samples.csv", index=False)
    pairs = samples.pivot(index="patient_id", columns="timepoint", values="sample_id")
    pairs[["diagnosis", "relapse"]].to_csv(folder / "patient_pairs.csv")
    original.iloc[:10].to_csv(folder / "preview_original_signal.csv")
    reread = pd.read_csv(folder / "expression_log2.tsv.gz", sep="\t", index_col=0)
    assert reread.shape == original.shape
    assert list(reread.columns) == columns
    assert list(reread.index) == list(original.index)
    assert np.allclose(reread.values, log_signal.values, rtol=0, atol=5.1e-9)
    # Per-patient, all-probe arithmetic references, without selecting biological hits.
    checks = []
    for patient, pair in pairs.iterrows():
        delta = log_signal[pair.relapse] - log_signal[pair.diagnosis]
        checks.append({"patient_id": patient, "diagnosis": pair.diagnosis,
                       "relapse": pair.relapse,
                       "median_absolute_log2_difference_all_probes": float(delta.abs().median()),
                       "number_probes_increased": int((delta > 0).sum()),
                       "number_probes_decreased": int((delta < 0).sum()),
                       "number_probes_unchanged": int((delta == 0).sum())})
    pd.DataFrame(checks).to_csv(EVAL / f"{name}_arithmetic_reference.csv", index=False)
    return {"patients": len(pairs), "samples": len(samples), "probes": len(frame),
            "lineages": dict(Counter(samples.drop_duplicates("patient_id").lineage)),
            "all_pairs_complete": True, "roundtrip_passed": True}


def main():
    INPUT.mkdir(exist_ok=True)
    EVAL.mkdir(exist_ok=True)
    hashes = []
    for name, url in URLS.items():
        path = SOURCE / name
        hashes.append({"file": name, "url": url, "bytes": path.stat().st_size,
                       "sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest()})
    pd.DataFrame(hashes).to_csv(ROOT / "download_manifest.csv", index=False)
    with gzip.open(SOURCE / "GPL570.annot.gz", "rt") as handle:
        for line in handle:
            if line.startswith("!platform_table_begin"):
                break
        annotations = []
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["ID"].startswith("!"):
                break
            symbol = row["Gene symbol"].strip()
            annotations.append({"probe_id": row["ID"], "gene_symbol": symbol,
                                "gene_id": row["Gene ID"], "gene_title": row["Gene title"],
                                "mapping_status": "missing" if not symbol else
                                "multiple_symbols" if "///" in symbol else "single_symbol"})
        handle.read()  # Finish the gzip integrity check.
    annotation = pd.DataFrame(annotations)
    assert annotation.probe_id.is_unique
    annotation.to_csv(INPUT / "probe_annotation.tsv", sep="\t", index=False)
    audit = {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
             "annotation_mapping": dict(Counter(annotation.mapping_status)),
             "source": {}, "agent_groups": {}}
    for acc in ["GSE28460", "GSE18497"]:
        meta, frame = read_matrix(SOURCE / f"{acc}_series_matrix.txt.gz")
        samples = manifest(acc, meta)
        assert set(frame.index) == set(annotation.probe_id)
        values = frame.to_numpy()
        audit["source"][acc] = {
            "samples": len(samples), "patients": samples.patient_id.nunique(),
            "probes": len(frame), "missing_or_nonfinite_values": int((~np.isfinite(values)).sum()),
            "original_signal_quantiles_0_1_50_99_100_percent": np.quantile(values, [0, .01, .5, .99, 1]).tolist(),
            "all_pairs_complete": True,
            "lineages_by_patient": dict(Counter(samples.drop_duplicates("patient_id").lineage)),
            "deposited_relapse_group_by_patient": dict(Counter(samples.drop_duplicates("patient_id").relapse_group_deposited)),
        }
        samples.to_csv(SOURCE / f"{acc}_sample_manifest.csv", index=False)
        if acc == "GSE28460":
            audit["agent_groups"]["discovery_B_ALL"] = export_group("discovery_B_ALL", frame, samples)
        else:
            for name, lineage in [("validation_B_ALL", "Precursor-B-ALL"), ("optional_T_ALL", "T-ALL")]:
                selected = samples[samples.lineage == lineage].copy()
                audit["agent_groups"][name] = export_group(name, frame, selected)
    audit["known_discrepancy"] = (
        "GSE28460 deposited metadata label 29 patients E and 20 L; the primary paper reports "
        "27 early and 22 late in the 49-patient expression cohort. Do not silently relabel. "
        "Use all 49 paired patients for the primary contrast; exclude timing subgroups until reconciled.")
    (EVAL / "validation_report.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
