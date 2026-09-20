"""Executable recommendation boundaries; all inference is explicitly mocked."""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app import analysis_tools, followups, main, providers, worker
from app.provider_schemas import Investigation
from app.store import Store, digest
from test_providers import decision


SOURCE = {"path": "sources/test/table.tsv", "sha256": "b" * 64}
RECIPE = {"id": "test-analysis", "title": "Test source comparison", "description": "Recompute a pinned comparison.",
          "input_sources": [SOURCE]}


def recommendation():
    return {"kind": "data_analysis", "analysis_id": "test-analysis", "title": "Compare the qualified groups",
            "rationale": "The accepted source leaves a measurable contrast unresolved.",
            "decision_it_could_change": "Whether the group difference supports the proposed mechanism.",
            "prerequisites": ["Pinned source table"], "evidence_ids": ["e1"], "status": "ready"}


def analysis_record():
    values = {"case_id": "case-1", "analysis_id": "test-analysis", "input_sources": [SOURCE], "contrast": 3.0}
    checksum = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return {"id": "ANALYSIS-TEST", "title": "Recomputed comparison", "kind": "analysis", "summary": "The observed contrast is 3.",
            "source": {"name": "Pinned test analysis", "url": "https://example.org/data", "locator": "test-analysis", "sha256": checksum}, "values": values}


@pytest.fixture
def harness(tmp_path, monkeypatch):
    from governance_fixtures import pin_legacy_manual_policy
    monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda case_id: [copy.deepcopy(RECIPE)])
    monkeypatch.setattr(worker, "RUNTIME", tmp_path / "runtime")
    monkeypatch.setattr(main, "RUNTIME", tmp_path / "runtime")
    store = Store(tmp_path / "state.sqlite")
    case = {"id": "case-1", "title": "Source packet", "hypothesis": "Original exact wording.\n", "source_manifest": [SOURCE],
            "evidence": [{"id": "e1", "title": "Source", "summary": "An observation", "source": {"name": "Source", "locator": "table", "url": "https://example.org/data", "sha256": "b" * 64}}]}
    run = store.create(case, {"idempotency_key": uuid.uuid4().hex, "hypothesis": case["hypothesis"], "source_name": "scientist.md", "mode": "live"})
    pin_legacy_manual_policy(store, run["id"])
    store.mutate(run["id"], lambda r: r.update(evidence=copy.deepcopy(case["evidence"])))
    app = main.create_app(store, embedded=False)
    initial = decision()
    initial["followups"] = [recommendation()]
    app.state.worker.publish(run["id"], initial)
    with TestClient(app) as client:
        yield client, store, app.state.worker, run["id"]


def selection(client, run_id):
    response = client.get(f"/api/runs/{run_id}/followups")
    assert response.status_code == 200
    result = response.json()
    return {"decision_version": result["decision_version"], "recommendation_id": result["followups"][0]["id"], "idempotency_key": uuid.uuid4().hex}


def test_recommendation_is_bound_to_registered_recipe_and_accepted_evidence():
    value = decision()
    value["followups"] = [recommendation()]
    approved = [{**RECIPE, "kind": "data_analysis"}]
    evidence = [{"id": "e1"}]
    assert providers.validate_investigation(Investigation.model_validate(value), evidence, approved_followups=approved)["insights"][0]["finding"]
    value["followups"][0]["analysis_id"] = "model-invented-code"
    with pytest.raises(providers.ProviderError, match="registered recipe"):
        providers.validate_investigation(Investigation.model_validate(value), evidence, approved_followups=approved)
    value["followups"] = []
    value["insights"][0]["evidence_ids"] = ["invented"]
    with pytest.raises(providers.ProviderError, match="accepted evidence"):
        providers.validate_investigation(Investigation.model_validate(value), evidence, approved_followups=approved)


def test_followup_api_versions_idempotency_and_serialization(harness):
    client, store, _, run_id = harness
    payload = selection(client, run_id)
    stale = client.post(f"/api/runs/{run_id}/followups", json={**payload, "decision_version": 2})
    assert stale.status_code == 409
    first = client.post(f"/api/runs/{run_id}/followups", json=payload)
    assert first.status_code == 202
    assert first.json()["operation"]["kind"] == "followup"
    assert client.post(f"/api/runs/{run_id}/followups", json=payload).status_code == 202
    assert len(store.get(run_id)["followup_operations"]) == 1
    assert client.post(f"/api/runs/{run_id}/followups", json={**payload, "idempotency_key": "another"}).status_code == 409
    assert client.post(f"/api/runs/{run_id}/followups", json={**payload, "recommendation_id": "different"}).status_code == 409
    assert client.get(f"/api/runs/{run_id}/followups").json()["followups"][0]["status"] == "running"


def test_old_snapshot_requires_fresh_investigation(harness):
    client, store, _, run_id = harness
    payload = selection(client, run_id)
    store.mutate(run_id, lambda r: r["case_snapshot"].update(source_manifest=[]))
    result = client.get(f"/api/runs/{run_id}/followups").json()["followups"][0]
    assert result["status"] == "needs_inputs" and result["executable"] is False
    assert "fresh investigation" in result["reason"]
    assert client.post(f"/api/runs/{run_id}/followups", json=payload).status_code == 409


def test_legacy_catalog_is_never_labelled_as_model_recommendation(harness):
    client, store, _, run_id = harness
    store.mutate(run_id, lambda r: r["decisions"][-1].pop("followups"))
    result = client.get(f"/api/runs/{run_id}/followups").json()["followups"][0]
    assert result["origin"] == "registered_catalog"
    store.mutate(run_id, lambda r: r.update(mode="demo"))
    assert client.get(f"/api/runs/{run_id}/followups").json()["followups"][0]["executable"] is False


@pytest.mark.parametrize("followup_only", [False, True])
def test_selected_analysis_is_accepted_before_review_and_preserves_prior_decision(harness, monkeypatch, followup_only):
    client, store, engine, run_id = harness
    if followup_only:
        monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda case_id: [{**RECIPE, "followup_only": True}])
    before = store.get(run_id)
    calls = []
    def analyze(case_id, analysis_id):
        calls.append((case_id, analysis_id))
        return analysis_record()
    monkeypatch.setattr(analysis_tools, "analyze_case", analyze)
    async def review(case, hypothesis, evidence, emit, cancelled, **kwargs):
        assert hypothesis == before["hypothesis"]["text"]
        assert case["followup_context"]["evidence_ids"] == ["ANALYSIS-TEST"]
        assert "metadata" not in case["followup_context"]["previous_decision"]
        assert "ANALYSIS-TEST" in {e["id"] for e in store.get(run_id)["evidence"]}
        result = decision()
        result["insights"][0].update(finding="The recomputed contrast is 3; causality remains unresolved.", evidence_ids=["ANALYSIS-TEST"])
        return result
    monkeypatch.setattr(providers, "investigate", review)
    payload = selection(client, run_id)
    assert client.post(f"/api/runs/{run_id}/followups", json=payload).status_code == 202
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert after["status"] == "completed", after["error"]
    assert calls == [("case-1", "test-analysis")]
    assert after["hypothesis"] == before["hypothesis"]
    assert after["decisions"][0] == before["decisions"][0]
    assert after["decisions"][-1]["version"] == 2
    assert after["followup_operations"][0]["new_decision_version"] == 2
    assert after["followup_operations"][0]["evidence_id"] == "ANALYSIS-TEST"
    assert all(a["state"] == "succeeded" for a in after["actions"])
    assert client.post(f"/api/runs/{run_id}/followups", json=payload).status_code == 202
    assert len(store.get(run_id)["decisions"]) == 2
    assert client.get(f"/api/runs/{run_id}/followups").json()["followups"][0]["status"] == "completed"


@pytest.mark.parametrize("failure", ["bad_hash", "changed_recipe", "source_error"])
def test_failed_followup_has_no_new_decision_or_fabricated_evidence(harness, monkeypatch, failure):
    client, store, engine, run_id = harness
    assert client.post(f"/api/runs/{run_id}/followups", json=selection(client, run_id)).status_code == 202
    def analyze(*args):
        if failure == "source_error":
            raise ValueError("Source QC failed")
        value = analysis_record()
        value["source"]["sha256"] = "a" * 64
        return value
    monkeypatch.setattr(analysis_tools, "analyze_case", analyze)
    if failure == "changed_recipe":
        monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda case_id: [{**RECIPE, "description": "Changed method"}])
    async def forbidden(*args, **kwargs):
        pytest.fail("Review must not start without accepted follow-up evidence")
    monkeypatch.setattr(providers, "investigate", forbidden)
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "failed"
    assert len(result["evidence"]) == len(result["decisions"]) == 1
    assert result["followup_operations"][0]["status"] == "failed"


def test_published_artifact_hash_is_revalidated_on_every_download(harness):
    client, store, _, run_id = harness
    action_id = "test-artifact"
    directory = main.RUNTIME / "artifacts" / action_id
    directory.mkdir(parents=True)
    path = directory / "prediction.cif"
    path.write_bytes(b"recorded structure bytes")
    url = f"/api/runs/{run_id}/artifacts/{action_id}/prediction.cif"
    def attach(run):
        run["actions"].append({"id": action_id, "state": "succeeded"})
        run["followup_operations"] = [{"artifacts": [{"url": url, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}]
    store.mutate(run_id, attach)
    assert client.get(url).content == b"recorded structure bytes"
    path.write_bytes(b"tampered")
    assert client.get(url).status_code == 409
    path.unlink()
    other = directory.parent / "external.cif"
    other.write_bytes(b"recorded structure bytes")
    path.symlink_to(other)
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("pending", [False, "first", "second"])
def test_structural_followup_receipts_and_preview_are_separate_from_binder_modeling(harness, monkeypatch, pending):
    import httpx
    from app import structural_followups as structural
    from test_structural_followups import mock_client, synthetic_cif
    client, store, engine, run_id = harness
    inputs = structural.qualified_inputs()
    def qualify(run):
        run["case_id"] = "cd19-car-t"
        run["case_snapshot"].update(id="cd19-car-t", source_manifest=[SOURCE] + inputs["sources"])
    store.mutate(run_id, qualify)
    requests = []
    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if pending == "first" or (pending == "second" and len(requests) == 2):
            return httpx.Response(202, headers={"nvcf-reqid": "test-pending"}, json={"status": "pending"})
        sequence = payload["polymers"][0]["sequence"]
        return httpx.Response(200, headers={"nvcf-reqid": "test-" + str(len(requests))}, json={
            "structures": [{"format": "mmcif", "structure": synthetic_cif(sequence)}], "confidence_scores": [.7]})
    mock_client(monkeypatch, handler)
    async def review(case, hypothesis, evidence, emit, cancelled, **kwargs):
        assert pending is False
        operation = store.get(run_id)["followup_operations"][-1]
        assert operation["status"] == "reviewing" and len(operation["artifacts"]) == 2
        assert all("path" not in artifact for artifact in operation["artifacts"])
        result = decision()
        result["insights"][0].update(finding="The public isoforms have different predicted structures; binding remains untested.",
                                    evidence_ids=case["followup_context"]["evidence_ids"])
        return result
    monkeypatch.setattr(providers, "investigate", review)
    menu = client.get(f"/api/runs/{run_id}/followups").json()
    action = next(item for item in menu["followups"] if item["analysis_id"] == structural.RECIPE)
    assert action["executable"] is True, action
    payload = {"decision_version": 1, "recommendation_id": action["id"], "idempotency_key": uuid.uuid4().hex}
    assert client.post(f"/api/runs/{run_id}/followups", json=payload).status_code == 202
    asyncio.run(engine.execute(run_id))
    result = store.get(run_id)
    if pending:
        assert len(requests) == (1 if pending == "first" else 2) and result["status"] == "blocked"
        assert result["actions"][-1]["state"] == "unknown"
        assert len(result["decisions"]) == 1 and len(result["evidence"]) == 1
        operation = result["followup_operations"][0]
        assert operation["result_status"] == "pending"
        assert operation["provider_receipts"][-1]["request_id"] == "test-pending"
        assert len(operation["artifacts"]) == (0 if pending == "first" else 1)
        for artifact in operation["artifacts"]:
            assert client.get(artifact["preview_url"]).status_code == 200
        assert client.post(f"/api/runs/{run_id}/resume").status_code == 409
        return
    assert len(requests) == 2 and result["status"] == "completed", result["error"]
    assert result["decisions"][-1]["rd_handoff"]["modeling"]["status"] == "blocked"
    operation = result["followup_operations"][0]
    for artifact in operation["artifacts"]:
        downloaded = client.get(artifact["url"])
        assert downloaded.status_code == 200
        assert hashlib.sha256(downloaded.content).hexdigest() == artifact["sha256"]
        preview = client.get(artifact["preview_url"])
        assert preview.status_code == 200, preview.text
        assert preview.json()["scope"] == structural.SCOPE
        assert preview.json()["receipt"]["request_id"] == artifact["request_id"]
        assert preview.json()["residue_count"] in {272, 183}


def test_engineering_preview_reuses_verified_download_boundary(harness):
    from test_engineering_checks import make_check
    from test_structure_preview import cif
    client, _, _, _ = harness
    directory, receipt, receipt_path = make_check(main.RUNTIME)
    data = cif()
    (directory / "prediction.cif").write_bytes(data)
    receipt["artifacts"][0]["sha256"] = hashlib.sha256(data).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    url = client.get("/api/health").json()["engineering_checks"]["bionemo"]["links"]["preview"]
    result = client.get(url)
    assert result.status_code == 200, result.text
    assert result.json()["scope"] == "engineering_monomer_only"
    assert result.json()["receipt"]["sha256"] == receipt["artifacts"][0]["sha256"]
    (directory / "prediction.cif").write_bytes(b"tampered")
    assert client.get(url).status_code == 404
