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

  const scheduleRepair = reason => {
    cancelAnimationFrame(scheduled);
    scheduled = requestAnimationFrame(() => {
      requestAnimationFrame(() => repair(reason));
    });
  };

  const repair = reason => {
    const canvas = document.querySelector(CANVAS_SELECTOR);
    const manager = window.spatialViewportManager;
    if (!canvas || !manager || repairing) return;

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
      manager.resize?.();
      manager.render?.();

      // A second activation is intentional: leaving/re-entering the geometry
      // tab can leave the canonical renderer attached to an empty active scene.
      // Re-selecting the current canonical target rebuilds the active layer.
      if (canvasLooksBlank(canvas) && typeof manager.setSpatialTarget === 'function') {
        manager.setSpatialTarget({ ...target });
        manager.resize?.();
        manager.render?.();
      }

      window.dispatchEvent(new CustomEvent('testhp:viewport-lifecycle-repaired', {
        detail: {
          reason,
          target,
          before,
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

  // Internal UI tabs do not necessarily change document visibility. Detect a
  // return to the geometry/surface UI by checking the main renderer after UI
  // interactions, without touching the renderer when it is already healthy.
  document.addEventListener('click', event => {
    const target = event.target?.closest?.('button,[role="tab"],a');
    if (!target) return;
    window.setTimeout(() => scheduleRepair('ui-navigation'), 0);
  }, true);

  // Wait for the asynchronously bootstrapped manager if the script itself is
  // evaluated before twin-bootstrap finishes importing app.js.
  let attempts = 0;
  const timer = window.setInterval(() => {
    attempts += 1;
    if (window.spatialViewportManager) scheduleRepair('manager-poll');
    if (attempts >= 40) window.clearInterval(timer);
  }, 250);
  window.addEventListener('beforeunload', () => window.clearInterval(timer), { once: true });
})();
