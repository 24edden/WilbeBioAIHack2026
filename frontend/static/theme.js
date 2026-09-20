// A visual preference never calls setStateValue/setTriggerValue or reruns Python.
export function installHelpDismissal(surface, component) {
  const selector = '.trace-help-anchor, .help';
  const anchors = () => [...surface.querySelectorAll(selector), ...component.querySelectorAll(selector)];
  const escape = event => {
    if (event.key !== 'Escape') return;
    for (const anchor of anchors()) {
      if (anchor.matches(':hover, :focus-within')) anchor.dataset.helpDismissed = 'true';
    }
  };
  const enter = event => {
    const target = event.composedPath?.()[0] || event.target;
    const anchor = target?.closest?.(selector);
    if (!anchor || anchor.contains(event.relatedTarget)) return;
    delete anchor.dataset.helpDismissed;
  };
  surface.addEventListener('keydown', escape, true);
  surface.addEventListener('pointerover', enter, true);
  surface.addEventListener('focusin', enter, true);
  return () => {
    surface.removeEventListener('keydown', escape, true);
    surface.removeEventListener('pointerover', enter, true);
    surface.removeEventListener('focusin', enter, true);
  };
}

export default function render({parentElement, data}) {
  const root = document.documentElement;
  const control = parentElement.querySelector('.theme-control');
  const toggle = parentElement.querySelector('#theme-toggle');
  let stored;
  try { stored = window.localStorage.getItem('trace-theme'); } catch {}
  function apply(theme, persist = false) {
    const value = theme === 'astral' ? 'astral' : 'dark';
    root.dataset.traceTheme = value;
    control.dataset.theme = value;
    toggle.setAttribute('aria-checked', String(value === 'astral'));
    if (persist) { try { window.localStorage.setItem('trace-theme', value); } catch {} }
    window.dispatchEvent(new CustomEvent('trace-theme-change', {detail: value}));
  }
  apply(root.dataset.traceTheme || stored || data.defaultTheme);
  toggle.onclick = () => apply(root.dataset.traceTheme === 'astral' ? 'dark' : 'astral', true);
  const onStorage = event => { if (event.key === 'trace-theme') apply(event.newValue); };
  window.addEventListener('storage', onStorage);
  const cleanHelp = installHelpDismissal(document, parentElement);
  return () => { cleanHelp(); toggle.onclick = null; window.removeEventListener('storage', onStorage); };
}
