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

  let repairing = false;
  let scheduled = 0;
  let lastRepairAt = 0;

  const currentTarget = () => {
    const manager = window.spatialViewportManager;
    const state = manager?.state || {};
    const node = document.getElementById('spatial-node');
    const label = node?.querySelector('strong')?.textContent?.trim() || state.target || 'Palm';
    const id = state.spatial_id || state.spatialId || manager?.spatialTarget || 'hand/palm';
    const path = [...document.querySelectorAll('#spatial-breadcrumb button')]
      .map(button => button.textContent.trim())
      .filter(Boolean);
    const level = String(state.level || document.getElementById('spatial-level-badge')?.textContent || 'macro')
      .toLowerCase();

    return {
      id: String(id),
      spatial_id: String(id),
      spatialId: String(id),
      spatial_node_id: String(id),
      targetSpatialId: String(id),
      targetId: state.id || 'palm',
      label,
      level,
      path
    };
  };

  const canvasLooksBlank = canvas => {
    const gl = canvas?.getContext('webgl2');
    if (!gl || gl.isContextLost?.()) return false;
    if (!gl.drawingBufferWidth || !gl.drawingBufferHeight) return false;

    const pixel = new Uint8Array(4);
    gl.readPixels(
      Math.floor(gl.drawingBufferWidth / 2),
      Math.floor(gl.drawingBufferHeight / 2),
      1,
      1,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      pixel
    );

    return pixel[3] === 0;
  };

  const refreshSceneBounds = scene => {
    let meshCount = 0;

    scene?.traverse?.(object => {
      if (!object?.isMesh) return;
      meshCount += 1;

      // Geometry/transform edits performed by the hand-surface layer can leave
      // cached bounds from the previous tab activation. Three.js uses those
      // bounds for frustum culling, so explicitly invalidate/rebuild them.
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

  const renderScene = (manager, scene, camera, renderer) => {
    camera?.updateMatrixWorld?.(true);
    camera?.updateProjectionMatrix?.();
    renderer?.setRenderTarget?.(null);
    renderer?.setScissorTest?.(false);
    renderer?.setViewport?.(0, 0, renderer.domElement.width, renderer.domElement.height);
    renderer?.render?.(scene, camera);
  };

  const forceVisibleFallback = (scene, renderer, camera) => {
    const changed = [];

    scene?.traverse?.(object => {
      if (!object?.isMesh || !object.visible || object.frustumCulled === false) return;
      changed.push([object, object.frustumCulled]);
      object.frustumCulled = false;
    });

    if (!changed.length) return false;

    renderScene(null, scene, camera, renderer);

    // If the fallback made the framebuffer non-empty, keep culling disabled for
    // this active scene. Re-enabling it immediately recreates the black-screen
    // state on the next render. The fallback is intentionally scoped to the
    // currently active scene rather than changing Three.js globally.
    return true;
  };

  const scheduleRepair = reason => {
    cancelAnimationFrame(scheduled);
    scheduled = requestAnimationFrame(() => {
      requestAnimationFrame(() => repair(reason));
    });
  };

  const repair = reason => {
    const canvas = document.querySelector(CANVAS_SELECTOR);
    const manager = window.spatialViewportManager;
    const renderer = manager?.deepRenderer;
    const scene = manager?.active?.scene;
    const camera = manager?.active?.camera;

    if (!canvas || !manager || !renderer || !scene || !camera || repairing) return;
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
      canvas: `${canvas.width}x${canvas.height}`
    };

    try {
      if (typeof manager.setSpatialTarget === 'function') {
        manager.setSpatialTarget(target);
      }

      const meshCount = refreshSceneBounds(manager.active?.scene || scene);
      manager.resize?.();
      renderScene(manager, scene, camera, renderer);

      let fallbackUsed = false;
      if (canvasLooksBlank(canvas)) {
        // Proven lifecycle failure mode: the canonical hand scene contains
        // valid meshes and draw calls, but frustum culling rejects them after
        // returning from Geometria. Disable culling only for this active scene
        // as a deterministic recovery path.
        fallbackUsed = forceVisibleFallback(scene, renderer, camera);
      }

      if (canvasLooksBlank(canvas) && typeof manager.setSpatialTarget === 'function') {
        manager.setSpatialTarget({ ...target });
        refreshSceneBounds(manager.active?.scene || scene);
        manager.resize?.();
        renderScene(manager, manager.active?.scene || scene, manager.active?.camera || camera, renderer);
      }

      window.dispatchEvent(new CustomEvent('testhp:viewport-lifecycle-repaired', {
        detail: {
          reason,
          target,
          before,
          meshCount,
          fallbackUsed,
          blankAfterRepair: canvasLooksBlank(canvas)
        }
      }));
    } catch (error) {
      console.error('[Twin Viewport] lifecycle repair failed', error);
      window.dispatchEvent(new CustomEvent('testhp:viewport-lifecycle-repair-error', {
        detail: { reason, error, target }
      }));
    } finally {
      repairing = false;
    }
  };

  const onManagerReady = () => {
    window.setTimeout(() => scheduleRepair('manager-ready'), 0);
  };

  window.addEventListener(MANAGER_READY_EVENT, onManagerReady);
  window.addEventListener('pageshow', () => scheduleRepair('pageshow'));
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') scheduleRepair('visibility-visible');
  });
  window.addEventListener('resize', () => scheduleRepair('resize'), { passive: true });

  REPAIR_EVENT_NAMES.forEach(name => {
    window.addEventListener(name, () => scheduleRepair(name));
  });

  document.addEventListener('click', event => {
    const target = event.target?.closest?.('button,[role="tab"],a');
    if (!target) return;
    window.setTimeout(() => scheduleRepair('ui-navigation'), 0);
  }, true);

  let attempts = 0;
  const timer = window.setInterval(() => {
    attempts += 1;
    if (window.spatialViewportManager) scheduleRepair('manager-poll');
    if (attempts >= 40) window.clearInterval(timer);
  }, 250);
  window.addEventListener('beforeunload', () => window.clearInterval(timer), { once: true });
})();
