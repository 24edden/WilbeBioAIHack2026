"""Authoritative UI regressions with isolated fake transport; never vendor work."""
from copy import deepcopy
import importlib
from pathlib import Path

import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:18997"


def button(app, label):
    return next(item for item in app.button if item.label == label)


def clean(app):
    assert not app.exception, [item.message for item in app.exception]


@pytest.fixture
def scientific_app(monkeypatch):
    monkeypatch.setenv("TEAM_TBD_BACKEND_URL", BASE)
    monkeypatch.delenv("TEAM_TBD_CAPSULE", raising=False)
    monkeypatch.syspath_prepend(str(ROOT / "frontend"))
    workspace = importlib.import_module("ui.scientific_workspace")
    transport = importlib.import_module("ui.team_tbd_client")
    adapter = importlib.import_module("ui.team_tbd_adapter")

    def no_network(*args, **kwargs):
        raise AssertionError("Scientific UI tests may not reach a real service")

    monkeypatch.setattr(httpx.Client, "send", no_network)

    class FakeClient:
        base = BASE

        def __init__(self):
            self.reads = []
            self.writes = []
            self.next_error = None
            self.server_version = 2
            self.nvidia_status = "unconfigured"
            self.followup_records = []
            self.run = {
                "id": "isolated-run", "case_id": "registered-case", "title": "Isolated contract fixture",
                "status": "completed", "mode": "live", "review_status": "unreviewed",
                "hypothesis": {"text": "Does this registered evidence support the hypothesis?", "source_name": "Fixture"},
                "decisions": [{"version": 2, "assessment": "uncertain", "summary": "Fixture decision", "rd_handoff": {}}],
                "events": [], "evidence": [], "handoffs": [], "stage_evaluations": [],
                "actions": [], "operation": {"id": "fixture-operation"}, "usage": {},
            }

        def health(self):
            self.reads.append("health")
            return {"service": "Team TBD", "worker_alive": True,
                    "capabilities": {"rosalind": {"status": "verified", "model": "gpt-6-astra"},
                                     "bionemo": {"status": self.nvidia_status}}}

        def cases(self):
            self.reads.append("cases")
            return [{"id": "registered-case", "title": "Registered fixture", "description": "Approved evidence context",
                     "hypothesis": "  Exact registered hypothesis\nwith original whitespace.  ",
                     "hypothesis_source": {"name": "Exact source record"}, "readiness": []}]

        def list_runs(self):
            self.reads.append("list_runs")
            return [deepcopy(self.run)]

        def get_run(self, run_id):
            self.reads.append("get_run")
            assert run_id == self.run["id"]
            return deepcopy(self.run)

        def load(self, run_id):
            self.reads.append("load")
            assert run_id == self.run["id"]
            run = deepcopy(self.run)
            return {"run": run, "view": adapter.run_view(run), "evidence": [], "artifacts": []}

        def synthesis_checkpoint(self, run_id):
            self.reads.append("checkpoint")
            return {"eligible": False, "reason": "No saved recovery checkpoint"}

        def followups(self, run_id):
            self.reads.append("followups")
            return {"decision_version": 2, "followups": deepcopy(self.followup_records)}

        def create_run(self, payload):
            self.writes.append(("create", deepcopy(payload)))
            if self.next_error:
                error, self.next_error = self.next_error, None
                raise error
            self.run.update(status="queued", decisions=[],
                            hypothesis={"text": payload["hypothesis"], "source_name": payload["source_name"]})
            return deepcopy(self.run)

        def feedback(self, run_id, payload):
            self.writes.append(("feedback", deepcopy(payload)))
            if payload["decision_version"] != self.server_version:
                raise transport.APIError(409, "The displayed decision version is stale.")
            self.run["status"] = "queued"
            return deepcopy(self.run)

        def cancel(self, run_id):
            self.writes.append(("cancel", None))
            self.run["status"] = "cancelled"
            return deepcopy(self.run)

        def resume(self, run_id):
            self.writes.append(("resume", None))
            self.run["status"] = "queued"
            return deepcopy(self.run)

        def followup(self, run_id, payload):
            return self.record_action("followup", payload)

        def research_brief(self, run_id, payload):
            return self.record_action("research_brief", payload)

        def sequence_discovery(self, run_id, payload):
            return self.record_action("sequence_discovery", payload)

        def outcome(self, run_id, payload):
            return self.record_action("outcome", payload)

        def modeling(self, run_id, payload):
            return self.record_action("modeling", payload)

        def record_action(self, action, payload):
            self.writes.append((action, deepcopy(payload)))
            self.run["status"] = "queued"
            return deepcopy(self.run)

    client = FakeClient()
    monkeypatch.setattr(workspace, "client_at", lambda base: client)

    def composer(draft, **options):
        st.session_state["_test_composer_options"] = deepcopy(options)
        return st.session_state.pop("_test_scientific_action", None)

    monkeypatch.setattr(workspace, "render_composer", composer)
    st.cache_data.clear()
    app = AppTest.from_file(str(ROOT / "frontend/app.py"), default_timeout=15).run()
    clean(app)
    yield app, client, workspace, transport
    st.cache_data.clear()


def connect(app):
    button(app, "Connect scientific service").click().run()
    clean(app)


def open_run(app):
    app.query_params["active_run"] = "isolated-run"
    app.query_params["service"] = "scientific"
    app.run()
    clean(app)


def submit_question(app, text="  Keep my original scientific question.\n  "):
    app.session_state["_test_scientific_action"] = {"type": "start", "question": text, "uploads": []}
    app.run()
    clean(app)


def test_home_is_prompt_first_without_network_or_legacy_controls(scientific_app):
    app, client, _, _ = scientific_app
    assert client.reads == [] and client.writes == []
    assert not app.get("file_uploader")
    assert not any(item.label in {"Evidence source", "Research service URL", "Reasoning model"} for item in app.selectbox)
    assert any("What are we investigating?" in item.value for item in app.markdown)
    options = app.session_state["_test_composer_options"]
    assert options["allow_uploads"] is False and options["allow_demo"] is False
    assert options["preserve_question"] is True and options["disabled"] is True


def test_connection_reads_do_not_probe_or_submit(scientific_app):
    app, client, _, _ = scientific_app
    connect(app)
    assert client.reads == ["health", "cases"]
    assert client.writes == []
    assert app.session_state["_test_composer_options"]["disabled"] is False


def test_create_preserves_exact_question_source_and_nine_role_contract(scientific_app):
    app, client, workspace, _ = scientific_app
    connect(app)
    source = "  Original scientist note  "
    app.text_input(key="scientific_source").set_value(source).run()
    question = "  Do the registered measurements support this hypothesis?\nKeep this line.  "
    submit_question(app, question)
    assert len(client.writes) == 1
    operation, payload = client.writes[0]
    assert operation == "create"
    assert payload["hypothesis"] == question and payload["source_name"] == source
    assert payload["case_id"] == "registered-case" and payload["mode"] == "live"
    assert len(workspace.ROLE_IDS) == len(set(workspace.ROLE_IDS)) == 9
    assert set(payload) == {"hypothesis", "source_name", "case_id", "mode", "required_analysis_ids", "idempotency_key"}
    assert app.query_params["active_run"] == ["isolated-run"]


def test_registered_hypothesis_button_preserves_original_text_and_source(scientific_app):
    app, client, _, _ = scientific_app
    connect(app)
    button(app, "Use this study’s original hypothesis").click().run()
    clean(app)
    assert app.session_state["draft"]["question"] == client.cases()[0]["hypothesis"]
    assert app.text_input(key="scientific_source").value == "Exact source record"
    assert client.writes == []


@pytest.mark.parametrize("action", [
    {"type": "demo", "question": "Do not run demo", "uploads": []},
    {"type": "start", "question": "Do not upload this file", "uploads": [("private.csv", b"data")]},
])
def test_unsupported_actions_never_submit(scientific_app, action):
    app, client, _, _ = scientific_app
    connect(app)
    app.session_state["_test_scientific_action"] = action
    app.run()
    clean(app)
    assert client.writes == [] and app.error


def test_unknown_create_retains_exact_intent_and_reconciles_same_key(scientific_app):
    app, client, _, transport = scientific_app
    connect(app)
    client.next_error = transport.UncertainWriteError("create", "unknown")
    submit_question(app)
    assert len(client.writes) == 1
    original = deepcopy(app.session_state["scientific_pending"])
    app.run()
    clean(app)
    assert len(client.writes) == 1
    assert app.session_state["_test_composer_options"]["disabled"] is True
    button(app, "Reconcile using the same request key").click().run()
    clean(app)
    assert len(client.writes) == 2 and client.writes[0] == client.writes[1]
    assert client.writes[1][1] == original["payload"]
    assert app.session_state["scientific_pending"] is None


def test_stale_feedback_version_is_visible_and_never_retried(scientific_app):
    app, client, _, _ = scientific_app
    open_run(app)
    client.server_version = 3
    next(item for item in app.text_area if item.label == "Scientific feedback or follow-up question").set_value("Preserve this scientist correction.")
    button(app, "Submit feedback for a new decision").click().run()
    clean(app)
    assert len(client.writes) == 1
    assert client.writes[0][1]["decision_version"] == 2
    assert any("stale" in item.value for item in app.error)
    assert app.session_state["scientific_pending"] is None
    app.run()
    assert len(client.writes) == 1


def test_accepted_feedback_returns_to_durable_run_without_changing_original(scientific_app):
    app, client, _, _ = scientific_app
    original = deepcopy(client.run["hypothesis"])
    open_run(app)
    next(item for item in app.text_area if item.label == "Scientific feedback or follow-up question").set_value("Preserve this scientist correction.")
    button(app, "Submit feedback for a new decision").click().run()
    clean(app)
    assert len(client.writes) == 1 and client.writes[0][0] == "feedback"
    assert client.run["hypothesis"] == original and client.run["decisions"][0]["version"] == 2
    assert app.session_state["scientific_pending"] is None


@pytest.mark.parametrize("status, label, action", [
    ("queued", "Request cancellation", "cancel"),
    ("cancelled", "Resume safely", "resume"),
])
def test_explicit_cancellation_and_resume_return_to_durable_status(scientific_app, status, label, action):
    app, client, _, _ = scientific_app
    client.run["status"] = status
    open_run(app)
    button(app, label).click().run()
    clean(app)
    assert client.writes == [(action, None)]


def test_frozen_navigation_from_live_clears_execution_route(scientific_app, monkeypatch):
    app, client, workspace, _ = scientific_app
    monkeypatch.setenv("TEAM_TBD_CAPSULE", "/unused-read-only-fixture")
    monkeypatch.setattr(workspace, "render_workspace", lambda: st.info("Isolated frozen reader"))
    open_run(app)
    button(app, "Completed studies").click().run()
    clean(app)
    assert "active_run" not in app.query_params and "service" not in app.query_params
    assert app.query_params["mode"] == ["replay"]
    assert any(item.value == "Isolated frozen reader" for item in app.info)
    assert client.writes == []


def test_direct_frozen_route_never_constructs_control_transport(scientific_app, monkeypatch):
    app, client, workspace, _ = scientific_app
    monkeypatch.setenv("TEAM_TBD_CAPSULE", "/unused-read-only-fixture")
    monkeypatch.setattr(workspace, "render_workspace", lambda: st.info("Isolated frozen reader"))
    app.query_params.update(run="frozen-id", view="Overview", mode="replay")
    app.run()
    clean(app)
    assert client.reads == [] and client.writes == []
    assert not any(item.label == "Submit feedback for a new decision" for item in app.button)


def test_refresh_and_results_navigation_only_read(scientific_app):
    app, client, _, _ = scientific_app
    open_run(app)
    button(app, "Refresh recorded status").click().run()
    app.radio(key="tbd_page").set_value("Decisions & review").run()
    clean(app)
    assert client.writes == []
    assert client.run["decisions"][0]["version"] == 2


def test_older_brief_is_labeled_against_current_decision(scientific_app):
    app, client, _, _ = scientific_app
    original = {"version": 1, "source_decision_version": 1,
                "content": {"headline": "Prior interpretation", "plain_summary": "Based on the earlier decision."}}
    client.run["research_briefs"] = [deepcopy(original)]
    open_run(app)
    assert any("decision 1" in item.value and "decision: 2" in item.value for item in app.caption)
    assert any("historical interpretation" in item.value for item in app.warning)
    app.radio(key="tbd_page").set_value("Findings").run()
    clean(app)
    assert any("historical interpretation" in item.value for item in app.warning)
    assert client.run["research_briefs"] == [original] and client.writes == []


@pytest.mark.parametrize("label, action", [
    ("Generate research brief", "research_brief"),
    ("Discover qualified sequences", "sequence_discovery"),
])
def test_optional_operations_require_explicit_click_and_current_version(scientific_app, label, action):
    app, client, _, _ = scientific_app
    open_run(app)
    assert client.writes == []
    button(app, label).click().run()
    clean(app)
    assert len(client.writes) == 1
    assert client.writes[0][0] == action and client.writes[0][1]["decision_version"] == 2
    assert client.run["decisions"][0]["version"] == 2


def test_followup_uses_server_recommendation_id(scientific_app):
    app, client, _, _ = scientific_app
    client.followup_records = [{"id": "registered-analysis", "title": "Registered analysis", "executable": True}]
    open_run(app)
    button(app, "Run supported follow-up").click().run()
    clean(app)
    assert client.writes[0][0] == "followup"
    assert client.writes[0][1]["recommendation_id"] == "registered-analysis"
    assert client.writes[0][1]["decision_version"] == 2


def test_unknown_provider_work_blocks_new_operations(scientific_app):
    app, client, _, _ = scientific_app
    client.run.update(status="failed", actions=[{"id": "fixture-operation-provider", "state": "unknown"}])
    client.followup_records = [{"id": "registered-analysis", "title": "Registered analysis", "executable": True}]
    open_run(app)
    for label in ["Resume safely", "Submit feedback for a new decision", "Generate research brief",
                  "Discover qualified sequences", "Run supported follow-up"]:
        assert button(app, label).disabled
    assert client.writes == []


def test_measured_outcome_keeps_scientist_identifiers_and_value(scientific_app):
    app, client, _, _ = scientific_app
    client.run["decisions"][0]["rd_handoff"] = {"experiment_id": "experiment-2", "candidates": [{"id": "candidate-1"}]}
    open_run(app)
    for label, value in [("Experiment ID", "experiment-2"), ("Candidate ID", "candidate-1"),
                         ("Measured endpoint", "Observed response"), ("Unit", "percent")]:
        next(item for item in app.text_input if item.label == label).set_value(value)
    next(item for item in app.number_input if item.label == "Measured value").set_value(12.5)
    next(item for item in app.text_area if item.label == "Measurement source and notes").set_value("Actual recorded experimental measurement.")
    button(app, "Submit measured outcome").click().run()
    clean(app)
    action, payload = client.writes[0]
    assert action == "outcome" and payload["decision_version"] == 2
    assert payload["experiment_id"] == "experiment-2" and payload["candidate_id"] == "candidate-1"
    assert payload["value"] == 12.5 and payload["unit"] == "percent"


def test_modeling_needs_explicit_retention_attestation(scientific_app):
    app, client, _, _ = scientific_app
    client.nvidia_status = "configured"
    open_run(app)
    for label, value in [("Exact target amino-acid sequence", "ACDEFGHIKLMNPQRSTVWY"),
                         ("Exact reference binder sequence", "ACDEFGHIKLMNPQRSTVWYA"),
                         ("Exact candidate binder sequence", "ACDEFGHIKLMNPQRSTVWYC"),
                         ("Sequence source and construct qualification", "Qualified exact sequences from the scientist.")]:
        next(item for item in app.text_area if item.label == label).set_value(value)
    button(app, "Submit qualified comparison").click().run()
    clean(app)
    assert client.writes == [] and any("attestation" in item.value for item in app.error)
    next(item for item in app.checkbox if item.label == "I attest that the accessible target is retained in the relevant context").check()
    button(app, "Submit qualified comparison").click().run()
    clean(app)
    action, payload = client.writes[0]
    assert action == "modeling" and payload["decision_version"] == 2 and payload["target_retained"] is True
    assert payload["target_sequence"] == "ACDEFGHIKLMNPQRSTVWY"


def test_composer_validation_preserves_raw_text_for_scientific_contract():
    from frontend.ui.composer import validate_action
    text = "  Exact scientific question.\nSecond line.  "
    result = validate_action({"id": "action", "type": "start", "question": text, "files": []}, preserve_question=True)
    assert result["question"] == text
