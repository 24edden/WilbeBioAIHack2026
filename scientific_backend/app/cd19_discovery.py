"""Versioned, source-qualified CD19 minigene reanalysis; never patient inference.

The public processed counts are recomputed. Author methods are reproduced where
specified; unresolved weighting/denominator choices are explicit, not hidden.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import re
import warnings

import numpy as np
from scipy import sparse
from scipy.special import softmax
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from . import analysis_tools as base

RECIPE_ID = "cd19-variant-splicing-discovery"
EVIDENCE_ID = "ANALYSIS-CD19-DISCOVERY"
SOFTMAX_ID = "cd19-softmax-followup"
SOFTMAX_EVIDENCE_ID = "ANALYSIS-CD19-SOFTMAX"
VERSION = "cd19-discovery-1.0"
DOI = "https://doi.org/10.1038/s41467-022-31818-y"
COMMIT = "edd69ccba3a193ca13ee66a5a4b191d980a940a1"
AUTHOR = "https://raw.githubusercontent.com/mcortes-lopez/CD19_splicing_mutagenesis/" + COMMIT + "/"
MAJOR = {
    "inclusion": "(219 475)(743 1040)",
    "exon2_skipping": "(219 1040)",
    "intron2_retention": "(219 475)",
    "alt_exon2": "(219 657)(743 1040)",
    "alt_exon3": "(219 475)(743 1073)",
}
LABELS = (*MAJOR, "other")
# Scientific references are immutable recipe inputs, not replaceable downloads.
_REFERENCES = {
    "paper.xml": ("9f0955da414495f649181a5e3904a275fcb4567e74f697918273cee0a498ce70", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9500061/fullTextXML"),
    "CD19_WT.minigene.fa": ("0718f3e82821c6460294068a1ea2db6d26e707e60cd57500139836ae544223a0", AUTHOR + "minigene_annotation/CD19_WT.minigene.fa"),
    "CD19_WT.minigene.anno.gtf": ("6e1cc2ba37c7b159f403fd44487c958ecd1840b692f876bfc009292eb7096b55", AUTHOR + "minigene_annotation/CD19_WT.minigene.anno.gtf"),
    "author_variant_table_for_RNASeq_analysis.R": ("bb27862eed94d20b842b4bfe6b2eadcb82382a6c43cca143f699706bab4f6fa0", AUTHOR + "VariantCalling_DNAseq/variant_table_for_RNASeq_analysis.R"),
    "P15391.json": ("a000a6a2049d4fd263c8af16fe0c0e85f97293aaf3d76b9f61db88f196fb3545", "https://rest.uniprot.org/uniprotkb/P15391.json"),
}
_DNA_SHA = "17cf79b3880d6a331f8223f7e20fd42998bc27b2a328cadfe0d823333a2568cb"
_RNA_SHA = "a7fbe062d414f45d398658c6c79356cc1ff589a561b5b0263c64522d077cc7db"
MAX_MUTATIONS = 5000
MAX_BARCODES = 11000
MODEL_MAX_ITER = 1500
MODEL_TOL = 0.001
MODEL_SEED = 182892


def required_sources():
    return [{"path": base._SOURCES["cd19_dna"][0], "sha256": _DNA_SHA},
            {"path": base._SOURCES["cd19_rna"][0], "sha256": _RNA_SHA},
            *[{"path": "sources/cd19-discovery/" + name, "sha256": sha} for name, (sha, _) in _REFERENCES.items()]]


def catalog_entry():
    return {"id": RECIPE_ID, "title": "CD19 paper-supported variant-to-splicing discovery",
            "description": "Qualify barcode orientation, explicit unmutated controls and mutation calls against author methods; compare observed single-mutant splicing with empirical control ranges and rank replicate-concordant cryptic associations. No regression fitting. Requires the pinned public DNA/RNA tables, author reference sequence/annotation and publication; reporter assay only.",
            "input_sources": required_sources()}


def softmax_catalog_entry():
    item = catalog_entry()
    item.update(id=SOFTMAX_ID, title="Optional CD19 L1 softmax model follow-up", description="Expensive optional follow-up: fit separate L1 multinomial models to combined-mutation reporter measurements using C=10 and bounded iterations. May take several minutes; convergence failures remain incomplete. No held-out validation or exact reproduction of paper calls is claimed. Use direct discovery first.")
    item["followup_only"] = True
    item["runtime_expectation"] = "Several minutes to tens of minutes on CPU; bounded at1500 iterations per replicate; no automatic retry."
    return item


def _references():
    manifest = json.loads(base._bounded_bytes(base.CASE_ROOT / "MANIFEST.json", base.MAX_MANIFEST_BYTES))
    refs, inputs = {}, []
    for name, (expected, url) in _REFERENCES.items():
        relative = "sources/cd19-discovery/" + name
        path = (base.CASE_ROOT / relative).resolve()
        if not path.is_relative_to((base.CASE_ROOT / "sources").resolve()):
            raise base.SourceIntegrityError("Discovery reference escapes the pinned sources")
        data = base._bounded_bytes(path, base.MAX_FILE_BYTES)
        checksum = hashlib.sha256(data).hexdigest()
        entries = [r for r in manifest["source_files"] if r["path"] == relative]
        if checksum != expected or len(entries) != 1 or entries[0]["sha256"] != expected or entries[0]["bytes"] != len(data):
            raise base.SourceIntegrityError("CD19 discovery reference does not match its recipe pin: " + name)
        refs[name] = data
        inputs.append({"path": relative, "name": name, "url": url, "sha256": checksum,
                       "bytes": len(data), "locator": "Complete pinned reference; author commit " + COMMIT})
    return refs, inputs


def _tokens(value):
    if value == "-":
        return frozenset()
    tokens = value.split(",")
    if not value or len(tokens) != len(set(tokens)) or any(not re.fullmatch(r"[ACGT]+[1-9][0-9]*[ACGT]+", t) for t in tokens):
        raise base.AnalysisInputError("Missing or malformed RNA mutation annotation is not a wild-type control")
    return frozenset(tokens)


def _classify(tokens, barcode, dna, dna_all):
    """Missing dictionary identity alone can never assign WT status."""
    if not tokens:
        return "wild_type" if not dna.get(barcode, set()) else "discordant"
    if barcode not in dna_all:
        return "unresolved_variant_barcode"
    return "mutated" if tokens == dna.get(barcode, set()) else "discordant"


def _sequence_reference(refs):
    fasta = refs["CD19_WT.minigene.fa"].decode().splitlines()
    sequence = "".join(line.strip() for line in fasta if not line.startswith(">")).upper()
    if len(sequence) > 10000 or not re.fullmatch("[ACGT]+", sequence):
        raise base.AnalysisInputError("Invalid author minigene reference")
    exons = []
    for line in refs["CD19_WT.minigene.anno.gtf"].decode().splitlines():
        parts = line.split("\t")
        if len(parts) == 9 and parts[2] == "exon":
            start, end = int(parts[3]), int(parts[4])
            if not 1 <= start <= end <= len(sequence):
                raise base.AnalysisInputError("Author exon outside minigene sequence")
            exons.append([start, end])
    if exons != [[69, 218], [476, 742], [1041, 1244]]:
        raise base.AnalysisInputError("Unexpected author exon annotation for this recipe")
    return sequence, exons


def _qualify(dna, rna, reference):
    # Paper Methods explicitly engineered G748T in the assay baseline.
    # Original author FASTA remains unchanged; record the exact transform.
    if reference[747] != "G":
        raise base.AnalysisInputError("Unexpected pre-transform base at author position748")
    assay_reference = reference[:747] + "T" + reference[748:]
    dmap, all_barcodes = defaultdict(set), set()
    orientation_errors = ref_errors = low_penetrance = 0
    complement = str.maketrans("ACGT", "TGCA")
    for line, row in dna:
        barcode = row["RNA_BARCODE"]
        if not re.fullmatch("[ACGT]{1,32}", barcode) or row["BARCODE"].translate(complement)[::-1] != barcode:
            orientation_errors += 1
        pos = base._nonnegative_int(row["POS"], "DNA POS")
        ref, alt = row["REF"], row["ALT"]
        if not re.fullmatch("[ACGT]+", ref) or not re.fullmatch("[ACGT]+", alt) or pos < 1 or assay_reference[pos - 1:pos - 1 + len(ref)] != ref:
            ref_errors += 1
        penetrance = float(row["PENETRANCE"])
        if not np.isfinite(penetrance) or not 0 <= penetrance <= 1:
            raise base.AnalysisInputError("Invalid DNA penetrance")
        all_barcodes.add(barcode)
        if penetrance >= 0.8:
            dmap[barcode].add(ref + str(pos) + alt)
        else:
            low_penetrance += 1
    if orientation_errors or ref_errors:
        raise base.AnalysisInputError("DNA barcode orientation or reference allele fails author sequence qualification")
    qualified, excluded, keys, counts = [], [], set(), Counter()
    for line, row in rna:
        key = (row["replicate"], row["barcode"])
        if key in keys or row["replicate"] not in ("1", "2"):
            raise base.AnalysisInputError("Duplicate RNA barcode/replicate or unknown replicate label")
        keys.add(key)
        if not re.fullmatch("[ACGT]{1,32}", row["barcode"]):
            raise base.AnalysisInputError("Malformed RNA barcode")
        tokens = _tokens(row["mutations"])
        status = _classify(tokens, row["barcode"], dmap, all_barcodes)
        counts[status] += 1
        depth = base._nonnegative_int(row["readcount"], "RNA readcount")
        if depth <= 0:
            raise base.AnalysisInputError("Zero RNA readcount cannot define isoform frequencies")
        values = np.array([base._nonnegative_int(row[col], col) for col in MAJOR.values()], dtype=float)
        if values.sum() > depth:
            raise base.AnalysisInputError("Major isoform counts exceed reported RNA readcount")
        fractions = np.append(values / depth, 1 - values.sum() / depth)
        record = {"line": line, "barcode": row["barcode"], "replicate": row["replicate"], "tokens": tokens,
                  "status": status, "readcount": depth, "fractions": fractions, "raw": row}
        if status in ("wild_type", "mutated"):
            qualified.append(record)
        else:
            excluded.append({"line": line, "barcode": row["barcode"], "replicate": row["replicate"], "reason": status})
    audit = {"dna_variant_rows": len(dna), "rna_rows": len(rna),
             "dna_barcode_length_row_counts": dict(sorted(Counter(str(len(row["RNA_BARCODE"])) for _, row in dna).items())),
             "rna_barcode_length_row_counts": dict(sorted(Counter(str(len(row["barcode"])) for _, row in rna).items())), "dna_low_penetrance_rows_excluded_from_calls": low_penetrance,
             "barcode_orientation_errors": orientation_errors, "reference_allele_errors": ref_errors,
             "assay_baseline_reference_adjustment": {"position_1based":748,"author_reference":"G","experimental_WT":"T","source":DOI,"locator":"Methods / Cloning and mutagenesis of the CD19 minigene", "assay_reference_sha256":hashlib.sha256(assay_reference.encode()).hexdigest()},
             "row_classifications": dict(counts), "unresolved_or_discordant_rows_excluded": len(excluded),
             "excluded_examples": excluded[:20], "excluded_records_sha256": base._hash_json(excluded),
             "no_dna_variant_row_barcodes": len({r['barcode'] for r in qualified if r['barcode'] not in all_barcodes}),
             "no_dna_row_control_basis": "RNA mutations is explicitly '-' and no penetrance-qualified DNA variants; exact barcode identity is preserved. Missing DNA dictionary keys with nonempty mutations are unresolved, never WT.",
             "rna_rows_below_paper_100_read_filter": sum(r['readcount'] < 100 for r in qualified),
             "below_100_policy": "Retain published processed rows for direct descriptive summaries; exclude readcount<100 from regression.",
             "correction_of_prior_qc": "ANALYSIS-CD19-QC counted unmatched variant-table barcodes. It did not establish missing data. Explicit unmutated RNA annotations plus paper Methods resolve these as control barcodes; old evidence is preserved."}
    if len(qualified) > 2 * MAX_BARCODES:
        raise base.AnalysisInputError("Qualified barcode count exceeds recipe bound")
    return qualified, audit


def _number(value):
    return round(float(value), 10)


def _vector(array):
    return {key: _number(value) for key, value in zip(LABELS, array, strict=True)}


def _wt_summaries(rows):
    result, baseline = {}, {}
    for rep in ("1", "2"):
        wt = [r for r in rows if r["replicate"] == rep and r["status"] == "wild_type"]
        if len(wt) < 3:
            raise base.AnalysisInputError("Insufficient explicit unmutated controls for empirical ranges")
        values = np.array([r["fractions"] for r in wt])
        mean = values.mean(axis=0)
        lower, upper = np.quantile(values, [0.025, 0.975], axis=0)
        baseline[rep] = (mean, lower, upper)
        result[rep] = {"barcode_count": len(wt), "mean": _vector(mean), "sd": _vector(values.std(axis=0, ddof=1)),
                       "empirical_2_5_percentile": _vector(lower), "empirical_97_5_percentile": _vector(upper),
                       "reference_background": "Engineered G748T assay baseline; WT denotes unmutated relative to this baseline",
                       "range_interpretation": "Central empirical control distribution; not a confidence interval on a mutant effect and not multiplicity-adjusted."}
    return result, baseline


def _concordant(predictions, baseline):
    changes = []
    for i, name in enumerate(LABELS[:-1]):
        first, second = predictions["1"][i], predictions["2"][i]
        if all(predictions[rep][i] > baseline[rep][2][i] for rep in ("1", "2")):
            changes.append({"isoform": name, "direction": "increase"})
        elif all(predictions[rep][i] < baseline[rep][1][i] for rep in ("1", "2")):
            changes.append({"isoform": name, "direction": "decrease"})
    return changes


def _direct_singles(rows, baseline):
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if len(row["tokens"]) == 1:
            groups[next(iter(row["tokens"]))][row["replicate"]].append(row)
    records = []
    for token, reps in sorted(groups.items()):
        if set(reps) != {"1", "2"}:
            continue
        observed = {rep: np.mean([r["fractions"] for r in rs], axis=0) for rep, rs in reps.items()}
        effects = _concordant(observed, baseline)
        records.append({"variant": token, "measurement_status": "one additional called mutation relative to engineered G748T assay baseline; not a patient variant",
                        "replicates": {rep: {"barcodes": [r["barcode"] for r in rs], "source_lines": [r["line"] for r in rs],
                                               "readcounts": [r["readcount"] for r in rs], "isoform_fractions": _vector(observed[rep]),
                                               "delta_from_wt_mean": _vector(observed[rep] - baseline[rep][0])} for rep, rs in reps.items()},
                        "replicate_concordant_outside_control_range": effects})
    records.sort(key=lambda r: (-min(abs(r['replicates'][rep]['delta_from_wt_mean']['inclusion']) for rep in ('1', '2')), r['variant']))
    return {"reference_background": "Engineered assay reference with G748T. Single-mutant means one additional called mutation, not one difference from the native genomic sequence.", "variant_count_measured_in_both_replicates": len(records), "variant_count_outside_control_range_in_both": sum(bool(r['replicate_concordant_outside_control_range']) for r in records),
            "ranking": "Minimum absolute inclusion difference across replicates, descending; exploratory ranking, not significance.", "all_variant_records_sha256": base._hash_json(records), "reported_top_variants": min(12, len(records)), "variants": records[:12],
            "uncertainty": "Most variants have one reporter barcode measured in two experimental replicates. No independent mutant-barcode confidence interval or clinical effect estimate is identifiable."}


def _matrix(rows, tokens):
    index = {token: i for i, token in enumerate(tokens)}
    rr, cc = [], []
    for row_num, row in enumerate(rows):
        for token in sorted(row["tokens"]):
            if token in index:
                rr.append(row_num); cc.append(index[token])
    return sparse.csr_matrix((np.ones(len(rr)), (rr, cc)), shape=(len(rows), len(tokens)))


def _fit_model(x, y):
    """Fractional multinomial labels via weighted expansion, one unit/barcode."""
    expanded = x[np.repeat(np.arange(x.shape[0]), len(LABELS))]
    target = np.tile(np.arange(len(LABELS)), x.shape[0])
    weight = y.ravel()
    # Explicit fixed seed + one numerical thread; bounded sparse matrix only.
    model = LogisticRegression(solver="saga", l1_ratio=1.0, C=10, fit_intercept=True,
                               max_iter=MODEL_MAX_ITER, tol=MODEL_TOL, random_state=MODEL_SEED)
    with warnings.catch_warnings(record=True) as observed, threadpool_limits(limits=1):
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(expanded, target, sample_weight=weight)
    converged = not any(issubclass(w.category, ConvergenceWarning) for w in observed)
    return model, converged


def _correlations(observed, predicted):
    return {key: _number(np.corrcoef(observed[:, i], predicted[:, i])[0, 1])
            if np.std(observed[:, i]) > 0 and np.std(predicted[:, i]) > 0 else None
            for i, key in enumerate(LABELS)}


def _softmax_analysis(rows, common, baseline):
    eligible = {rep: [r for r in rows if r['replicate'] == rep and r['barcode'] in common
                      and r['readcount'] >= 100 and r['fractions'][-1] <= 0.05 + 1e-12] for rep in ('1', '2')}
    tokens = sorted({t for rs in eligible.values() for r in rs for t in r['tokens']})
    if not tokens or len(tokens) > MAX_MUTATIONS:
        raise base.AnalysisInputError("Mutation design exceeds recipe bounds or is empty")
    predictions, support, fit_records = {}, {}, {}
    for rep, rs in eligible.items():
        x = _matrix(rs, tokens)
        y = np.array([r['fractions'] for r in rs])
        model, converged = _fit_model(x, y)
        support[rep] = np.asarray(x.sum(axis=0)).ravel().astype(int)
        predictions[rep] = softmax(model.coef_.T + model.intercept_, axis=1)
        fit_records[rep] = {"barcodes": len(rs), "wt_barcodes": sum(r['status'] == 'wild_type' for r in rs),
                            "observed_mutation_features": int(np.count_nonzero(support[rep])),
                            "iterations": int(model.n_iter_[0]), "converged": converged,
                            "training_pearson_r": _correlations(y, model.predict_proba(x)),
                            "training_correlation_is_validation": False}
    both_converged = all(r['converged'] for r in fit_records.values())
    ranked = []
    for i, token in enumerate(tokens):
        if not both_converged or any(support[rep][i] < 3 for rep in ('1', '2')):
            continue
        pred = {rep: predictions[rep][i] for rep in ('1', '2')}
        effects = _concordant(pred, baseline)
        if not effects:
            continue
        delta = {rep: pred[rep] - baseline[rep][0] for rep in ('1', '2')}
        score = max(min(abs(delta[rep][list(LABELS).index(effect['isoform'])]) for rep in ('1', '2')) for effect in effects)
        ranked.append({"variant": token, "variant_type": "SNV" if re.fullmatch(r'[ACGT][0-9]+[ACGT]', token) else "indel",
                       "rank_score": _number(score), "background_count": {rep: int(support[rep][i]) for rep in ('1', '2')},
                       "predicted_single_mutant_fractions": {rep: _vector(pred[rep]) for rep in ('1', '2')},
                       "delta_from_empirical_wt_mean": {rep: _vector(delta[rep]) for rep in ('1', '2')},
                       "replicate_concordant_outside_control_range": effects})
    ranked.sort(key=lambda r: (-r['rank_score'], r['variant']))
    return {"status": "completed_method_matched_partial_reproduction" if both_converged else "incomplete_optimizer_did_not_converge",
            "fits": fit_records, "mutation_features": len(tokens),
            "both_replicates_minimum_three_backgrounds": sum(all(support[rep][i] >= 3 for rep in ('1', '2')) for i in range(len(tokens))),
            "exploratory_concordant_candidate_count": len(ranked), "candidate_table_sha256": base._hash_json(ranked),
            "top_candidates": ranked[:20], "ranking": "Largest replicated absolute isoform shift; minimum three qualifying backgrounds in each replicate. Exploratory control-range rule, not FDR significance.",
            "validation_status": "Training fit only; no held-out validation performed by this recipe. The paper's tenfold correlations and 193 calls are not reproduced claims.",
            "uncertainty": "Empirical WT ranges do not quantify regression parameter uncertainty; correlated mutations, limited backgrounds, regularization and denominator choices can alter rankings."}


def _cryptic_associations(rows, common, columns):
    tokens = sorted({t for r in rows if r['barcode'] in common for t in r['tokens']})
    if len(tokens) > MAX_MUTATIONS:
        raise base.AnalysisInputError("Cryptic analysis mutation bound exceeded")
    cryptic = [c for c in columns if c.startswith('(') and c not in MAJOR.values()]
    if len(cryptic) > 150:
        raise base.AnalysisInputError("Cryptic isoform column bound exceeded")
    scores, details = {}, {}
    for rep in ('1', '2'):
        rs = [r for r in rows if r['replicate'] == rep and r['barcode'] in common]
        x = _matrix(rs, tokens)
        high = np.array([[base._nonnegative_int(r['raw'][c], c) / r['readcount'] > .05 for c in cryptic] for r in rs], dtype=float)
        joint = np.asarray(x.T @ high)
        mut_counts = np.asarray(x.sum(axis=0)).ravel()
        high_counts = high.sum(axis=0)
        denominator = mut_counts[:, None] * high_counts[None, :]
        score = np.divide(joint ** 2, denominator, out=np.zeros_like(joint), where=denominator > 0)
        scores[rep] = score
        details[rep] = (joint, mut_counts, high_counts)
    pairs = []
    for i, j in zip(*np.where(np.minimum(scores['1'], scores['2']) > .25)):
        if any(details[rep][1][i] < 3 for rep in ('1', '2')):
            continue
        pairs.append({"variant": tokens[i], "isoform_junctions": cryptic[j], "rank_score": _number(min(scores[rep][i, j] for rep in ('1', '2'))),
                      "replicates": {rep: {"prevalence_score": _number(scores[rep][i, j]), "joint_high_and_mutated": int(details[rep][0][i, j]),
                                             "mutation_backgrounds": int(details[rep][1][i]), "high_isoform_barcodes": int(details[rep][2][j])} for rep in ('1', '2')}})
    pairs.sort(key=lambda p: (-p['rank_score'], p['variant'], p['isoform_junctions']))
    return {"cryptic_isoforms_tested": len(cryptic), "replicate_concordant_pairs_above_threshold": len(pairs),
            "all_pairs_sha256": base._hash_json(pairs), "top_pairs": pairs[:20],
            "formula": "P(mutation | isoform fraction>0.05) * P(isoform fraction>0.05 | mutation) = joint^2/(mutation_count * high_isoform_count)",
            "selection": "Score>0.25 and mutation in>=3 barcodes in each replicate; common barcode cohort; source readcount denominator. Same barcode library is reused across replicates.",
            "interpretation": "Association in combinatorially mutated reporters; co-occurring variants may confound it. Not a causal mutation assignment or patient prevalence."}


def _structure_mapping(refs, sequence, exons):
    from Bio.Seq import Seq
    canonical = json.loads(refs['P15391.json'])['sequence']['value']
    transcript = ''.join(sequence[start - 1:end] for start, end in exons)
    skipped = ''.join(sequence[start - 1:end] for i, (start, end) in enumerate(exons) if i != 1)
    start = transcript.find('ATG')
    if start < 0 or skipped.find('ATG') != start:
        raise base.AnalysisInputError("Author transcript start codon cannot be qualified")
    def translate(s):
        coding = s[start:]
        return str(Seq(coding[:len(coding) // 3 * 3]).translate())
    wt, delta = translate(transcript), translate(skipped)
    candidates = [(i + 1, i + len(wt) - len(delta)) for i in range(len(wt) - len(delta) + 1)
                  if wt[:i] + wt[i + len(wt) - len(delta):] == delta]
    if not canonical.startswith(wt) or len(candidates) != 1:
        raise base.AnalysisInputError("Translated author isoform does not uniquely map to canonical CD19")
    first, last = candidates[0]
    return {"author_exons_1based_inclusive": exons, "minigene_length_nt": len(sequence),
            "wt_spliced_length_nt": len(transcript), "skipped_spliced_length_nt": len(skipped),
            "start_codon_spliced_offset_0based": start, "translated_complete_codon_lengths": {"wt": len(wt), "exon2_skip": len(delta)},
            "wt_matches_canonical_prefix": True, "unique_inframe_deleted_residues_1based_inclusive": [first, last],
            "uniprot_accession": "P15391", "canonical_sequence_length": len(canonical),
            "canonical_sequence_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "interpretation": "Author minigene sequence independently validates an in-frame exon2-skipping protein deletion. Only a partial coding region is represented; a full ectodomain construct requires explicit canonical extension. This is sequence mapping, not a structure prediction, surface localization measurement, or binder affinity result."}


def analyze(*, include_softmax=False):
    refs, inputs = _references()
    sequence, exons = _sequence_reference(refs)
    dna_raw, dna_source = base._load_source('cd19_dna')
    rna_raw, rna_source = base._load_source('cd19_rna')
    if dna_source['sha256'] != _DNA_SHA or rna_source['sha256'] != _RNA_SHA:
        raise base.SourceIntegrityError("CD19 raw table identity differs from this versioned discovery recipe")
    _, dna = base._tsv(dna_raw, compressed=True, required=('RNA_BARCODE', 'BARCODE', 'POS', 'REF', 'ALT', 'PENETRANCE'))
    columns, rna = base._tsv(rna_raw, compressed=True, required=('replicate', 'barcode', 'mutations', 'readcount', *MAJOR.values()))
    rows, audit = _qualify(dna, rna, sequence)
    common = {r['barcode'] for r in rows if r['replicate'] == '1'} & {r['barcode'] for r in rows if r['replicate'] == '2'}
    audit['shared_barcode_cohort'] = len(common)
    audit['shared_mutated_barcode_cohort'] = len({r['barcode'] for r in rows if r['barcode'] in common and r['status'] == 'mutated'})
    wt, baseline = _wt_summaries(rows)
    direct = _direct_singles(rows, baseline)
    cryptic = _cryptic_associations(rows, common, columns)
    fitted = _softmax_analysis(rows, common, baseline) if include_softmax else {"status":"not_run", "reason":"Separate optional expensive follow-up; direct observations and cryptic associations are computed by this primary recipe.", "followup_analysis_id": SOFTMAX_ID, "exploratory_concordant_candidate_count":None}
    dna_source['locator'] = 'All TSV data rows; reverse-complement identity, reference allele and PENETRANCE>=0.8 calls'
    rna_source['locator'] = 'All TSV data rows; explicit mutations annotation, barcode and replicate; readcount and junction columns'
    values = {"analysis_id": SOFTMAX_ID if include_softmax else RECIPE_ID, "analysis_version": VERSION, "case_id": "cd19-car-t",
              "input_sources": [dna_source, rna_source, *inputs], "inference_performed": include_softmax,
              "inference_scope": "Local statistical softmax estimation" if include_softmax else "Descriptive single-mutant measurements and combinatorial associations; no fitted prediction",
              "qualification": audit, "wild_type_controls": wt, "observed_single_mutants": direct,
              "softmax_reanalysis": fitted, "cryptic_splicing_associations": cryptic, "sequence_mapping": _structure_mapping(refs, sequence, exons),
              "publication": {"doi": DOI, "pmcid": "PMC9500061", "author_repository_commit": COMMIT,
                              "paper_reported_separate_from_reproduction": {"shared_minigenes": 9321, "single_mutation_effects": 4255, "splicing_affecting_mutations": 193, "cross_validation": "10-fold; reported per-isoform r 0.68–0.95 and 0.71–0.93",
                                  "PTBP1_mechanism": {"kind":"literature_only_not_recomputed", "locator":"Results: Depletion of PTBP1 and several other RBPs results in non-functional CD19 isoforms; Fig6", "summary":"The authors report that PTBP1 depletion increases intron2 retention, and that PTBP1 binds CD19 intron2 in NALM-6 cells. Separate PTBP1 knockdown and flow-cytometry experiments in P493-6 and MHHCALL4 cells reduced surface CD19. These trans-regulator and protein experiments are not reproduced from the minigene mutation/count tables.", "followup":"Test cis-splicing and PTBP1-related regulation as distinct hypotheses; measure isoforms and surface-accessible antigen before inferring resistance."}}},
              "parameters": {"DNA_penetrance_minimum": 0.8, "isoforms": MAJOR, "denominator": "source readcount; residual includes all unlisted and non-major counts", "regression_common_barcodes_only": True,
                             "regression_readcount_minimum": 100, "regression_maximum_other_fraction": 0.05, "regression_method": "Sparse binary mutation indicators; six-class fractional-label multinomial logistic regression via weighted expansion; every barcode has total weight1",
                             "solver": "saga", "L1_ratio": 1, "C": 10, "seed": MODEL_SEED, "max_iter": MODEL_MAX_ITER, "tolerance": MODEL_TOL,
                             "candidate_background_minimum_each_replicate": 3, "holdout_validation_performed": False,
                             "WT_quantiles": [0.025, 0.975], "single_mutant_ranking": "Replicate-minimum absolute inclusion difference", "cryptic_threshold": 0.05},
              "limitations": ["This reanalysis uses public processed tables, not raw read re-alignment; author preprocessing is not rerun.",
                              "Exact author softmax fitting code, weighting and random split are not in the retrieved code. Our equal-barcode weighted objective, conservative denominator, explicit filter and optimizer are declared; paper call counts and cross-validation are not claimed reproduced.",
                              "Control quantiles are descriptive empirical distributions, not effect confidence intervals or multiplicity-adjusted significance. Regression rankings have no held-out validation in this recipe.",
                              "Multiple variants share reporter barcodes; fitted additivity and cryptic associations do not establish mutation causality. Same library across two experimental replicates is not independent patient replication.",
                              "Reporter RNA splicing does not demonstrate surface CD19 loss, CAR epitope accessibility, CAR-T resistance or rescue by affinity engineering; those require orthogonal experiments.",
                              "The author's in-frame exon2-skipping sequence supports a qualified structural follow-up, not a functional claim. Glycosylation, trafficking and binder interaction are not measured here."]}
    summary = (f"Source annotations resolve {audit['no_dna_variant_row_barcodes']} barcodes absent from the DNA variant table as explicit WT controls ({wt['1']['barcode_count']}/{wt['2']['barcode_count']} by replicate), with {audit['unresolved_or_discordant_rows_excluded']} unresolved or discordant rows. "
               f"The shared cohort contains {len(common):,} barcodes. Fresh analysis compares {direct['variant_count_measured_in_both_replicates']} directly measured single mutants and ranks {cryptic['replicate_concordant_pairs_above_threshold']} replicated cryptic-splicing associations. Softmax status: {fitted['status']}. RNA mechanisms remain hypotheses for protein-level testing.")
    return {"id": SOFTMAX_EVIDENCE_ID if include_softmax else EVIDENCE_ID, "title": "CD19 source-qualified variant-to-splicing discovery", "kind": "derived", "summary": summary,
            "source": {"name": "Runtime CD19 discovery reanalysis", "url": DOI, "locator": "Pinned processed GEO tables; paper Methods and author minigene annotation; canonical values JSON", "sha256": base._hash_json(values)}, "values": values}
