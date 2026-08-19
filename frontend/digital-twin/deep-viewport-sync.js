(() => {
  // Compatibility bridge. app.js is the single owner of the canonical
  // Three.js scene and now owns both macro and deep spatial layers.
  // This module deliberately creates no second renderer, overlay, polling
  // loop, or independent deep scene.
  function sync() {
    const manager = window.spatialViewportManager;
    if (!manager?.active?.scene) return;
    manager.render?.();
    window.dispatchEvent(new CustomEvent('testhp:deep-viewport-synced', {
      detail: {
        activeKey: manager.activeKey,
        activeLayer: manager.activeLayer,
        sceneChildren: manager.active.scene.children.length,
        clickable: manager.active.clickable?.length || 0
      }
    }));
  }
  window.addEventListener('testhp:viewport-manager-ready', sync);
  window.addEventListener('testhp:spatial-layer-changed', sync);
})();
