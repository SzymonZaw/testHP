(() => {
  const CANVAS_SELECTOR = '#twin-canvas';
  const MANAGER_READY_EVENT = 'testhp:viewport-manager-ready';
  const WATCH_EVENTS = [
    'testhp:spatial-layer-changed',
    'testhp:spatial-target-changed',
    'testhp:spatial-contract-changed',
    'testhp:deep-3d-active',
    'testhp:geometry-updated',
    'testhp:geometry-changed'
  ];

  if (window.__testhpViewportLifecycleRepairInstalled) return;
  window.__testhpViewportLifecycleRepairInstalled = true;
  window.__testhpViewportLifecycleRepairVersion = 'lifecycle-repair-5-passive';

  const readCenterPixel = canvas => {
    const gl = canvas?.getContext('webgl2');
    if (!gl || gl.isContextLost?.() || !gl.drawingBufferWidth || !gl.drawingBufferHeight) return null;
    const pixel = new Uint8Array(4);
    gl.readPixels(
      Math.floor(gl.drawingBufferWidth / 2),
      Math.floor(gl.drawingBufferHeight / 2),
      1, 1,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      pixel
    );
    return [...pixel];
  };

  const snapshot = reason => {
    const canvas = document.querySelector(CANVAS_SELECTOR);
    const manager = window.spatialViewportManager;
    const active = manager?.active;
    const pixel = readCenterPixel(canvas);
    const meshes = [];
    active?.scene?.traverse?.(object => {
      if (!object?.isMesh) return;
      meshes.push({ name: object.name || object.type, visible: object.visible, frustumCulled: object.frustumCulled });
    });

    return {
      reason,
      activeKey: manager?.activeKey || null,
      activeLayer: manager?.activeLayer || active?.activeLayer || null,
      spatialId: manager?.state?.spatial_id || null,
      canvasConnected: !!canvas?.isConnected,
      canvas: canvas ? `${canvas.width}x${canvas.height}` : null,
      drawingBuffer: canvas?.getContext?.('webgl2') ? `${canvas.getContext('webgl2').drawingBufferWidth}x${canvas.getContext('webgl2').drawingBufferHeight}` : null,
      contextLost: canvas?.getContext?.('webgl2')?.isContextLost?.() ?? null,
      pixel,
      blank: !!pixel && pixel[3] === 0,
      drawCalls: manager?.deepRenderer?.info?.render?.calls ?? null,
      triangles: manager?.deepRenderer?.info?.render?.triangles ?? null,
      meshCount: meshes.length,
      meshes
    };
  };

  const inspect = reason => {
    const detail = snapshot(reason);
    window.__testhpViewportLifecycleLastRepair = detail;
    window.dispatchEvent(new CustomEvent('testhp:viewport-lifecycle-repaired', { detail }));
    return detail;
  };

  // Lifecycle repairer is intentionally passive. It must never render, resize,
  // change frustum culling, change spatial targets, or mutate renderer state.
  // The canonical renderer owns all rendering and state restoration.
  window.__testhpViewportLifecycleRepairNow = reason => inspect(reason || 'manual');

  const scheduleInspect = reason => {
    requestAnimationFrame(() => inspect(reason));
  };

  window.addEventListener(MANAGER_READY_EVENT, () => scheduleInspect('manager-ready'));
  WATCH_EVENTS.forEach(name => window.addEventListener(name, () => scheduleInspect(name)));
  window.addEventListener('pageshow', () => scheduleInspect('pageshow'));
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') scheduleInspect('visibility-visible');
  });
  window.addEventListener('resize', () => scheduleInspect('resize'), { passive: true });
  window.addEventListener('beforeunload', () => {
    delete window.__testhpViewportLifecycleRepairNow;
  }, { once: true });
})();
