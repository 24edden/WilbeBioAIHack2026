/** Dependency-free browser importer. Serve the bundle over HTTP(S), including localhost.
 * Does integrity and identity checks; use the supplied schemas for full shape validation.
 * Source data is untrusted: render text with textContent and sandbox/sanitize SVG/HTML assets.
 */
const ARCHIVE = 'team-tbd-archive/1.0.0';
const RUN = 'team-tbd-run-view/1.0.0';
function assert(ok, message) { if (!ok) throw new Error(message); }
export function relativeURL(baseURL, path) {
  assert(typeof path === 'string' && path.length > 0, 'Missing bundle-relative path');
  assert(!path.startsWith('/') && !/[\\?#]/.test(path) && !/^[a-z][a-z\d+.-]*:/i.test(path), 'Absolute or ambiguous path rejected');
  let decoded;
  try { decoded = decodeURIComponent(path); } catch { throw new Error('Invalid path encoding'); }
  assert(!decoded.split('/').some(x => x === '..' || x === '.'), 'Path traversal rejected');
  assert(!decoded.startsWith('/') && !/[\\?#]/.test(decoded), 'Encoded ambiguous path rejected');
  const base = new URL(baseURL);
  const resolved = new URL(path, base);
  assert(resolved.origin === base.origin && resolved.pathname.startsWith(base.pathname), 'Path escapes archive');
  return resolved;
}
async function fetchBytes(url) {
  const response = await fetch(url, { credentials: 'same-origin', redirect: 'error' });
  assert(response.ok, `Read failed (${response.status}): ${url}`);
  return new Uint8Array(await response.arrayBuffer());
}
async function sha256(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map(x => x.toString(16).padStart(2, '0')).join('');
}
export async function readVerified(baseURL, ref) {
  assert(ref && /^[a-f0-9]{64}$/.test(ref.sha256), 'Missing file SHA-256');
  assert(Number.isSafeInteger(ref.bytes) && ref.bytes >= 0, 'Invalid file size');
  const bytes = await fetchBytes(relativeURL(baseURL, ref.path));
  assert(bytes.byteLength === ref.bytes, `Size mismatch: ${ref.path}`);
  assert(await sha256(bytes) === ref.sha256, `Checksum mismatch: ${ref.path}`);
  return bytes;
}
async function readJSON(baseURL, ref) {
  return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(await readVerified(baseURL, ref)));
}
export async function loadArchive(manifestURL) {
  const url = new URL(manifestURL, globalThis.location?.href);
  const manifest = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(await fetchBytes(url)));
  assert(manifest.schema_version === ARCHIVE, 'Unsupported archive schema');
  assert(Array.isArray(manifest.runs), 'Archive run index missing');
  return { manifest, baseURL: new URL('./', url) };
}
export async function loadRun(archive, entry) {
  const [view, raw] = await Promise.all([
    readJSON(archive.baseURL, entry.view),
    readJSON(archive.baseURL, entry.raw_export),
  ]);
  assert(view.schema_version === RUN, 'Unsupported run schema');
  assert(view.run_id === entry.run_id && raw.run?.id === entry.run_id, 'Run identity mismatch');
  assert(view.environment_id === entry.environment_id, 'Environment identity mismatch');
  assert(view.raw_export?.sha256 === entry.raw_export.sha256 && view.raw_export?.path === entry.raw_export.path, 'Raw export reference mismatch');
  assert(view.state?.status === raw.run.status && entry.status === raw.run.status, 'Run state mismatch');
  assert(view.hypothesis?.text === (raw.run.hypothesis?.text ?? null), 'Hypothesis text was modified');
  assert(view.hypothesis?.source_name === (raw.run.hypothesis?.source_name ?? null), 'Hypothesis source was modified');
  assert(view.hypothesis?.sha256 === (raw.run.hypothesis?.sha256 ?? null), 'Hypothesis hash was modified');
  return { view, raw };
}
export function resolvePointer(raw, pointer) {
  assert(typeof pointer === 'string' && (pointer === '' || pointer.startsWith('/')), 'Invalid JSON pointer');
  if (pointer === '') return raw;
  return pointer.slice(1).split('/').reduce((value, escaped) => {
    assert(!/~(?:[^01]|$)/.test(escaped), 'Invalid JSON pointer escape');
    const key = escaped.replace(/~1/g, '/').replace(/~0/g, '~');
    assert(value !== null && typeof value === 'object' && Object.hasOwn(value, key), `Unresolved JSON pointer: ${pointer}`);
    return value[key];
  }, raw);
}

// Minimal integration:
// const archive = await loadArchive('/frozen-runs/manifest.json');
// const { view, raw } = await loadRun(archive, archive.manifest.runs[0]);
// document.querySelector('#hypothesis').textContent = view.hypothesis.text ?? 'Not captured';
// for (const decision of view.decisions ?? []) {
//   const sourceDecision = resolvePointer(raw, decision.raw_pointer);
//   console.log(sourceDecision.version, sourceDecision.assessment, sourceDecision.limitations);
// }
// Fetch included assets only, and retain status for every missing/failed/excluded item:
// const asset = view.artifacts?.find(a => a.status === 'included');
// if (asset) { const bytes = await readVerified(archive.baseURL, asset.file); /* render safely */ }
