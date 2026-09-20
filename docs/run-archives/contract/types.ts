/** Team TBD immutable archive contract 1.0.0. All paths are manifest-root-relative. */
export type JsonValue = null | boolean | number | string | JsonValue[] | JsonObject;
export type JsonObject = { [key: string]: JsonValue };
export type Captured<T> = T | null;
export interface FileRef {
  path: string;
  /** SHA-256 of exact file bytes, lowercase hex; not the application's content_sha256. */
  sha256: string;
  bytes: number;
  media_type: string | null;
}
export interface SourceRecord {
  id: string | null;
  /** RFC 6901 pointer into raw_export, or null for an external source identified in data. */
  raw_pointer: string | null;
  data: JsonObject;
  decision_version?: number | null;
  scope?: string | null;
}
export interface Asset {
  id: string;
  kind: string;
  title: string | null;
  status: 'included' | 'missing' | 'excluded' | 'unavailable' | 'external_reference';
  /** Non-null if and only if status is included. */
  file: FileRef | null;
  source_url: string | null;
  source_path: string | null;
  expected_sha256: string | null;
  run_ids: string[];
  raw_pointers: string[];
  notes: string[];
}
export interface DatasetSource {
  id: string | null;
  name: string | null;
  path: string | null;
  relative_path?: string | null;
  sha256: string | null;
  bytes: number | null;
  url: string | null;
  provenance: string | null;
  asset_id: string | null;
  raw_pointer: string | null;
  data: JsonObject;
}
export interface Claim {
  id: string | null;
  text: string | null;
  kind: string | null;
  evidence_ids: string[] | null;
  sources: JsonObject[] | null;
  decision_version: number | null;
  scope: string | null;
  raw_pointer: string | null;
  data: JsonObject;
}
export interface Environment {
  id: string;
  label: string;
  kind: 'local' | 'brev' | 'github' | 'other';
  source_path: string | null;
  source_url: string | null;
  github_url: string | null;
  git_commit: string | null;
  notes: string[];
}
export interface RunEntry {
  run_id: string;
  environment_id: string;
  status: string | null;
  view: FileRef;
  raw_export: FileRef;
  report: FileRef | null;
}
export interface ArchiveManifest {
  schema_version: 'team-tbd-archive/1.0.0';
  bundle_id: string;
  frozen_at: string;
  title: string;
  runs: RunEntry[];
  environments: Environment[];
  assets: Asset[];
  omissions: { scope: string; reason: string }[];
  provenance: JsonObject;
  /** Curated IDs, never lexical or implicit latest ordering. */
  recommended_run_ids?: string[];
  selection?: JsonObject;
}
export interface RunView {
  schema_version: 'team-tbd-run-view/1.0.0';
  run_id: string;
  as_of: string;
  raw_export: FileRef;
  environment_id: string;
  case: {
    id: string | null;
    title: string | null;
    data_mode: string | null;
    dataset_scope: string[] | null;
    limitations: string[] | null;
  };
  hypothesis: { text: string | null; source_name: string | null; sha256: string | null };
  state: { status: string | null; stage: string | null; error: JsonValue; review_status: string | null };
  datasets: DatasetSource[] | null;
  findings: SourceRecord[] | null;
  evidence: SourceRecord[] | null;
  decisions: SourceRecord[] | null;
  handoffs: SourceRecord[] | null;
  claims: Claim[] | null;
  timeline: SourceRecord[] | null;
  quality_checks: SourceRecord[] | null;
  /** Plans, recommendations, draft requests and their recorded states. Never proof of execution. */
  followups: SourceRecord[] | null;
  /** Observed actions and operations, retaining succeeded/failed/pending/unknown states. */
  executions: SourceRecord[] | null;
  artifacts: Asset[] | null;
  /** Applied instruction receipts. A skill receipt does not establish model identity or service use. */
  skills: SourceRecord[] | null;
  models: {
    configuration: JsonObject | null;
    receipts: SourceRecord[] | null;
    usage: JsonObject | null;
  };
  briefs: SourceRecord[] | null;
  source_locations: JsonObject | null;
}
