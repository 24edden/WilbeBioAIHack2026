-- Proposed migration 001. Empty-database syntax checked during plan validation.
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE cases (
  id TEXT PRIMARY KEY,
  manifest_version TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  manifest_json TEXT NOT NULL CHECK (json_valid(manifest_json)),
  created_at TEXT NOT NULL
);

CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(id),
  idempotency_key TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('live','replay','synthetic')),
  status TEXT NOT NULL CHECK (status IN (
    'queued','qualifying','investigating','waiting_for_input','waiting_for_tool',
    'reviewing','awaiting_scientist','completed','failed','cancelled','budget_exhausted')),
  conclusion_status TEXT CHECK (conclusion_status IN (
    'supported_within_scope','contradicted','unresolved','not_evaluable')),
  review_status TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (review_status IN ('unreviewed','changes_requested','accepted')),
  state_version INTEGER NOT NULL DEFAULT 0,
  checkpoint_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(checkpoint_json)),
  budget_json TEXT NOT NULL CHECK (json_valid(budget_json)),
  usage_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(usage_json)),
  model_manifest_json TEXT NOT NULL CHECK (json_valid(model_manifest_json)),
  code_commit TEXT NOT NULL,
  lock_hash TEXT NOT NULL,
  session_id TEXT,
  memory_release_id TEXT,
  lease_owner TEXT,
  lease_expires_at TEXT,
  cancellation_requested_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (case_id, idempotency_key)
);

CREATE TABLE actions (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(id),
  logical_key TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  contract_version TEXT NOT NULL,
  backend TEXT NOT NULL,
  replicate_index INTEGER NOT NULL DEFAULT 0 CHECK (replicate_index >= 0),
  parent_action_id TEXT,
  state TEXT NOT NULL CHECK (state IN (
    'queued','submitting','pending','succeeded','failed','unknown','cancelled')),
  request_json TEXT NOT NULL CHECK (json_valid(request_json)),
  result_summary_json TEXT CHECK (result_summary_json IS NULL OR json_valid(result_summary_json)),
  reserved_cost_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(reserved_cost_json)),
  lease_owner TEXT,
  lease_expires_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (run_id, logical_key),
  UNIQUE (id, run_id),
  FOREIGN KEY (parent_action_id, run_id) REFERENCES actions(id, run_id)
);

CREATE TABLE action_attempts (
  id TEXT PRIMARY KEY,
  action_id TEXT NOT NULL REFERENCES actions(id),
  attempt_index INTEGER NOT NULL CHECK (attempt_index >= 1),
  endpoint_origin TEXT NOT NULL,
  external_request_id TEXT,
  state TEXT NOT NULL CHECK (state IN (
    'submitting','pending','succeeded','failed','unknown','cancelled')),
  http_status INTEGER,
  error_code TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  UNIQUE (action_id, attempt_index)
);

CREATE TABLE artifacts (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(id),
  sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
  relative_path TEXT NOT NULL,
  media_type TEXT NOT NULL,
  byte_count INTEGER NOT NULL CHECK (byte_count >= 0),
  artifact_kind TEXT NOT NULL CHECK (artifact_kind IN (
    'source','request','raw_response','derived_table','structure','tensor','report','manifest')),
  created_at TEXT NOT NULL,
  UNIQUE (run_id, relative_path),
  UNIQUE (id, run_id)
);

CREATE TABLE evidence (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(id),
  action_id TEXT,
  artifact_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN (
    'measurement','derived_analysis','model_prediction','literature_interpretation','synthetic')),
  quality_state TEXT NOT NULL CHECK (quality_state IN ('accepted','rejected','provisional')),
  source_locator_json TEXT NOT NULL CHECK (json_valid(source_locator_json)),
  summary_json TEXT NOT NULL CHECK (json_valid(summary_json)),
  limitations_json TEXT NOT NULL CHECK (json_valid(limitations_json)),
  created_at TEXT NOT NULL,
  FOREIGN KEY (action_id, run_id) REFERENCES actions(id, run_id),
  FOREIGN KEY (artifact_id, run_id) REFERENCES artifacts(id, run_id),
  UNIQUE (id, run_id)
);

CREATE TABLE decisions (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(id),
  version INTEGER NOT NULL CHECK (version >= 1),
  previous_decision_id TEXT,
  payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
  payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
  created_at TEXT NOT NULL,
  UNIQUE (run_id, version),
  UNIQUE (id, run_id),
  FOREIGN KEY (previous_decision_id, run_id) REFERENCES decisions(id, run_id)
);

CREATE TABLE feedback (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(id),
  decision_id TEXT NOT NULL,
  claim_id TEXT,
  reviewer_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN (
    'accept','correct_claim','request_evidence','retain_disagreement')),
  body TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (decision_id, run_id) REFERENCES decisions(id, run_id),
  UNIQUE (run_id, idempotency_key)
);

CREATE TABLE events (
  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  run_id TEXT NOT NULL REFERENCES runs(id),
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
  created_at TEXT NOT NULL
);

CREATE INDEX runs_dispatch ON runs(status, lease_expires_at);
CREATE INDEX actions_dispatch ON actions(state, lease_expires_at);
CREATE INDEX events_run_sequence ON events(run_id, sequence);
CREATE INDEX evidence_run_kind ON evidence(run_id, kind, quality_state);

-- Immutable scientific history. Corrections append versions/events.
CREATE TRIGGER decisions_no_update BEFORE UPDATE ON decisions
BEGIN SELECT RAISE(ABORT, 'append a decision version'); END;
CREATE TRIGGER decisions_no_delete BEFORE DELETE ON decisions
BEGIN SELECT RAISE(ABORT, 'decision history is immutable'); END;
CREATE TRIGGER feedback_no_update BEFORE UPDATE ON feedback
BEGIN SELECT RAISE(ABORT, 'append feedback'); END;
CREATE TRIGGER feedback_no_delete BEFORE DELETE ON feedback
BEGIN SELECT RAISE(ABORT, 'feedback history is immutable'); END;
CREATE TRIGGER events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'append events'); END;
CREATE TRIGGER events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'event history is immutable'); END;
