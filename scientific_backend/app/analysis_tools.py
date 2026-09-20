"""Allowlisted, bounded runtime analyses of the pinned scientific inputs.

These functions run fresh computations, without model calls, arbitrary paths,
user code or a shell. Their derived evidence is persisted by the harness before
an investigator can cite it. Numeric summaries are descriptive, not causal tests.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from .cases import CASE_ROOT, SourceIntegrityError

ANALYSIS_VERSION = "1.0.0"
MAX_FILE_BYTES = 2_000_000
MAX_EXPANDED_BYTES = 8_000_000
MAX_TABLE_ROWS = 120_000
MAX_XML_MEMBER_BYTES = 3_000_000
MAX_MANIFEST_BYTES = 100_000

# This is the complete source allowlist. Inputs never control these paths.
_SOURCES = {
    "cd19_dna": ("sources/cd19/GSE182891_CD19_minigene_variants.tab.gz", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182891"),
    "cd19_rna": ("sources/cd19/GSE182892_CD19_minigene_isoforms.txt.gz", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182892"),
    "alk": ("sources/alk/13059_2026_3977_MOESM2_ESM.xlsx", "https://doi.org/10.1186/s13059-026-03977-4"),
    "bcma_case": ("sources/bcma/case.json", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551"),
    "bcma_samples": ("sources/bcma/sample_manifest.tsv", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551"),
    "bcma_variants": ("sources/bcma/post_second_infusion_variants.tsv", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164551"),
    "released_clinical_retention": ("sources/cd19-released-endpoints/clinical-retention.json", "https://doi.org/10.1038/s41467-022-31818-y"),
    "released_clinical_expression": ("sources/cd19-released-endpoints/clinical-rbp-expression.json", "https://doi.org/10.1038/s41467-022-31818-y"),
    "released_surface_staining": ("sources/cd19-released-endpoints/surface-staining.json", "https://doi.org/10.1038/s41467-022-31818-y"),
    "released_qpcr_wells": ("sources/cd19-released-endpoints/qpcr-wells.json", "https://doi.org/10.1038/s41467-022-31818-y"),
}

_CATALOG = {
    "cd19-car-t": [
        {"id": "cd19-barcode-qc", "title": "CD19 DNA/RNA barcode qualification", "description": "Read the actual DNA and RNA tables; count rows and replicate labels; join exact barcode identities and report unmatched barcodes and duplicate barcode/replicate keys."},
        {"id": "cd19-isoform-summary", "title": "CD19 prespecified junction-count summary", "description": "Aggregate three fixed source junction columns by replicate label, retaining source readcount denominators, discarded counts and unlisted residual counts. Descriptive reporter-library analysis only."},
    ],
    "alk-l1196m": [
        {"id": "alk-assay-extraction", "title": "ALK source-key assay extraction", "description": "Locate ALK_E23_C70A in Table S2 of the workbook, assert L1196M identity, and return exact classifications, scores, fitness and cell locators."},
    ],
    "bcma-gse164551": [
        {"id": "bcma-sample-variant-qc", "title": "BCMA sample and variant qualification", "description": "Check prepared sample identity and corrected S5/S6 aliases, count independent patients and timepoints, and extract the exact post-second-infusion TNFRSF17 truncating variant with read-depth checks."},
    ],
}

# Chosen in the analysis specification before aggregation. Coordinate strings are
# retained exactly; this tool does not assert an exon/epitope interpretation.
CD19_JUNCTION_COLUMNS = ("(219 475)(743 1040)", "(219 1040)", "(219 475)")


class AnalysisInputError(ValueError):
    """A source violates the bounded analysis contract."""


def _hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _bounded_bytes(path, maximum):
    if not path.is_file():
        raise SourceIntegrityError("Required pinned analysis source is missing")
    if path.stat().st_size > maximum:
        raise AnalysisInputError("Analysis source exceeds the configured byte limit")
    with path.open("rb") as handle:
        data = handle.read(maximum + 1)
    if len(data) > maximum:
        raise AnalysisInputError("Analysis source grew beyond the configured byte limit")
    return data


def _load_source(key):
    relative, url = _SOURCES[key]
    root = CASE_ROOT.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to((root / "sources").resolve()):
        raise SourceIntegrityError("Analysis source escapes the pinned source directory")
    manifest = json.loads(_bounded_bytes(root / "MANIFEST.json", MAX_MANIFEST_BYTES))
    records = [r for r in manifest["source_files"] if r["path"] == relative]
    if len(records) != 1:
        raise SourceIntegrityError("Analysis source has no unique manifest entry")
    data = _bounded_bytes(path, MAX_FILE_BYTES)
    record = records[0]
    checksum = hashlib.sha256(data).hexdigest()
    if len(data) != record["bytes"] or checksum != record["sha256"]:
        raise SourceIntegrityError("Pinned analysis source bytes do not match the manifest: " + relative)
    return data, {"name": path.name, "path": relative, "url": url, "sha256": checksum, "bytes": len(data)}


def _tsv(data, *, compressed=False, required=()):
    if compressed:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as archive:
            data = archive.read(MAX_EXPANDED_BYTES + 1)
    if len(data) > MAX_EXPANDED_BYTES:
        raise AnalysisInputError("Expanded table exceeds the configured byte limit")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")), delimiter="\t")
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or not set(required).issubset(fields):
        raise AnalysisInputError("Required table columns are missing or duplicated")
    rows = []
    for line, row in enumerate(reader, 2):
        if len(rows) >= MAX_TABLE_ROWS:
            raise AnalysisInputError("Table exceeds the configured row limit")
        if None in row or any(value is None for value in row.values()):
            raise AnalysisInputError("Malformed table row at line " + str(line))
        rows.append((line, row))
    return fields, rows


def _nonnegative_int(value, label):
    if not re.fullmatch(r"\d+", value):
        raise AnalysisInputError("Invalid nonnegative integer in " + label)
    return int(value)


def _result(case_id, analysis_id, evidence_id, title, summary, inputs, values, parameters, locator, limitations, *, analysis_version=ANALYSIS_VERSION):
    # source.sha256 identifies this canonical derived values record. Each raw
    # source hash and the complete recipe identity remain in values below.
    values = {**values, "analysis_id": analysis_id, "analysis_version": analysis_version,
              "case_id": case_id, "parameters": parameters, "input_sources": inputs,
              "limitations": limitations, "inference_performed": False}
    return {"id": evidence_id, "title": title, "kind": "derived", "summary": summary,
            "source": {"name": "Runtime analysis: " + analysis_id, "url": inputs[0]["url"],
                       "locator": locator + "; canonical derived values JSON; raw hashes in values.input_sources", "sha256": _hash_json(values)},
            "values": values}


def _cd19_barcode_qc():
    dna_bytes, dna_source = _load_source("cd19_dna")
    rna_bytes, rna_source = _load_source("cd19_rna")
    _, dna = _tsv(dna_bytes, compressed=True, required=("RNA_BARCODE", "BARCODE", "POS", "REF", "ALT"))
    _, rna = _tsv(rna_bytes, compressed=True, required=("barcode", "replicate", "readcount", "mutations"))
    dna_barcodes = {row["RNA_BARCODE"] for _, row in dna}
    rna_barcodes = {row["barcode"] for _, row in rna}
    if "" in dna_barcodes or "" in rna_barcodes:
        raise AnalysisInputError("Empty barcode cannot be qualified as a source identity")
    labels = Counter(row["replicate"] for _, row in rna)
    keys = Counter((row["replicate"], row["barcode"]) for _, row in rna)
    shared = rna_barcodes & dna_barcodes
    missing = sorted(rna_barcodes - dna_barcodes)
    missing_rows = [row for _, row in rna if row["barcode"] not in dna_barcodes]
    unmutated = {row["barcode"] for row in missing_rows if row["mutations"] == "-"}
    unresolved = {row["barcode"] for row in missing_rows if row["mutations"] != "-"}
    controls = Counter(row["replicate"] for _, row in rna if row["mutations"] == "-")
    values = {"dna_variant_rows": len(dna), "dna_rna_barcodes": len(dna_barcodes), "rna_rows": len(rna),
              "rna_unique_barcodes": len(rna_barcodes), "replicate_rows": dict(sorted(labels.items())),
              "joined_barcodes": len(shared), "unmatched_rna_barcodes": len(missing),
              "explicit_unmutated_control_barcodes_without_variant_rows": len(unmutated - unresolved),
              "unresolved_noncontrol_barcodes_without_variant_rows": len(unresolved),
              "explicit_unmutated_rows_by_replicate": dict(sorted(controls.items())),
              "unmatched_examples": missing[:10], "unmatched_list_sha256": _hash_json(missing),
              "duplicate_barcode_replicate_keys": sum(count > 1 for count in keys.values()),
              "rows_in_duplicate_keys": sum(count for count in keys.values() if count > 1),
              "total_reported_readcount": sum(_nonnegative_int(row["readcount"], "readcount") for _, row in rna)}
    dna_source["locator"] = "All data rows; RNA_BARCODE"
    rna_source["locator"] = "All data rows; barcode, replicate and readcount"
    return _result("cd19-car-t", "cd19-barcode-qc", "ANALYSIS-CD19-QC", "Runtime CD19 barcode QC",
                   f"Fresh source analysis matches {len(shared):,}/{len(rna_barcodes):,} RNA barcodes to the DNA variant-only table. Of {len(missing)} barcodes absent from that table, {len(unmutated - unresolved)} are explicitly RNA mutations='-' unmutated controls and {len(unresolved)} are unresolved non-controls. Absence from a variant-only table is not an identity failure. {len(rna):,} RNA rows are reporter-library observations, not patient replicates.",
                   [dna_source, rna_source], values,
                   {"join": "DNA.RNA_BARCODE == RNA.barcode", "unit": "distinct barcode", "unmatched_policy": "Separate explicit RNA mutations='-' unmutated controls from unresolved non-controls; never infer WT from dictionary absence alone", "duplicate_key": ["replicate", "barcode"]},
                   "DNA/RNA exact set join across all rows",
                   ["The join does not establish mutation causality or patient-specific antigen escape.", "This basic join reads explicit RNA control labels; full mutation-set, assay reference and barcode orientation qualification is provided by cd19-variant-splicing-discovery.", "Replicate labels do not establish independent clinical replication."], analysis_version="1.1.0")


def _cd19_isoform_summary():
    raw, src = _load_source("cd19_rna")
    fields, rows = _tsv(raw, compressed=True, required=("replicate", "barcode", "readcount", "discarded", *CD19_JUNCTION_COLUMNS))
    junction_columns = [column for column in fields if column.startswith("(")]
    total = defaultdict(Counter)
    for line, row in rows:
        counts = {col: _nonnegative_int(row[col], f"{col} at line {line}") for col in ("readcount", "discarded", *junction_columns)}
        target = total[row["replicate"]]
        target["rows"] += 1
        for col in ("readcount", "discarded", *CD19_JUNCTION_COLUMNS):
            target[col] += counts[col]
        listed = sum(counts[col] for col in junction_columns) + counts["discarded"]
        target["listed_junction_plus_discarded"] += listed
        target["rows_count_coverage_gap"] += listed != counts["readcount"]
        target["rows_listed_exceed_readcount"] += listed > counts["readcount"]
        target["zero_readcount_rows"] += counts["readcount"] == 0
    records = []
    for label, data in sorted(total.items()):
        denominator = data["readcount"]
        records.append({"replicate": label, "rows": data["rows"], "reported_readcount": denominator,
                        "discarded": data["discarded"], "listed_junction_plus_discarded": data["listed_junction_plus_discarded"],
                        "unassigned_count_difference": denominator - data["listed_junction_plus_discarded"],
                        "rows_count_coverage_gap": data["rows_count_coverage_gap"],
                        "rows_listed_exceed_readcount": data["rows_listed_exceed_readcount"], "zero_readcount_rows": data["zero_readcount_rows"],
                        "junctions": [{"source_column": col, "count": data[col],
                                       "ratio_to_reported_readcount": data[col] / denominator if denominator else None}
                                      for col in CD19_JUNCTION_COLUMNS]})
    src["locator"] = "All decompressed TSV data rows; group by replicate; fixed three source junction columns"
    gap = sum(r["rows_count_coverage_gap"] for r in records)
    return _result("cd19-car-t", "cd19-isoform-summary", "ANALYSIS-CD19-ISOFORMS", "Runtime CD19 junction summaries",
                   f"Aggregated {len(rows):,} RNA rows by {len(records)} source replicate labels for three prespecified junction columns. In {gap:,} rows, listed junction plus discarded counts do not exhaust the reported readcount; ratios retain the source denominator. The selected columns are partial descriptive isoform fractions; the unlisted residual is audited rather than interpreted as missing input.",
                   [src], {"rna_rows": len(rows), "junction_columns_in_source": len(junction_columns), "replicates": records},
                   {"selected_junction_columns": list(CD19_JUNCTION_COLUMNS), "aggregation": "Sum integer counts within each source replicate label; no outcome-selected barcode filtering", "ratio_denominator": "Sum source readcount in the same replicate; unlisted residual retained", "statistical_test": None, "variant_effect_estimation": False},
                   "Group-by-replicate count aggregation and source-count coverage audit",
                   ["Read-weighted reporter-library summaries are not patient-level measurements or biological effect sizes.", "Junction coordinate strings have no new exon/epitope annotation in this tool.", "No mutation-specific effect, differential-splicing significance or causal conclusion is estimated.", "These three selected isoform fractions need not sum to one. The discovery recipe models a complete six-category partition by explicitly retaining other = readcount - five major counts."], analysis_version="1.1.0")


def _xml_member(archive, member):
    info = archive.getinfo(member)
    if info.file_size > MAX_XML_MEMBER_BYTES:
        raise AnalysisInputError("Workbook member exceeds the configured byte limit")
    with archive.open(member) as handle:
        data = handle.read(MAX_XML_MEMBER_BYTES + 1)
    if len(data) > MAX_XML_MEMBER_BYTES:
        raise AnalysisInputError("Expanded workbook member exceeds the configured byte limit")
    return ET.fromstring(data)


def _alk_assay_extraction():
    raw, src = _load_source("alk")
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        shared = ["".join(item.itertext()) for item in _xml_member(archive, "xl/sharedStrings.xml").findall("s:si", ns)]
        sheet = _xml_member(archive, "xl/worksheets/sheet2.xml")
        rows = sheet.findall(".//s:row", ns)
        if len(rows) > MAX_TABLE_ROWS:
            raise AnalysisInputError("Workbook exceeds the configured row limit")
        matching = []
        headers = {}
        for row in rows:
            row_number = int(row.attrib["r"])
            cells = {}
            for cell in row.findall("s:c", ns):
                value = cell.find("s:v", ns)
                if value is not None:
                    cells[cell.attrib["r"]] = shared[int(value.text)] if cell.get("t") == "s" else value.text
            if row_number == 2:
                headers = {re.sub(r"\d+", "", key): value for key, value in cells.items()}
            if cells.get(f"A{row_number}") == "ALK_E23_C70A":
                matching.append((row_number, cells))
    if len(matching) != 1:
        raise AnalysisInputError("ALK source key must resolve to exactly one row")
    number, cells = matching[0]
    if cells.get(f"B{number}") != "L1196M":
        raise AnalysisInputError("ALK source key does not match the expected protein change")
    expected_headers = {"A": "ID", "B": "AA_Change", "C": "Type", "D": "Alectinib_Classification", "E": "Alectinib_Resistance_Score", "F": "Lorlatinib_Classification", "G": "Lorlatinib_Resistance_Score", "H": "Zotizalkib_Classification", "I": "Zotizalkib_Resistance_Score", "J": "Fitness_Score"}
    if headers != expected_headers:
        raise AnalysisInputError("ALK Table S2 headers do not match the pinned extraction contract")
    records = [{"drug": drug, "classification": cells[f"{col}{number}"], "resistance_score": cells[f"{score}{number}"],
                "classification_cell": f"{col}{number}", "score_cell": f"{score}{number}"}
               for drug, col, score in (("Alectinib", "D", "E"), ("Lorlatinib", "F", "G"), ("Zotizalkib", "H", "I"))]
    src["locator"] = f"Table S2; A{number}:J{number}; headers A2:J2; source-key lookup"
    labels_differ = len({record["classification"] for record in records}) > 1
    classification_text = "; ".join(f"{record['drug']} {record['classification']}" for record in records)
    return _result("alk-l1196m", "alk-assay-extraction", "ANALYSIS-ALK-ASSAY", "Runtime ALK assay extraction",
                   f"Fresh workbook lookup identifies ALK_E23_C70A / L1196M: {classification_text}. Source scores retain full precision and fitness remains a separate endpoint.",
                   [src], {"source_key": "ALK_E23_C70A", "amino_acid_change": "L1196M", "variant_type": cells[f"C{number}"], "source_row": number,
                           "drugs": records, "fitness_score": cells[f"J{number}"], "fitness_cell": f"J{number}", "source_classifications_differ": labels_differ},
                   {"sheet": "Table S2", "source_key": "ALK_E23_C70A", "required_protein_identity": "L1196M", "numeric_encoding": "source decimal strings, no rounding", "statistical_test": None},
                   src["locator"], ["Classification differences describe this assay; they do not establish clinical efficacy or an interaction mechanism.", "Resistance scores are not IC50s, clinical probabilities or necessarily comparable across drugs.", "The project flags an unresolved Table S5 concentration discrepancy; this extraction does not resolve it."])


def _bcma_sample_variant_qc():
    case_bytes, case_source = _load_source("bcma_case")
    sample_bytes, sample_source = _load_source("bcma_samples")
    variant_bytes, variant_source = _load_source("bcma_variants")
    brief = json.loads(case_bytes)
    _, samples = _tsv(sample_bytes, required=("sample_id", "gsm", "matrix_alias", "source_metadata_alias", "timepoint", "alias_disagreement", "barcode_join_fraction", "notes"))
    _, variants = _tsv(variant_bytes, required=("Hugo_Symbol", "HGVSp_Short", "Variant_Classification", "t_depth", "t_ref_count", "t_alt_count", "n_depth", "n_ref_count", "n_alt_count", "FILTER"))
    ids = Counter(row["sample_id"] for _, row in samples)
    gsms = Counter(row["gsm"] for _, row in samples)
    changed = [{"source_line": line, **{key: row[key] for key in ("sample_id", "gsm", "matrix_alias", "source_metadata_alias", "timepoint", "barcode_join_fraction")}}
               for line, row in samples if row["alias_disagreement"] == "True"]
    found = [(line, row) for line, row in variants if row["Hugo_Symbol"] == "TNFRSF17"]
    if len(found) != 1:
        raise AnalysisInputError("TNFRSF17 source must resolve to exactly one prepared variant row")
    line, var = found[0]
    numeric = {key: _nonnegative_int(var[key], key) for key in ("t_depth", "t_ref_count", "t_alt_count", "n_depth", "n_ref_count", "n_alt_count")}
    depth_checks = {"tumor_counts_do_not_exceed_depth": numeric["t_ref_count"] + numeric["t_alt_count"] <= numeric["t_depth"],
                    "normal_counts_do_not_exceed_depth": numeric["n_ref_count"] + numeric["n_alt_count"] <= numeric["n_depth"]}
    if not all(depth_checks.values()):
        raise AnalysisInputError("Prepared allele counts exceed stated read depth")
    case_source["locator"] = "independent_patients, genomic_sample_timing, specimens and constraints"
    sample_source["locator"] = "All sample rows; alias_disagreement=True; sample_01 baseline notes"
    variant_source["locator"] = f"Line {line}; Hugo_Symbol=TNFRSF17"
    return _result("bcma-gse164551", "bcma-sample-variant-qc", "ANALYSIS-BCMA-QC", "Runtime BCMA identity and variant QC",
                   f"Fresh prepared-input analysis finds {len(samples)} samples from {brief['independent_patients']} patient, {len(changed)} corrected sample-alias records, and post-second-infusion TNFRSF17 {var['HGVSp_Short']}. Tumor alternate count is {numeric['t_alt_count']}/{numeric['t_depth']}; timing and variant-class limitations remain explicit.",
                   [case_source, sample_source, variant_source],
                   {"independent_patients": brief["independent_patients"], "sample_count": len(samples),
                    "duplicate_sample_ids": sum(v > 1 for v in ids.values()), "duplicate_gsm_ids": sum(v > 1 for v in gsms.values()),
                    "corrected_aliases": changed, "baseline_note": next(row["notes"] for _, row in samples if row["sample_id"] == "sample_01"),
                    "genomic_sample_timing": brief["genomic_sample_timing"], "variant_source_line": line,
                    "variant": var, "depth_checks": depth_checks,
                    "tumor_alt_read_fraction": numeric["t_alt_count"] / numeric["t_depth"] if numeric["t_depth"] else None,
                    "truncating_variant": var["Variant_Classification"] in ("Nonsense_Mutation", "Frame_Shift_Del", "Frame_Shift_Ins"),
                    "missense_pair_model_eligible": False},
                   {"variant_gene": "TNFRSF17", "unit": "one patient; longitudinal samples are not independent patients", "allele_fraction_definition": "tumor alternate read count / stated tumor read depth; not cancer-cell fraction", "raw_h5_reconciliation_performed": False, "copy_number_inference_performed": False},
                   "Prepared manifest identity audit and gene-key variant extraction",
                   ["The baseline was CD138-depleted; the demo does not recompute H5 barcode matching or cell-type expression.", "Post-treatment variant presence does not establish pretreatment absence or acquisition time.", "A read fraction is not tumor purity, clone fraction, biallelic-loss proof or surface-protein evidence.", "A truncating variant is not eligible for a simple missense-pair model; no molecular sequence set has been qualified."])


_ANALYSES = {
    "cd19-barcode-qc": _cd19_barcode_qc,
    "cd19-isoform-summary": _cd19_isoform_summary,
    "alk-assay-extraction": _alk_assay_extraction,
    "bcma-sample-variant-qc": _bcma_sample_variant_qc,
}


def _cd19_discovery():
    from .cd19_discovery import analyze
    return analyze()


def _cd19_softmax_followup():
    from .cd19_discovery import analyze
    return analyze(include_softmax=True)


_ANALYSES["cd19-variant-splicing-discovery"] = _cd19_discovery
_ANALYSES["cd19-softmax-followup"] = _cd19_softmax_followup

# Lazy module functions avoid an import cycle with shared bounded source helpers.
from .reproduction_analysis import clinical_paired, surface_qpcr
_ANALYSES["cd19-clinical-paired-endpoints"] = clinical_paired
_ANALYSES["cd19-ptbp1-surface-qpcr"] = surface_qpcr
from .gse28460_analysis import analyze as gse28460_paired_expression
_ANALYSES["gse28460-paired-expression"] = gse28460_paired_expression


def analysis_catalog(case_id: str) -> list[dict]:
    """Return only analyses permitted for the selected pinned case."""
    if case_id == "cart-discovery":
        catalog = copy.deepcopy(_CATALOG["cd19-car-t"] + _CATALOG["bcma-gse164551"])
        # Discovery presents methods, not source outcomes or the curated case's
        # conclusion. Variant identity/class and alias corrections come from
        # executing the source-qualified recipe, not from listing this menu.
        catalog[-1]["description"] = "Audit prepared sample identifiers and manifest aliases, extract TNFRSF17 source variant records, and validate timing and read-depth consistency; longitudinal samples are not independent patients."
        from .cd19_discovery import catalog_entry, softmax_catalog_entry
        catalog.extend([catalog_entry(), softmax_catalog_entry()])
        from .reproduction_analysis import CATALOG
        catalog.extend(copy.deepcopy(CATALOG))
        from .gse28460_analysis import catalog_entry as paired_catalog_entry
        catalog.append(paired_catalog_entry())
        return catalog
    if case_id not in _CATALOG:
        raise AnalysisInputError("No runtime analysis catalog for this case ID")
    catalog = copy.deepcopy(_CATALOG[case_id])
    if case_id == "cd19-car-t":
        from .cd19_discovery import catalog_entry, softmax_catalog_entry
        catalog.extend([catalog_entry(), softmax_catalog_entry()])
        from .reproduction_analysis import CATALOG
        catalog.extend(copy.deepcopy(CATALOG))
        from .gse28460_analysis import catalog_entry as paired_catalog_entry
        catalog.append(paired_catalog_entry())
    return catalog


def analyze_case(case_id: str, analysis_id: str) -> dict:
    """Compute one fresh source-linked evidence object; no arbitrary paths/code."""
    allowed = {item["id"] for item in analysis_catalog(case_id)}
    if analysis_id not in allowed:
        raise AnalysisInputError("Analysis ID is not permitted for the selected case")
    result = _ANALYSES[analysis_id]()
    if case_id == "cart-discovery":
        # Execute the original qualified reader, preserving every measurement,
        # raw input identity and limitation. Only the active workspace identity
        # changes, and its canonical derived-content hash changes with it.
        result["values"]["source_case_id"] = result["values"]["case_id"]
        result["values"]["case_id"] = case_id
        result["source"]["sha256"] = _hash_json(result["values"])
    return result
