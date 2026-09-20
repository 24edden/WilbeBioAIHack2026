/** Read-only, dependency-free consumer for a frozen Team TBD results capsule. */
export const SCHEMA_VERSION = "team-tbd-results-capsule/1.0";
export const PACKAGE_ID = "team-tbd-results-capsule-2026-09-20-v1";

export class CapsuleError extends Error {
  constructor(message) { super(message); this.name = "CapsuleError"; }
}

const MANIFEST_KEYS = ["schema_version", "package_id", "created_at", "freeze", "entrypoints", "sources",
  "featured_run_ids", "runs", "counts", "files", "locations", "limitations"];
const RUN_KEYS = ["run_id", "source_id", "label", "status", "mode", "case_id", "updated_at",
  "raw_export_path", "view_path", "report_path", "event_path", "source_content_sha256"];
const VIEW_KEYS = ["run_id", "source_id", "label", "status", "mode", "case_id", "scope", "question",
  "findings", "decisions", "handoffs", "checks", "governance", "skills", "model_receipts", "nvidia",
  "sequence_discoveries", "research_briefs", "artifacts", "usage", "error", "links"];
const HEX256 = /^[a-f0-9]{64}$/;
const fail = (message) => { throw new CapsuleError(message); };
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);

function keys(value, required, where, strict = true) {
  if (!object(value) || required.some((key) => !Object.hasOwn(value, key)) ||
      (strict && Object.keys(value).some((key) => !required.includes(key)))) fail(`Invalid ${where} fields.`);
}

function string(value, where) {
  if (typeof value !== "string" || !value.trim()) fail(`Invalid ${where}.`);
}

/** Paths are literal capsule-relative names, never URLs or encoded locators. */
export function validateRelativePath(path) {
  if (typeof path !== "string" || !path || path.length > 4096 || path.startsWith("/") ||
      /[\\%?#:\u0000-\u001f\u007f]/.test(path) || path.split("/").some((part) => !part || part === "." || part === "..")) {
    fail("Unsafe capsule-relative path.");
  }
  return path;
}

function identity(value) {
  if (value.schema_version !== SCHEMA_VERSION || value.package_id !== PACKAGE_ID) fail("Unsupported capsule identity.");
}

export function validateManifest(value) {
  keys(value, MANIFEST_KEYS, "manifest");
  identity(value);
  string(value.created_at, "manifest creation time");
  keys(value.freeze, ["kind", "no_new_inference", "source_runs_unchanged"], "freeze");
  if (value.freeze.kind !== "snapshot" || value.freeze.no_new_inference !== true || value.freeze.source_runs_unchanged !== true) {
    fail("Capsule must describe an unchanged-source snapshot without new inference.");
  }
  keys(value.entrypoints, ["results", "artifact_index"], "entrypoints");
  if (value.entrypoints.results !== "results.json" || value.entrypoints.artifact_index !== "artifact-index.json") fail("Unexpected capsule entrypoints.");
  if (!Array.isArray(value.files)) fail("Invalid manifest files.");
  const files = new Map();
  for (const file of value.files) {
    keys(file, ["path", "sha256", "bytes", "media_type"], "file");
    validateRelativePath(file.path);
    if (file.path === "manifest.json" || files.has(file.path)) fail("Duplicate or self-referential manifest file.");
    if (!HEX256.test(file.sha256) || !Number.isSafeInteger(file.bytes) || file.bytes < 0) fail("Invalid file integrity metadata.");
    string(file.media_type, "file media type");
    files.set(file.path, file);
  }
  for (const path of Object.values(value.entrypoints)) if (!files.has(path)) fail("Entrypoint is not indexed by the manifest.");
  if (!Array.isArray(value.sources) || value.sources.some((source) => !object(source))) fail("Invalid capsule sources.");
  if (!Array.isArray(value.runs)) fail("Invalid capsule runs.");
  const runIds = new Set();
  for (const run of value.runs) {
    keys(run, RUN_KEYS, "run");
    for (const key of ["run_id", "source_id", "label", "status", "mode", "case_id"]) string(run[key], `run ${key}`);
    if (run.updated_at !== null) string(run.updated_at, "run update time");
    if (runIds.has(run.run_id)) fail("Duplicate capsule run identity.");
    runIds.add(run.run_id);
    if (!HEX256.test(run.source_content_sha256)) fail("Invalid source content hash.");
    for (const key of ["raw_export_path", "view_path", "report_path", "event_path"]) {
      if (run[key] === null && ["report_path", "event_path"].includes(key)) continue;
      validateRelativePath(run[key]);
      if (!files.has(run[key])) fail("Run path is not indexed by the manifest.");
    }
  }
  if (!Array.isArray(value.featured_run_ids) || new Set(value.featured_run_ids).size !== value.featured_run_ids.length ||
      value.featured_run_ids.some((id) => !runIds.has(id))) fail("Invalid featured run identities.");
  if (!object(value.counts) || Object.values(value.counts).some((count) => !Number.isSafeInteger(count) || count < 0)) fail("Invalid capsule counts.");
  if (!object(value.locations) || !Array.isArray(value.limitations) || value.limitations.some((item) => typeof item !== "string")) fail("Invalid capsule locations or limitations.");
  return value;
}

function freeze(value) {
  if (value !== null && typeof value === "object") {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}

function parseJson(bytes, path) {
  try { return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
  catch { fail(`Invalid UTF-8 JSON in ${path}.`); }
}

async function hash(bytes, cryptoImpl) {
  if (!cryptoImpl?.subtle) fail("SHA-256 verification needs Web Crypto (HTTPS or localhost).");
  const digest = await cryptoImpl.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function readResponse(response, maximum) {
  const reportedLength = response.headers?.get("content-length");
  if (reportedLength && Number(reportedLength) > maximum) fail("Capsule file exceeds its allowed size.");
  if (!response.body?.getReader) {
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.length > maximum) fail("Capsule file exceeds its allowed size.");
    return bytes;
  }
  const reader = response.body.getReader();
  const chunks = [];
  let length = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.length;
      if (length > maximum) {
        await reader.cancel();
        fail("Capsule file exceeds its allowed size.");
      }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return bytes;
}

function validateView(view, record) {
  keys(view, VIEW_KEYS, "run view", false);
  for (const key of ["run_id", "source_id", "label", "status", "mode", "case_id"]) {
    if (view[key] !== record[key]) fail("Run view differs from its manifest identity.");
  }
  return view;
}

/** Manifest is the trust anchor; pin its hash out of band for tamper detection. */
export async function createCapsuleLoader(baseURL, {
  fetchImpl = globalThis.fetch,
  cryptoImpl = globalThis.crypto,
  expectedManifestSha256 = null,
  maxManifestBytes = 5 * 1024 * 1024,
  maxFileBytes = 128 * 1024 * 1024,
} = {}) {
  if (typeof fetchImpl !== "function") fail("A Fetch implementation is required.");
  for (const limit of [maxManifestBytes, maxFileBytes]) if (!Number.isSafeInteger(limit) || limit < 1) fail("Invalid capsule size limit.");
  if (expectedManifestSha256 !== null && !HEX256.test(expectedManifestSha256)) fail("Invalid trusted manifest hash.");
  let base;
  try { base = new URL(baseURL, globalThis.location?.href); } catch { fail("Invalid capsule base URL."); }
  if (!["http:", "https:"].includes(base.protocol) || base.username || base.password || base.search || base.hash) fail("Capsule base must be an HTTP(S) directory without credentials or query.");
  if (!base.pathname.endsWith("/")) base.pathname += "/";

  async function fetchBytes(path, maximum) {
    validateRelativePath(path);
    const url = new URL(path.split("/").map(encodeURIComponent).join("/"), base);
    if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) fail("Path escaped the capsule directory.");
    const response = await fetchImpl(url.href, { method: "GET", credentials: "omit", redirect: "error", cache: "no-store" });
    if (!response.ok) fail(`Capsule fetch failed for ${path} (HTTP ${response.status}).`);
    if (response.redirected || (response.url && new URL(response.url).href !== url.href)) fail("Capsule fetch changed its requested location.");
    return readResponse(response, maximum);
  }

  const manifestBytes = await fetchBytes("manifest.json", maxManifestBytes);
  if (expectedManifestSha256 !== null && await hash(manifestBytes, cryptoImpl) !== expectedManifestSha256) fail("Manifest SHA-256 differs from its trusted hash.");
  const manifest = freeze(validateManifest(parseJson(manifestBytes, "manifest.json")));
  const files = new Map(manifest.files.map((file) => [file.path, file]));
  const runs = new Map(manifest.runs.map((run) => [run.run_id, run]));

  async function readBytes(path) {
    validateRelativePath(path);
    const file = files.get(path);
    if (!file) fail("Requested file is not indexed by the manifest.");
    if (file.bytes > maxFileBytes) fail("Indexed file exceeds the configured consumer size limit.");
    const bytes = await fetchBytes(path, file.bytes);
    if (bytes.length !== file.bytes) fail(`Byte count mismatch for ${path}.`);
    if (await hash(bytes, cryptoImpl) !== file.sha256) fail(`SHA-256 mismatch for ${path}.`);
    return bytes;
  }

  async function readJson(path) { return parseJson(await readBytes(path), path); }

  async function loadResults() {
    const results = await readJson(manifest.entrypoints.results);
    keys(results, ["schema_version", "package_id", "featured_run_ids", "runs"], "results", false);
    identity(results);
    if (!Array.isArray(results.runs) || results.runs.length !== runs.size ||
        JSON.stringify(results.featured_run_ids) !== JSON.stringify(manifest.featured_run_ids)) fail("Results catalog differs from its manifest.");
    const seen = new Set();
    for (const view of results.runs) {
      const record = runs.get(view?.run_id);
      if (!record || seen.has(view.run_id)) fail("Unrecognized or duplicate results run.");
      seen.add(view.run_id);
      validateView(view, record);
    }
    return results;
  }

  async function loadRun(runId) {
    const record = runs.get(runId);
    if (!record) fail("Unknown capsule run.");
    return validateView(await readJson(record.view_path), record);
  }

  async function loadArtifactIndex() {
    const index = await readJson(manifest.entrypoints.artifact_index);
    if (!object(index)) fail("Invalid artifact index.");
    return index;
  }

  return Object.freeze({ manifest, readBytes, readJson, loadResults, loadRun, loadArtifactIndex });
}

/** Convenience entrypoint for applications that render the complete catalog. */
export async function loadCapsule(baseURL, options) {
  const loader = await createCapsuleLoader(baseURL, options);
  const [results, artifactIndex] = await Promise.all([loader.loadResults(), loader.loadArtifactIndex()]);
  return Object.freeze({ ...loader, results, artifactIndex });
}
