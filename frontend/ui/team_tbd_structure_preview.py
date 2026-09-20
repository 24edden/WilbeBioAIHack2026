"""Automatic, run-bound images of saved NVIDIA predictions; no inference calls."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parents[1] / 'static' / 'nvidia'


@lru_cache(maxsize=1)
def _catalog():
    return json.loads((ASSETS / 'catalog.json').read_text())


def saved_structure_images(artifacts, run_id=None):
    """Match exact artifact content, never a filename, study label or prior run."""
    hashes = {
        item.get('sha256')
        for item in artifacts
        if item.get('name', '').lower().endswith('.cif')
        and (run_id is None or item.get('run_id', run_id) == run_id)
    }
    results = []
    for item in _catalog():
        if item['source_sha256'] not in hashes:
            continue
        data = (ASSETS / item['image']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['image_sha256']:
            continue
        results.append((item, data))
    return results


def render_structure_previews(artifacts, run_id=None, *, heading=True):
    """Render immediately on page load, with native click-to-expand images."""
    images = saved_structure_images(artifacts, run_id)
    if not images:
        return
    if heading:
        st.subheader('NVIDIA structure predictions')
    columns = st.columns(min(2, len(images)))
    for index, (item, data) in enumerate(images):
        with columns[index % len(columns)]:
            st.image(data, caption=item['title'] + ' · ' + item['model'], width='stretch')
    st.caption('Saved NVIDIA Boltz-2 predictions · Click an image to enlarge.')
