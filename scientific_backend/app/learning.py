"""L4: lessons stay provisional until reviewed and evaluated on disjoint runs.

This is a release gate, not automatic biological validation. Scientist evaluation
is explicitly attributed, and demo-mode releases cannot enter live investigations.
"""
import copy
import json
import uuid
from .store import Conflict, Store, digest, now


class Learning:
    def __init__(self, store: Store):
        self.store = store
        with store.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS memory_releases(id TEXT PRIMARY KEY, body TEXT NOT NULL, suspended INTEGER NOT NULL DEFAULT 0);
            """)

    def list(self):
        with self.store.connect() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT body FROM lessons ORDER BY rowid DESC")]

    def get(self, lesson_id, db):
        row = db.execute("SELECT body FROM lessons WHERE id=?", (lesson_id,)).fetchone()
        if not row:
            raise KeyError(lesson_id)
        return json.loads(row[0])

    def save(self, db, lesson):
        db.execute("INSERT OR REPLACE INTO lessons VALUES (?,?)", (lesson["id"], json.dumps(lesson)))

    def propose(self, payload):
        with self.store.transaction() as db:
            origin = self.store.get(payload["origin_run_id"], db)
            decision = next((d for d in origin["decisions"] if d["version"] == payload["decision_version"]), None)
            if not decision:
                raise Conflict("Lesson must cite an existing immutable decision version.")
            if set(payload["scope_case_ids"]) & set(payload["excluded_case_ids"]):
                raise Conflict("A case cannot be both in and out of scope.")
            lesson_id = "lesson-" + digest(payload)[:24]
            existing = db.execute("SELECT body FROM lessons WHERE id=?", (lesson_id,)).fetchone()
            if existing:
                return json.loads(existing[0])
            lesson = {**payload, "id": lesson_id, "version": 1, "origin_case_id": origin["case_id"],
                      "origin_decision_sha256": decision["sha256"], "mode": origin["mode"], "status": "provisional",
                      "created_at": now(), "review": None, "evaluation": None, "release_id": None}
            self.save(db, lesson)
            return lesson

    def review(self, lesson_id, payload):
        with self.store.transaction() as db:
            lesson = self.get(lesson_id, db)
            if lesson["release_id"]:
                raise Conflict("Released lessons are immutable; suspend and propose a new version.")
            lesson["review"] = {**payload, "time": now(), "attribution": "User-supplied scientist review"}
            lesson["status"] = "reviewed" if payload["approved"] else "provisional"
            self.save(db, lesson)
            return lesson

    def evaluate(self, lesson_id, payload):
        with self.store.transaction() as db:
            lesson = self.get(lesson_id, db)
            if lesson["release_id"]:
                raise Conflict("Evaluation for a released lesson is immutable.")
            base = self.store.get(payload["baseline_run_id"], db)
            trial = self.store.get(payload["candidate_run_id"], db)
            outside = self.store.get(payload["out_of_scope_run_id"], db)
            if len({base["id"], trial["id"], outside["id"]}) != 3:
                raise Conflict("Evaluation requires three distinct baseline, candidate and out-of-scope runs.")
            if any(r["status"] != "completed" or not r["decisions"] for r in (base, trial, outside)):
                raise Conflict("Evaluation runs must be completed with valid decisions.")
            if any(r["mode"] != lesson["mode"] for r in (base, trial, outside)):
                raise Conflict("Evaluation cannot mix live and demonstration modes.")
            if base["case_id"] == lesson["origin_case_id"] or base["case_id"] != trial["case_id"]:
                raise Conflict("The evaluation case must be disjoint from the origin, with matching baseline/candidate cases.")
            if base["case_id"] not in lesson["scope_case_ids"] or outside["case_id"] not in lesson["excluded_case_ids"]:
                raise Conflict("Evaluation must include an in-scope and explicitly excluded case.")
            if base["hypothesis"]["sha256"] != trial["hypothesis"]["sha256"] or digest(base["case_snapshot"]["evidence"]) != digest(trial["case_snapshot"]["evidence"]):
                raise Conflict("Baseline/candidate evaluation must use matched hypotheses and source evidence.")
            if digest(base.get("memory_releases", [])) != digest(trial.get("memory_releases", [])):
                raise Conflict("Baseline/candidate evaluation must use identical released procedural memory.")
            if base.get("evaluation_lesson_id") or trial.get("evaluation_lesson_id") != lesson_id or outside.get("evaluation_lesson_id"):
                raise Conflict("Only the candidate evaluation run may receive this provisional lesson.")
            pinned_ids = [r["id"] for r in (base, trial, outside)]
            lesson["evaluation"] = {**payload, "time": now(), "checks_passed": True,
                "run_decision_hashes": {r["id"]: r["decisions"][-1]["sha256"] for r in (base, trial, outside)},
                "attribution": "Scientist-supplied quality judgment; identity, disjointness and scope verified by software"}
            self.save(db, lesson)
            return lesson

    def release(self, lesson_id):
        with self.store.transaction() as db:
            lesson = self.get(lesson_id, db)
            if lesson["release_id"]:
                return lesson
            review, evaluation = lesson.get("review"), lesson.get("evaluation")
            if not review or not review["approved"] or not evaluation or not evaluation["quality_passed"]:
                raise Conflict("Lesson remains provisional: approved scientist review and a passing disjoint evaluation are required.")
            for run_id, expected in evaluation["run_decision_hashes"].items():
                run = self.store.get(run_id, db)
                if run["status"] != "completed" or run["decisions"][-1]["sha256"] != expected:
                    raise Conflict("An evaluated decision changed. Re-evaluate the latest version before release.")
            release = {"id": "release-"+uuid.uuid4().hex, "lesson_id": lesson_id, "mode": lesson["mode"],
                       "lesson": copy.deepcopy(lesson), "created_at": now()}
            release["sha256"] = digest(release)
            db.execute("INSERT INTO memory_releases(id,body,suspended) VALUES (?,?,0)", (release["id"], json.dumps(release)))
            lesson.update(status="released", release_id=release["id"])
            self.save(db, lesson)
            return lesson

    def suspend(self, release_id):
        with self.store.transaction() as db:
            result = db.execute("UPDATE memory_releases SET suspended=1 WHERE id=?", (release_id,))
            if not result.rowcount:
                raise KeyError(release_id)
        return {"release_id": release_id, "status": "suspended", "detail": "Future investigations will not receive this release. Existing pinned runs retain their history."}

    def applicable(self, case_id, mode):
        with self.store.connect() as db:
            releases = [json.loads(row[0]) for row in db.execute("SELECT body FROM memory_releases WHERE suspended=0")]
        return [r for r in releases if r["mode"] == mode and case_id in r["lesson"]["scope_case_ids"] and case_id not in r["lesson"]["excluded_case_ids"]]

    def candidate_for_evaluation(self, lesson_id, case_id, mode):
        with self.store.connect() as db:
            lesson = self.get(lesson_id, db)
        if lesson["mode"] != mode or lesson["origin_case_id"] == case_id or case_id not in lesson["scope_case_ids"] or case_id in lesson["excluded_case_ids"]:
            raise Conflict("Provisional lesson evaluation must use a disjoint, in-scope case in the same execution mode.")
        if not lesson.get("review") or not lesson["review"]["approved"]:
            raise Conflict("Scientist review is required before a provisional lesson enters evaluation.")
        return {"id": lesson["id"], "status": "provisional_evaluation_only", "procedure": lesson["procedure"], "conditions": lesson["conditions"], "source_decision_sha256": lesson["origin_decision_sha256"]}
