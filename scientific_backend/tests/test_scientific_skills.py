"""Skill integrity and durable receipts; orchestration is mocked, no vendor calls."""
import asyncio
import copy
import hashlib
import json
import shutil
import uuid

import pytest

from app import providers, scientific_skills, worker as workflow
from app.cases import get_case
from app.store import Store


@pytest.fixture
def isolated_skills(tmp_path, monkeypatch):
    root = tmp_path / "skills"
    shutil.copytree(scientific_skills.SKILL_ROOT, root)
    monkeypatch.setattr(scientific_skills, "SKILL_ROOT", root)
    return root


@pytest.fixture
def live_context(tmp_path):
    from governance_fixtures import pin_legacy_manual_policy
    store = Store(tmp_path / "skills.sqlite")
    case = get_case("cd19-car-t")
    run = store.create(case, {"case_id": case["id"], "hypothesis": case["hypothesis"],
        "source_name": "Isolated skill receipt test", "mode": "live", "idempotency_key": uuid.uuid4().hex})
    pin_legacy_manual_policy(store, run["id"])
    return workflow.Worker(store), store, run["id"], case


def request(skill_id="bioinformatician", role="bioinformatician"):
    skill = scientific_skills.load_skill(skill_id, role)
    return {"skill_id": skill_id, "role": role, "version": skill["version"], "sha256": skill["sha256"]}


def test_every_registered_skill_loads_exact_pinned_bytes_for_its_roles():
    for entry in scientific_skills.skill_catalog():
        for role in entry["roles"]:
            loaded = scientific_skills.load_skill(entry["id"], role)
            assert hashlib.sha256(loaded["instructions"].encode()).hexdigest() == entry["sha256"]
            assert loaded["version"] == entry["version"]
            assert loaded["origin"]


def test_wrong_role_and_unknown_skill_are_rejected():
    with pytest.raises(ValueError, match="not registered"):
        scientific_skills.load_skill("clinical_pharmacologist", "bioinformatician")
    with pytest.raises(ValueError, match="not registered"):
        scientific_skills.load_skill("unregistered-scientific-procedure", "coordinator")


def test_modified_instruction_bytes_fail_before_use(isolated_skills):
    record = scientific_skills.skill_catalog("bioinformatician")[0]
    path = isolated_skills / record["path"]
    path.write_text(path.read_text() + "\nChanged without releasing a new pinned version.\n")
    with pytest.raises(ValueError, match="pinned release"):
        scientific_skills.load_skill(record["id"], "bioinformatician")


def test_registry_path_cannot_escape_skill_root(isolated_skills):
    manifest = json.loads((isolated_skills / "manifest.json").read_text())
    outside = isolated_skills.parent / "outside.md"
    outside.write_text("Unregistered instructions outside the allowed directory.")
    manifest[0].update(path="../outside.md", sha256=hashlib.sha256(outside.read_bytes()).hexdigest())
    (isolated_skills / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="escapes"):
        scientific_skills.load_skill(manifest[0]["id"], manifest[0]["roles"][0])


def test_receipts_are_durable_idempotent_and_operation_scoped(live_context, monkeypatch):
    worker, store, run_id, case = live_context
    seen = []

    async def investigate(*args, **callbacks):
        first = await callbacks["accept_skill"](request())
        again = await callbacks["accept_skill"](request())
        assert first == again
        saved = Store(store.path).get(run_id)
        assert first in saved["skill_receipts"]
        assert first["operation_id"] == saved["operation"]["id"]
        assert first["sha256"] == scientific_skills.load_skill("bioinformatician", "bioinformatician")["sha256"]
        seen.append(copy.deepcopy(first))
        return copy.deepcopy(case["demo_decision"])

    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    initial = store.get(run_id)
    assert initial["status"] == "completed", initial.get("error")
    assert len(initial["skill_receipts"]) == 1
    store.enqueue_revision(run_id, "feedback", {"decision_version": 1,
        "text": "Isolated software test: preserve the source-scope limitation.", "idempotency_key": "skill-revision"})
    asyncio.run(worker.execute(run_id))
    revised = Store(store.path).get(run_id)
    assert revised["status"] == "completed", revised.get("error")
    assert len(revised["skill_receipts"]) == 2
    assert revised["skill_receipts"][0] == initial["skill_receipts"][0]
    assert seen[0]["id"] != seen[1]["id"]
    assert seen[0]["operation_id"] != seen[1]["operation_id"]
    assert len([e for e in revised["events"] if e["type"] == "skill.loaded"]) == 2
    assert revised["usage"]["model_calls"] == 0


def test_worker_cannot_persist_receipt_for_tampered_skill(live_context, isolated_skills, monkeypatch):
    worker, store, run_id, case = live_context
    original_request = request()
    record = scientific_skills.skill_catalog("bioinformatician")[0]
    path = isolated_skills / record["path"]
    path.write_text(path.read_text() + "\nTampered after instruction selection.\n")

    async def investigate(*args, **callbacks):
        with pytest.raises(ValueError, match="pinned release"):
            await callbacks["accept_skill"](original_request)
        assert Store(store.path).get(run_id).get("skill_receipts", []) == []
        return copy.deepcopy(case["demo_decision"])

    monkeypatch.setattr(providers, "investigate", investigate)
    asyncio.run(worker.execute(run_id))
    result = store.get(run_id)
    assert result["status"] == "completed", result.get("error")
    assert not result.get("skill_receipts")
    assert not any(e["type"] == "skill.loaded" for e in result["events"])
