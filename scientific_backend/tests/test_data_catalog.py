"""Small synthetic software fixtures test real readers; these are not case data."""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

import h5py
import numpy as np
import pytest

from app import data_catalog as catalog
from app.cases import SourceIntegrityError, get_case


@pytest.fixture
def registry(tmp_path, monkeypatch):
    data = {"version": "test", "inventory_date": "test", "selection_rule": "synthetic software fixtures", "datasets": [{"id": "TEST", "title": "Test", "description": "Software fixture", "files_count": 0, "bytes": 0}], "files": []}
    monkeypatch.setattr(catalog, "_registry", lambda: copy.deepcopy(data))
    monkeypatch.setattr(catalog, "_roots", lambda: {"shared": tmp_path})
    catalog._HASH_CACHE.clear()
    def add(name, content=None, member=None, parent=None):
        path = tmp_path / name
        if content is not None: path.write_bytes(content)
        raw = path.read_bytes()
        record = {"id": "test-"+str(len(data['files'])), "dataset_id": "TEST", "root": "shared", "relative_path": name, "name": member or name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "source_url": "https://example.invalid/software-fixture", "member": member}
        if member:
            with tarfile.open(path) as archive: record['bytes'] = archive.getmember(member).size
            record.update(parent_sha256=record.pop('sha256'), archive_id=parent)
        data['files'].append(record)
        return record['id']
    return tmp_path, data, add


def make_h5(path, change=None):
    with h5py.File(path, 'w') as data:
        group = data.create_group('matrix')
        group['shape'] = np.array([3, 3], dtype='int64')
        group['data'] = np.array([1, 2, 3, 4, 5], dtype='int64')
        group['indices'] = np.array([0, 2, 1, 0, 2], dtype='int64')
        group['indptr'] = np.array([0, 2, 3, 5], dtype='int64')
        feat = group.create_group('features')
        feat['name'] = np.array([b'CD19', b'TNFRSF17', b'CD3D'])
        feat['id'] = np.array([b'id1', b'id2', b'id3'])
        feat['feature_type'] = np.array([b'Gene Expression']*3)
        if change: change(data)


def tar_bytes(files, compressed=False):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz' if compressed else 'w') as archive:
        for name, content in files.items():
            item = tarfile.TarInfo(name); item.size = len(content)
            archive.addfile(item, io.BytesIO(content))
    return buf.getvalue()


MATRIX = b'%%MatrixMarket matrix coordinate integer general\n% fixture\n3 3 5\n1 1 1\n3 1 2\n2 2 3\n1 3 4\n3 3 5\n'
FEATURES = b'id1\tCD19\tGene Expression\nid2\tTNFRSF17\tGene Expression\nid3\tCD3D\tGene Expression\n'


def test_actual_inventory_and_original_hypothesis():
    result = catalog.list_datasets()
    assert len(result['datasets']) == 22
    assert {d['id'] for d in result['datasets']} >= {'GSE164551', 'GSE234261', 'LEON-BCMA', 'TEAM-HYPOTHESES', 'GSE28460'}
    case = get_case('cart-discovery')
    assert case['hypothesis'] == get_case('cd19-car-t')['hypothesis']
    assert case['evidence'][0]['values']['files_count'] == 734
    assert case['evidence'][0]['values']['verification'] == 'catalog-unverified'


def test_table_prefix_is_explicit_and_hash_validated(registry):
    _, _, add = registry
    file_id = add('table.tsv.gz', gzip.compress(b'id\tvalue\na\t2\nb\t4\nc\tNA\n'))
    result = catalog.analyze_data_file(file_id, 'table_profile', {'max_rows': 2, 'selected_columns': ['value']})
    values = result['values']['result']
    assert values['complete'] is False
    assert values['rows_profiled'] == 2
    assert values['column_summaries']['value']['mean_of_numeric_values'] == 3
    catalog.validate_catalog_evidence(result)
    result['values']['result']['rows_profiled'] = 3
    with pytest.raises(catalog.CatalogAnalysisError): catalog.validate_catalog_evidence(result)


def test_rehashed_result_cannot_replace_pinned_raw_source(registry):
    _, _, add = registry
    file_id = add('data.tsv', b'id\tcount\na\t2\n')
    evidence = catalog.analyze_data_file(file_id, 'table_profile')
    evidence['values']['input_sources'][0]['sha256'] = '0'*64
    evidence['source']['sha256'] = catalog._sha(catalog._canonical(evidence['values']))
    with pytest.raises(SourceIntegrityError): catalog.validate_catalog_evidence(evidence)


def test_source_mutation_invalidates_hash_cache(registry):
    root, _, add = registry
    file_id = add('data.tsv', b'id\tcount\na\t2\n')
    catalog.analyze_data_file(file_id, 'table_profile')
    (root/'data.tsv').write_bytes(b'id\tcount\na\t3\n')
    with pytest.raises(SourceIntegrityError): catalog.analyze_data_file(file_id, 'table_profile')


def test_same_stat_signature_cannot_hide_rewritten_source(registry, monkeypatch):
    root, _, add = registry
    file_id = add('data.tsv', b'id\tcount\na\t2\n')
    signature = catalog._stat(root/'data.tsv')
    monkeypatch.setattr(catalog, '_stat', lambda _: signature)
    catalog.analyze_data_file(file_id, 'table_profile')
    (root/'data.tsv').write_bytes(b'id\tcount\na\t3\n')
    with pytest.raises(SourceIntegrityError): catalog.analyze_data_file(file_id, 'table_profile')


@pytest.mark.parametrize('parameters', [{'path':'/etc/passwd'}, {'max_rows':True}, {'max_rows':100001}, [], '', False, 0])
def test_parameters_do_not_accept_paths_or_unbounded_work(registry, parameters):
    _, _, add = registry
    file_id = add('data.tsv', b'a\n1\n')
    with pytest.raises(catalog.CatalogAnalysisError): catalog.analyze_data_file(file_id, 'table_profile', parameters)


def test_unknown_id_and_registry_path_escape_block(registry):
    _, data, add = registry
    with pytest.raises(catalog.CatalogAnalysisError): catalog.inspect_data_file('/etc/passwd')
    file_id = add('data.tsv', b'a\n1\n')
    data['files'][0]['relative_path'] = '../outside'
    with pytest.raises(catalog.CatalogAnalysisError): catalog.inspect_data_file(file_id)


def test_sparse_h5_gene_counts_match_known_matrix(registry):
    root, _, add = registry
    make_h5(root/'matrix.h5'); file_id = add('matrix.h5')
    evidence = catalog.analyze_data_file(file_id, 'gene_summary', {'genes':['CD19','TNFRSF17','absent']})
    values = evidence['values']['result']
    assert values['total_counts'] == 15
    assert values['genes'][0]['sum'] == 5
    assert values['genes'][0]['nonzero_barcodes'] == 2
    assert values['genes'][1]['sum'] == 3
    assert values['missing_genes'] == ['absent']
    assert values['dense_matrix_allocated'] is False
    catalog.validate_catalog_evidence(evidence)


@pytest.mark.parametrize('malformation', ['short_types', 'shape', 'soft_matrix', 'external_feature', 'virtual_data'])
def test_malformed_or_external_h5_rejected_before_analysis(registry, malformation):
    root, _, add = registry
    def change(data):
        if malformation == 'short_types':
            del data['matrix/features/feature_type']; data['matrix/features/feature_type'] = np.array([b'Gene Expression'])
        elif malformation == 'shape':
            del data['matrix/shape']; data['matrix/shape'] = np.array([3,3,3])
        elif malformation == 'soft_matrix':
            data.move('matrix', 'elsewhere'); data['matrix'] = h5py.SoftLink('/elsewhere')
        elif malformation == 'external_feature':
            del data['matrix/features/name']; data['matrix/features/name'] = h5py.ExternalLink('/does/not/exist.h5','/names')
        else:
            del data['matrix/data']; layout = h5py.VirtualLayout(shape=(5,), dtype='int64')
            layout[:] = h5py.VirtualSource('/does/not/exist.h5', '/data', shape=(5,))
            data['matrix'].create_virtual_dataset('data', layout)
    make_h5(root/'bad.h5', change); file_id = add('bad.h5')
    with pytest.raises(catalog.CatalogAnalysisError): catalog.analyze_data_file(file_id, 'gene_summary', {'genes':['CD19']})


def test_mtx_companion_ids_and_counts(registry):
    _, _, add = registry
    file_id = add('sample_matrix.mtx.gz', gzip.compress(MATRIX))
    features_id = add('sample_features.tsv.gz', gzip.compress(FEATURES))
    evidence = catalog.analyze_data_file(file_id, 'gene_summary', {'genes':['CD19']})
    assert evidence['values']['result']['genes'][0]['sum'] == 5
    assert [v['file_id'] for v in evidence['values']['input_sources']] == [file_id, features_id]
    catalog.validate_catalog_evidence(evidence)


def test_legacy_mtx_features_do_not_qualify_an_arbitrary_modality(registry):
    _, _, add = registry
    file_id = add('sample_matrix.mtx', MATRIX)
    add('sample_genes.tsv', b'id1\tCD19\nid2\tTNFRSF17\nid3\tCD3D\n')
    output = catalog.analyze_data_file(file_id, 'gene_summary', {'genes':['CD19']})
    assert output['values']['result']['genes'][0]['sum'] == 5
    for modality in ['Antibody Capture', '', '  ']:
        with pytest.raises(catalog.CatalogAnalysisError):
            catalog.analyze_data_file(file_id, 'gene_summary', {'genes':['CD19'], 'feature_type':modality})


def test_registered_outer_archive_member_and_nested_bundle(registry):
    _, _, add = registry
    bundle = tar_bytes({'sample/matrix.mtx':MATRIX,'sample/features.tsv':FEATURES}, compressed=True)
    outer_id = add('data.tar', tar_bytes({'sample.tar.gz':bundle}))
    member_id = add('data.tar', member='sample.tar.gz', parent=outer_id)
    evidence = catalog.analyze_data_file(member_id, 'gene_summary', {'genes':['CD19']})
    assert evidence['values']['result']['total_counts'] == 15
    assert evidence['values']['result']['genes'][0]['sum'] == 5
    assert evidence['values']['input_sources'][0]['archive_sha256']
    catalog.validate_catalog_evidence(evidence)


def test_many_nested_directory_entries_are_bounded(registry):
    _, _, add = registry
    content = io.BytesIO()
    with tarfile.open(fileobj=content, mode='w:gz') as archive:
        for index in range(1001):
            item = tarfile.TarInfo(f'd{index}'); item.type = tarfile.DIRTYPE; archive.addfile(item)
    file_id = add('directories.tar.gz', content.getvalue())
    with pytest.raises(catalog.CatalogAnalysisError): catalog.inspect_data_file(file_id)
    with pytest.raises(catalog.CatalogAnalysisError): catalog.analyze_data_file(file_id, 'sparse_summary')


def test_mtx_rejects_inconsistent_declared_entries(registry):
    _, _, add = registry
    file_id = add('matrix.mtx', MATRIX.replace(b'3 3 5', b'3 3 4'))
    with pytest.raises(catalog.CatalogAnalysisError): catalog.analyze_data_file(file_id, 'sparse_summary')


def test_dense_gene_table_retains_source_units_and_missing(registry):
    _, _, add = registry
    file_id = add('genes.csv', b'gene,cell1,cell2\nCD19,1.2,3.8\nTNFRSF17,0,2\n')
    result = catalog.analyze_data_file(file_id, 'gene_summary', {'genes':['CD19','none']})['values']['result']
    assert result['genes'][0]['sum'] == 5
    assert result['missing_genes'] == ['none']
    assert 'normalization' in result['units']
