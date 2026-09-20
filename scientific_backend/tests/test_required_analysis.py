"""Scientist-required analyses must qualify before any model sees a fresh study.

Provider and analysis execution are mocked: these test orchestration, not scientific
findings or vendor access. The real paired adapter has separate source/QC tests.
"""
import asyncio
import copy
import hashlib
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app import analysis_tools, cases, config, gse28460_analysis, main, providers, worker
from app.store import Conflict, Store, digest
from governance_fixtures import pin_legacy_manual_policy
from test_providers import decision


SOURCE = {"path": "ana-agent-access/GSE28460/samples.csv", "sha256": "b" * 64}
RECIPE = {"id": gse28460_analysis.RECIPE_ID, "title": "Historical diagnosis/relapse pairs",
          "input_sources": [SOURCE]}
HYPOTHESIS = "My original CD19 hypothesis; preserve this exact wording.\n"


def evidence_record(*, case_id="case-1", sources=None, artifacts=None):
    values = {"case_id": case_id, "analysis_id": RECIPE["id"],
              "input_sources": copy.deepcopy([SOURCE] if sources is None else sources),
              "cohort": {"accession": "GSE28460", "therapy_context": "conventional treatment",
                         "car_t_exposure_established": False},
              "artifacts": artifacts or []}
    return {"id": "ANALYSIS-PAIRS", "title": "Paired expression context", "kind": "derived",
            "summary": "A separate historical-relapse cohort; not CAR-T replication.",
            "source": {"locator": RECIPE["id"], "sha256": digest(values)}, "values": values}


@pytest.fixture
def required(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    for module in (worker, config, main):
        monkeypatch.setattr(module, "RUNTIME", runtime)
    monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda _: [copy.deepcopy(RECIPE)])
    case = {"id": "case-1", "title": "Two distinct study contexts", "hypothesis": "Curator context.",
            "source_manifest": [copy.deepcopy(SOURCE)],
            "evidence": [{"id": "e1", "title": "Original CAR-T evidence", "summary": "Original source.",
                          "source": {"sha256": "a" * 64, "locator": "original source"}}]}
    monkeypatch.setattr(cases, "get_case", lambda _: copy.deepcopy(case))
    store = Store(tmp_path / "state.sqlite")
    payload = {"case_id": "case-1", "idempotency_key": uuid.uuid4().hex, "hypothesis": HYPOTHESIS,
               "source_name": "scientist.md", "mode": "live", "required_analysis_ids": [RECIPE["id"]]}
    run = store.create(case, payload)
    pin_legacy_manual_policy(store, run["id"])
    app = main.create_app(store, embedded=False)
    with TestClient(app) as client:
        yield client, store, app.state.worker, run["id"], case, payload


def test_required_analysis_is_accepted_before_model_and_original_hypothesis_is_unchanged(required, monkeypatch):
    _, store, engine, run_id, original_case, _ = required
    original_hypothesis = copy.deepcopy(store.get(run_id)["hypothesis"])
    ordering = []

    def analyze(*, case_id, output_dir):
        assert store.get(run_id)["actions"][-1]["state"] == "submitting"
        assert output_dir.parent == config.RUNTIME / "artifacts"
        ordering.append("analysis")
        return evidence_record(case_id=case_id)

    async def investigate(case, hypothesis, evidence, *args, **kwargs):
        ordering.append("model")
        run = store.get(run_id)
        accepted = next(item for item in evidence if item["id"] == "ANALYSIS-PAIRS")
        assert accepted in run["evidence"]
        assert accepted["values"]["cohort"]["car_t_exposure_established"] is False
        assert next(item for item in evidence if item["id"] == "e1") == original_case["evidence"][0]
        assert hypothesis == HYPOTHESIS
        assert case["required_analysis_ids"] == [RECIPE["id"]]
        assert run["required_analysis_operations"][0]["origin"] == "scientist_required_study_input"
        assert run["actions"][0]["state"] == "succeeded"
        with store.connect() as db:
            row = db.execute("SELECT request FROM actions WHERE id=?", (run["actions"][0]["id"],)).fetchone()
        assert json.loads(row[0])["source_manifest_sha256"] == digest(case["source_manifest"])
        return decision()

    monkeypatch.setattr(gse28460_analysis, "analyze", analyze)
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert after["status"] == "completed", after["error"]
    assert ordering == ["analysis", "model"]
    assert after["hypothesis"] == original_hypothesis
    assert original_case.get("required_analysis_ids") is None
    assert len(after["decisions"]) == 1


@pytest.mark.parametrize("failure", ["missing_file", "bad_hash", "wrong_case", "unpinned_source",
                                    "missing_sources", "removed_recipe", "followup_only"])
def test_required_analysis_failure_stops_before_any_model_or_decision(required, monkeypatch, failure):
    _, store, engine, run_id, _, _ = required
    calls = []

    def analyze(**kwargs):
        calls.append("analysis")
        if failure == "missing_file":
            raise FileNotFoundError("Required source file is missing")
        value = evidence_record(case_id="other-case" if failure == "wrong_case" else "case-1",
                                sources=[] if failure == "missing_sources" else None)
        if failure == "bad_hash":
            value["source"]["sha256"] = "f" * 64
        if failure == "unpinned_source":
            value["values"]["input_sources"][0]["sha256"] = "c" * 64
            value["source"]["sha256"] = digest(value["values"])
        return value

    async def forbidden(*args, **kwargs):
        pytest.fail("Model must not start without the required accepted analysis")

    monkeypatch.setattr(gse28460_analysis, "analyze", analyze)
    monkeypatch.setattr(providers, "investigate", forbidden)
    if failure == "removed_recipe":
        monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda _: [])
    if failure == "followup_only":
        monkeypatch.setattr(analysis_tools, "analysis_catalog", lambda _: [{**RECIPE, "followup_only": True}])
    asyncio.run(engine.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "failed"
    assert run["decisions"] == []
    assert [item["id"] for item in run["evidence"]] == ["e1"]
    assert not run.get("required_analysis_operations")
    assert all(action["kind"] != "research-model-investigation" for action in run["actions"])
    assert len(calls) == (0 if failure in {"removed_recipe", "followup_only"} else 1)


def test_successful_journal_entry_is_reused_without_recomputing_or_duplicate_evidence(required, monkeypatch):
    _, store, engine, run_id, _, _ = required
    run = store.get(run_id)
    action_id = run["operation"]["id"] + "-required-" + digest(RECIPE["id"])[:12]
    request = {"analysis_id": RECIPE["id"], "case_id": "case-1",
               "source_manifest_sha256": digest(run["case_snapshot"]["source_manifest"])}
    store.begin_action(run_id, action_id, "scientist-required-analysis", request)
    store.end_action(run_id, action_id, "succeeded", evidence_record())
    monkeypatch.setattr(gse28460_analysis, "analyze", lambda **_: pytest.fail("Accepted execution must not repeat"))
    model_calls = []

    async def investigate(*args, **kwargs):
        model_calls.append(True)
        return decision()

    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(engine.execute(run_id))
    asyncio.run(engine.execute(run_id))
    after = store.get(run_id)
    assert model_calls == [True]
    assert len(after["decisions"]) == len(after["required_analysis_operations"]) == 1
    assert [item["id"] for item in after["evidence"]].count("ANALYSIS-PAIRS") == 1
    assert len(after["actions"]) == 2


def test_required_artifacts_are_staged_downloadable_and_hash_checked(required, monkeypatch):
    client, store, engine, run_id, _, _ = required
    contents = {"gene-results.tsv": b"gene\teffect\nTEST\t0.25\n",
                "paired-summary.svg": b'<svg xmlns="http://www.w3.org/2000/svg"><text>Paired context</text></svg>'}

    def analyze(*, case_id, output_dir):
        output_dir.mkdir(parents=True)
        artifacts = []
        for name, data in contents.items():
            (output_dir / name).write_bytes(data)
            artifacts.append({"name": name, "sha256": hashlib.sha256(data).hexdigest(),
                              "bytes": len(data), "written": True})
        artifacts.append({"name": "not-written.tsv", "sha256": "c" * 64, "bytes": 1, "written": False})
        return evidence_record(case_id=case_id, artifacts=artifacts)

    async def investigate(*args, **kwargs):
        return decision()

    monkeypatch.setattr(gse28460_analysis, "analyze", analyze)
    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(engine.execute(run_id))
    run = store.get(run_id)
    assert run["status"] == "completed", run["error"]
    operation = run["required_analysis_operations"][0]
    assert len(operation["artifacts"]) == 2
    for artifact in operation["artifacts"]:
        response = client.get(artifact["url"])
        assert response.status_code == 200
        assert response.content == contents[artifact["name"]]
        assert response.headers["content-type"] == "application/octet-stream"
        assert response.headers["content-disposition"].startswith("attachment;")
        assert response.headers["x-content-type-options"] == "nosniff"
        path = config.RUNTIME / "artifacts" / operation["action_id"] / artifact["name"]
        path.write_bytes(b"changed bytes")
        assert client.get(artifact["url"]).status_code == 409
    unpublished = f"/api/runs/{run_id}/artifacts/{operation['action_id']}/not-written.tsv"
    assert client.get(unpublished).status_code == 404


@pytest.mark.parametrize("ids,status", [([RECIPE["id"], RECIPE["id"]], 409), (["not-registered"], 409),
                                      (["recipe-" + str(i) for i in range(9)], 422), ([], 202),
                                      ([RECIPE["id"]], 202)])
def test_intake_validates_required_recipes_and_preserves_user_text(required, ids, status):
    client, store, _, _, _, payload = required
    response = client.post("/api/runs", json={**payload, "mode": "demo", "idempotency_key": uuid.uuid4().hex,
                                              "required_analysis_ids": ids})
    assert response.status_code == status, response.text
    if status == 202:
        run = store.get(response.json()["id"])
        assert run["hypothesis"]["text"] == HYPOTHESIS
        assert run["case_snapshot"].get("required_analysis_ids", []) == ids


def test_store_also_rejects_duplicate_recipes_when_bypassing_http(required):
    _, store, _, _, case, payload = required
    before = len(store.list())
    with pytest.raises(Conflict, match="unique registered"):
        store.create(case, {**payload, "idempotency_key": uuid.uuid4().hex,
                            "required_analysis_ids": [RECIPE["id"], RECIPE["id"]]})
    assert len(store.list()) == before
