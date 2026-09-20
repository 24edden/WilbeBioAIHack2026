import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source = await readFile(new URL('../frontend/static/run_clock.js', import.meta.url), 'utf8');
const {default: render, SubmissionClock, formatDuration} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
let now = 0, nextTimer = 0;
const timers = new Map(), windowHandlers = new Map(), documentHandlers = new Map();
Object.defineProperty(globalThis, 'performance', {value: {now: () => now}, configurable: true});
globalThis.setInterval = fn => {const id = ++nextTimer; timers.set(id, fn); return id;};
globalThis.clearInterval = id => timers.delete(id);
globalThis.document = {documentElement: {dataset: {traceTheme: 'dark'}}, visibilityState: 'visible',
  addEventListener: (key, fn) => documentHandlers.set(key, fn),
  removeEventListener: (key, fn) => {if (documentHandlers.get(key) === fn) documentHandlers.delete(key);}};
globalThis.window = {addEventListener: (key, fn) => windowHandlers.set(key, fn),
  removeEventListener: (key, fn) => {if (windowHandlers.get(key) === fn) windowHandlers.delete(key);}};
const elements = new Map(['.run-clock', '#clock-value', '#clock-measured'].map(key => [key, {dataset: {}, textContent: ''}]));
const parentElement = {querySelector: selector => elements.get(selector)};
const mount = data => render({parentElement, data,
  setStateValue: () => assert.fail('Clock ticks cannot call Python'),
  setTriggerValue: () => assert.fail('Clock ticks cannot dispatch actions')});
const advance = milliseconds => {now += milliseconds; for (const tick of [...timers.values()]) tick();};
const text = () => elements.get('#clock-value').textContent;

const firstCleanup = mount({runKey: 'local-run-1', active: true, elapsedMs: 2500});
assert.equal(text(), '00:00:02');
assert.equal(timers.size, 1);
// Ten seconds with no events, descriptors or calls back to the application.
advance(10000);
assert.equal(text(), '00:00:12');
const secondCleanup = mount({runKey: 'local-run-1', active: true, elapsedMs: 0});
firstCleanup(); // Late cleanup of the replaced owner must not stop the new one.
assert.equal(timers.size, 1);
assert.equal(text(), '00:00:12');
assert.equal(documentHandlers.size, 1);
assert.equal(windowHandlers.size, 1);

// Hidden-tab throttling cannot lose time; derive from the anchor on resume.
document.visibilityState = 'hidden'; documentHandlers.get('visibilitychange')();
assert.equal(timers.size, 0);
advance(60000);
document.visibilityState = 'visible'; documentHandlers.get('visibilitychange')();
assert.equal(text(), '00:01:12');
assert.equal(timers.size, 1);
document.documentElement.dataset.traceTheme = 'astral'; windowHandlers.get('trace-theme-change')();
assert.equal(elements.get('.run-clock').dataset.theme, 'astral');
assert.equal(text(), '00:01:12');

secondCleanup();
assert.equal(timers.size, 0);
assert.equal(documentHandlers.size, 0);
assert.equal(windowHandlers.size, 0);
advance(2000);
mount({runKey: 'local-run-1', active: true, elapsedMs: 1});
assert.equal(text(), '00:01:14'); // Unmount removed work, not the same-run anchor.
mount({runKey: 'local-run-1', active: false, elapsedMs: 75000, measuredMs: 61002});
assert.equal(text(), '00:01:15');
assert.equal(timers.size, 0);
assert.equal(elements.get('#clock-measured').textContent, 'Measured execution time: 61.0s');
advance(10000);
mount({runKey: 'local-run-1', active: true, elapsedMs: 0});
assert.equal(text(), '00:01:15'); // Stale active payload cannot revive a terminal run.
assert.equal(timers.size, 0);

const lastCleanup = mount({runKey: 'local-run-2', active: true, elapsedMs: 0});
assert.equal(text(), '00:00:00');
assert.equal(timers.size, 1);
advance(10000);
assert.equal(text(), '00:00:10');
mount({runKey: 'local-run-2', active: false, elapsedMs: 10000, measuredMs: -1});
assert.equal(elements.get('#clock-measured').textContent, 'Measured execution time: unavailable');
lastCleanup();
assert.equal(timers.size, 0);
const cleanup = mount({runKey: 'local-run-3', active: true, elapsedMs: 0});
cleanup(); cleanup();
assert.equal(timers.size, 0);
assert.equal(documentHandlers.size, 0);
assert.equal(windowHandlers.size, 0);
for (const value of [null, true, NaN, Infinity, -1]) {
  const clock = new SubmissionClock({active: false, elapsedMs: 1000, measuredMs: value}, () => 0);
  assert.equal(clock.measuredMs, null);
}
assert.equal(formatDuration(100 * 3600000), '100:00:00');
console.log(JSON.stringify({passed: true}));
