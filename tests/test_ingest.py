from app.ingest import build_bundle, parse_labs, parse_notes, parse_vcf, sniff_kind


def test_vcf_parsing_keeps_annotation_and_line(sample_files):
    vcf_text = next(text for _, name, text in sample_files if name.endswith(".vcf"))
    variants = parse_vcf(vcf_text)

    assert [v.gene for v in variants] == ["KRAS", "DPYD", "MTHFR", "TP53", "APC"]
    kras = variants[0]
    assert kras.label == "KRAS p.Gly12Asp"
    assert kras.rsid == "rs121913529"
    assert kras.zygosity == "het"
    assert kras.source_line == 7  # header lines are counted, so provenance points at the row


def test_vcf_ignores_headers_and_short_rows():
    assert parse_vcf("##fileformat=VCFv4.2\n#CHROM\tPOS\n1\t123\n") == []


def test_labs_flagging_uses_reference_range(sample_files):
    labs_text = next(text for _, name, text in sample_files if name.endswith(".csv"))
    labs = parse_labs(labs_text)

    by_name = {(lab.name, lab.date): lab for lab in labs}
    assert by_name[("CEA", "2025-04-20")].flag == "high"
    assert by_name[("Neutrophils", "2025-03-02")].flag == "low"
    assert by_name[("Neutrophils", "2025-01-12")].flag == "normal"


def test_labs_accepts_a_combined_reference_range_column():
    labs = parse_labs("test,value,reference_range\nCEA,9,0-5\n")
    assert labs[0].ref_low == 0 and labs[0].ref_high == 5
    assert labs[0].flag == "high"


def test_notes_split_into_cited_sections(sample_files):
    notes_text = next(text for _, name, text in sample_files if name.endswith(".txt"))
    sections = parse_notes(notes_text)

    headings = [s.heading for s in sections]
    assert "Treatment" in headings
    assert all(s.source_line for s in sections)


def test_sniff_kind_falls_back_to_content():
    assert sniff_kind("mystery", "##fileformat=VCFv4.2\n") == "vcf"
    assert sniff_kind("mystery", "test,value\nCEA,9\n") == "labs"
    assert sniff_kind("mystery", "free text") == "notes"


def test_build_bundle_records_every_file(sample_files):
    bundle = build_bundle(sample_files)
    assert {f.kind for f in bundle.files} == {"vcf", "labs", "notes"}
    assert bundle.variants and bundle.labs and bundle.notes
    assert not bundle.is_empty
