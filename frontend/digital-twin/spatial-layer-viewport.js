(() => {
  // Observe the canonical Three.js viewport owned by app.js.
  // This module must never create a fake renderer/manager: doing so can make
  // the bootstrap report READY while the real 3D scene is still missing.
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

  const report = () => {
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
  };

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