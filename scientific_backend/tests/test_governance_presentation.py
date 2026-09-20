"""Offline API and renderer checks for visible, cancellable hypothesis testing."""
import copy
import json
import shutil
import subprocess
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from app import main
from test_hypothesis_continuation import governed_decision, harness  # Shared source-qualified offline fixture.


@pytest.fixture
def presentation(harness):
    store, engine, run_id = harness
    value = governed_decision("first-analysis")
    primary = value["governance"]["hypotheses"][0]
    supported = {**copy.deepcopy(primary), "hypothesis_id": "alternative-supported", "origin": "agent_generated",
                 "statement": "The synthetic observation supports an alternative within this assay.",
                 "status": "probable", "next_analysis_ids": [],
                 "rationale": "The accepted synthetic measurement supports this limited explanation; it does not establish a patient-level cause."}
    excluded = {**copy.deepcopy(primary), "hypothesis_id": "alternative-excluded", "origin": "agent_generated",
                "statement": "A separately tested synthetic alternative is excluded within this assay.",
                "status": "clearly_ruled_out", "supporting_evidence_ids": [], "contradicting_evidence_ids": ["e1"],
                "test_evidence_ids": ["e1"], "next_analysis_ids": [],
                "rationale": "The accepted synthetic test contradicts this specific alternative within the stated assay scope.",
                "falsification_test": "Prespecified synthetic contrast with a matched control.",
                "falsification_result": "The observed synthetic contrast contradicts this restricted alternative."}
    value["governance"]["hypotheses"].extend([supported, excluded])
    engine.publish(run_id, value)
    with TestClient(main.create_app(store, embedded=False)) as client:
        yield client, store, run_id


def actual_state_from_report(text):
    section = text.split("## Actual continuation state\n\n", 1)[1].split("\n\n## Execution provenance", 1)[0]
    return json.loads(section)


def test_cancel_endpoint_stops_queued_agent_operation_without_rewriting_published_history(presentation):
    client, store, run_id = presentation
    before = copy.deepcopy(store.get(run_id))
    operation_id = before["operation"]["id"]
    assert before["status"] == "queued"
    assert before["followup_operations"][0]["origin"] == "agent_governance"
    response = client.post(f"/api/runs/{run_id}/cancel")
    assert response.status_code == 200
    after = response.json()
    assert after["status"] == "cancelled" and after["cancel_requested"] is True
    assert after["operation"]["id"] == operation_id
    operation = next(item for item in after["followup_operations"] if item["id"] == operation_id)
    assert operation["status"] == "cancelled" and operation["finished_at"]
    assert after["governance_state"]["status"] == "stopped"
    assert after["governance_state"]["stop_reason"] == "cancelled"
    assert after["governance_state"]["operation_id"] == operation_id
    assert after["hypothesis"] == before["hypothesis"]
    assert after["decisions"] == before["decisions"]
    assert after["governance_transitions"][:-1] == before["governance_transitions"]
    assert after["events"][:len(before["events"])] == before["events"]
    assert after["actions"] == before["actions"] == []
    assert after["decisions"][0]["governance"]["stop_reason"] == "continue"
    repeated = client.post(f"/api/runs/{run_id}/cancel").json()
    assert repeated["events"] == after["events"]
    assert repeated["governance_transitions"] == after["governance_transitions"]
    exported = client.get(f"/api/runs/{run_id}/export.json").json()["run"]
    assert exported["decisions"] == before["decisions"]
    assert exported["governance_state"] == after["governance_state"]
    report = client.get(f"/api/runs/{run_id}/report.md")
    assert actual_state_from_report(report.text)["stop_reason"] == "cancelled"


@pytest.mark.parametrize("actual_status", ["queued", "running", "stopped"])
def test_report_preserves_scientific_states_citations_and_current_operational_status(presentation, actual_status):
    client, store, run_id = presentation
    original = copy.deepcopy(store.get(run_id)["decisions"])
    if actual_status == "stopped":
        assert client.post(f"/api/runs/{run_id}/cancel").status_code == 200
    elif actual_status == "running":
        def start(run):
            run["status"] = "running"
            run["governance_state"]["status"] = "running"
            run["governance_state"]["reason"] = "The registered comparison is currently running."
            run["followup_operations"][0]["status"] = "running"
        store.mutate(run_id, start)
    response = client.get(f"/api/runs/{run_id}/report.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "attachment;" in response.headers["content-disposition"]
    text = response.text
    assert "### Hypothesis testing governance" in text
    assert "Selected next analysis: first-analysis" in text
    for item in original[0]["governance"]["hypotheses"]:
        assert f"**{item['hypothesis_id']} · {item['status'].replace('_', ' ')}**" in text
        assert item["statement"] in text and item["rationale"] in text
        assert "Scope: " + item["scope"] in text
        assert "Supporting evidence: " + ", ".join(item["supporting_evidence_ids"]) in text
        assert "Counterevidence: " + ", ".join(item["contradicting_evidence_ids"]) in text
        assert "Test evidence: " + ", ".join(item["test_evidence_ids"]) in text
    excluded = original[0]["governance"]["hypotheses"][2]
    assert "Falsification test: " + excluded["falsification_test"] in text
    assert "Test result: " + excluded["falsification_result"] in text
    current = client.get(f"/api/runs/{run_id}").json()
    assert actual_state_from_report(text) == current["governance_state"]
    assert current["governance_state"]["status"] == actual_status
    assert current["decisions"] == original
    assert "Decision: continue" in text  # Historical selection stays separate from current execution.


class RenderedHTML(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


def render_governance(client, run, decision):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the offline production-renderer test.")
    source = client.get("/static/app.js")
    assert source.status_code == 200
    script = r"""
const fs = require('fs');
const vm = require('vm');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const context = vm.createContext({payload});
const source = payload.source.replace(/\ninit\(\);\s*$/, '\n');
if (source === payload.source) throw new Error('Expected the production bootstrap marker');
vm.runInContext(source, context, {timeout: 1000});
const html = vm.runInContext('state.run = payload.run; renderHypothesisGovernance(payload.decision)', context, {timeout: 1000});
process.stdout.write(JSON.stringify(html));
"""
    output = subprocess.run([node, "-e", script], input=json.dumps({"source": source.text, "run": run, "decision": decision}),
                            text=True, capture_output=True, check=True, timeout=5)
    return json.loads(output.stdout)


@pytest.mark.parametrize("actual_status,label", [
    ("queued", "Next test queued"), ("running", "Testing the next hypothesis"), ("stopped", "Investigation stopped"),
])
def test_html_governance_uses_actual_status_and_escapes_every_supplied_field(presentation, actual_status, label):
    client, store, run_id = presentation
    run = client.get(f"/api/runs/{run_id}").json()
    decision = copy.deepcopy(run["decisions"][0])
    payload = '<img src=x onerror="alert(1)"><script>alert(2)</script> & \'quoted\''
    item = decision["governance"]["hypotheses"][0]
    for field in ("hypothesis_id", "statement", "scope", "scope_type", "rationale", "falsification_test", "falsification_result", "blocker"):
        item[field] = field + " " + payload
    for field in ("supporting_evidence_ids", "contradicting_evidence_ids", "test_evidence_ids", "next_analysis_ids"):
        item[field] = [field + " " + payload]
    decision["governance"]["continuation_reason"] = "Earlier decision rationale"
    run["governance_state"].update(status=actual_status, reason="Current reason " + payload,
                                   next_analysis_id="Next recipe " + payload,
                                   stop_reason="cancelled" if actual_status == "stopped" else "continue")
    markup = render_governance(client, run, decision)
    assert label in markup
    assert "Earlier decision rationale" not in markup
    assert "&lt;img" in markup and "&lt;script&gt;" in markup and "&quot;alert(1)&quot;" in markup
    assert payload not in markup
    parsed = RenderedHTML(markup)
    assert not any(tag in {"img", "script", "iframe", "svg"} for tag, _ in parsed.elements)
    assert not any(key.lower().startswith("on") for _, attrs in parsed.elements for key in attrs)
    rendered_text = " ".join(parsed.text)
    for field in ("statement", "scope", "scope_type", "rationale", "falsification_test", "falsification_result", "blocker"):
        assert item[field] in rendered_text
    assert "Current reason " + payload in rendered_text
    evidence_buttons = [attrs["data-show-evidence"] for tag, attrs in parsed.elements
                        if tag == "button" and "data-show-evidence" in attrs]
    for field in ("supporting_evidence_ids", "contradicting_evidence_ids", "test_evidence_ids"):
        assert item[field][0] in evidence_buttons
    assert store.get(run_id)["decisions"][0] != decision  # Injection stayed exclusively in the renderer input.


def test_historical_decision_does_not_adopt_newer_operation_status(presentation):
    client, _, run_id = presentation
    run = client.get(f"/api/runs/{run_id}").json()
    old_decision = copy.deepcopy(run["decisions"][0])
    run["governance_state"].update(decision_version=2, status="stopped", reason="Later operation was cancelled.", stop_reason="cancelled")
    markup = render_governance(client, run, old_decision)
    assert "Next test selected" in markup
    assert old_decision["governance"]["continuation_reason"] in markup
    assert "Later operation was cancelled." not in markup
