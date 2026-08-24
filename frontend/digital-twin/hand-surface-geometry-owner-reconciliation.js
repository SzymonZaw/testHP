(() => {
  const PARAMS = ['palmLength','palmWidth','thickness','fingerSpread','taper','thumbAngle'];
  const DEFAULTS = Object.fromEntries(PARAMS.map(key => [key, 1]));
  const STORAGE = 'digitalTwinHandSurface.v1';
  const LIVE_STORAGE = 'digitalTwinHandGeometry.live.v1';
  const clone = value => Object.fromEntries(PARAMS.map(key => [key, Number(value?.[key] ?? 1)]));
  const readStudioGeometry = () => {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      return raw?.geometry && typeof raw.geometry === 'object' ? clone(raw.geometry) : null;
    } catch {
      return null;
    }
  };
  const writeGeometry = geometry => {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE) || '{}');
      localStorage.setItem(STORAGE, JSON.stringify({ ...raw, geometry: clone(geometry) }));
    } catch {}
    try {
      const raw = JSON.parse(localStorage.getItem(LIVE_STORAGE) || '{}');
      localStorage.setItem(LIVE_STORAGE, JSON.stringify({
        ...raw,
        schema: 'hand-surface-geometry-live-v4',
        parameters: clone(geometry),
        updatedAt: new Date().toISOString()
      }));
    } catch {}
  };
  const sync = reason => {
    const api = window.digitalTwinGeometry;
    const geometry = readStudioGeometry();
    if (!api?.setState || !geometry) return false;
    const next = clone(geometry);
    api.setState(next);
    window.dispatchEvent(new CustomEvent('testhp:geometry-owner-reconciled', { detail: { reason, geometry: next } }));
    return true;
  };
  const removeQuickStart = () => {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio) return;
    studio.querySelectorAll('.hss-geometry-group').forEach(group => {
      if (/^\s*Szybki start\s*$/i.test(group.textContent || '')) group.remove();
    });
  };
  const setStatus = text => {
    const status = document.querySelector('.hss-geometry-status');
    if (status) status.textContent = text;
  };
  let past = [];
  let future = [];
  let internal = false;
  const remember = state => {
    if (internal) return;
    past.push(clone(state));
    if (past.length > 30) past.shift();
    future = [];
  };
  const apply = (state, message) => {
    const api = window.digitalTwinGeometry;
    if (!api?.setState) return;
    internal = true;
    try {
      const next = clone(state);
      writeGeometry(next);
      api.setState(next);
      window.dispatchEvent(new CustomEvent('testhp:geometry-owner-reconciled', { detail: { reason: message, geometry: next } }));
      setStatus(`✓ ${message}`);
    } finally {
      internal = false;
    }
  };
  const bind = () => {
    const studio = document.getElementById('hand-surface-studio');
    if (!studio || studio.dataset.geometryOwnerFix === '1') return;
    studio.dataset.geometryOwnerFix = '1';

    studio.addEventListener('input', event => {
      if (internal) return;
      const input = event.target?.closest?.('input[data-g]');
      if (!input || !PARAMS.includes(input.dataset.g)) return;
      const api = window.digitalTwinGeometry;
      if (api?.getState) remember(api.getState());
      requestAnimationFrame(() => sync(`slider:${input.dataset.g}`));
    });

    studio.addEventListener('change', event => {
      if (internal) return;
      const input = event.target?.closest?.('input[data-number-g]');
      if (!input || !PARAMS.includes(input.dataset.numberG)) return;
      const api = window.digitalTwinGeometry;
      if (api?.getState) remember(api.getState());
      requestAnimationFrame(() => sync(`number:${input.dataset.numberG}`));
    });

    // The legacy toolbar mutates the same meshes directly. Intercept it in the
    // capture phase and make the canonical geometry API the only owner.
    studio.addEventListener('click', event => {
      const control = event.target?.closest?.('#hss-geometry-undo,#hss-geometry-redo,#hss-geometry-reset');
      if (!control) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      const api = window.digitalTwinGeometry;
      if (!api?.getState || !api?.setState) return;
      const current = clone(api.getState());

      if (control.id === 'hss-geometry-undo') {
        const previous = past.pop();
        if (!previous) { setStatus('✓ Brak wcześniejszej zmiany'); return; }
        future.push(current);
        apply(previous, 'Cofnięto zmianę');
        return;
      }
      if (control.id === 'hss-geometry-redo') {
        const next = future.pop();
        if (!next) { setStatus('✓ Brak zmiany do ponowienia'); return; }
        past.push(current);
        apply(next, 'Ponowiono zmianę');
        return;
      }
      if (control.id === 'hss-geometry-reset') {
        if (PARAMS.some(key => current[key] !== 1)) past.push(current);
        future = [];
        apply(DEFAULTS, 'Przywrócono geometrię bazową');
      }
    }, true);
  };

  const boot = () => {
    bind();
    removeQuickStart();
    [0,100,300,800,1500,3000].forEach(ms => setTimeout(() => {
      bind();
      removeQuickStart();
      sync(`boot:${ms}`);
    }, ms));
    new MutationObserver(() => {
      bind();
      removeQuickStart();
    }).observe(document.body, { childList: true, subtree: true });
    ['testhp:deep-3d-active','testhp:viewport-manager-ready','testhp:spatial-layer-changed'].forEach(name => {
      window.addEventListener(name, () => setTimeout(() => sync(`event:${name}`), 0));
    });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
