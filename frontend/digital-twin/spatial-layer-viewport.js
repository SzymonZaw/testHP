(() => {
  // Passive bridge around the canonical Three.js viewport owned by app.js.
  // This module never creates, resizes, or renders a renderer.
  const viewport = document.getElementById('twin-viewport');
  const canvas = document.getElementById('twin-canvas');
  if (!viewport || !canvas) return;

  const level = () => (document.getElementById('spatial-level-badge')?.textContent || 'MACRO').trim().toLowerCase();
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const crumbs = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);

  const canonical = () => {
    const manager = window.spatialViewportManager;
    return !!(manager && manager.version === 'canonical-three-1' && manager.active?.scene && manager.active?.camera && manager.deepRenderer);
  };

  let lastSignature = '';

  function publish(reason = 'state-change') {
    const manager = window.spatialViewportManager;
    if (!manager) {
      window.dispatchEvent(new CustomEvent('testhp:viewport-waiting', { detail: { reason: 'canonical manager not published yet' } }));
      return false;
    }
    if (!canonical()) {
      window.dispatchEvent(new CustomEvent('testhp:viewport-error', { detail: { error: new Error('Non-canonical viewport manager detected; refusing to replace the real renderer') } }));
      return false;
    }

    const detail = {
      level: level(),
      target: target(),
      path: crumbs(),
      children: children(),
      renderer: manager.active?.constructor?.name || 'ThreeCanvasRenderer',
      reason
    };
    const signature = JSON.stringify(detail);
    if (signature !== lastSignature) {
      lastSignature = signature;
      window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', { detail }));
    }
    return true;
  }

  // The macro renderer historically handled canvas clicks globally. Deeper
  // layers must not fall through to that handler.
  canvas.addEventListener('click', event => {
    const currentLevel = level();
    if (currentLevel === 'macro' || currentLevel === 'macro anatomy') return;
    event.preventDefault();
    event.stopImmediatePropagation();
    window.dispatchEvent(new CustomEvent('testhp:viewport-deep-click', {
      detail: {
        level: currentLevel,
        target: target(),
        path: crumbs(),
        children: children(),
        clientX: event.clientX,
        clientY: event.clientY,
        message: 'Deep-layer click intercepted; macro region selector was not invoked.'
      }
    }));
  }, true);

  const observer = new MutationObserver(() => publish('dom-mutation'));
  ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });

  window.addEventListener('testhp:viewport-manager-ready', () => publish('manager-ready'));
  window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });

  publish('initial');
})();
