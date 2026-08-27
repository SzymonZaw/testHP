(() => {
  // Compatibility bridge. app.js is the single owner of the canonical
  // Three.js scene and now owns both macro and deep spatial layers.
  // This module deliberately creates no second renderer, overlay, polling
  // loop, or independent deep scene.
  function loadScript(id, src) {
    const existing = document.getElementById(id);
    if (existing) return Promise.resolve(existing);
    return new Promise(resolve => {
      const script = document.createElement('script');
      script.id = id;
      script.src = src;
      script.onload = () => resolve(script);
      script.onerror = () => resolve(null);
      document.head.appendChild(script);
    });
  }

  function loadArchitecture() {
    if (window.testhpHandSurfaceArchitecture) return Promise.resolve(window.testhpHandSurfaceArchitecture);
    if (window.__testhpHandSurfaceArchitectureLoad) return window.__testhpHandSurfaceArchitectureLoad;
    window.__testhpHandSurfaceArchitectureLoad = loadScript(
      'hand-surface-architecture-v1',
      '/digital-twin/hand-surface-architecture-v1.js?v=architecture-1'
    ).then(() => window.testhpHandSurfaceArchitecture || null);
    return window.__testhpHandSurfaceArchitectureLoad;
  }

  function loadModeBridge() {
    if (window.testhpHandSurfaceArchitectureModeBridge) return Promise.resolve(window.testhpHandSurfaceArchitectureModeBridge);
    return loadScript(
      'hand-surface-architecture-mode-bridge',
      '/digital-twin/hand-surface-architecture-mode-bridge.js?v=architecture-mode-1'
    ).then(() => window.testhpHandSurfaceArchitectureModeBridge || null);
  }

  function markProjectionOwnership() {
    const manager = window.spatialViewportManager;
    const scene = manager?.active?.scene;
    if (!scene) return;
    scene.userData = scene.userData || {};
    scene.userData.handSurfaceProjection = {
      schema: 'hand-surface-projection-anchor-v1',
      owner: 'scene',
      invariant: true,
      rule: 'Projection remains attached to the canonical scene while macro/deep geometry changes.'
    };

    // A projection group is allowed to live only under the canonical scene.
    // Never move it into deepRoot when the user changes spatial depth.
    const projection = scene.getObjectByName?.('__photo_surface_projection__');
    if (projection && manager.active.root && projection.parent === manager.active.root && manager.active.root !== scene) {
      scene.add(projection);
    }
  }

  function sync() {
    const manager = window.spatialViewportManager;
    if (!manager?.active?.scene) return;
    markProjectionOwnership();
    manager.render?.();
    window.dispatchEvent(new CustomEvent('testhp:deep-viewport-synced', {
      detail: {
        activeKey: manager.activeKey,
        activeLayer: manager.activeLayer,
        sceneChildren: manager.active.scene.children.length,
        clickable: manager.active.clickable?.length || 0,
        projectionOwner: manager.active.scene.userData?.handSurfaceProjection?.owner || null
      }
    }));
  }

  Promise.all([loadArchitecture(), loadModeBridge()]).then(sync);
  window.addEventListener('testhp:viewport-manager-ready', () => { Promise.all([loadArchitecture(), loadModeBridge()]).then(sync); });
  window.addEventListener('testhp:spatial-layer-changed', sync);
  window.addEventListener('testhp:hand-surface-ready', sync);
})();
