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
ANA_RUN = "f10acf36fcfd4cfc97b84d92c631e8ab"
CART_RUN = "037a6844bfb54d5a8d9010043d6c0a89"
VISIBLE_RUNS = [ANA_RUN, CART_RUN]


def button_named(app, label):
    return next(button for button in app.button if button.label == label)


def test_study_picker_excludes_other_runs_and_preserves_requested_order():
    from frontend.ui.team_tbd import platform_studies

    runs = [{"run_id": CART_RUN, "label": "Original CAR-T label", "source_id": "brev-main"},
            {"run_id": "older-run", "label": "Earlier investigation"},
            {"run_id": ANA_RUN, "label": "Original Ana label", "source_id": "mac-ana-isolated"}]
    entries = platform_studies(runs)

    assert [entry["run_id"] for entry in entries] == VISIBLE_RUNS
    assert [entry["source_id"] for entry in entries] == ["mac-ana-isolated", "brev-main"]
    assert "Ana" in entries[0]["label"] and "GSE28460" in entries[0]["label"]
    assert "CAR-T" in entries[1]["label"] and "CD19" in entries[1]["label"]
    assert runs[0]["label"] == "Original CAR-T label"  # Display curation must not rewrite metadata.
    assert platform_studies([runs[1]]) == []


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


@pytest.mark.parametrize("run_id", VISIBLE_RUNS)
def test_actual_featured_study_renders_all_pages(private_capsule, run_id):
    app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=30).run()
    app.selectbox(key="tbd_study").set_value(run_id).run()
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
    for run_id in VISIBLE_RUNS:
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


@pytest.mark.parametrize("stale_state", [False, True])
def test_actual_old_bookmark_cannot_reintroduce_hidden_studies(private_capsule, stale_state):
    old_run = next(item["run_id"] for item in private_capsule.runs if item["run_id"] not in VISIBLE_RUNS)
    app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=30)
    app.query_params["run"] = old_run
    if stale_state:
        app.session_state["tbd_study"] = old_run
    app.run()

    assert_clean(app)
    study = app.selectbox(key="tbd_study")
    assert study.value == ANA_RUN
    assert len(study.options) == 2
    assert study.options[0].startswith("Ana")
    assert "CAR-T" in study.options[1] and "CD19" in study.options[1]
    assert app.query_params["run"] == [ANA_RUN]


@pytest.mark.parametrize("run_id", VISIBLE_RUNS)
def test_actual_overview_opens_agent_collaboration(private_capsule, run_id):
    app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=30)
    app.query_params["run"] = run_id
    app.run()
    assert_clean(app)
    button_named(app, "Explore agent collaboration →").click().run()

    assert_clean(app)
    assert app.radio(key="tbd_page").value == "Agent collaboration"
    assert app.query_params["view"] == ["Agent collaboration"]
    assert app.selectbox(key="tbd_study").value == run_id


@pytest.mark.parametrize("run_id", VISIBLE_RUNS)
def test_actual_finding_opens_exact_evidence_and_clears_filter(private_capsule, run_id):
    bundle = private_capsule.load(run_id)
    findings = bundle["view"]["findings"]["findings"]
    evidence_id = next(eid for finding in findings for eid in finding.get("evidence_ids", []))
    evidence = next(item for item in bundle["evidence"] if item["id"] == evidence_id)
    app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=30)
    app.query_params["run"] = run_id
    app.run()
    button_named(app, "Trace findings to evidence →").click().run()
    assert_clean(app)
    assert app.radio(key="tbd_page").value == "Findings"
    button_named(app, f"Open evidence {evidence_id} →").click().run()

    assert_clean(app)
    assert app.radio(key="tbd_page").value == "Evidence"
    assert app.text_input(key="tbd_evidence_search").value == evidence_id
    assert any(panel.label == f'{evidence_id} · {evidence["title"]}' for panel in app.expander)
    button_named(app, "Show all evidence").click().run()
    assert_clean(app)
    assert app.text_input(key="tbd_evidence_search").value == ""
    assert len(app.expander) == len(bundle["evidence"])


def test_collaboration_distinguishes_recipient_routes_from_actual_inputs():
    from frontend.ui.team_tbd_collaboration import collaboration_index

    first = {"id": "first", "sender": "bioinformatician", "recipient": ["statistician"],
             "input_versions": {"upstream_handoff_ids": []}}
    unrelated = {"id": "unrelated", "sender": "statistician", "recipient": ["reviewer"],
                 "input_versions": {"upstream_handoff_ids": []}}
    consumer = {"id": "consumer", "sender": "reviewer", "recipient": ["scientist"],
                "input_versions": {"upstream_handoff_ids": ["first"]}}
    index = collaboration_index({"handoffs": [consumer, unrelated, first]})

    assert index["consumers"]["first"] == [consumer]
    assert index["consumers"]["unrelated"] == []
    assert index["incoming"]["statistician"] == [first]
    assert index["routes"][("bioinformatician", "statistician")] == 1
    assert ("bioinformatician", "reviewer") not in index["routes"]
    assert index["outgoing"]["scientist"] == []
    assert index["incoming"]["scientist"] == [consumer]


@pytest.mark.parametrize("run_id", VISIBLE_RUNS)
def test_actual_collaboration_follows_upstream_and_downstream_records(private_capsule, run_id):
    run = private_capsule.load(run_id)["run"]
    handoff = next(item for item in run["handoffs"]
                   if item.get("input_versions", {}).get("upstream_handoff_ids"))
    upstream_id = handoff["input_versions"]["upstream_handoff_ids"][0]
    upstream = next(item for item in run["handoffs"] if item["id"] == upstream_id)
    prefix = f"tbd_collaboration:{run_id}"
    app = AppTest.from_file(str(ROOT / "frontend" / "app.py"), default_timeout=30)
    app.query_params["run"] = run_id
    app.query_params["view"] = "Agent collaboration"
    app.run()
    app.selectbox(key=prefix + ":role").set_value(handoff["sender"]).run()
    app.selectbox(key=prefix + ":handoff").set_value(handoff["id"]).run()
    assert_clean(app)

    upstream_button = f'{prefix}:detail:{run_id}:{handoff["id"]}:upstream:0'
    app.button(key=upstream_button).click().run()
    assert_clean(app)
    assert app.selectbox(key=prefix + ":role").value == upstream["sender"]
    assert app.selectbox(key=prefix + ":handoff").value == upstream_id

    consumers = [item for item in run["handoffs"]
                 if upstream_id in item.get("input_versions", {}).get("upstream_handoff_ids", [])]
    destination_index = next(i for i, item in enumerate(consumers) if item["id"] == handoff["id"])
    downstream_button = f"{prefix}:detail:{run_id}:{upstream_id}:downstream:{destination_index}"
    app.button(key=downstream_button).click().run()
    assert_clean(app)
    assert app.selectbox(key=prefix + ":handoff").value == handoff["id"]
    assert app.selectbox(key=prefix + ":role").value == handoff["sender"]

    evidence_id = handoff["input_versions"]["evidence_ids"][-1]
    evidence_key = f'{prefix}:detail:{run_id}:{handoff["id"]}:evidence'
    app.selectbox(key=evidence_key).set_value(evidence_id).run()
    assert_clean(app)
    assert app.selectbox(key=evidence_key).value == evidence_id
    assert any(evidence_id in caption.value for caption in app.caption)
    assert any(handoff["input_versions"]["evidence_versions"][evidence_id] == block.value
               for block in app.code)

    app.radio(key=prefix + ":view").set_value("Communication map").run()
    route = (upstream["sender"], upstream["recipient"][0])
    app.selectbox(key=prefix + ":route").set_value(route).run()
    assert_clean(app)
    handoff_index = next(i for i, item in enumerate(run["handoffs"]) if item["id"] == upstream_id)
    app.button(key=f"{prefix}:route-open:{handoff_index}").click().run()
    assert_clean(app)
    assert app.radio(key=prefix + ":view").value == "Agent work"
    assert app.selectbox(key=prefix + ":handoff").value == upstream_id
