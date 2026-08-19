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

  // DOM mutations are produced by the canonical renderer itself. Calling
  // manager.render() from the MutationObserver therefore creates a render ->
  // DOM mutation -> observer -> render loop and can lock the browser main
  // thread. State publication and rendering are deliberately separated.
  let lastSignature = '';
  let renderScheduled = false;

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

  function renderOnce() {
    if (renderScheduled) return;
    renderScheduled = true;
    requestAnimationFrame(() => {
      renderScheduled = false;
      const manager = window.spatialViewportManager;
      if (!canonical()) return;
      manager.render?.();
      publish('manager-render');
    });
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

  const observer = new MutationObserver(() => {
    // Publish the new spatial state only. Never render from this callback.
    publish('dom-mutation');
  });
  ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });

  window.addEventListener('testhp:viewport-manager-ready', () => {
    if (publish('manager-ready')) renderOnce();
  });
  window.addEventListener('resize', () => window.spatialViewportManager?.resize?.(), { passive: true });
  window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });

  publish('initial');
})();
