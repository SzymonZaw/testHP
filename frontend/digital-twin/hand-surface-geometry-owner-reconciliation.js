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
    if (!api?.setState || !geometry) return false;
    const next = Object.fromEntries(PARAMS.map(key => [key, Number(geometry[key] ?? 1)]));
    api.setState(next);
    window.dispatchEvent(new CustomEvent('testhp:geometry-owner-reconciled', { detail: { reason, geometry: next } }));
    return true;
  };
  const bind = () => {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio || studio.dataset.geometryOwnerFix === '1') return;
    studio.dataset.geometryOwnerFix='1';

    studio.addEventListener('input', event => {
      const input=event.target?.closest?.('input[data-g]');
      if (!input || !PARAMS.includes(input.dataset.g)) return;
      requestAnimationFrame(() => sync(`slider:${input.dataset.g}`));
    });

    studio.addEventListener('change', event => {
      const input=event.target?.closest?.('input[data-number-g]');
      if (!input || !PARAMS.includes(input.dataset.numberG)) return;
      requestAnimationFrame(() => sync(`number:${input.dataset.numberG}`));
    });

    studio.addEventListener('click', event => {
      const control=event.target?.closest?.('[data-preset],#hss-geometry-undo,#hss-geometry-redo,#hss-geometry-reset');
      if (!control) return;
      setTimeout(() => sync(`button:${control.id || control.dataset.preset || 'geometry'}`),0);
    });
  };

  const boot = () => {
    bind();
    [0,100,300,800,1500,3000].forEach(ms => setTimeout(() => sync(`boot:${ms}`),ms));
    new MutationObserver(bind).observe(document.body,{childList:true,subtree:true});
    ['testhp:deep-3d-active','testhp:viewport-manager-ready','testhp:spatial-layer-changed'].forEach(name => {
      window.addEventListener(name, () => setTimeout(() => sync(`event:${name}`),0));
    });
  };

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
