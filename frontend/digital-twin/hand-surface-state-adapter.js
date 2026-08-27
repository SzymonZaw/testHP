(() => {
  'use strict';
  const BOOT = '__testhpHandSurfaceStateAdapterBooted';
  if (window[BOOT]) return;
  window[BOOT] = true;

  const store = () => window.handSurfaceLayerState;
  const mode = () => window.testhpHandGeometryMode?.getMode?.() || 'classic';
  const measurements = () => window.testhpHandGeometryMode?.getMeasurements?.() || null;

  function syncMode() {
    const api = store();
    if (api) api.setMode(mode(), { persist: true });
  }

  function syncMeasurements() {
    const api = store();
    const data = measurements();
    if (api && data && Object.keys(data).some(k => data[k] != null && data[k] !== '')) {
      api.setMeasurements(data, { source: 'real', status: 'ready' });
    }
  }

  function syncProjection() {
    const api = store();
    const projection = window.testhpPhotoSurfaceProjection?.getPlan?.();
    if (api && projection) {
      api.setProjection(projection, {
        source: 'derived',
        status: projection.status === 'ready' ? 'ready' : 'partial'
      });
    }
  }

  async function syncEvidence() {
    const api = store();
    if (!api) return;
    const target = api.getTarget?.()?.spatial_id || 'hand';
    try {
      const r = await fetch(`/api/hand/photo-reconstruction/state?subject_id=own_cohort&timepoint=T0&spatial_id=${encodeURIComponent(target)}`, { cache: 'no-store' });
      if (!r.ok) return;
      const state = await r.json();
      for (const item of state.evidence || []) {
        api.upsertImage({
          asset_id: item.asset_id,
          evidence_id: item.evidence_id,
          view: item.registration?.view || item.view || null,
          spatial_id: item.spatial_node_id || target,
          prepared: !!item.prepared_asset,
          registered: item.registration?.status === 'registered',
          projection: item.projection || null,
          archived: item.archived === true
        });
      }
    } catch (_) {}
  }

  function syncAll() {
    if (!store()) return;
    syncMode();
    syncMeasurements();
    syncProjection();
    syncEvidence();
  }

  window.testhpHandSurfaceStateAdapter = { sync: syncAll, syncEvidence, syncProjection };
  window.addEventListener('testhp:hand-geometry-mode-changed', syncMode);
  window.addEventListener('testhp:real-hand-geometry-applied', syncMeasurements);
  window.addEventListener('testhp:surface-projection-plan-changed', syncProjection);
  window.addEventListener('testhp:evidence-registry-synced', syncEvidence);
  window.addEventListener('testhp:evidence-attached', syncEvidence);
  window.addEventListener('testhp:hand-surface-state-ready', syncAll);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(syncAll, 300), { once: true });
  else setTimeout(syncAll, 300);
})();
