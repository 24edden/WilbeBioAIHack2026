"""Independent numerical anchors for source-qualified CD19 reporter reanalysis."""
import copy
import hashlib
import json
import shutil

import numpy as np
import pytest
from scipy import sparse

from app import analysis_tools as base
from app import cd19_discovery as discovery
from app.cases import SourceIntegrityError


@pytest.fixture(scope='module')
def result():
    return base.analyze_case('cart-discovery', discovery.RECIPE_ID)


def test_source_annotations_resolve_controls_without_assuming_missing_keys_are_wt(result):
    v = result['values']; q = v['qualification']
    assert q['no_dna_variant_row_barcodes'] == 195
    assert q['row_classifications'] == {'mutated':18654, 'wild_type':389}
    assert q['shared_barcode_cohort'] == 9321
    assert q['shared_mutated_barcode_cohort'] == 9127
    assert q['unresolved_or_discordant_rows_excluded'] == 0
    assert [v['wild_type_controls'][r]['barcode_count'] for r in ('1','2')] == [195,194]
    assert discovery._classify(frozenset({'A100C'}), 'MISSING', {}, set()) == 'unresolved_variant_barcode'
    assert discovery._classify(frozenset(), 'CONTROL', {}, set()) == 'wild_type'
    assert discovery._classify(frozenset(), 'DISAGREE', {'DISAGREE':{'A100C'}}, {'DISAGREE'}) == 'discordant'
    with pytest.raises(base.AnalysisInputError, match='not a wild-type'):
        discovery._tokens('')


def test_assay_reference_transformation_and_real_variable_length_barcodes(result):
    q = result['values']['qualification']
    assert q['reference_allele_errors'] == q['barcode_orientation_errors'] == 0
    assert q['assay_baseline_reference_adjustment']['position_1based'] == 748
    assert q['assay_baseline_reference_adjustment']['experimental_WT'] == 'T'
    assert q['rna_barcode_length_row_counts'] == {'14':281,'15':18660,'16':102}
    assert q['dna_low_penetrance_rows_excluded_from_calls'] == 621
    assert q['rna_rows_below_paper_100_read_filter'] == 7
    refs, _ = discovery._references()
    seq, _ = discovery._sequence_reference(refs)
    assert seq[747] == 'G'  # Original reference is never rewritten in place.
    with pytest.raises(base.AnalysisInputError, match='orientation or reference'):
        discovery._qualify([(2, {'RNA_BARCODE':'AAAA','BARCODE':'AAAA','POS':'748','REF':'T','ALT':'C','PENETRANCE':'1'})], [], seq)
    with pytest.raises(base.AnalysisInputError, match='orientation or reference'):
        discovery._qualify([(2, {'RNA_BARCODE':'AAAA','BARCODE':'TTTT','POS':'748','REF':'G','ALT':'C','PENETRANCE':'1'})], [], seq)


def test_observed_single_mutant_effects_have_exact_source_support_and_no_false_uncertainty(result):
    v = result['values']; direct = v['observed_single_mutants']
    assert direct['variant_count_measured_in_both_replicates'] == 56
    assert direct['variant_count_outside_control_range_in_both'] == 8
    top = direct['variants'][0]
    assert top['variant'] == 'A746G'
    assert top['replicates']['1']['barcodes'] == top['replicates']['2']['barcodes'] == ['GGTCACATTCGGTT']
    assert top['replicates']['1']['source_lines'] == [5895]
    assert top['replicates']['2']['source_lines'] == [15400]
    assert top['replicates']['1']['readcounts'] == [375]
    assert top['replicates']['2']['readcounts'] == [1022]
    assert top['replicates']['1']['isoform_fractions']['exon2_skipping'] == pytest.approx(339/375)
    assert top['replicates']['2']['isoform_fractions']['exon2_skipping'] == pytest.approx(942/1022)
    assert v['wild_type_controls']['1']['mean']['exon2_skipping'] == pytest.approx(.0715740437)
    assert v['wild_type_controls']['2']['mean']['exon2_skipping'] == pytest.approx(.1426766016)
    assert 'No independent mutant-barcode confidence interval' in direct['uncertainty']
    assert direct['reported_top_variants'] == len(direct['variants']) == 12
    assert len(direct['all_variant_records_sha256']) == 64


def test_cryptic_prevalence_is_joint_squared_over_marginals_not_p_value(result):
    c = result['values']['cryptic_splicing_associations']
    assert c['cryptic_isoforms_tested'] == 96
    assert c['replicate_concordant_pairs_above_threshold'] == 30
    first = c['top_pairs'][0]
    assert (first['variant'], first['isoform_junctions']) == ('C864G','(219 475)(864 1040)')
    assert first['rank_score'] == 1
    for pair in c['top_pairs']:
        for r in pair['replicates'].values():
            assert r['prevalence_score'] == pytest.approx(r['joint_high_and_mutated']**2/(r['mutation_backgrounds']*r['high_isoform_barcodes']))
            assert r['mutation_backgrounds'] >= 3
    assert 'co-occurring variants may confound' in c['interpretation']


def test_primary_has_no_expensive_fit_or_paper_discovery_substitution(result, monkeypatch):
    assert result['values']['softmax_reanalysis']['status'] == 'not_run'
    assert result['values']['inference_performed'] is False
    reported = result['values']['publication']['paper_reported_separate_from_reproduction']
    assert reported['splicing_affecting_mutations'] == 193
    assert reported['PTBP1_mechanism']['kind'] == 'literature_only_not_recomputed'
    def reject(*args, **kwargs):
        raise AssertionError('Primary recipe must not fit a softmax model')
    monkeypatch.setattr(discovery, '_softmax_analysis', reject)
    assert base.analyze_case('cd19-car-t', discovery.RECIPE_ID)['id'] == discovery.EVIDENCE_ID
    optional = next(c for c in base.analysis_catalog('cart-discovery') if c['id'] == discovery.SOFTMAX_ID)
    assert optional['followup_only'] is True
    assert 'minutes' in optional['runtime_expectation']


def test_translated_isoform_maps_uniquely_to_canonical_inframe_deletion(result):
    mapping = result['values']['sequence_mapping']
    assert mapping['unique_inframe_deleted_residues_1based_inclusive'] == [30,118]
    assert mapping['translated_complete_codon_lengths'] == {'wt':186,'exon2_skip':97}
    assert mapping['wt_matches_canonical_prefix'] is True
    assert mapping['wt_spliced_length_nt'] - mapping['skipped_spliced_length_nt'] == 267
    assert mapping['canonical_sequence_length'] == 556
    assert 'not a structure prediction' in mapping['interpretation']


def test_evidence_compact_identity_hash_and_required_sources_are_pinned(result):
    assert len(json.dumps(result, ensure_ascii=False)) < 80_000
    assert result['source']['sha256'] == base._hash_json(result['values'])
    assert result['values']['case_id'] == 'cart-discovery'
    assert result['values']['source_case_id'] == 'cd19-car-t'
    assert result['values']['analysis_version'] == 'cd19-discovery-1.0'
    assert {r['path']:r['sha256'] for r in result['values']['input_sources']} == {r['path']:r['sha256'] for r in discovery.required_sources()}
    for source in result['values']['input_sources']:
        assert hashlib.sha256((base.CASE_ROOT/source['path']).read_bytes()).hexdigest() == source['sha256']
    assert result == base.analyze_case('cart-discovery', discovery.RECIPE_ID)


def test_mutated_author_reference_fails_before_computation(tmp_path, monkeypatch):
    target = tmp_path/'casepacks'
    shutil.copytree(base.CASE_ROOT/'sources/cd19-discovery', target/'sources/cd19-discovery')
    shutil.copyfile(base.CASE_ROOT/'MANIFEST.json', target/'MANIFEST.json')
    changed = target/'sources/cd19-discovery/CD19_WT.minigene.fa'
    changed.write_bytes(changed.read_bytes()+b'\n')
    monkeypatch.setattr(base,'CASE_ROOT',target)
    with pytest.raises(SourceIntegrityError, match='recipe pin'):
        discovery.analyze()


def test_optional_fractional_multinomial_fit_computes_valid_probabilities_on_small_fixture(monkeypatch):
    # Synthetic software fixture only; it is never an empirical evidence source.
    x = sparse.csr_matrix([[0],[0],[1],[1]]*8, dtype=float)
    y = np.array([[.70,.10,.05,.05,.05,.05],[.70,.10,.05,.05,.05,.05],
                  [.15,.65,.05,.05,.05,.05],[.15,.65,.05,.05,.05,.05]]*8)
    monkeypatch.setattr(discovery, 'MODEL_MAX_ITER', 1000)
    model, converged = discovery._fit_model(x,y)
    pred = model.predict_proba(sparse.csr_matrix([[0],[1]],dtype=float))
    assert converged
    assert pred.shape == (2,6)
    assert np.allclose(pred.sum(axis=1),1)
    assert pred[1,1] > pred[0,1] + .4
    assert pred[1,0] < pred[0,0] - .4


def test_nonconverged_optional_fit_cannot_emit_candidate_claims(monkeypatch, result):
    class MockModel:
        coef_ = np.zeros((6,1)); intercept_ = np.zeros(6); n_iter_ = [1]
        def predict_proba(self,x): return np.tile(np.ones(6)/6,(x.shape[0],1))
    monkeypatch.setattr(discovery,'_fit_model',lambda x,y:(MockModel(),False))
    fractions=np.array([.8,.1,.025,.025,.025,.025])
    rows=[{'replicate':rep,'barcode':'same','tokens':frozenset({'A100C'}),'readcount':100,
           'fractions':fractions,'status':'mutated'} for rep in ('1','2')]
    baseline={rep:(fractions,np.zeros(6),np.ones(6)) for rep in ('1','2')}
    fit=discovery._softmax_analysis(rows,{'same'},baseline)
    assert fit['status'] == 'incomplete_optimizer_did_not_converge'
    assert fit['top_candidates'] == []
    assert fit['exploratory_concordant_candidate_count'] == 0
