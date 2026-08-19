(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const baseCanvas = document.getElementById('twin-canvas');
  const managerReady = () => window.spatialViewportManager;
  let installed = false;

  function install() {
    const manager = managerReady();
    if (!manager || installed) return !!manager;
    installed = true;

    const base = manager.base.bind(manager);
    const deep = manager.deep.bind(manager);

    const apply = () => {
      const level = manager.level?.() || 'macro';
      const root = manager.rootMacro?.() ?? level === 'macro';
      const active = !root;
      const baseVisible = root;
      const deepVisible = active;

      if (baseCanvas) {
        baseCanvas.style.display = baseVisible ? 'block' : 'none';
        baseCanvas.style.visibility = baseVisible ? 'visible' : 'hidden';
        baseCanvas.style.opacity = baseVisible ? '1' : '0';
        baseCanvas.style.pointerEvents = baseVisible ? 'auto' : 'none';
        baseCanvas.setAttribute('aria-hidden', baseVisible ? 'false' : 'true');
      }

      if (manager.deepCanvas) {
        manager.deepCanvas.style.display = deepVisible ? 'block' : 'none';
        manager.deepCanvas.style.visibility = deepVisible ? 'visible' : 'hidden';
        manager.deepCanvas.style.opacity = deepVisible ? '1' : '0';
        manager.deepCanvas.style.pointerEvents = deepVisible ? 'auto' : 'none';
        manager.deepCanvas.setAttribute('aria-hidden', deepVisible ? 'false' : 'true');
      }

      if (manager.deepLabels) {
        manager.deepLabels.style.display = deepVisible ? 'block' : 'none';
        manager.deepLabels.style.visibility = deepVisible ? 'visible' : 'hidden';
        manager.deepLabels.style.pointerEvents = 'none';
      }

      viewport.dataset.activeLayer = root ? 'macro' : level;
      viewport.dataset.inputOwner = root ? 'base' : 'deep';
      viewport.dataset.spatialPath = manager.path?.().join(' > ') || '';
    };

    manager.base = visible => { base(visible); apply(); };
    manager.deep = (visible, title = '') => { deep(visible, title); apply(); };

    const render = manager.render.bind(manager);
    manager.render = () => {
      const result = render();
      apply();
      return result;
    };

    manager.getViewportState = () => ({
      activeLayer: viewport.dataset.activeLayer || 'unknown',
      inputOwner: viewport.dataset.inputOwner || 'unknown',
      path: viewport.dataset.spatialPath || '',
      base: baseCanvas ? {
        display: getComputedStyle(baseCanvas).display,
        visibility: getComputedStyle(baseCanvas).visibility,
        pointerEvents: getComputedStyle(baseCanvas).pointerEvents,
        rect: (() => { const r = baseCanvas.getBoundingClientRect(); return { width: Math.round(r.width), height: Math.round(r.height) }; })()
      } : null,
      deep: manager.deepCanvas ? {
        display: getComputedStyle(manager.deepCanvas).display,
        visibility: getComputedStyle(manager.deepCanvas).visibility,
        pointerEvents: getComputedStyle(manager.deepCanvas).pointerEvents,
        rect: (() => { const r = manager.deepCanvas.getBoundingClientRect(); return { width: Math.round(r.width), height: Math.round(r.height) }; })()
      } : null
    });

    apply();
    return true;
  }

  const timer = setInterval(() => {
    if (install()) clearInterval(timer);
  }, 50);
  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
})();
