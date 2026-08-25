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

  // UX: rejestracja i wynik są jednym krokiem dla użytkownika.
  // Nie usuwamy istniejącej logiki stanu; tylko łączymy prezentację obu etapów.
  const unifyRegistrationAndResult = () => {
    const shell = document.getElementById('hand-surface-unified');
    if (!shell || shell.dataset.registrationResultUnified === '1') return false;
    const registration = shell.querySelector('[data-hsu-section="registration"]');
    const result = shell.querySelector('[data-hsu-section="result"]');
    const resultTab = shell.querySelector('[data-hsu-tab="result"]');
    const registrationTab = shell.querySelector('[data-hsu-tab="registration"]');
    if (!registration || !result || !registrationTab) return false;

    shell.dataset.registrationResultUnified = '1';
    registrationTab.textContent = '2. Rejestracja i wynik';
    if (resultTab) {
      resultTab.hidden = true;
      resultTab.setAttribute('aria-hidden', 'true');
      resultTab.setAttribute('tabindex', '-1');
    }

    result.hidden = false;
    result.removeAttribute('data-hsu-section');
    result.dataset.hsuUnifiedResult = 'true';
    registration.appendChild(result);

    const resultTitle = result.querySelector('h3');
    if (!resultTitle) {
      const heading = document.createElement('div');
      heading.className = 'hsu-unified-result-heading';
      heading.textContent = 'Stan i wynik';
      result.prepend(heading);
    }

    const goRegistration = result.querySelector('#hsu-go-registration');
    if (goRegistration) goRegistration.hidden = true;

    // Existing renderer is intentionally reused once so its current state is shown.
    if (resultTab) {
      resultTab.click();
      registrationTab.click();
    }
    return true;
  };

  const installUnifiedCss = () => {
    if (document.getElementById('hsu-registration-result-unified-css')) return;
    const style = document.createElement('style');
    style.id = 'hsu-registration-result-unified-css';
    style.textContent = `
      #hand-surface-unified [data-hsu-unified-result]{display:block!important;margin-top:18px;padding-top:14px;border-top:1px solid var(--border,#d8dee8)}
      #hand-surface-unified .hsu-unified-result-heading{font-size:14px;font-weight:800;margin:0 0 8px;color:#344054}
      #hand-surface-unified [data-hsu-tab="result"][hidden]{display:none!important}
    `;
    document.head.appendChild(style);
  };

  const boot = () => {
    bind();
    removeQuickStart();
    installUnifiedCss();
    unifyRegistrationAndResult();
    [0,100,300,800,1500,3000].forEach(ms => setTimeout(() => {
      bind();
      removeQuickStart();
      installUnifiedCss();
      unifyRegistrationAndResult();
      sync(`boot:${ms}`);
    }, ms));
    new MutationObserver(() => {
      bind();
      removeQuickStart();
      installUnifiedCss();
      unifyRegistrationAndResult();
    }).observe(document.body, { childList: true, subtree: true });
    ['testhp:deep-3d-active','testhp:viewport-manager-ready','testhp:spatial-layer-changed'].forEach(name => {
      window.addEventListener(name, () => setTimeout(() => sync(`event:${name}`), 0));
    });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();