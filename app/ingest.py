"""Uploaded files -> `PatientBundle`.

Deliberately dependency-free (no pandas, no pyvcf): the parsers handle the
shapes we actually demo, and every parsed record keeps its source line so
findings can cite `file + line` in their provenance.
"""

from __future__ import annotations

import csv
import io
import re

from app.models import LabResult, NoteSection, PatientBundle, SourceFile, Variant

VCF_EXT = (".vcf", ".vcf.txt")
LABS_EXT = (".csv", ".tsv")
NOTES_EXT = (".txt", ".md", ".note")

_GENE_RE = re.compile(r"(?:^|;)(?:GENE|GENEINFO|SYMBOL)=([^;,:]+)", re.IGNORECASE)
_CSQ_RE = re.compile(r"(?:^|;)(?:CSQ|CONSEQUENCE|ANN)=([^;,]+)", re.IGNORECASE)
_RANGE_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*[-–]\s*(-?\d+(?:\.\d+)?)\s*$")


def detect_kind(filename: str) -> str:
    name = filename.lower()
    if name.endswith(VCF_EXT):
        return "vcf"
    if name.endswith(LABS_EXT):
        return "labs"
    if name.endswith(NOTES_EXT):
        return "notes"
    return "unknown"


def sniff_kind(filename: str, text: str) -> str:
    """Extension first, content as the tie-breaker for `unknown`."""
    kind = detect_kind(filename)
    if kind != "unknown":
        return kind
    head = text.lstrip()[:400].lower()
    if head.startswith("##fileformat=vcf") or "\t#chrom" in head or head.startswith("#chrom"):
        return "vcf"
    first_line = text.splitlines()[0].lower() if text.strip() else ""
    if "," in first_line and any(k in first_line for k in ("test", "analyte", "value", "result")):
        return "labs"
    return "notes"


def parse_vcf(text: str) -> list[Variant]:
    variants: list[Variant] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t") if "\t" in line else line.split()
        if len(cols) < 5:
            continue
        chrom, pos, vid, ref, alt = cols[0], cols[1], cols[2], cols[3], cols[4]
        try:
            position = int(pos)
        except ValueError:
            continue
        info = cols[7] if len(cols) > 7 else ""
        gene_match = _GENE_RE.search(info)
        csq_match = _CSQ_RE.search(info)
        zygosity = None
        if len(cols) > 9:
            genotype = cols[9].split(":")[0].replace("|", "/")
            zygosity = {"0/1": "het", "1/0": "het", "1/1": "hom", "0/0": "ref"}.get(genotype)
        variants.append(
            Variant(
                chrom=chrom.replace("chr", ""),
                pos=position,
                ref=ref,
                alt=alt,
                gene=gene_match.group(1) if gene_match else None,
                rsid=vid if vid and vid != "." else None,
                consequence=csq_match.group(1) if csq_match else None,
                zygosity=zygosity,
                source_line=lineno,
            )
        )
    return variants


def _to_float(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    cleaned = re.sub(r"^[<>~=]+", "", cleaned).strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _pick(row: dict[str, str], *candidates: str) -> str | None:
    for key, value in row.items():
        if key and key.strip().lower() in candidates and value not in (None, ""):
            return value
    return None


def parse_labs(text: str) -> list[LabResult]:
    """CSV/TSV of lab values. Column names are matched loosely because every
    export names them differently."""
    if not text.strip():
        return []
    dialect_delimiter = "\t" if text.splitlines()[0].count("\t") >= 1 else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=dialect_delimiter)
    results: list[LabResult] = []
    for offset, row in enumerate(reader, start=2):  # header is line 1
        name = _pick(row, "test", "name", "analyte", "marker", "lab")
        if not name:
            continue
        raw_value = _pick(row, "value", "result", "measurement") or ""
        ref_low = _pick(row, "ref_low", "low", "range_low", "reference_low")
        ref_high = _pick(row, "ref_high", "high", "range_high", "reference_high")
        ref_range = _pick(row, "reference_range", "ref_range", "range", "reference")
        if ref_range and (ref_low is None or ref_high is None):
            match = _RANGE_RE.match(ref_range)
            if match:
                ref_low, ref_high = match.group(1), match.group(2)
        results.append(
            LabResult(
                name=name.strip(),
                value=_to_float(raw_value),
                raw_value=raw_value.strip() or None,
                unit=(_pick(row, "unit", "units") or None),
                ref_low=_to_float(ref_low) if ref_low else None,
                ref_high=_to_float(ref_high) if ref_high else None,
                date=(_pick(row, "date", "collected", "timestamp") or None),
                source_line=offset,
            )
        )
    return results


def parse_notes(text: str) -> list[NoteSection]:
    """Split free text on markdown headings or `Heading:` lines, so a finding
    can cite the section it came from rather than the whole document."""
    sections: list[NoteSection] = []
    heading: str | None = None
    buffer: list[str] = []
    start_line = 1

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body or heading:
            sections.append(NoteSection(heading=heading, text=body, source_line=start_line))

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        is_md_heading = line.startswith("#")
        is_label = bool(re.match(r"^[A-Z][A-Za-z /&-]{2,40}:\s*$", line))
        if is_md_heading or is_label:
            flush()
            heading = line.lstrip("#").rstrip(":").strip()
            buffer = []
            start_line = lineno
            continue
        buffer.append(line)
    flush()
    return [s for s in sections if s.text or s.heading]


def build_bundle(files: list[tuple[str, str, str]], patient_id: str = "patient-0") -> PatientBundle:
    """`files` is a list of `(file_id, filename, text)`."""
    bundle = PatientBundle(patient_id=patient_id)
    for file_id, filename, text in files:
        kind = sniff_kind(filename, text)
        n_records = 0
        if kind == "vcf":
            parsed = parse_vcf(text)
            bundle.variants.extend(parsed)
            n_records = len(parsed)
        elif kind == "labs":
            parsed_labs = parse_labs(text)
            bundle.labs.extend(parsed_labs)
            n_records = len(parsed_labs)
        else:
            kind = "notes"
            parsed_notes = parse_notes(text)
            bundle.notes.extend(parsed_notes)
            n_records = len(parsed_notes)
        bundle.files.append(
            SourceFile(file_id=file_id, filename=filename, kind=kind, n_records=n_records)
        )
    return bundle
