(() => {
  const loading = document.getElementById('viewer-loading');
  const canvas = document.getElementById('twin-canvas');
  const viewport = document.getElementById('twin-viewport');
  const status = document.getElementById('twin-status');
  if (!loading || !canvas || !viewport) return;

  const progress = (step, detail = '') => {
    window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step, detail } }));
  };

  const syncSize = () => {
    // app.js owns the renderer and listens for resize. This guarantees that
    // CSS/layout changes are also propagated to the Three.js drawing buffer.
    window.dispatchEvent(new Event('resize'));
    progress('viewport-size-sync', `${Math.round(viewport.clientWidth)}x${Math.round(viewport.clientHeight)} css / ${canvas.width}x${canvas.height} buffer`);
  };

  const hideLoading = (message = 'Digital Twin ready') => {
    loading.hidden = true;
    loading.setAttribute('aria-hidden', 'true');
    loading.style.display = 'none';
    loading.classList.remove('viewer-loading-error');
    if (status && (!status.textContent || /starting|building/i.test(status.textContent))) status.textContent = message;
    window.__testhpTwinReady = true;
    window.dispatchEvent(new CustomEvent('testhp:twin-ready', { detail: { width: canvas.width, height: canvas.height, renderer: 'WebGL' } }));
  };

  const showFailure = (message) => {
    loading.hidden = false;
    loading.style.display = 'grid';
    loading.textContent = message;
    loading.classList.add('viewer-loading-error');
    if (status) status.textContent = 'Twin Viewport error';
    window.dispatchEvent(new CustomEvent('testhp:twin-error', { detail: { error: new Error(message) } }));
  };

  const report = () => {
    try {
      progress('canvas-check');
      if (!canvas.isConnected) throw new Error('Twin canvas is not connected to the DOM');

      if (window.__testhpTwinReady) {
        progress('already-ready');
        syncSize();
        hideLoading();
        return true;
      }

      syncSize();
      progress('manager-check');
      const manager = window.spatialViewportManager;
      if (!manager) return false;

      progress('render-call');
      if (typeof manager.render === 'function') manager.render();

      progress('webgl-check');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) {
        showFailure('3D rendering is unavailable. Check WebGL support in the browser.');
        return true;
      }

      progress('ready');
      hideLoading();
      return true;
    } catch (error) {
      console.error('[Twin Viewport] bootstrap failed', error);
      showFailure(`Twin Viewport initialization failed: ${error?.message || error}`);
      return true;
    }
  };

  window.addEventListener('error', event => {
    if (event?.message) console.error('[Twin Viewport] runtime error:', event.message);
  });
  window.addEventListener('unhandledrejection', event => console.error('[Twin Viewport] unhandled rejection:', event.reason));

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    const done = report();
    if (done || attempts >= 20) {
      clearInterval(timer);
      if (!done && !window.__testhpTwinReady) showFailure('Twin Viewport initialization timed out after 5 seconds. Open DEBUG for diagnostics.');
    }
  }, 250);

  const resizeObserver = new ResizeObserver(() => syncSize());
  resizeObserver.observe(viewport);
  window.addEventListener('beforeunload', () => {
    clearInterval(timer);
    resizeObserver.disconnect();
  }, { once: true });
})();