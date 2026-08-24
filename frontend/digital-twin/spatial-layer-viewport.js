(() => {
  const canvas = document.getElementById('twin-canvas');
  if (!canvas) return;

  const loadGeometryBridge = () => {
    if (document.querySelector('script[data-canonical-geometry-bridge]')) return;
    const script = document.createElement('script');
    script.src = '/digital-twin/hand-surface-geometry-canonical-bridge.js?v=canonical-geometry-1';
    script.dataset.canonicalGeometryBridge = 'true';
    document.body.appendChild(script);
  };

  // app.js + spatial-root-anatomy-fix.js own the navigator DOM. This bridge
  // only reports viewport state and never writes #spatial-children.
  const read = () => ({
    level: document.getElementById('spatial-level-badge')?.textContent?.trim() || '?',
    target: document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || '?',
    path: [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean),
    children: [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean)
  });

  const report = reason => {
    const state = read();
    const manager = window.spatialViewportManager;
    window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {
      detail: {
        ...state,
        renderer: 'ThreeCanvasRenderer',
        reason,
        managerPresent: !!manager,
        activeKey: manager?.activeKey || null,
        activeLayer: manager?.activeLayer || null
      }
    }));
    loadGeometryBridge();
  };

  window.addEventListener('testhp:viewport-manager-ready', () => report('manager-ready'));
  window.addEventListener('testhp:spatial-layer-changed', () => report('spatial-layer-changed'));
  window.addEventListener('resize', () => window.spatialViewportManager?.resize?.(), { passive: true });
  report('loaded-without-dom-mutation');
})();
