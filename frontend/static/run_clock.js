// Ticking is browser-owned. No Streamlit callback, inference or progress estimate.
const sessions = new Map();
let mounted = null;
const validMs = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;

export function formatDuration(milliseconds) {
  const seconds = Math.floor(Math.max(0, milliseconds) / 1000);
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
    .map(value => String(value).padStart(2, '0')).join(':');
}

export class SubmissionClock {
  constructor(data, now = () => performance.now()) {
    this.now = now;
    this.anchor = now();
    this.initialMs = validMs(data.elapsedMs) ? data.elapsedMs : 0;
    this.terminal = false;
    this.measuredMs = null;
    this.update(data);
  }
  update(data) {
    if (data.active === false) {
      if (!this.terminal) {
        this.frozenMs = validMs(data.elapsedMs) ? data.elapsedMs : this.elapsed();
        this.terminal = true;
      }
      if (validMs(data.measuredMs)) this.measuredMs = data.measuredMs;
    }
    // Same-run updates never re-anchor or revive a completed clock.
  }
  elapsed() {
    return this.terminal ? this.frozenMs : this.initialMs + Math.max(0, this.now() - this.anchor);
  }
}

export default function render({parentElement, data}) {
  if (!data || typeof data.runKey !== 'string' || !data.runKey) return () => {};
  // A remount/new run replaces the previous display owner, with one timer total.
  if (mounted) mounted.dispose();
  for (const key of sessions.keys()) if (key !== data.runKey) sessions.delete(key);
  let clock = sessions.get(data.runKey);
  if (!clock) {
    clock = new SubmissionClock(data);
    sessions.set(data.runKey, clock);
  } else clock.update(data);
  const surface = parentElement.querySelector('.run-clock');
  const value = parentElement.querySelector('#clock-value');
  const measured = parentElement.querySelector('#clock-measured');
  let timer = null;
  let disposed = false;
  const syncTheme = () => {
    surface.dataset.theme = document.documentElement.dataset.traceTheme === 'astral' ? 'astral' : 'dark';
  };
  const paint = () => {
    value.textContent = formatDuration(clock.elapsed());
    surface.dataset.active = String(!clock.terminal);
    measured.textContent = clock.terminal
      ? (clock.measuredMs === null ? 'Measured execution time: unavailable'
         : `Measured execution time: ${(clock.measuredMs / 1000).toFixed(1)}s`)
      : '';
  };
  const stopTicking = () => { if (timer !== null) { clearInterval(timer); timer = null; } };
  const visibility = () => {
    stopTicking();
    if (document.visibilityState !== 'hidden') {
      paint();
      if (!clock.terminal) timer = setInterval(paint, 1000);
    }
  };
  const owner = {
    dispose() {
      if (disposed) return;
      disposed = true;
      stopTicking();
      document.removeEventListener('visibilitychange', visibility);
      window.removeEventListener('trace-theme-change', syncTheme);
      if (mounted === owner) mounted = null;
    },
  };
  mounted = owner;
  syncTheme();
  paint();
  visibility();
  document.addEventListener('visibilitychange', visibility);
  window.addEventListener('trace-theme-change', syncTheme);
  return owner.dispose;
}
