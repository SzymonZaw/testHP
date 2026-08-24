(() => {
  const CANVAS_SELECTOR = '#twin-canvas';
  const MANAGER_READY_EVENT = 'testhp:viewport-manager-ready';
  const REPAIR_EVENT_NAMES = [
    'testhp:spatial-layer-changed',
    'testhp:spatial-target-changed',
    'testhp:spatial-contract-changed',
    'testhp:deep-3d-active',
    'testhp:geometry-updated',
    'testhp:geometry-changed'
  ];

  if (window.__testhpViewportLifecycleRepairInstalled) return;
  window.__testhpViewportLifecycleRepairInstalled = true;
  window.__testhpViewportLifecycleRepairVersion = 'lifecycle-repair-4';

  let repairing = false;
  let scheduled = 0;
  let lastRepairAt = 0;

  const currentTarget = () => {
    const manager = window.spatialViewportManager;
    const state = manager?.state || {};
    const node = document.getElementById('spatial-node');
    const label = node?.querySelector('strong')?.textContent?.trim() || state.target || 'Palm';
    const rawId = state.spatial_id || state.spatialId || manager?.spatialTarget || 'hand/palm';
    const id = String(rawId || 'hand/palm').replace(/^\/+|\/+$/g, '');
    const path = [...document.querySelectorAll('#spatial-breadcrumb button')].map(button => button.textContent.trim()).filter(Boolean);
    const level = String(state.level || document.getElementById('spatial-level-badge')?.textContent || 'macro').toLowerCase();
    return { id, spatial_id: id, spatialId: id, spatial_node_id: id, targetSpatialId: id, targetId: state.id || 'palm', label, level, path };
  };

  const readCenterPixel = canvas => {
    const gl = canvas?.getContext('webgl2');
    if (!gl || gl.isContextLost?.() || !gl.drawingBufferWidth || !gl.drawingBufferHeight) return null;
    const pixel = new Uint8Array(4);
    gl.readPixels(Math.floor(gl.drawingBufferWidth / 2), Math.floor(gl.drawingBufferHeight / 2), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    return [...pixel];
  };

  const canvasLooksBlank = canvas => {
    const pixel = readCenterPixel(canvas);
    return !!pixel && pixel[3] === 0;
  };

  const refreshSceneBounds = scene => {
    let meshCount = 0;
    scene?.traverse?.(object => {
      if (!object?.isMesh) return;
      meshCount += 1;
      const geometry = object.geometry;
      if (geometry) {
        geometry.boundingSphere = null;
        geometry.boundingBox = null;
        geometry.computeBoundingSphere?.();
        geometry.computeBoundingBox?.();
      }
      object.matrixWorldNeedsUpdate = true;
      object.updateMatrixWorld?.(true);
    });
    scene?.updateMatrixWorld?.(true);
    return meshCount;
  };

  const renderScene = (scene, camera, renderer) => {
    if (!scene || !camera || !renderer) return;
    camera.updateMatrixWorld?.(true);
    camera.updateProjectionMatrix?.();
    scene.updateMatrixWorld?.(true);
    renderer.setRenderTarget?.(null);
    renderer.setScissorTest?.(false);
    renderer.setViewport?.(0, 0, renderer.domElement.width, renderer.domElement.height);
    renderer.render(scene, camera);
  };

  const disableCullingForActiveScene = scene => {
    const changed = [];
    scene?.traverse?.(object => {
      if (!object?.isMesh || !object.visible) return;
      if (object.frustumCulled !== false) {
        changed.push(object.name || object.type);
        object.frustumCulled = false;
      }
    });
    return changed;
  };

  const repair = reason => {
    const canvas = document.querySelector(CANVAS_SELECTOR);
    const manager = window.spatialViewportManager;
    const renderer = manager?.deepRenderer;
    const scene = manager?.active?.scene;
    const camera = manager?.active?.camera;
    if (!canvas || !manager || !renderer || !scene || !camera || repairing) return;

    // This module is a rendering lifecycle repairer, not a spatial-navigation
    // owner. Never call setSpatialTarget() here: doing so can feed the target
    // back through the canonicalizer and navigation/API observers and turn a
    // stable hand/palm target into hand/palm/hand/palm/... request storms.
    // Only repair the renderer when the framebuffer is actually blank.
    if (!canvasLooksBlank(canvas)) return;

    const now = performance.now();
    if (now - lastRepairAt < 400) return;
    lastRepairAt = now;
    repairing = true;

    const target = currentTarget();
    const before = {
      activeKey: manager.activeKey,
      activeLayer: manager.activeLayer,
      target: manager.spatialTarget,
      canvas: `${canvas.width}x${canvas.height}`,
      pixel: readCenterPixel(canvas)
    };

    try {
      const activeScene = manager.active?.scene || scene;
      const activeCamera = manager.active?.camera || camera;
      const meshCount = refreshSceneBounds(activeScene);
      manager.resize?.();
      renderScene(activeScene, activeCamera, renderer);

      let fallbackUsed = false;
      let culledMeshes = [];
      if (canvasLooksBlank(canvas)) {
        culledMeshes = disableCullingForActiveScene(activeScene);
        fallbackUsed = culledMeshes.length > 0;
        renderScene(activeScene, activeCamera, renderer);
      }

      const detail = {
        reason,
        target,
        before,
        meshCount,
        fallbackUsed,
        culledMeshes,
        blankAfterRepair: canvasLooksBlank(canvas),
        pixelAfterRepair: readCenterPixel(canvas),
        activeKey: manager.activeKey,
        activeLayer: manager.activeLayer
      };

      window.__testhpViewportLifecycleLastRepair = detail;
      window.dispatchEvent(new CustomEvent('testhp:viewport-lifecycle-repaired', { detail }));
      if (detail.blankAfterRepair) console.warn('[Twin Viewport] lifecycle repair completed but framebuffer is still blank', detail);
    } catch (error) {
      console.error('[Twin Viewport] lifecycle repair failed', error);
      window.dispatchEvent(new CustomEvent('testhp:viewport-lifecycle-repair-error', { detail: { reason, error, target } }));
    } finally {
      repairing = false;
    }
  };

  const scheduleRepair = reason => {
    cancelAnimationFrame(scheduled);
    scheduled = requestAnimationFrame(() => requestAnimationFrame(() => repair(reason)));
  };

  window.__testhpViewportLifecycleRepairNow = reason => repair(reason || 'manual');

  window.addEventListener(MANAGER_READY_EVENT, () => setTimeout(() => scheduleRepair('manager-ready'), 0));
  window.addEventListener('pageshow', () => scheduleRepair('pageshow'));
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') scheduleRepair('visibility-visible');
  });
  window.addEventListener('resize', () => scheduleRepair('resize'), { passive: true });
  REPAIR_EVENT_NAMES.forEach(name => window.addEventListener(name, () => scheduleRepair(name)));

  document.addEventListener('click', event => {
    const target = event.target?.closest?.('button,[role="tab"],a');
    if (!target) return;
    setTimeout(() => scheduleRepair('ui-navigation'), 0);
  }, true);

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (window.spatialViewportManager) scheduleRepair('manager-poll');
    if (attempts >= 40) clearInterval(timer);
  }, 250);
  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
})();
