(() => {
  // Boot verifier: validate the already-created canonical viewport without
  // creating another renderer or blocking the application on diagnostics.
  const manager = () => window.spatialViewportManager;
  const verify = () => {
    const m = manager();
    const canvas = document.getElementById('twin-canvas');
    const viewport = document.getElementById('twin-viewport');
    const valid = !!(
      viewport &&
      canvas &&
      m &&
      m.active &&
      m.active.scene &&
      m.active.camera &&
      typeof m.setSpatialTarget === 'function' &&
      typeof m.render === 'function'
    );
    const detail = {
      valid,
      managerPresent: !!m,
      managerVersion: m?.version || null,
      activeKey: m?.activeKey || null,
      canvasPresent: !!canvas,
      scenePresent: !!m?.active?.scene,
      cameraPresent: !!m?.active?.camera,
      setSpatialTarget: typeof m?.setSpatialTarget === 'function',
      render: typeof m?.render === 'function'
    };
    window.__testhpViewportBootVerification = detail;
    window.dispatchEvent(new CustomEvent('testhp:viewport-boot-verified', { detail }));
    return detail;
  };

  const run = () => {
    const result = verify();
    // Do not turn a diagnostics-only verifier into a boot blocker. The
    // canonical renderer is already usable when the structural checks pass.
    if (result.valid) {
      window.__testhpViewportBootVerified = true;
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }
})();
