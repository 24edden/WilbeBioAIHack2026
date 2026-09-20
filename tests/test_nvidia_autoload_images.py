"""Saved images load without clicks and cannot leak into unrelated studies."""
from streamlit.testing.v1 import AppTest
from frontend.ui.team_tbd_structure_preview import saved_structure_images

WT = 'ec0667e5dbe57c4666938e7fa78b09820f84f16b4632bcc8b3a668156f050b0a'
DELETED = '61be3a4739d6d6a436f67bee4b023f3763cb1eafe1bcb4d80b30b83ef2652641'


def test_only_exact_recorded_structures_get_saved_images():
    artifacts = [{'name': 'wild_type_prediction.cif', 'sha256': WT, 'run_id': 'cart'},
                 {'name': 'exon2_deleted_prediction.cif', 'sha256': DELETED, 'run_id': 'cart'}]
    assert len(saved_structure_images(artifacts, 'cart')) == 2
    assert not saved_structure_images(artifacts, 'ana')
    assert not saved_structure_images([], 'ana')
    assert not saved_structure_images([{'name': 'wild_type_prediction.cif', 'sha256': 'changed'}])
    assert len(saved_structure_images(artifacts * 2, 'cart')) == 2


def test_images_appear_on_initial_render_without_buttons():
    app = AppTest.from_string('''
from frontend.ui.team_tbd_structure_preview import render_structure_previews
render_structure_previews([
    {'name':'wild_type_prediction.cif', 'sha256':'%s'},
    {'name':'exon2_deleted_prediction.cif', 'sha256':'%s'}
], 'cart')
''' % (WT, DELETED)).run()
    assert not app.exception
    assert len(app.get('image')) == 2
    assert not app.button
