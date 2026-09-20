"""Presentation regressions; private capsule/live checks are explicitly opt-in.

TEAM_TBD_TEST_CAPSULE enables local private-data checks. Live checks additionally
require TEAM_TBD_TEST_LIVE_READS=1 and only read existing runs and artifacts.
"""
from pathlib import Path
import os

import httpx
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def no_implicit_network(monkeypatch):
    if os.environ.get("TEAM_TBD_TEST_LIVE_READS") != "1":
        def forbidden(*args, **kwargs):
            raise AssertionError("Network requires TEAM_TBD_TEST_LIVE_READS=1")
        monkeypatch.setattr(httpx.Client, "send", forbidden)


def assert_clean(app):
    assert not app.exception, [item.message for item in app.exception]
    assert not app.error, [item.value for item in app.error]


def artifact_cache_app():
    import hashlib
    import streamlit as st
    from frontend.ui.team_tbd import render_nvidia

    origin = st.selectbox("Test origin", ["http://127.0.0.1:8101", "http://127.0.0.1:8102"])
    revision = st.selectbox("Test revision", ["Original", "Reordered", "Changed bytes"])
    payloads = {"a.bin": b"alpha revised" if revision == "Changed bytes" else b"alpha", "b.bin": b"beta"}

    class Source:
        base = origin

        def artifact_bytes(self, artifact):
            return payloads[artifact["name"]]

    artifacts = [{"name": name, "url": f"/api/runs/sample/artifacts/op/{name}",
                  "sha256": hashlib.sha256(data).hexdigest()} for name, data in payloads.items()]
    if revision == "Reordered":
        artifacts.reverse()
    render_nvidia({"id": "sample"}, {}, artifacts, Source())


def artifact_panel(app, name):
    return next(panel for panel in app.expander if panel.label == name)


def test_download_cache_follows_artifact_identity_not_position():
    app = AppTest.from_function(artifact_cache_app).run()
    assert_clean(app)
    artifact_panel(app, "a.bin").button[0].click().run()
    assert_clean(app)
    assert len(artifact_panel(app, "a.bin").get("download_button")) == 1

    app.selectbox[1].set_value("Reordered").run()
    assert_clean(app)
    assert len(artifact_panel(app, "a.bin").get("download_button")) == 1
    assert len(artifact_panel(app, "b.bin").get("download_button")) == 0

    app.selectbox[1].set_value("Changed bytes").run()
    assert_clean(app)
    assert len(artifact_panel(app, "a.bin").get("download_button")) == 0
    artifact_panel(app, "a.bin").button[0].click().run()
    assert_clean(app)
    assert len(artifact_panel(app, "a.bin").get("download_button")) == 1

    app.selectbox[0].set_value("http://127.0.0.1:8102").run()
    assert_clean(app)
    assert not app.get("download_button")


def handoff_map_app():
    from frontend.ui.team_tbd import render_review
    render_review({"handoffs": [{"sender": "reviewer", "recipient": ["scientist"],
                                 "result": "Recorded review delivered to the human scientist."}]}, {}, [])


def test_handoff_map_includes_recipient_without_inventing_spawn():
    app = AppTest.from_function(handoff_map_app).run()
    assert_clean(app)
    svg = next(item.value for item in app.markdown if 'class="network-canvas' in item.value)
    assert svg.count('class="network-node') == 2
    assert 'reviewer to scientist: 1 message(s)' in svg
    assert 'class="network-spawn"' not in svg
    assert 'human scientist' in svg.lower()
    assert 'handoffs' in svg


@pytest.fixture
def private_capsule(monkeypatch):
    root = os.environ.get("TEAM_TBD_TEST_CAPSULE")
    if not root:
        pytest.skip("Set TEAM_TBD_TEST_CAPSULE for private frozen UI checks")
    from frontend.ui.team_tbd_adapter import Capsule
    capsule = Capsule(root)
    monkeypatch.setenv("TEAM_TBD_CAPSULE", root)
    monkeypatch.syspath_prepend(str(ROOT / "frontend"))
    return capsule


def test_actual_featured_study_renders_all_pages(private_capsule):
    app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=30).run()
    app.selectbox(key="tbd_study").set_value(private_capsule.manifest["featured_run_ids"][0]).run()
    pages = app.radio(key="tbd_page").options
    assert len(pages) == 8
    for page in pages:
        app.radio(key="tbd_page").set_value(page).run()
        assert_clean(app)
        captions = [item.value for item in app.caption]
        assert any("FROZEN REPLAY" in text for text in captions)
        assert not any("LIVE BACKEND READ" in text for text in captions)


def test_actual_mode_switch_and_cached_live_artifact(private_capsule):
    if os.environ.get("TEAM_TBD_TEST_LIVE_READS") != "1":
        pytest.skip("Set TEAM_TBD_TEST_LIVE_READS=1 to GET the existing services")
    for run_id in private_capsule.manifest["featured_run_ids"]:
        app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=45).run()
        app.selectbox(key="tbd_study").set_value(run_id).run()
        app.radio(key="tbd_page").set_value("NVIDIA & sequences").run()
        assert_clean(app)
        next(button for button in app.button if button.label == "Load artifact").click().run()
        assert_clean(app)
        assert len(app.get("download_button")) == 1

        app.selectbox(key="tbd_mode").set_value("Live reads").run()
        assert_clean(app)
        assert not app.get("download_button")  # Replay bytes must not stand in for a live read.
        assert any("LIVE BACKEND READ" in item.value for item in app.caption)
        next(button for button in app.button if button.label == "Load artifact").click().run()
        assert_clean(app)
        assert len(app.get("download_button")) == 1

        app.selectbox(key="tbd_mode").set_value("Frozen replay").run()
        assert_clean(app)
        assert len(app.get("download_button")) == 1
