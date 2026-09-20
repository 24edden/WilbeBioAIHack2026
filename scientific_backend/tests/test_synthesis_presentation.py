"""Offline API and production UI boundaries for explicitly selected synthesis reuse."""
import copy
import json
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app import main, providers
from test_synthesis_checkpoint import create_failed_synthesis, select


@pytest.fixture
def presentation(tmp_path, monkeypatch):
    store, engine, run_id, case = create_failed_synthesis(tmp_path, monkeypatch)

    def forbidden(*args, **kwargs):
        pytest.fail("An eligibility or queue request must not dispatch a model or GPU call")

    monkeypatch.setattr(providers, "investigate", forbidden)
    monkeypatch.setattr(providers, "predict_complex", forbidden)
    with TestClient(main.create_app(store, embedded=False)) as client:
        yield client, store, engine, run_id


def test_api_inspection_then_explicit_queue_preserves_receipts_and_deduplicates(presentation):
    client, store, _, run_id = presentation
    before = store.get(run_id)
    endpoint = f"/api/runs/{run_id}"
    eligible = client.get(endpoint + "/synthesis-checkpoint")
    assert eligible.status_code == 200
    assert eligible.json()["eligible"] is True and eligible.json()["handoff_count"] == 7
    assert store.get(run_id) == before
    # Generic resume is still forbidden: recovery gets its own operation identity.
    assert client.post(endpoint + "/resume").status_code == 409
    payload = {"source_operation_id": before["operation"]["id"], "idempotency_key": "explicit-ui-selection"}
    response = client.post(endpoint + "/continue-synthesis", json=payload)
    assert response.status_code == 200
    queued = response.json()
    assert queued["status"] == "queued"
    assert queued["operation"]["kind"] == "synthesis_continuation"
    assert queued["operation"]["id"] != before["operation"]["id"]
    for field in ("handoffs", "actions", "hypothesis", "evidence", "skill_receipts", "stage_evaluations"):
        assert queued[field] == before[field]
    assert queued["decisions"] == []
    assert queued["operation"]["input"]["source_operation_id"] == before["operation"]["id"]
    assert queued["operation"]["input"]["reused_handoff_ids"] == [item["id"] for item in before["handoffs"]]
    retry = client.post(endpoint + "/continue-synthesis", json=payload)
    assert retry.status_code == 200
    assert retry.json() == queued
    assert len(store.get(run_id)["synthesis_operations"]) == 1
    assert client.get(endpoint + "/synthesis-checkpoint").json()["eligible"] is False
    assert client.post(endpoint + "/continue-synthesis", json={**payload, "idempotency_key": "second-click"}).status_code == 409


@pytest.mark.parametrize("field,value", [
    ("checkpoint", {"sha256": "forged", "work_products": []}),
    ("reused_handoff_ids", ["forged-accepted-product"]),
    ("hypothesis", "Replace the original question"),
])
def test_api_rejects_client_supplied_checkpoint_authority(presentation, field, value):
    client, store, _, run_id = presentation
    before = store.get(run_id)
    response = client.post(f"/api/runs/{run_id}/continue-synthesis", json={
        "source_operation_id": before["operation"]["id"], "idempotency_key": "forged", field: value})
    assert response.status_code == 422
    assert store.get(run_id) == before


@pytest.mark.parametrize("failure_status", ["unknown", "failed"])
def test_api_rejects_timeout_instead_of_treating_it_as_known_output_exhaustion(presentation, failure_status):
    client, store, engine, run_id = presentation
    run = store.get(run_id)
    action = run["actions"][0]
    metadata = copy.deepcopy(action["provider_metadata"])
    metadata["requests"][-1].update(status=failure_status, http_status=None,
                                     incomplete_details=None, reason_code="model_request_timeout")
    engine.provider_failure(run_id, action["id"], providers.ProviderError(
        "Timed-out coordinator request", status=failure_status, metadata=metadata))
    before = store.get(run_id)
    endpoint = f"/api/runs/{run_id}"
    assert client.get(endpoint + "/synthesis-checkpoint").json()["eligible"] is False
    response = client.post(endpoint + "/continue-synthesis", json={
        "source_operation_id": run["operation"]["id"], "idempotency_key": "timeout-is-not-a-checkpoint"})
    assert response.status_code == 409
    assert store.get(run_id) == before


def test_api_rechecks_changed_sources_between_inspection_and_selection(presentation, monkeypatch):
    from app import cases
    client, store, _, run_id = presentation
    before = store.get(run_id)
    endpoint = f"/api/runs/{run_id}"
    assert client.get(endpoint + "/synthesis-checkpoint").json()["eligible"] is True
    changed = copy.deepcopy(before["case_snapshot"])
    changed["source_manifest"][0]["sha256"] = "b" * 64
    monkeypatch.setattr(cases, "get_case", lambda _: changed)
    response = client.post(endpoint + "/continue-synthesis", json={
        "source_operation_id": before["operation"]["id"], "idempotency_key": "stale-eligibility"})
    assert response.status_code == 409
    assert store.get(run_id) == before


def test_api_cancels_queued_synthesis_without_changing_checkpoint_or_original_science(presentation):
    client, store, _, run_id = presentation
    queued = select(store, run_id)
    response = client.post(f"/api/runs/{run_id}/cancel")
    assert response.status_code == 200
    cancelled = response.json()
    assert cancelled["status"] == "cancelled" and cancelled["cancel_requested"] is True
    entry = next(item for item in cancelled["synthesis_operations"] if item["id"] == queued["operation"]["id"])
    assert entry["status"] == "cancelled" and entry["finished_at"]
    for field in ("handoffs", "actions", "hypothesis", "evidence", "skill_receipts", "stage_evaluations", "synthesis_checkpoints"):
        assert cancelled[field] == queued[field]
    assert cancelled["decisions"] == []


def run_ui(client, run, expression, **extra):
    """Execute the shipped UI; only suppress page bootstrap and supply DOM/network fakes."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to exercise the production renderer")
    source = client.get("/static/app.js")
    assert source.status_code == 200
    script = r"""
const fs = require('fs'), vm = require('vm');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const elements = new Map(), calls = [];
const element = id => {
  if (!elements.has(id)) elements.set(id, {id, hidden:false, disabled:false, title:'', listeners:{},
    addEventListener(type, handler) {this.listeners[type] = handler;}});
  return elements.get(id);
};
const context = vm.createContext({payload, calls, element, URL, location: {origin: "http://127.0.0.1:8081"},
  document: {getElementById:element, querySelectorAll:()=>[], addEventListener:()=>{}},
  window: {crypto:{randomUUID:()=> 'stable-ui-request-key'}}});
const source = payload.source.replace(/\ninit\(\);\s*$/, '\n');
if (source === payload.source) throw new Error('Expected production bootstrap marker');
vm.runInContext(source, context, {timeout:1000});
vm.runInContext('state.run = payload.run', context);
Promise.resolve(vm.runInContext('(async () => {' + payload.expression + '})()', context, {timeout:1000}))
 .then(value => process.stdout.write(JSON.stringify(value)))
 .catch(error => {console.error(error); process.exitCode = 1;});
"""
    output = subprocess.run([node, "-e", script], input=json.dumps({
        "source": source.text, "run": run, "expression": expression, **extra}),
        text=True, capture_output=True, check=True, timeout=5)
    return json.loads(output.stdout)


@pytest.mark.parametrize("result_status,label", [
    ("supported", "Reused accepted work"),
    ("inconclusive", "Reused · inconclusive"),
    ("blocked", "Reused · blocked finding"),
])
def test_ui_reused_scientist_work_keeps_qualification_and_original_provenance(presentation, result_status, label):
    client, store, _, run_id = presentation
    selected = select(store, run_id)
    original = copy.deepcopy(selected["handoffs"][0])
    original["result_status"] = result_status
    selected["handoffs"][0] = original
    selected["status"] = "running"
    selected["active_agent"] = "coordinator"
    # A prior lifecycle start must not light up the reused specialist card.
    selected["events"] = [{"time": "2000-01-01T00:00:00Z", "agent": original["sender"],
                           "type": "agent", "status": "running", "title": "Original role call"}]
    rendered = run_ui(client, selected, "return roleActivity(state.run, architectureRoles.find(r => r.id === payload.role));", role=original["sender"])
    assert rendered["status"] == label and rendered["status"] != "Working now"
    assert rendered["statusKey"] == ("blocked" if result_status == "blocked" else "completed")
    assert rendered["reused"] is True
    assert rendered["latest"] == original
    assert rendered["latest"]["operation_id"] != selected["operation"]["id"]


def test_ui_new_coordinator_is_active_and_unrelated_old_handoffs_are_excluded(presentation):
    client, store, _, run_id = presentation
    selected = select(store, run_id)
    selected["status"] = "running"
    selected["active_agent"] = "coordinator"
    selected["events"] = [{"time": "2099-01-01T00:00:00Z", "agent": "coordinator",
                           "type": "agent", "status": "running", "title": "New synthesis"}]
    selected["handoffs"].append({"id": "unrelated-old-review", "operation_id": "other-operation",
                                 "sender": "reviewer", "result_status": "supported"})
    rendered = run_ui(client, selected, "return ['coordinator','reviewer'].map(id => roleActivity(state.run, architectureRoles.find(r => r.id === id)));" )
    assert rendered[0]["status"] == "Working now" and rendered[0]["reused"] is False
    assert rendered[1]["status"] == "Not started" and rendered[1]["products"] == []


def test_ui_eligibility_is_server_checked_cached_and_hidden_after_queue(presentation):
    client, store, _, run_id = presentation
    run = store.get(run_id)
    result = run_ui(client, run, """
api = async path => {calls.push(path); return {eligible: true};};
await refreshSynthesisEligibility(state.run);
const visible = {...element('continue-synthesis')};
await refreshSynthesisEligibility(state.run);
state.run = {...state.run, status:'queued'};
await refreshSynthesisEligibility(state.run);
return {visible, hidden:element('continue-synthesis').hidden, calls};
""")
    assert result["visible"]["hidden"] is False and result["visible"]["disabled"] is False
    assert "failed request stays recorded" in result["visible"]["title"]
    assert result["calls"] == [f"/api/runs/{run_id}/synthesis-checkpoint"]
    assert result["hidden"] is True


def test_ui_click_queues_only_selection_and_retains_key_when_response_is_lost(presentation):
    client, store, _, run_id = presentation
    run = store.get(run_id)
    result = run_ui(client, run, """
updateStartButton = () => {}; setFormsEnabled = () => {}; toast = () => {};
renderRun = () => {}; schedulePoll = () => {}; refreshHistory = () => {};
let failFirst = true;
api = async (path, options = {}) => {
  calls.push({path, method:options.method || 'GET', body:options.body ? JSON.parse(options.body) : null});
  if (options.method === 'POST' && failFirst) {failFirst=false; throw new Error('Response lost');}
  return {...payload.run, status:'queued', operation:{id:'new-operation', kind:'synthesis_continuation'}};
};
installEvents();
element('continue-synthesis').listeners.click();
await Promise.resolve(); await Promise.resolve();
const retained = state.pendingKeys.size;
element('continue-synthesis').listeners.click();
await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
return {calls, retained, pending:state.pendingKeys.size, busy:state.busy, operation:state.run.operation};
""")
    posts = [item for item in result["calls"] if item["method"] == "POST"]
    assert len(posts) == 2 and posts[0] == posts[1]
    assert posts[0]["path"] == f"/api/runs/{run_id}/continue-synthesis"
    assert posts[0]["body"] == {"source_operation_id": run["operation"]["id"], "idempotency_key": "stable-ui-request-key"}
    assert result["retained"] == 1 and result["pending"] == 0
    assert result["busy"] is False and result["operation"]["id"] == "new-operation"
