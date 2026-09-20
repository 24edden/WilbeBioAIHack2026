// Synthetic contract tests only. Run with Node 20+; no service, network or run data needed.
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { loadArchive, loadRun, readVerified, relativeURL, resolvePointer } from './reader.mjs';
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const base = 'https://archive.example/frozen/';
const data = new Map();
const enc = new TextEncoder();
async function put(path, value) {
  const bytes = enc.encode(JSON.stringify(value));
  data.set(base + path, bytes);
  const sha256 = Buffer.from(await crypto.subtle.digest('SHA-256', bytes)).toString('hex');
  return { path, sha256, bytes: bytes.byteLength, media_type: 'application/json' };
}
const raw = {
  run: {
    id: 'synthetic-failed-run', status: 'failed',
    hypothesis: { text: 'Exact question.\n', source_name: 'synthetic', sha256: '0'.repeat(64) },
    decisions: [], events: [{ 'a/b': { '~key': 'kept' } }],
  },
};
const rawRef = await put('runs/example/raw-export.json', raw);
const view = {
  schema_version: 'team-tbd-run-view/1.0.0', run_id: raw.run.id, environment_id: 'synthetic',
  raw_export: rawRef, state: { status: 'failed' }, hypothesis: raw.run.hypothesis,
};
const viewRef = await put('runs/example/view.json', view);
const entry = { run_id: raw.run.id, environment_id: 'synthetic', status: 'failed', view: viewRef, raw_export: rawRef };
const manifest = { schema_version: 'team-tbd-archive/1.0.0', runs: [entry] };
await put('manifest.json', manifest);
globalThis.fetch = async url => {
  const bytes = data.get(String(url));
  return new Response(bytes ?? 'Missing', { status: bytes ? 200 : 404 });
};
const archive = await loadArchive(base + 'manifest.json');
const loaded = await loadRun(archive, entry);
assert.equal(loaded.view.state.status, 'failed');
assert.equal(loaded.view.hypothesis.text, 'Exact question.\n');
assert.equal(resolvePointer(raw, '/run/events/0/a~1b/~0key'), 'kept');
assert.throws(() => resolvePointer(raw, '/missing'), /Unresolved/);
assert.throws(() => resolvePointer(raw, '/run/~bad'), /Invalid/);
for (const path of ['../private', '/absolute', 'https://other.example/a', '%2e%2e/private', 'a/../b', 'a\\b', 'a?secret', 'a#fragment']) {
  assert.throws(() => relativeURL(archive.baseURL, path));
}
assert.equal(String(relativeURL(archive.baseURL, 'runs/example/view.json')), base + 'runs/example/view.json');
const correct = data.get(base + rawRef.path);
data.set(base + rawRef.path, Uint8Array.from(correct, (v, i) => i === 0 ? v ^ 1 : v));
await assert.rejects(() => readVerified(archive.baseURL, rawRef), /Checksum mismatch/);
data.set(base + rawRef.path, correct);
const modifiedViewRef = await put('runs/example/bad-view.json', { ...view, hypothesis: { ...view.hypothesis, text: 'Rewritten' } });
await assert.rejects(() => loadRun(archive, { ...entry, view: modifiedViewRef }), /Hypothesis text was modified/);
await assert.rejects(() => loadRun(archive, { ...entry, status: 'completed' }), /Run state mismatch/);
console.log('PASS: exact text, failed state, pointers, relative paths, tamper checks and identity checks.');
