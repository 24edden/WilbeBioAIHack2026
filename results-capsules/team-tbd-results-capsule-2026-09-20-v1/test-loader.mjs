import assert from "node:assert/strict";
import { createHash, webcrypto } from "node:crypto";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { CapsuleError, SCHEMA_VERSION, PACKAGE_ID, loadCapsule, createCapsuleLoader,
  validateRelativePath, validateManifest } from "./loader.mjs";

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const encode = (value) => new TextEncoder().encode(JSON.stringify(value));
const base = "http://localhost:8090/capsule/";

function fixture() {
  const view = { run_id: "run-1", source_id: "frozen-source", label: "A preserved study", status: "completed",
    mode: "live", case_id: "case-1", scope: "Research context", question: { text: "The supplied question" },
    findings: [], decisions: [], handoffs: [], checks: [], governance: {}, skills: [], model_receipts: [],
    nvidia: { status: "proposed" }, sequence_discoveries: [], research_briefs: [], artifacts: [], usage: {}, error: null,
    links: { source_reference: "private-host:/data/historical-source" } };
  const files = new Map([
    ["results.json", encode({ schema_version: SCHEMA_VERSION, package_id: PACKAGE_ID, featured_run_ids: [view.run_id], runs: [view] })],
    ["artifact-index.json", encode({ artifacts: [] })],
    ["runs/run-1/view.json", encode(view)],
    ["runs/run-1/export.json", encode({ run: { id: "run-1", preserved: true } })],
    ["artifacts/plot.svg", new TextEncoder().encode("<svg>read only</svg>")],
  ]);
  const manifest = { schema_version: SCHEMA_VERSION, package_id: PACKAGE_ID, created_at: "2026-09-20T12:00:00Z",
    freeze: { kind: "snapshot", no_new_inference: true, source_runs_unchanged: true },
    entrypoints: { results: "results.json", artifact_index: "artifact-index.json" },
    sources: [{ source_id: "frozen-source", source_reference: "private-host:/source" }], featured_run_ids: [view.run_id],
    runs: [{ run_id: view.run_id, source_id: view.source_id, label: view.label, status: view.status, mode: view.mode,
      case_id: view.case_id, updated_at: null, raw_export_path: "runs/run-1/export.json", view_path: "runs/run-1/view.json",
      report_path: null, event_path: null, source_content_sha256: sha("source content") }], counts: { runs: 1, artifacts: 1 },
    files: Array.from(files, ([path, bytes]) => ({ path, bytes: bytes.length, sha256: sha(bytes),
      media_type: path.endsWith(".json") ? "application/json" : "image/svg+xml" })), locations: {}, limitations: [] };
  const requests = [];
  let replacement = null;
  const fetchImpl = async (url, options) => {
    requests.push({ url, options });
    assert.ok(url.startsWith(base), "No external source lookup");
    const path = decodeURIComponent(url.slice(base.length));
    const bytes = path === "manifest.json" ? encode(manifest) : files.get(path);
    if (replacement) return replacement(path, bytes);
    return new Response(bytes, { status: bytes ? 200 : 404 });
  };
  const options = { fetchImpl, cryptoImpl: webcrypto };
  return { view, files, manifest, requests, options, replaceFetch: (callback) => { replacement = callback; } };
}

test("loads verified catalog, view and original export using only credential-free GET", async () => {
  const f = fixture();
  const capsule = await loadCapsule(base, { ...f.options, expectedManifestSha256: sha(encode(f.manifest)) });
  assert.equal(capsule.results.runs[0].question.text, "The supplied question");
  assert.equal((await capsule.loadRun("run-1")).nvidia.status, "proposed");
  assert.deepEqual(await capsule.readJson("runs/run-1/export.json"), { run: { id: "run-1", preserved: true } });
  assert.deepEqual(capsule.artifactIndex, { artifacts: [] });
  assert.ok(Object.isFrozen(capsule.manifest.runs[0]));
  assert.ok(f.requests.every(({ options }) => options.method === "GET" && options.credentials === "omit" && options.redirect === "error"));
  assert.ok(f.requests.every(({ url }) => !url.includes("private-host")));
});

test("relative paths reject traversal, encoded traversal, URL forms and browser delimiters", () => {
  for (const path of ["../secret", "runs/../secret", "./results.json", "/results.json", "//evil.test/file", "runs//file",
    "runs/", "runs\\secret", "https://evil.test/file", "file:secret", "%2e%2e/secret", "runs/%252e%252e/x",
    "results.json?download=1", "results.json#fragment", "runs/\u0000file", "runs/\nfile", ""]) {
    assert.throws(() => validateRelativePath(path), CapsuleError, path);
  }
  assert.equal(validateRelativePath("runs/run-1/exact result.json"), "runs/run-1/exact result.json");
});

test("unindexed file and source reference are rejected before fetching", async () => {
  const f = fixture();
  const loader = await createCapsuleLoader(base, f.options);
  const initial = f.requests.length;
  await assert.rejects(loader.readBytes("runs/run-1/missing.json"), /not indexed/);
  await assert.rejects(loader.readBytes(f.view.links.source_reference), /Unsafe/);
  assert.equal(f.requests.length, initial);
});

test("changed file of the same length fails SHA-256 before JSON parsing", async () => {
  const f = fixture();
  const original = f.files.get("results.json");
  const changed = new Uint8Array(original);
  changed[0] = 91;
  f.files.set("results.json", changed);
  await assert.rejects(loadCapsule(base, f.options), /SHA-256 mismatch/);
});

test("short and oversized file bodies fail exact-byte checks", async () => {
  for (const delta of [-1, 1]) {
    const f = fixture();
    f.files.set("results.json", new Uint8Array(f.files.get("results.json").length + delta));
    await assert.rejects(loadCapsule(base, f.options), delta < 0 ? /Byte count mismatch/ : /allowed size/);
  }
});

test("trusted manifest hash detects changed manifest", async () => {
  const f = fixture();
  const original = sha(encode(f.manifest));
  f.manifest.limitations.push("Changed after the separately recorded freeze.");
  await assert.rejects(createCapsuleLoader(base, { ...f.options, expectedManifestSha256: original }), /Manifest SHA-256 differs/);
});

test("a file over the configured limit is rejected without its download", async () => {
  const f = fixture();
  const loader = await createCapsuleLoader(base, { ...f.options, maxFileBytes: 10 });
  await assert.rejects(loader.readJson("results.json"), /configured consumer size limit/);
  assert.equal(f.requests.length, 1);
});

test("redirected or relocated responses are rejected", async () => {
  const f = fixture();
  f.replaceFetch((path, bytes) => {
    const response = new Response(bytes);
    Object.defineProperty(response, "url", { value: "https://elsewhere.test/manifest.json" });
    return response;
  });
  await assert.rejects(createCapsuleLoader(base, f.options), /changed its requested location/);
});

test("strict manifest rejects non-snapshot claims, unindexed paths and duplicate identities", () => {
  const changes = [
    (m) => { m.freeze.no_new_inference = false; },
    (m) => { m.extra = true; },
    (m) => { m.package_id = "another-package"; },
    (m) => { m.files.push(m.files[0]); },
    (m) => { m.files[0].path = "../escape"; },
    (m) => { m.runs.push(m.runs[0]); },
    (m) => { m.runs[0].report_path = "not-copied.md"; },
    (m) => { m.featured_run_ids = ["missing-run"]; },
    (m) => { m.counts.runs = -1; },
  ];
  for (const change of changes) {
    const f = fixture();
    change(f.manifest);
    assert.throws(() => validateManifest(f.manifest), CapsuleError);
  }
});

test("verified bytes do not excuse an inconsistent results identity", async () => {
  const f = fixture();
  const value = JSON.parse(new TextDecoder().decode(f.files.get("results.json")));
  value.runs[0].source_id = "another-source";
  const bytes = encode(value);
  f.files.set("results.json", bytes);
  Object.assign(f.manifest.files.find((file) => file.path === "results.json"), { bytes: bytes.length, sha256: sha(bytes) });
  await assert.rejects(loadCapsule(base, f.options), /differs from its manifest identity/);
});

test("JSON schema keeps identity and strict manifest fields aligned with the loader", async () => {
  const schema = JSON.parse(await readFile(new URL("./manifest.schema.json", import.meta.url), "utf8"));
  assert.equal(schema.$defs.schemaVersion.const, SCHEMA_VERSION);
  assert.equal(schema.$defs.packageId.const, PACKAGE_ID);
  assert.equal(schema.$defs.manifest.additionalProperties, false);
  assert.equal(schema.$defs.runView.additionalProperties, true);
  const f = fixture();
  assert.deepEqual(Object.keys(f.manifest).sort(), [...schema.$defs.manifest.required].sort());
  const pattern = new RegExp(schema.$defs.relativePath.pattern);
  for (const path of ["results.json", "runs/run-1/export.json", "artifacts/exact result.png"]) assert.ok(pattern.test(path), path);
  for (const path of ["../secret", "/root", "a/../b", "a\\b", "a%20b", "x:y", "a//b", "a/", "a?b", "a#b", "a\nfile"]) assert.ok(!pattern.test(path), path);
});
