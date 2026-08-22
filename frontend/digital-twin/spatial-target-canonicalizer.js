(() => {
  // Canonical spatial IDs are the contract shared by navigation, viewport
  // manager and evidence registry. Legacy/deep aliases must never become the
  // selected manager target, otherwise the viewport key and registry target
  // drift apart (e.g. hypothenar-eminence vs hypothenar).
  const ALIASES = new Map([
    ['hand/palm/thenar-eminence', 'hand/palm/thenar'],
    ['hand/palm/hypothenar-eminence', 'hand/palm/hypothenar'],
    ['hand/palm/central-palm-eminence', 'hand/palm/central-palm']
  ]);

  const canonical = value => {
    if (!value || typeof value !== 'string') return value;
    return ALIASES.get(value) || value;
  };

  const canonicalizeTarget = target => {
    if (!target || typeof target !== 'object') return target;
    const next = { ...target };
    for (const key of ['spatial_id', 'spatialId', 'spatial_node_id', 'targetSpatialId']) {
      if (typeof next[key] === 'string') next[key] = canonical(next[key]);
    }
    return next;
  };

  const normalizeObservedState = () => {
    const manager = window.spatialViewportManager;
    if (manager?.state && typeof manager.state === 'object') {
      if (typeof manager.state.spatialTarget === 'string') manager.state.spatialTarget = canonical(manager.state.spatialTarget);
      if (manager.state.target && typeof manager.state.target === 'object') manager.state.target = canonicalizeTarget(manager.state.target);
    }
    if (manager?.active && typeof manager.active === 'object') {
      if (typeof manager.active.spatial_id === 'string') manager.active.spatial_id = canonical(manager.active.spatial_id);
      if (typeof manager.active.spatialId === 'string') manager.active.spatialId = canonical(manager.active.spatialId);
    }

    for (const key of ['selectedSpatialNode', 'spatialEvidenceTarget', 'testhpSpatialTarget']) {
      const value = window[key];
      if (typeof value === 'string') window[key] = canonical(value);
      else if (value && typeof value === 'object') window[key] = canonicalizeTarget(value);
    }
  };

  const patchManager = manager => {
    if (!manager || manager.__testhpSpatialCanonicalizerInstalled) return;
    const original = manager.setSpatialTarget;
    if (typeof original !== 'function') return;

    manager.__testhpSpatialCanonicalizerInstalled = true;
    manager.setSpatialTarget = function(target, ...args) {
      const next = canonicalizeTarget(target);
      const result = original.call(this, next, ...args);
      normalizeObservedState();
      return result;
    };

    window.dispatchEvent(new CustomEvent('testhp:spatial-target-canonicalizer-ready', {
      detail: { aliases: Object.fromEntries(ALIASES) }
    }));
  };

  const install = () => {
    patchManager(window.spatialViewportManager);
    normalizeObservedState();
  };

  install();
  window.addEventListener('testhp:viewport-manager-ready', install);

  // Run after other spatial-layer listeners too, so a legacy writer cannot
  // leave selectedSpatialNode behind after the canonical contract updates.
  const reconcile = () => {
    patchManager(window.spatialViewportManager);
    queueMicrotask(normalizeObservedState);
    setTimeout(normalizeObservedState, 0);
  };
  window.addEventListener('testhp:spatial-layer-changed', reconcile);
  window.addEventListener('testhp:spatial-contract-changed', reconcile);
  window.addEventListener('testhp:spatial-target-changed', reconcile);

  // Some legacy writers update selectedSpatialNode/spatialEvidenceTarget after
  // the spatial-layer event without emitting another event. Keep the public
  // target globals canonical in that case as well; this is deliberately cheap
  // and prevents a late writer from reintroducing target drift.
  const reconcileTimer = setInterval(() => {
    patchManager(window.spatialViewportManager);
    normalizeObservedState();
  }, 100);
  window.addEventListener('beforeunload', () => clearInterval(reconcileTimer), { once: true });
})();
