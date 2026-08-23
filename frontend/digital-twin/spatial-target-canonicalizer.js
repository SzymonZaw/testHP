(() => {
  // Stage 1-5: canonical spatial identity is owned by spatial-contract.js.
  // This file is only a compatibility bridge for legacy callers. It must not
  // maintain a second target state, poll the DOM, or create a reconciliation loop.
  const contract = () => window.testhpSpatialContract;

  const canonical = value => {
    const api = contract();
    if (api?.normalizeId) return api.normalizeId(value);
    return String(value ?? '').trim().toLowerCase();
  };

  const canonicalizeTarget = target => {
    if (!target || typeof target !== 'object') return target;
    const next = { ...target };
    const raw = next.spatial_id || next.spatialId || next.spatial_node_id || next.targetSpatialId || next.id;
    const id = canonical(raw);
    if (id) {
      next.spatial_id = id;
      next.spatialId = id;
      next.spatial_node_id = id;
      next.targetSpatialId = id;
    }
    return next;
  };

  const reconcile = () => {
    const api = contract();
    if (api?.reconcile) api.reconcile();
    const manager = window.spatialViewportManager;
    if (manager && typeof manager === 'object') {
      const id = canonical(
        manager?.state?.spatial_id || manager?.state?.spatialId ||
        manager?.active?.spatial_id || manager?.active?.spatialId ||
        manager?.spatialTarget
      );
      if (id) {
        if (manager.state && typeof manager.state === 'object') {
          manager.state.spatial_id = id;
          manager.state.spatialId = id;
          manager.state.spatialTarget = id;
        }
        manager.spatialTarget = id;
      }
    }
  };

  const install = () => {
    reconcile();
    if (!window.spatialViewportManager || window.spatialViewportManager.__testhpSpatialCanonicalizerInstalled) return;
    const manager = window.spatialViewportManager;
    const original = manager.setSpatialTarget;
    if (typeof original !== 'function') return;
    manager.__testhpSpatialCanonicalizerInstalled = true;
    manager.setSpatialTarget = function(target, ...args) {
      const next = canonicalizeTarget(target);
      const result = original.call(this, next, ...args);
      reconcile();
      return result;
    };
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-canonicalizer-ready', {
      detail: { source: 'spatial-contract', canonical: true }
    }));
  };

  install();
  window.addEventListener('testhp:spatial-contract-changed', reconcile);
  window.addEventListener('testhp:spatial-layer-changed', reconcile);
  window.addEventListener('testhp:spatial-target-changed', reconcile);
  window.addEventListener('testhp:viewport-manager-ready', install);
})();