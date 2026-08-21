(() => {
  // app.js is the canonical owner of spatial navigation. This module is
  // intentionally passive: it must never replace or proxy navigation buttons.
  // Multiple writers of #spatial-children were causing stale DOM targets.
  const report = reason => window.dispatchEvent(new CustomEvent('testhp:spatial-navigation-debug', {
    detail: {
      source: 'spatial-navigation-v2',
      mode: 'canonical-passive',
      reason,
      managerPresent: !!window.spatialViewportManager,
      activeKey: window.spatialViewportManager?.activeKey || null,
      activeLayer: window.spatialViewportManager?.activeLayer || null
    }
  }));
  window.addEventListener('testhp:viewport-manager-ready', () => report('manager-ready'), { once: true });
  window.addEventListener('testhp:spatial-layer-changed', () => report('spatial-layer-changed'));
  report('loaded-without-dom-mutation');
})();
