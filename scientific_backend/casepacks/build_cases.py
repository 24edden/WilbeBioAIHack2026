"""Rebuild the compact evidence packs from pinned public inputs, without model calls.

Run: python casepacks/build_cases.py --check (verify) or without --check (rebuild).
The XLSX reader uses the standard library so bootstrapping does not require Excel.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "sources"
GEO = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc="
REMOTE = "/home/ubuntu/leon-workspace/bcma-gse164551-2026-09-19/input/"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(relative, locator, url="", origin=None):
    path = SRC / relative
    result = {"name": path.name, "url": url, "locator": locator, "sha256": digest(path),
              "path": "sources/" + relative}
    if origin:
        result["origin"] = origin
    return result


def evidence(eid, title, kind, summary, src, values=None):
    return {"id": eid, "title": title, "kind": kind, "summary": summary,
            "source": src, "values": values or {}}


def gate(label, status, detail):
    return {"label": label, "status": status, "detail": detail}


def claim(text, ids, kind="inference"):
    return {"text": text, "evidence_ids": ids, "kind": kind}


def experimental_arm(key, name, rationale, endpoint):
    """A planned measurement arm, never an invented molecular candidate."""
    return {"design_key": key, "name": name, "type": "experimental_arm", "status": "planned",
            "rationale": rationale, "endpoint": endpoint,
            "exact_sequences": "Not supplied. This is a planned assay arm, not a qualified or modeled molecular construct."}


def csv_rows(path, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rt", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def metadata_source(accession, fields):
    packet = json.loads((SRC / "geo_metadata_excerpt.json").read_text())
    lines = [r["line_1based"] for r in packet["rows"]
             if r["cells"][0] == accession and r["cells"][1] in fields]
    src = source("geo_metadata_excerpt.json", f"{accession}; original TSV lines {', '.join(map(str, lines))}; fields {', '.join(fields)}", GEO + accession)
    src.update({"origin": packet["origin"], "origin_sha256": packet["origin_sha256"]})
    return src


def cd19():
    dna_file = "cd19/GSE182891_CD19_minigene_variants.tab.gz"
    rna_file = "cd19/GSE182892_CD19_minigene_isoforms.txt.gz"
    dna = csv_rows(SRC / dna_file, True)
    rna = csv_rows(SRC / rna_file, True)
    dbar = {r["RNA_BARCODE"] for r in dna}
    rbar = {r["barcode"] for r in rna}
    counts = dict(sorted(Counter(r["replicate"] for r in rna).items()))
    unmatched_rows = [r for r in rna if r["barcode"] not in dbar]
    assert all(r["mutations"] == "-" for r in unmatched_rows), "Unmatched mutated barcodes must not be labeled WT"
    wt_counts = dict(sorted(Counter(r["replicate"] for r in rna if r["mutations"] == "-").items()))
    exact = (SRC / "cd19/CD19_CAR_T_.txt").read_text()
    sample = [{"line_1based": i, **{k: row[k] for k in ("replicate", "barcode", "mutations", "readcount", "(219 475)(743 1040)", "(219 1040)", "(219 475)", "discarded")}}
              for i, row in enumerate(rna, 2) if row["barcode"] == "AAAAAAAGCACGTGG"]
    ev = [
        evidence("CD19-01", "Public minigene RNA evidence", "measured",
                 f"The pinned RNA table contains {len(rna):,} barcode–replicate rows and {len(rbar):,} distinct barcodes across replicate labels {', '.join(counts)}. These are a reporter library, not patient samples.",
                 source(rna_file, "All data rows; distinct barcode and replicate columns", GEO + "GSE182892"),
                 {"rows": len(rna), "distinct_barcodes": len(rbar), "replicate_rows": counts, "total_readcount": sum(int(r["readcount"]) for r in rna)}),
        evidence("CD19-02", "DNA/RNA join distinguishes variants from unmutated controls", "measured",
                 f"Exact DNA RNA_BARCODE-to-RNA barcode matching covers {len(rbar & dbar):,} of {len(rbar):,} RNA barcodes. All {len(rbar - dbar)} barcodes absent from the variant table are explicitly annotated mutations='-' in RNA; they are unmutated controls, not failed mutant joins. The RNA table has {wt_counts['1']}/{wt_counts['2']} controls in the two replicates; paper Methods independently states these counts.",
                 source(dna_file, "All rows; RNA_BARCODE set intersected with GSE182892 barcode set; second source CD19-01", GEO + "GSE182891"),
                 {"dna_variant_rows": len(dna), "dna_rna_barcodes": len(dbar), "joined_barcodes": len(rbar & dbar), "unmatched_rna_barcodes": len(rbar - dbar), "explicit_unmutated_control_barcodes": len(rbar-dbar), "control_rows_by_replicate": wt_counts, "control_basis":"RNA mutations='-'; corroborated by paper Methods: Estimation of single-mutation effects", "paper_doi":"https://doi.org/10.1038/s41467-022-31818-y"}),
        evidence("CD19-03", "One exact barcode has multiple variants", "measured",
                 "Barcode AAAAAAAGCACGTGG has six listed mutations and distinct junction-count profiles in two replicate rows. A multi-variant construct cannot establish one mutation's causal effect without a qualified analysis.",
                 source(rna_file, "barcode=AAAAAAAGCACGTGG; decompressed TSV lines 2 and 9673 (header is line 1)", GEO + "GSE182892"),
                 {"records": sample, "variant_count": 6, "selection_rule": "First data-row barcode, selected before reviewing junction outcomes"}),
        evidence("CD19-04", "Escape mechanism is a study hypothesis", "literature",
                 "GSE182891/2 study metadata describes a CD19 exon 1–3 minigene assay in NALM-6 cells designed to investigate how sequence and splicing relate to epitope loss. This is mechanistic background, not proof of escape in a supplied patient.",
                 metadata_source("GSE182892", ["title", "summary", "overall_design", "pubmed_id"])),
        evidence("CD19-05", "A distinct retained-target alternative exists", "literature",
                 "GSE197215 describes infusion-product CAR-T responses under CD19 stimulation, TCR stimulation, non-target stimulation and unstimulated controls. The expression object has not been analyzed in this compact pack; this cohort must not be joined to the minigene library as matched patients.",
                 metadata_source("GSE197215", ["title", "summary", "overall_design", "pubmed_id"]))
    ]
    limits = [
        "No individual relapse tumor, surface-CD19 measurement, CAR construct or patient-specific variant was supplied in this pack.",
        "Reporter-library data and infusion-product study metadata are different studies, not paired patient observations.",
        "RNA counts do not establish surface-accessible CD19, recognition, affinity or CAR-T killing.",
        "No fitted variant-to-splicing model, clinical mechanism classification or BioNeMo prediction is represented as completed."
    ]
    experiment = {
        "title": "Distinguish antigen escape from retained-target CAR-T dysfunction",
        "design": "First qualify matched tumor and CAR-T sample identities. Obtain tumor-cell-resolved CD19 isoform/junction evidence and surface-accessible CD19 recognition, alongside antigen-specific CAR-T activity with CD19-present, CD19-absent and non-target controls. Define the independent sample unit and acceptance criteria before interpreting new results.",
        "positive": "Loss of functional surface recognition together with concordant isoform evidence supports the escape branch; retained recognition with impaired antigen-specific activity supports a CAR-T functional branch.",
        "negative": "Retained surface recognition and robust antigen-specific activity weaken both leading explanations and motivate a microenvironment or sampling review.",
        "inconclusive": "Unmatched timing, uncertain malignant-cell identity, missing controls, or RNA-only non-detection cannot distinguish these mechanisms."
    }
    return {
        "id": "cd19-car-t", "title": "CD19 CAR-T", "subtitle": "Antigen escape or a retained-target failure?",
        "hypothesis": exact,
        "hypothesis_source": source("cd19/CD19_CAR_T_.txt", "Entire source file, preserved byte-for-byte", origin="/home/ubuntu/ana-workspace/hypothesis/CD19_CAR_T_.txt"),
        "description": "Your Brev CD19 hypothesis, grounded in real public minigene evidence, with a separate CAR-T dysfunction alternative and an explicit R&D route.",
        "data_mode": "public_evidence", "evidence_count": len(ev), "evidence": ev, "limitations": limits,
        "readiness": [gate("Hypothesis preserved", "ready", "Original Brev question and all five hypotheses are pinned."),
                      gate("Source data verified", "ready", "DNA and RNA source bytes are pinned and joined explicitly."),
                      gate("Clinical adjudication", "limited", "Patient-specific matched tumor and CAR-T observations are missing."),
                      gate("BioNeMo binder comparison", "blocked", "Requires retained accessible target plus exact reference/candidate constructs, target sequence and matched prediction specification.")],
        "demo_decision": {
            "summary": "The supplied evidence can investigate CD19 splicing, but cannot choose antigen escape over CAR-T dysfunction for a particular failure. Measure functional target retention before selecting a design branch.",
            "assessment": "Unresolved — discriminating measurements required",
            "claims": [claim(ev[0]["summary"], ["CD19-01"], "measured"), claim(ev[1]["summary"], ["CD19-01", "CD19-02"], "measured"),
                       claim("The selected multi-variant barcode cannot isolate one causal mutation, and these reporter-library rows do not show a patient's mechanism.", ["CD19-03", "CD19-04"]),
                       claim("Antigen escape and target-retained functional failure remain separate alternatives; the current sources do not adjudicate between them in one individual.", ["CD19-04", "CD19-05"])],
            "alternatives": [{"title": "H1/H2 — CD19 splicing or RNA regulation", "reason": "The library enables mechanistic investigation; patient-specific isoforms and surface recognition remain absent."},
                             {"title": "H3/H4 — Retained target with CAR-T dysfunction", "reason": "Antigen-specific activity, expansion/persistence and microenvironment measurements are needed."},
                             {"title": "H5 — Composition or assay identity", "reason": "Cell identity, timing, technical effects and exact barcode joins can change the interpretation."}],
            "limitations": limits, "next_experiment": experiment,
            "rd_handoff": {"objective": "Choose a testable design objective after establishing whether functional CD19 recognition is retained.",
                           "status": "awaiting_discriminating_measurements", "reference": "No reference CAR antigen-binding construct has been supplied.",
                           "candidates": [experimental_arm("cd19-target-retention", "CD19 target-retention assay", "Measure surface-accessible CD19 in identified tumor cells to choose the escape or retained-target branch. Include matched target-present, target-absent and assay controls.", "Surface-accessible CD19 recognition; specify assay, units, timing and controls with the returned result.")],
                           "modeling": {"status": "blocked", "reason": "No qualified target-retained reference/candidate pair. Improving binding to an absent epitope is not a supported rescue. Boltz-2 may compare a qualified molecular interface after target retention and sequence/construct gates pass; it cannot simulate a whole CAR-T cell.", "artifacts": []},
                           "experiment_id": "CD19-TARGET-RETENTION-001",
                           "return_requirements": ["Experiment ID, source case/version and preserved hypothesis ID", "Matched sample/construct IDs, timing and malignant-cell identity", "Raw-data artifact/hash, measurement units, replicate unit and QC", "Surface recognition, isoform/junction and antigen-specific activity results with controls", "If retained-target design is justified: exact target, reference and candidate sequences, format, boundaries and provenance", "Prespecified endpoint and positive, negative or inconclusive assessment"]}
        }
    }


def xlsx_rows(path, sheet_number):
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        root = ET.fromstring(archive.read(f"xl/worksheets/sheet{sheet_number}.xml"))
        rows = []
        for row in root.findall(".//s:row", ns):
            values = {}
            for cell in row.findall("s:c", ns):
                value = cell.find("s:v", ns)
                if value is not None:
                    values[cell.attrib["r"]] = shared[int(value.text)] if cell.get("t") == "s" else value.text
            rows.append((int(row.attrib["r"]), values))
        return rows


def alk():
    relative = "alk/13059_2026_3977_MOESM2_ESM.xlsx"
    rows = xlsx_rows(SRC / relative, 2)
    found = [(n, r) for n, r in rows if r.get(f"A{n}") == "ALK_E23_C70A"]
    assert len(found) == 1
    number, row = found[0]
    assert row[f"B{number}"] == "L1196M"
    fields = {re.sub(r"\d+", "", k): v for k, v in rows[1][1].items()}
    record = {fields[re.sub(r"\d+", "", k)]: v for k, v in row.items()}
    drug_rows = [{"drug": drug, "classification": record[drug + "_Classification"],
                  "resistance_score": record[drug + "_Resistance_Score"],
                  "classification_cell": f"{col}{number}", "score_cell": f"{score_col}{number}"}
                 for drug, col, score_col in [("Alectinib", "D", "E"), ("Lorlatinib", "F", "G"), ("Zotizalkib", "H", "I")]]
    hypothesis = "ALK L1196M has a drug-specific resistance phenotype in the source assay, rather than equal resistance to every tested ALK inhibitor."
    url = "https://doi.org/10.1186/s13059-026-03977-4"
    ev = [evidence("ALK-01", "Exact variant identity", "measured", "Table S2 identifies ALK_E23_C70A as missense L1196M.", source(relative, f"Table S2; A{number}:C{number}; keyed by ALK_E23_C70A", url), {"source_key": "ALK_E23_C70A", "amino_acid_change": "L1196M", "variant_type": record["Type"]}),
          evidence("ALK-02", "Drug-specific source classifications", "measured", "The source classifies L1196M as Resistance for alectinib and lorlatinib, and Sensitive for zotizalkib. Scores retain source precision; they are not IC50s or resistance probabilities.", source(relative, f"Table S2; D{number}:I{number}; field headers D2:I2", url), {"drugs": drug_rows}),
          evidence("ALK-03", "Fitness is a separate endpoint", "measured", "The source reports Fitness_Score separately from drug resistance; it cannot be substituted for a drug-response measurement.", source(relative, f"Table S2; J{number}; header J2", url), {"Fitness_Score": record["Fitness_Score"]}),
          evidence("ALK-04", "Exposure and causal interpretation remain bounded", "inference", "The project case document records a Table S5 concentration-header versus supplementary-legend discrepancy and requires independent expression/editing checks. This pack does not resolve that discrepancy or extract independent validation assays.", source("alk/HYPOTHESIS_01_EASY_ALK_L1196M.md", "Analysis plan items 3–5; Falsification and next experiment", url))]
    limits = ["Functional assay evidence, not a patient treatment recommendation.", "Resistance scores are not IC50s, probabilities, or necessarily comparable across drugs.", "Table S5 concentration-header/legend discrepancy remains unresolved; no absolute exposure claim is supported.", "Independent biological replicates, variant expression and orthogonal validation are not adjudicated in this compact pack.", "No qualified ALK/ligand structures or live molecular predictions are included."]
    return {"id": "alk-l1196m", "title": "ALK L1196M", "subtitle": "Adjudicate drug-specific assay evidence", "hypothesis": hypothesis,
            "hypothesis_source": source("alk/HYPOTHESIS_01_EASY_ALK_L1196M.md", "Question and hypotheses > Primary hypothesis"),
            "description": "Exact source cells from the published ALK atlas, including source scores and a clear phenotype-versus-mechanism boundary.",
            "data_mode": "public_evidence", "evidence_count": len(ev), "evidence": ev, "limitations": limits,
            "readiness": [gate("Source assay", "ready", "Workbook hashed; identity keyed by ALK_E23_C70A and L1196M asserted."), gate("Exposure interpretation", "limited", "Concentration discrepancy remains unresolved."), gate("BioNeMo molecular comparison", "blocked", "Exact qualified WT/mutant constructs, residue mapping and ligand input are missing.")],
            "demo_decision": {"summary": "The atlas supports a drug-specific source-assay phenotype: Resistance for alectinib and lorlatinib, Sensitive for zotizalkib. It does not by itself establish an interaction mechanism or clinical benefit.", "assessment": "Supported within the source assay",
                              "claims": [claim(ev[0]["summary"], ["ALK-01"], "measured"), claim(ev[1]["summary"], ["ALK-02"], "measured"), claim("Differing source labels support the narrow hypothesis; causal transfer needs matched validation and exposure clarification.", ["ALK-02", "ALK-03", "ALK-04"])],
                              "alternatives": [{"title": "Assay and model context", "reason": "Exposure, baseline growth or expression can affect phenotype."}, {"title": "Editing or guide artifact", "reason": "Source labels do not replace edit identity and independent validation."}],
                              "limitations": limits,
                              "next_experiment": {"title": "Matched WT, L1196M and revertant validation", "design": "Compare verified constructs with matched expression, controls and independent biological replicates; assess within-drug response together with pathway inhibition. Resolve concentration meaning and predeclare effect criteria.", "positive": "A reproducible mutation-associated within-drug effect that reverts supports a causal phenotype.", "negative": "Failure to reproduce or revert weakens a mutation-specific interpretation.", "inconclusive": "Unmatched expression, exposure ambiguity or an unidentifiable response curve prevents causal comparison."},
                              "rd_handoff": {"objective": "Test whether the source phenotype survives a matched orthogonal assay before making a molecular design claim.", "status": "awaiting_experiment", "reference": "WT ALK construct; exact construct artifact and ligand identity still required.", "candidates": [experimental_arm("alk-matched-validation", "Matched ALK phenotype validation", "Test WT, L1196M and revertant assay arms with verified identity and matched expression; qualify exposure before interpreting a mutation effect.", "Within-drug response or pathway inhibition; identify construct, drug, exposure and units with each result.")], "modeling": {"status": "blocked", "reason": "Qualified sequence/construct, residue mapping and ligand input are absent. A predicted structure cannot overwrite an assay label.", "artifacts": []}, "experiment_id": "ALK-MATCHED-VALIDATION-001", "return_requirements": ["Construct/edit identity and source hashes", "Drug, concentration units, exposure time and discrepancy resolution", "Independent biological replicate IDs and matched expression controls", "Raw response and pathway data with QC", "Prespecified effect criterion and inconclusive/failure reasons"]}}}


def bcma():
    brief = json.loads((SRC / "bcma/case.json").read_text())
    samples = csv_rows(SRC / "bcma/sample_manifest.tsv")
    variants = csv_rows(SRC / "bcma/post_second_infusion_variants.tsv")
    hit = [(i, row) for i, row in enumerate(variants, 2) if row["Hugo_Symbol"] == "TNFRSF17"]
    assert len(hit) == 1
    line, var = hit[0]
    assert var["HGVSp_Short"] == "p.Q38*"
    changed = [r for r in samples if r["alias_disagreement"] == "True"]
    ev = [evidence("BCMA-01", "One patient; eight longitudinal samples", "literature", "The prepared case describes one patient and eight longitudinal bone-marrow RNA samples. The baseline was depleted of CD138-positive cells and is not an unbiased baseline tumor sample.", source("bcma/case.json", "independent_patients, specimens, genomic_sample_timing and constraints", GEO + "GSE164551", REMOTE + "case.json"), {"independent_patients": brief["independent_patients"], "sample_count": len(samples), "baseline_note": samples[0]["notes"]}),
          evidence("BCMA-02", "Corrected S5/S6 sample identities", "measured", "The prepared manifest maps sample_05/GSM5013825 to matrix S6 and metadata S5, and sample_06/GSM5013826 to matrix S5 and metadata S6. These mapped samples must not be interchanged by filename.", source("bcma/sample_manifest.tsv", "Rows where alias_disagreement=True; sample_05 and sample_06", GEO + "GSE164551", REMOTE + "sample_manifest.tsv"), {"corrected_samples": [{k:r[k] for k in ("sample_id", "gsm", "matrix_alias", "source_metadata_alias", "timepoint", "barcode_join_fraction")} for r in changed], "qualification": "Prepared-manifest measurements retained; large H5 objects not reprocessed in the demo."}),
          evidence("BCMA-03", "Post-treatment TNFRSF17 truncating variant", "measured", "The post-second-infusion source table reports TNFRSF17 p.Q38* (Nonsense_Mutation), PASS, tumor alternate count 10 of depth 41. This is post-treatment evidence and does not establish when the alteration arose or biallelic loss by itself.", source("bcma/post_second_infusion_variants.tsv", f"TSV line {line}; Hugo_Symbol=TNFRSF17; HGVSp_Short=p.Q38*", GEO + "GSE164551", REMOTE + "post_second_infusion_variants.tsv"), var),
          evidence("BCMA-04", "Copy number and surface protein remain unresolved here", "inference", "The prepared case explicitly requires qualified copy-number inference and warns that RNA non-detection is not surface-protein measurement. A truncating variant plus this metadata does not establish an exclusive resistance mechanism.", source("bcma/case.json", "constraints items 4–8; genomic_sample_timing", GEO + "GSE164551", REMOTE + "case.json"))]
    limits = list(brief["constraints"]) + ["Only compact case metadata, sample manifest and mutation table are bundled; H5, cell metadata and allele-count matrices remain on Brev.", "This is open-book development, not a blinded evaluation against the published mechanism."]
    return {"id": "bcma-gse164551", "title": "BCMA relapse", "subtitle": "One patient, longitudinal evidence, antigen-loss routing", "hypothesis": brief["question"],
            "hypothesis_source": source("bcma/case.json", "question", origin=REMOTE + "case.json"),
            "description": "A real prepared Brev packet that tests identity correction, post-treatment timing and the boundary between truncating variants and binder redesign.", "data_mode": "public_evidence", "evidence_count": len(ev), "evidence": ev, "limitations": limits,
            "readiness": [gate("Case and sample identity", "ready", "Original prepared case and corrected S5/S6 sample mapping pinned."), gate("Tumor variant", "ready", "TNFRSF17 p.Q38* extracted from exact post-treatment source row."), gate("Antigen-loss adjudication", "limited", "Requires qualified tumor-cell expression, copy number and accessible surface protein evidence."), gate("BioNeMo missense/binder routing", "blocked", "The observed variant is truncating, not a missense pair; retained target and exact binder constructs have not been qualified.")],
            "demo_decision": {"summary": "A post-treatment TNFRSF17 truncating variant makes antigen escape plausible, but this compact packet cannot establish biallelic loss, its timing, or exclusive causality. Qualify target presence before proposing a same-target design.", "assessment": "Plausible mechanism; incomplete causal evidence",
                              "claims": [claim(ev[0]["summary"], ["BCMA-01"], "literature"), claim(ev[1]["summary"], ["BCMA-02"], "measured"), claim(ev[2]["summary"], ["BCMA-03"], "measured"), claim("Binder structural comparison does not address complete absence of accessible target, and a truncating alteration is not the supported missense-pair use case.", ["BCMA-03", "BCMA-04"])],
                              "alternatives": [{"title": "BCMA escape", "reason": "Truncation is relevant, but copy number and surface expression must be qualified."}, {"title": "CAR-T activity or persistence", "reason": "Functional and longitudinal CAR-T evidence is not established by this compact packet."}, {"title": "Composition or timing", "reason": "Depleted baseline, corrected sample aliases and post-retreatment DNA constrain comparison."}], "limitations": limits,
                              "next_experiment": {"title": "Resolve accessible BCMA and allelic context", "design": "Validate tumor-cell identity, surface-accessible BCMA and allele/copy-number state at matched timepoints; interpret CAR-T activity with target-present and target-absent controls.", "positive": "Concordant loss of accessible BCMA with qualified allelic evidence supports an antigen-selection or multi-target research objective.", "negative": "Retained accessible BCMA weakens a complete target-loss explanation and shifts attention to functional alternatives.", "inconclusive": "RNA-only evidence, uncertain cell identity or unqualified allele-count orientation cannot establish functional antigen loss."},
                              "rd_handoff": {"objective": "Establish functional target availability, then select an antigen-selection or qualified retained-target design objective.", "status": "awaiting_discriminating_measurements", "reference": "Original ide-cel target is BCMA; no exact reference/candidate construct is bundled.", "candidates": [experimental_arm("bcma-target-retention", "BCMA target-retention assay", "Measure surface-accessible BCMA in correctly identified tumor samples; retain sample timing and required allelic evidence before selecting a design branch.", "Surface-accessible BCMA recognition; specify sample, infusion-relative timing, units and controls.")], "modeling": {"status": "blocked", "reason": "Observed p.Q38* is truncating. No missense comparison or supported affinity rescue can be inferred; a target-retained binder comparison requires a separately qualified construct packet.", "artifacts": []}, "experiment_id": "BCMA-RETENTION-001", "return_requirements": ["Sample/experiment IDs and timing relative to the correct infusion", "Tumor-cell identity and corrected manifest mapping", "Surface recognition and copy-number/allelic artifacts with QC", "Independent replicate definition, units and controls", "If using a retained-target scenario: separate manifest and exact target/reference/candidate constructs"]}}}


def generated_files():
    packs = [cd19(), alk(), bcma()]
    files = {p["id"] + ".json": p for p in packs}
    entries = []
    for path in sorted(SRC.rglob("*")):
        if path.is_file():
            entries.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": digest(path)})
    serialized = {name: json.dumps(obj, ensure_ascii=False, indent=2) + "\n" for name, obj in files.items()}
    files["MANIFEST.json"] = {"schema_version": "1.0", "generated_by": "casepacks/build_cases.py", "data_mode": "public_evidence", "source_files": entries,
        "case_files": [{"path": name, "sha256": hashlib.sha256(contents.encode()).hexdigest()} for name, contents in serialized.items()],
        "notes": ["Brev CD19 hypothesis and BCMA compact sources copied and hash-checked against originals on 2026-09-19.", "No patient-level CD19 result, synthetic measurement or BioNeMo prediction has been invented.", "Derived pack summaries are curated demonstration decisions; live model decisions are recorded separately."]}
    return {name: json.dumps(obj, ensure_ascii=False, indent=2) + "\n" for name, obj in files.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, contents in generated_files().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != contents:
                raise SystemExit("Evidence pack mismatch: " + name)
        else:
            path.write_text(contents)
    print("Verified" if args.check else "Built", "3 reproducible public-evidence packs")


if __name__ == "__main__":
    main()
