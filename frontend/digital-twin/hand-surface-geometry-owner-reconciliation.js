(() => {
  const PARAMS = ['palmLength','palmWidth','thickness','fingerSpread','taper','thumbAngle'];
  const STORAGE = 'digitalTwinHandSurface.v1';
  const readStudioGeometry = () => {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      return raw?.geometry && typeof raw.geometry === 'object' ? raw.geometry : null;
    } catch {
      return null;
    }
  };
  const sync = reason => {
    const api = window.digitalTwinGeometry;
    const geometry = readStudioGeometry();
    if (!api?.setState || !geometry) return;
    const next = Object.fromEntries(PARAMS.map(key => [key, Number(geometry[key] ?? 1)]));
    api.setState(next);
    window.dispatchEvent(new CustomEvent('testhp:geometry-owner-reconciled', { detail: { reason, geometry: next } }));
  };
  const bind = () => {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio || studio.dataset.geometryOwnerFix === '1') return;
    studio.dataset.geometryOwnerFix = '1';

    studio.addEventListener('input', event => {
      const input = event.target?.closest?.('input[data-g]');
      if (!input || !PARAMS.includes(input.dataset.g)) return;
      requestAnimationFrame(() => sync(`slider:${input.dataset.g}`));
    });

    studio.addEventListener('change', event => {
      const input = event.target?.closest?.('input[data-number-g]');
      if (!input || !PARAMS.includes(input.dataset.numberG)) return;
      requestAnimationFrame(() => sync(`number:${input.dataset.numberG}`));
    });

    studio.addEventListener('click', event => {
      const control = event.target?.closest?.('[data-preset],#hss-geometry-undo,#hss-geometry-redo,#hss-geometry-reset');
      if (!control) return;
      setTimeout(() => sync(`button:${control.id || control.dataset.preset || 'geometry'}`), 0);
    });
  };

  const boot = () => {
    bind();
    setTimeout(() => sync('initial'), 0);
    new MutationObserver(bind).observe(document.body, { childList: true, subtree: true });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
