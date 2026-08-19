(() => {
  const loading = document.getElementById('viewer-loading');
  const canvas = document.getElementById('twin-canvas');
  const status = document.getElementById('twin-status');
  if (!loading || !canvas) return;

  const hideLoading = (message = 'Digital Twin ready') => {
    loading.hidden = true;
    loading.setAttribute('aria-hidden', 'true');
    if (status && (!status.textContent || /starting|building/i.test(status.textContent))) {
      status.textContent = message;
    }
  };

  const showFailure = (message) => {
    loading.hidden = false;
    loading.textContent = message;
    loading.classList.add('viewer-loading-error');
    if (status) status.textContent = 'Twin Viewport error';
  };

  const report = () => {
    try {
      window.dispatchEvent(new Event('resize'));
      window.spatialViewportManager?.render?.();

      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) {
        showFailure('3D rendering is unavailable. Check WebGL support in the browser.');
        return true;
      }

      hideLoading();
      window.dispatchEvent(new CustomEvent('testhp:twin-ready', {
        detail: { width: canvas.width, height: canvas.height, renderer: 'WebGL' }
      }));
      return true;
    } catch (error) {
      console.error('[Twin Viewport] bootstrap failed', error);
      showFailure('Twin Viewport could not initialize. Open DEBUG for details.');
      window.dispatchEvent(new CustomEvent('testhp:twin-error', { detail: { error } }));
      return true;
    }
  };

  window.addEventListener('error', (event) => {
    if (event?.message) console.error('[Twin Viewport] runtime error:', event.message);
  });

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (report() || attempts >= 10) clearInterval(timer);
  }, 250);

  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
})();
