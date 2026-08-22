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

  const patchManager = manager => {
    if (!manager || manager.__testhpSpatialCanonicalizerInstalled) return;
    const original = manager.setSpatialTarget;
    if (typeof original !== 'function') return;

    manager.__testhpSpatialCanonicalizerInstalled = true;
    manager.setSpatialTarget = function(target, ...args) {
      const next = canonicalizeTarget(target);
      const result = original.call(this, next, ...args);

      // Keep all externally inspected manager state on the same canonical ID.
      if (this.state && typeof this.state === 'object') {
        if (typeof this.state.spatialTarget === 'string') this.state.spatialTarget = canonical(this.state.spatialTarget);
        if (this.state.target && typeof this.state.target === 'object') this.state.target = canonicalizeTarget(this.state.target);
      }
      if (this.active && typeof this.active === 'object') {
        if (typeof this.active.spatial_id === 'string') this.active.spatial_id = canonical(this.active.spatial_id);
        if (typeof this.active.spatialId === 'string') this.active.spatialId = canonical(this.active.spatialId);
      }
      return result;
    };

    window.dispatchEvent(new CustomEvent('testhp:spatial-target-canonicalizer-ready', {
      detail: { aliases: Object.fromEntries(ALIASES) }
    }));
  };

  const install = () => patchManager(window.spatialViewportManager);
  install();
  window.addEventListener('testhp:viewport-manager-ready', install);

  // The manager may publish a legacy target before this bridge gets installed.
  // Normalize that state as soon as the spatial layer changes as well.
  window.addEventListener('testhp:spatial-layer-changed', () => {
    const manager = window.spatialViewportManager;
    patchManager(manager);
    if (!manager) return;
    if (manager.state && typeof manager.state === 'object') {
      if (typeof manager.state.spatialTarget === 'string') manager.state.spatialTarget = canonical(manager.state.spatialTarget);
    }
  });
})();
