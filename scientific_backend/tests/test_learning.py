import asyncio
import copy
import uuid
import pytest
from app.cases import get_case
from app.learning import Learning
from app.store import Conflict, Store
from app.worker import Worker


@pytest.fixture
def memory(tmp_path, monkeypatch):
    monkeypatch.setattr("app.worker.DEMO_DELAY", 0)
    store = Store(tmp_path / "state.sqlite")
    return store, Learning(store)


def make_run(store, case_id, evaluation_lesson_id=None, lesson=None, mode="demo"):
    case = get_case(case_id)
    payload = {"case_id": case_id, "hypothesis": case["hypothesis"], "source_name": "test case selection", "mode": mode, "idempotency_key": uuid.uuid4().hex}
    if evaluation_lesson_id:
        payload["evaluation_lesson_id"] = evaluation_lesson_id
    run = store.create(case, payload, evaluation_lesson=lesson)
    if mode == "demo":
        asyncio.run(Worker(store).execute(run["id"]))
    return store.get(run["id"])


def proposal(store, learning):
    origin = make_run(store, "cd19-car-t")
    return learning.propose({"origin_run_id": origin["id"], "decision_version": 1,
        "procedure": "Retain a missing-measurement statement rather than infer absent protein from incomplete evidence.",
        "conditions": "Apply only to the declared assay interpretation; request a direct protein assay when absent.",
        "scope_case_ids": ["alk-l1196m"], "excluded_case_ids": ["bcma-gse164551"], "author": "test scientist"})


def passing_evaluation(store, learning, lesson):
    learning.review(lesson["id"], {"approved": True, "reviewer": "test reviewer", "notes": "Fixture review tests the gate, not scientific validity."})
    base = make_run(store, "alk-l1196m")
    candidate = learning.candidate_for_evaluation(lesson["id"], "alk-l1196m", "demo")
    trial = make_run(store, "alk-l1196m", lesson["id"], candidate)
    outside = make_run(store, "bcma-gse164551")
    report = {"baseline_run_id": base["id"], "candidate_run_id": trial["id"], "out_of_scope_run_id": outside["id"],
              "quality_passed": True, "evaluator": "fixture evaluator", "notes": "Synthetic test judgment only; no scientific efficacy claim."}
    learning.evaluate(lesson["id"], report)
    return base, trial, outside, report


def test_provisional_cannot_release_or_influence_runs(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    assert lesson["status"] == "provisional"
    assert learning.applicable("alk-l1196m", "demo") == []
    with pytest.raises(Conflict, match="provisional"):
        learning.release(lesson["id"])
    with pytest.raises(Conflict, match="review"):
        learning.candidate_for_evaluation(lesson["id"], "alk-l1196m", "demo")


def test_review_disjoint_evaluation_release_mode_scope_and_suspend(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    passing_evaluation(store, learning, lesson)
    released = learning.release(lesson["id"])
    assert learning.release(lesson["id"])["release_id"] == released["release_id"]
    assert len(learning.applicable("alk-l1196m", "demo")) == 1
    assert learning.applicable("alk-l1196m", "live") == []
    assert learning.applicable("bcma-gse164551", "demo") == []
    pinned = learning.applicable("alk-l1196m", "demo")
    learning.suspend(released["release_id"])
    assert learning.applicable("alk-l1196m", "demo") == []
    assert pinned[0]["sha256"]  # Existing run snapshots remain available.


def test_evaluation_rejects_same_case_origin_and_unequal_hypotheses(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    base, trial, outside, report = passing_evaluation(store, learning, lesson)
    altered = {**report, "baseline_run_id": lesson["origin_run_id"]}
    with pytest.raises(Conflict, match="disjoint"):
        learning.evaluate(lesson["id"], altered)
    store.mutate(trial["id"], lambda r: r["hypothesis"].update(sha256="changed"))
    with pytest.raises(Conflict, match="matched hypotheses"):
        learning.evaluate(lesson["id"], report)


def test_changed_decision_invalidates_release(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    base, _, _, _ = passing_evaluation(store, learning, lesson)
    store.mutate(base["id"], lambda r: r["decisions"][-1].update(sha256="changed-after-evaluation"))
    with pytest.raises(Conflict, match="changed"):
        learning.release(lesson["id"])


def test_failed_quality_review_and_out_of_scope_stay_provisional(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    _, _, _, report = passing_evaluation(store, learning, lesson)
    learning.evaluate(lesson["id"], {**report, "quality_passed": False})
    with pytest.raises(Conflict, match="provisional"):
        learning.release(lesson["id"])
    with pytest.raises(Conflict, match="in-scope"):
        learning.candidate_for_evaluation(lesson["id"], "bcma-gse164551", "demo")


def test_new_reassessment_invalidates_release_before_new_decision_exists(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    base, _, _, _ = passing_evaluation(store, learning, lesson)
    store.enqueue_revision(base["id"], "feedback", {"decision_version": 1, "text": "A source assumption requires reassessment.", "idempotency_key": uuid.uuid4().hex})
    with pytest.raises(Conflict, match="changed"):
        learning.release(lesson["id"])


def test_unmatched_released_memory_invalidates_comparison(memory):
    store, learning = memory
    lesson = proposal(store, learning)
    _, trial, _, report = passing_evaluation(store, learning, lesson)
    store.mutate(trial["id"], lambda r: r.update(memory_releases=[{"id": "different-procedure"}]))
    with pytest.raises(Conflict, match="identical released"):
        learning.evaluate(lesson["id"], report)
