(() => {
  const PARAMS = ['palmLength','palmWidth','thickness','fingerSpread','taper','thumbAngle'];
  const FINGERS = ['index','middle','ring','little'];
  const base = new WeakMap();
  let lastRoot = null;
  let installed = false;
  let timer = 0;

  const getActive = () => window.spatialViewportManager?.active || null;
  const getRoot = () => {
    const active = getActive();
    return active?.root || active?.scene?.getObjectByName?.('macro-hand-root') || active?.scene || null;
  };
  const getMeshes = () => {
    const root = getRoot();
    const result = new Map();
    if (!root) return result;
    const visit = object => {
      if (!object || result.size >= 6) return;
      const name = String(object.name || '').replace(/^skin:/, '');
      if (['palm', ...FINGERS, 'thumb'].includes(name) && object.isMesh) result.set(name, object);
      object.children?.forEach(visit);
    };
    visit(root);
    return result;
  };
  const capture = mesh => {
    if (!base.has(mesh)) base.set(mesh, { p: mesh.position.clone(), s: mesh.scale.clone(), r: mesh.rotation.clone() });
    return base.get(mesh);
  };
  const read = () => {
    const state = window.digitalTwinGeometry?.getState?.() || {};
    return Object.fromEntries(PARAMS.map(k => [k, Number(state[k]) || 1]));
  };
  const apply = () => {
    const meshes = getMeshes();
    if (!meshes.size) return false;
    const root = getRoot();
    if (root !== lastRoot) lastRoot = root;
    const g = read();
    const palm = meshes.get('palm');
    if (palm) {
      const b = capture(palm);
      palm.position.copy(b.p);
      palm.scale.set(b.s.x * g.palmWidth, b.s.y * g.palmLength, b.s.z * g.thickness);
    }
    FINGERS.forEach((name, index) => {
      const mesh = meshes.get(name);
      if (!mesh) return;
      const b = capture(mesh);
      mesh.position.set(b.p.x + (index - 1.5) * .2 * (g.fingerSpread - 1), b.p.y, b.p.z);
      const width = 1 - .22 * (g.taper - 1);
      mesh.scale.set(b.s.x * width, b.s.y, b.s.z * g.thickness);
      mesh.rotation.copy(b.r);
    });
    const thumb = meshes.get('thumb');
    if (thumb) {
      const b = capture(thumb);
      thumb.position.copy(b.p);
      thumb.rotation.copy(b.r);
      thumb.rotation.z = b.r.z - .42 * (g.thumbAngle - 1);
      thumb.scale.set(b.s.x * (1 - .1 * (g.taper - 1)), b.s.y, b.s.z * g.thickness);
    }
    const active = getActive();
    if (active?.renderer && active.scene && active.camera) {
      try { active.renderer.render(active.scene, active.camera); } catch {}
    }
    return true;
  };
  const schedule = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      apply();
      window.dispatchEvent(new CustomEvent('testhp:geometry-stability-synced'));
    }, 0);
  };
  const wrapApi = () => {
    const api = window.digitalTwinGeometry;
    if (!api || api.__geometryStabilityWrapped) return !!api;
    const originalSetParameter = api.setParameter?.bind(api);
    if (originalSetParameter) api.setParameter = (key, value) => { const result = originalSetParameter(key, value); schedule(); return result; };
    const originalSetState = api.setState?.bind(api);
    if (originalSetState) api.setState = next => { const result = originalSetState(next); schedule(); return result; };
    const originalReset = api.reset?.bind(api);
    if (originalReset) api.reset = () => { const result = originalReset(); schedule(); return result; };
    api.__geometryStabilityWrapped = true;
    schedule();
    return true;
  };
  const boot = () => {
    if (installed) return;
    installed = true;
    const observer = new MutationObserver(() => { wrapApi(); schedule(); });
    if (document.body) observer.observe(document.body, { childList: true, subtree: true });
    ['testhp:viewport-manager-ready','testhp:deep-3d-active','testhp:spatial-layer-changed','testhp:hand-surface-geometry-changed'].forEach(name => window.addEventListener(name, () => { wrapApi(); schedule(); }));
    [0,100,300,800,1500,3000].forEach(ms => setTimeout(() => { wrapApi(); apply(); }, ms));
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true}); else boot();
})();
