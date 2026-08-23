(() => {
  // Optional authoritative-target diagnostics. This module must never block
  // viewport startup, so it only observes the current canonical target.
  const normalize = value => String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
  const canonical = value => {
    const api = window.testhpSpatialContract;
    if (api?.normalizeId) return api.normalizeId(value);
    const raw = normalize(value);
    return ({ palm: 'hand/palm', 'śródręcze': 'hand/palm', srodrecze: 'hand/palm' })[raw] || raw;
  };
  const inspect = () => {
    const manager = window.spatialViewportManager;
    const state = manager?.state || {};
    const active = manager?.active || {};
    const target = canonical(
      active.spatial_node_id || active.spatial_id || active.spatialId ||
      state.spatial_node_id || state.spatial_id || state.spatialId ||
      window.selectedSpatialNode || window.spatialEvidenceTarget || 'hand'
    );
    const detail = {
      target,
      selectedSpatialNode: canonical(window.selectedSpatialNode),
      spatialEvidenceTarget: canonical(window.spatialEvidenceTarget),
      managerVersion: manager?.version || null,
      activeKey: manager?.activeKey || null
    };
    window.__testhpSpatialTargetDriftDiagnostics = detail;
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-drift-debug', { detail }));
    return detail;
  };
  const schedule = () => queueMicrotask(inspect);
  inspect();
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-target-changed', schedule);
  window.addEventListener('testhp:viewport-manager-ready', schedule);
})();
