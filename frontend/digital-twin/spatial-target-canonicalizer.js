(() => {
  // Canonical spatial IDs are the contract shared by navigation, viewport
  // manager, DOM compatibility state and evidence registry. Legacy/deep
  // aliases must never become the selected manager target, otherwise the
  // viewport key and registry target drift apart (e.g. hypothenar-eminence vs hypothenar).
  const ALIASES = new Map([
    ['hand/palm/thenar-eminence', 'hand/palm/thenar'],
    ['hand/palm/hypothenar-eminence', 'hand/palm/hypothenar'],
    ['hand/palm/central-palm-eminence', 'hand/palm/central-palm']
  ]);

  const canonical = value => {
    if (!value || typeof value !== 'string') return value;
    if (ALIASES.has(value)) return ALIASES.get(value);

    // Canonicalize descendants as well, not only the exact legacy node.
    // Example:
    // hand/palm/hypothenar-eminence/hypothenar-field-a
    // -> hand/palm/hypothenar/hypothenar-field-a
    for (const [legacy, target] of ALIASES) {
      if (value.startsWith(`${legacy}/`)) {
        return `${target}${value.slice(legacy.length)}`;
      }
    }
    return value;
  };

  const canonicalizeTarget = target => {
    if (!target || typeof target !== 'object') return target;
    const next = { ...target };
    for (const key of ['spatial_id', 'spatialId', 'spatial_node_id', 'targetSpatialId']) {
      if (typeof next[key] === 'string') next[key] = canonical(next[key]);
    }
    return next;
  };

  const managerCanonicalTarget = manager => {
    const state = manager?.state;
    const candidates = [
      state?.spatial_id,
      state?.spatialId,
      state?.spatialTarget,
      state?.targetSpatialId,
      manager?.active?.spatial_id,
      manager?.active?.spatialId
    ];
    return candidates.map(value => canonical(typeof value === 'object' ? (value?.spatial_id || value?.spatialId || value?.targetSpatialId) : value))
      .find(value => typeof value === 'string' && value);
  };

  const normalizeObservedState = () => {
    const manager = window.spatialViewportManager;
    if (manager?.state && typeof manager.state === 'object') {
      if (typeof manager.state.spatialTarget === 'string') manager.state.spatialTarget = canonical(manager.state.spatialTarget);
      if (typeof manager.state.spatial_id === 'string') manager.state.spatial_id = canonical(manager.state.spatial_id);
      if (typeof manager.state.spatialId === 'string') manager.state.spatialId = canonical(manager.state.spatialId);
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

    const body = document.body;
    if (body?.dataset) {
      const currentBodyTarget = canonical(body.dataset.spatialTarget);
      const chosenTarget = managerCanonicalTarget(manager)
        || canonical(typeof window.selectedSpatialNode === 'string' ? window.selectedSpatialNode : window.selectedSpatialNode?.spatial_id || window.selectedSpatialNode?.spatialId)
        || canonical(typeof window.spatialEvidenceTarget === 'string' ? window.spatialEvidenceTarget : window.spatialEvidenceTarget?.spatial_id || window.spatialEvidenceTarget?.spatialId)
        || currentBodyTarget;
      if (chosenTarget && currentBodyTarget !== chosenTarget) body.dataset.spatialTarget = chosenTarget;
      else if (currentBodyTarget && body.dataset.spatialTarget !== currentBodyTarget) body.dataset.spatialTarget = currentBodyTarget;
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

  const reconcile = () => {
    patchManager(window.spatialViewportManager);
    queueMicrotask(normalizeObservedState);
    setTimeout(normalizeObservedState, 0);
  };
  window.addEventListener('testhp:spatial-layer-changed', reconcile);
  window.addEventListener('testhp:spatial-contract-changed', reconcile);
  window.addEventListener('testhp:spatial-target-changed', reconcile);

  const bodyObserver = new MutationObserver(() => normalizeObservedState());
  const observeBody = () => {
    if (!document.body) return;
    bodyObserver.observe(document.body, { attributes: true, attributeFilter: ['data-spatial-target'] });
  };
  if (document.body) observeBody();
  else document.addEventListener('DOMContentLoaded', observeBody, { once: true });

  const reconcileTimer = setInterval(() => {
    patchManager(window.spatialViewportManager);
    normalizeObservedState();
  }, 100);
  window.addEventListener('beforeunload', () => {
    clearInterval(reconcileTimer);
    bodyObserver.disconnect();
  }, { once: true });
})();
