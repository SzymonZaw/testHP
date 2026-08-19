(() => {
  // Observe the canonical Three.js viewport owned by app.js.
  // This module must never create a fake renderer/manager.
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

  function report() {
    const manager = window.spatialViewportManager;
    if (!manager) {
      window.dispatchEvent(new CustomEvent('testhp:viewport-waiting', { detail: { reason: 'canonical manager not published yet' } }));
      return;
    }
    if (!canonical()) {
      window.dispatchEvent(new CustomEvent('testhp:viewport-error', { detail: { error: new Error('Non-canonical viewport manager detected; refusing to replace the real renderer') } }));
      return;
    }
    manager.render?.();
    window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {
      detail: {
        level: level(),
        target: target(),
        path: crumbs(),
        children: children(),
        renderer: manager.active?.constructor?.name || 'ThreeCanvasRenderer'
      }
    }));
  }

  // The macro renderer owns the hand meshes and app.js historically raycasted
  // against those meshes on every canvas click. That meant a click made while
  // drilling into tissue/cellular/cell could jump back to Thumb/Palm/etc.
  // Gate the legacy macro click handler at the capture phase. Deeper layers
  // must be handled by their own renderer/interaction path, never by the
  // macro-region selector.
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

  const observer = new MutationObserver(report);
  ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });

  window.addEventListener('testhp:viewport-manager-ready', report);
  window.addEventListener('resize', () => window.spatialViewportManager?.resize?.(), { passive: true });
  window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });

  report();
})();
