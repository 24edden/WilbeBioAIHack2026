"""Transactional run state, immutable decisions, and durable action intents.

SQLite lives on one machine. One worker lease is global to this database.
External operations never retry after an ambiguous crash or timeout.
"""
from __future__ import annotations
import copy
import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import DB_PATH


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    raw = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, path=DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests(scope TEXT, key TEXT, digest TEXT NOT NULL, run_id TEXT NOT NULL,
                PRIMARY KEY(scope,key));
            CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, kind TEXT NOT NULL,
                state TEXT NOT NULL, request TEXT NOT NULL, result TEXT, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS leases(name TEXT PRIMARY KEY, owner TEXT NOT NULL, expires REAL NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            yield db

    def get(self, run_id, db=None):
        if db is None:
            with self.connect() as connection:
                return self.get(run_id, connection)
        row = db.execute("SELECT body FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return json.loads(row[0])

    def list(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT body FROM runs ORDER BY rowid DESC LIMIT 100")]

    def save(self, db, run):
        run["updated_at"] = now()
        db.execute("INSERT OR REPLACE INTO runs(id,body) VALUES (?,?)", (run["id"], json.dumps(run, allow_nan=False)))

    def mutate(self, run_id, fn):
        with self.transaction() as db:
            run = self.get(run_id, db)
            fn(run)
            self.save(db, run)
            return run

    def dedupe(self, db, scope, key, payload):
        row = db.execute("SELECT digest,run_id FROM requests WHERE scope=? AND key=?", (scope, key)).fetchone()
        if row:
            if row[0] != digest(payload):
                raise Conflict("This request key was already used with different content.")
            return self.get(row[1], db)
        return None

    def record_request(self, db, scope, key, payload, run_id):
        db.execute("INSERT INTO requests VALUES (?,?,?,?)", (scope, key, digest(payload), run_id))

    def create(self, case, payload, memory_releases=None, evaluation_lesson=None):
        key = payload["idempotency_key"]
        with self.transaction() as db:
            existing = self.dedupe(db, "create", key, payload)
            if existing:
                return existing
            run_id = uuid.uuid4().hex
            text = payload["hypothesis"]
            run = dict(id=run_id, case_id=case["id"], title=case["title"],
                hypothesis={"text": text, "source_name": payload["source_name"], "sha256": digest(text)},
                mode=payload["mode"], status="queued", stage="intake", created_at=now(), updated_at=now(),
                events=[], evidence=[], decisions=[], actions=[], feedback=[], outcomes=[], handoffs=[], error=None,
                usage={"model_calls": 0, "tool_calls": 0, "input_tokens": 0, "output_tokens": 0},
                case_snapshot=copy.deepcopy(case), operation={"kind": "investigation", "id": uuid.uuid4().hex},
                cancel_requested=False, checkpoint=0, review_status="unreviewed")
            from .process_contract import get_process_contract
            run["process_contract"] = get_process_contract()
            run["memory_releases"] = copy.deepcopy(memory_releases or [])
            run["evaluation_lesson_id"] = payload.get("evaluation_lesson_id")
            run["case_snapshot"]["memory_releases"] = copy.deepcopy(memory_releases or [])
            if evaluation_lesson:
                run["case_snapshot"]["evaluation_lesson"] = copy.deepcopy(evaluation_lesson)
            if payload.get("required_analysis_ids"):
                from .analysis_tools import analysis_catalog
                requested = payload["required_analysis_ids"]
                allowed = {entry["id"] for entry in analysis_catalog(case["id"])} - {"cd19-softmax-followup"}
                if not isinstance(requested, list) or len(requested) > 8 or len(set(requested)) != len(requested) or not set(requested) <= allowed:
                    raise Conflict("Required analyses must be unique registered initial recipes.")
                run["case_snapshot"]["required_analysis_ids"] = list(requested)
            if payload.get("molecular_inputs"):
                run["case_snapshot"]["molecular_inputs"] = copy.deepcopy(payload["molecular_inputs"])
            self.append_event(run, "Intake", "Hypothesis preserved", "Original wording and source SHA-256 are pinned to this run.")
            self.save(db, run)
            self.record_request(db, "create", key, payload, run_id)
            return run

    @staticmethod
    def append_event(run, agent, title, detail, status="completed", type="step"):
        event = dict(id=len(run["events"])+1, time=now(), agent=agent, title=title, detail=detail, status=status, type=type)
        run["events"].append(event)
        return event

    def event(self, run_id, agent, title, detail, status="completed", type="step"):
        return self.mutate(run_id, lambda r: self.append_event(r, agent, title, detail, status, type))

    def lease(self, owner, seconds=20):
        with self.transaction() as db:
            row = db.execute("SELECT owner,expires FROM leases WHERE name='worker'").fetchone()
            if row and row[0] != owner and row[1] > time.time():
                return False
            db.execute("INSERT OR REPLACE INTO leases VALUES ('worker',?,?)", (owner, time.time()+seconds))
            return True

    def release(self, owner):
        with self.transaction() as db:
            db.execute("DELETE FROM leases WHERE name='worker' AND owner=?", (owner,))

    def begin_action(self, run_id, action_id, kind, request):
        with self.transaction() as db:
            row = db.execute("SELECT state,result FROM actions WHERE id=?", (action_id,)).fetchone()
            if row:
                if row[0] == "succeeded":
                    return json.loads(row[1])
                raise Conflict("External action has an unresolved prior attempt; it will not be resubmitted.")
            run = self.get(run_id, db)
            if run["cancel_requested"]:
                raise Conflict("Run was cancelled before external submission.")
            db.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?)",
                       (action_id, run_id, kind, "submitting", json.dumps(request), None, now()))
            run["actions"].append({"id": action_id, "kind": kind, "state": "submitting", "started_at": now()})
            self.save(db, run)
            return None

    def end_action(self, run_id, action_id, state, result):
        with self.transaction() as db:
            db.execute("UPDATE actions SET state=?,result=?,updated_at=? WHERE id=?",
                       (state, json.dumps(result), now(), action_id))
            run = self.get(run_id, db)
            for item in run["actions"]:
                if item["id"] == action_id:
                    item.update(state=state, finished_at=now())
            self.save(db, run)

    def recover(self):
        # Called only after holding the sole worker lease.
        for run in self.list():
            if run["status"] == "running":
                pending = any(a["state"] == "submitting" for a in run["actions"])
                if pending:
                    for action in run["actions"]:
                        if action["state"] == "submitting":
                            self.end_action(run["id"], action["id"], "unknown", {"reason": "Worker interrupted after intent; reconcile provider before repeat."})
                def update(r):
                    r["status"] = "blocked" if pending else "paused"
                    r["error"] = "External outcome unknown after worker interruption; no automatic resubmission." if pending else "Worker restarted. Resume this run from its saved inputs."
                    self.append_event(r, "Harness", "Run recovered", r["error"], "blocked" if pending else "paused", "recovery")
                self.mutate(run["id"], update)

    def enqueue_revision(self, run_id, kind, payload):
        with self.transaction() as db:
            existing = self.dedupe(db, f"{run_id}:{kind}", payload["idempotency_key"], payload)
            if existing:
                return existing
            run = self.get(run_id, db)
            if run["status"] in ("running", "queued"):
                raise Conflict("Wait for the active operation to finish before revising it.")
            if not run["decisions"] or payload["decision_version"] != run["decisions"][-1]["version"]:
                raise Conflict("This decision has changed. Reload and attach your input to the current version.")
            if kind == "outcome":
                handoff = run["decisions"][-1]["rd_handoff"]
                if payload["experiment_id"] != handoff["experiment_id"]:
                    raise Conflict("Experiment ID does not match this decision's R&D handoff.")
                candidates = {c["id"] for c in handoff.get("candidates", [])}
                if payload["candidate_id"] not in candidates:
                    raise Conflict("Candidate ID is not part of this decision's R&D handoff.")
            entry = {**payload, "id": uuid.uuid4().hex, "created_at": now()}
            run["feedback" if kind == "feedback" else "outcomes"].append(entry)
            run.update(status="queued", stage="revision", error=None, cancel_requested=False, checkpoint=0,
                       operation={"kind": kind, "id": entry["id"], "input": entry})
            self.append_event(run, "Scientist", "Correction received" if kind == "feedback" else "Measured outcome received",
                              f"Attached to immutable decision v{payload['decision_version']}; a new version will be issued.", type="feedback")
            self.save(db, run)
            self.record_request(db, f"{run_id}:{kind}", payload["idempotency_key"], payload, run_id)
            return run
