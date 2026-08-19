(() => {
  // Canonical viewport adapter.
  // The actual 3D renderer and spatial navigation live in app.js.
  // This adapter intentionally does NOT create a second Three.js renderer.
  // It exists as a stable integration surface for diagnostics and legacy modules.
  const viewport = document.getElementById('twin-viewport');
  const canvas = document.getElementById('twin-canvas');
  if (!viewport || !canvas) return;

  const level = () => (document.getElementById('spatial-level-badge')?.textContent || 'MACRO').trim().toLowerCase();
  const target = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const crumbs = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
  const children = () => [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);

  const manager = {
    version: 'canonical-adapter-1',
    deepCanvas: canvas,
    deepRenderer: null,
    activeKey: 'macro|hand',
    active: { constructor: { name: 'AppThreeRenderer' }, clickable: [] },
    render() {
      const path = crumbs();
      const currentLevel = level();
      const currentTarget = target();
      this.activeKey = `${currentLevel}|${path.join('>') || currentTarget}`;
      this.active = {
        constructor: { name: 'AppThreeRenderer' },
        clickable: [],
        root: null,
        scene: null,
        camera: null
      };
      window.dispatchEvent(new CustomEvent('testhp:viewport-rendered', {
        detail: { level: currentLevel, target: currentTarget, path, children: children() }
      }));
    },
    resize() {
      window.dispatchEvent(new Event('resize'));
    },
    base() {},
    deep() {}
  };

  window.spatialViewportManager = manager;
  window.spatialEvidenceTarget = 'hand';
  manager.render();

  const observer = new MutationObserver(() => manager.render());
  ['spatial-level-badge', 'spatial-breadcrumb', 'spatial-node', 'spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });
  window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });
})();
