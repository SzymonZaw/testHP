(() => {
  const PARAMS = ['palmLength','palmWidth','thickness','fingerSpread','taper','thumbAngle'];
  const clone = value => Object.fromEntries(PARAMS.map(key => [key, Number(value?.[key] ?? 1)]));

  const install = () => {
    const api = window.digitalTwinGeometry;
    const manager = window.spatialViewportManager;
    if (!api || !manager?.render) return false;
    if (api.__mainViewportGeometryBridge) return true;

    const originalSetState = api.setState?.bind(api);
    const originalSetParameter = api.setParameter?.bind(api);
    if (!originalSetState && !originalSetParameter) return false;

    const sync = reason => {
      const state = clone(api.getState?.() || {});
      // The canonical viewport renderer owns the main scene. Keep geometry
      // changes on the same API, then explicitly redraw the active main view.
      try {
        manager.deep?.userData && (manager.deep.userData.digitalTwinGeometry = state);
        manager.active?.scene?.userData && (manager.active.scene.userData.digitalTwinGeometry = state);
      } catch {}
      try { manager.render(); } catch (error) { console.warn('[geometry→main] render failed', error); }
      window.dispatchEvent(new CustomEvent('testhp:main-geometry-synced', { detail: { reason, geometry: state } }));
    };

    if (originalSetState) {
      const wrapped = function (state, ...rest) {
        const result = originalSetState(state, ...rest);
        sync('setState');
        return result;
      };
      wrapped.__mainViewportGeometryBridgeWrapped = true;
      api.setState = wrapped;
    }
    if (originalSetParameter) {
      const wrapped = function (key, value, ...rest) {
        const result = originalSetParameter(key, value, ...rest);
        sync(`setParameter:${key}`);
        return result;
      };
      wrapped.__mainViewportGeometryBridgeWrapped = true;
      api.setParameter = wrapped;
    }

    api.__mainViewportGeometryBridge = true;
    sync('boot');
    return true;
  };

  const boot = () => {
    let tries = 0;
    const timer = setInterval(() => {
      if (install() || ++tries > 80) clearInterval(timer);
    }, 250);
    install();
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
