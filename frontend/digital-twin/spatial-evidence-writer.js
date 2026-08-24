(() => {
  if (window.__testhpSpatialEvidenceWriterInstalled) return;
  window.__testhpSpatialEvidenceWriterInstalled = true;

  const EVIDENCE = 'digitalTwinEvidenceUX.v2';
  const VIEW_STORE = 'digitalTwinEvidenceUX.views.v1';
  const SURFACE = 'digitalTwinHandSurface.v1';
  let syncing = false;

  const canonical = value => {
    const raw = typeof value === 'string'
      ? value
      : value?.spatial_node_id || value?.spatial_id || value?.spatialId || value?.targetSpatialId || value?.target || value?.spatialTarget || null;
    if (!raw) return null;
    const shared = window.testhpSpatialContract?.canonicalTargetId;
    if (typeof shared === 'function') return shared(raw);
    return String(raw).replace(/^\/+|\/+$/g, '').toLowerCase().replace(/_/g, '-');
  };
  const currentTarget = () => canonical(
    window.spatialViewportManager?.state?.spatialTarget ||
    window.spatialViewportManager?.active?.spatial_id ||
    window.testhpSpatialContract?.getTarget?.()?.spatial_id ||
    window.spatialEvidenceTarget || window.selectedSpatialNode || 'hand'
  ) || 'hand';
  const levelFor = id => { const depth = id.split('/').filter(Boolean).length; return depth <= 2 ? 'macro' : depth === 3 ? 'tissue' : depth === 4 ? 'cellular' : 'cell'; };
  const read = key => { try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch { return {}; } };
  const rawSetItem = localStorage.setItem.bind(localStorage);
  const rawGetItem = localStorage.getItem.bind(localStorage);

  const persistViewsFrom = evidence => {
    const saved = read(VIEW_STORE);
    const views = { ...(saved && typeof saved === 'object' ? saved : {}) };
    (Array.isArray(evidence) ? evidence : []).forEach(item => {
      if (item?.id && item.view) views[item.id] = item.view;
    });
    rawSetItem(VIEW_STORE, JSON.stringify(views));
  };

  const mergeSavedViews = evidence => {
    const saved = read(VIEW_STORE);
    if (!saved || typeof saved !== 'object') return evidence;
    return (Array.isArray(evidence) ? evidence : []).map(item => {
      if (item?.id && !item.view && saved[item.id]) return { ...item, view: saved[item.id] };
      return item;
    });
  };

  // EVIDENCE is rewritten by several parts of the UI and by the registry bridge.
  // Capture view metadata at the storage boundary, before another writer can
  // replace the UX record with a backend-shaped record that has no `view` field.
  localStorage.setItem = (key, value) => {
    if (key === EVIDENCE) {
      try {
        const incoming = JSON.parse(value || '{}');
        if (Array.isArray(incoming.evidence)) {
          persistViewsFrom(incoming.evidence);
          incoming.evidence = mergeSavedViews(incoming.evidence);
          value = JSON.stringify(incoming);
        }
      } catch {}
    }
    if (key === SURFACE) {
      try {
        const state = JSON.parse(value || '{}');
        if (state && typeof state === 'object') {
          state.spatial_id = currentTarget();
          value = JSON.stringify(state);
        }
      } catch {}
    }
    return rawSetItem(key, value);
  };

  const restoreViews = () => {
    const store = read(EVIDENCE);
    if (!Array.isArray(store.evidence)) return false;
    const restored = mergeSavedViews(store.evidence);
    const changed = restored.some((item, i) => item?.view && item.view !== store.evidence[i]?.view);
    if (changed) {
      rawSetItem(EVIDENCE, JSON.stringify({ ...store, evidence: restored }));
      window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
    }
    return changed;
  };

  const dataUrlToBlob = async dataUrl => (await fetch(dataUrl)).blob();

  async function syncPreparedEvidence() {
    if (syncing) return;
    restoreViews();
    const store = read(EVIDENCE);
    const evidence = Array.isArray(store.evidence) ? store.evidence : [];
    persistViewsFrom(evidence);
    const pending = evidence.filter(x => !x.archived && x.prepared && (x.fileData === '' || x.fileData == null) && !x.backendAssetId && x.preparedAsset?.dataUrl);
    if (!pending.length) return;

    syncing = true;
    try {
      for (const item of pending) {
        const target = canonical(item.target) || currentTarget();
        const blob = await dataUrlToBlob(item.preparedAsset.dataUrl);
        const form = new FormData();
        form.append('file', blob, `prepared-${item.id || Date.now()}.png`);
        form.append('subject_id', item.subject || 'own_cohort');
        form.append('timepoint', item.timepoint || 'T0');
        form.append('spatial_node_id', target);
        form.append('spatial_level', levelFor(target));
        form.append('modality', 'hand');
        form.append('source', 'prepared_surface');
        form.append('signals_json', '{}');
        const response = await fetch('/api/spatial/attach', { method: 'POST', body: form, cache: 'no-store' });
        if (!response.ok) throw new Error(`canonical spatial attach HTTP ${response.status}`);
        const payload = await response.json();
        const i = evidence.findIndex(x => x.id === item.id);
        if (i >= 0) evidence[i] = { ...evidence[i], target, spatial_id: target, backendAssetId: payload.evidence?.asset_id || null, backendEvidenceId: payload.evidence?.evidence_id || null, canonicalSpatialId: payload.evidence?.spatial_node_id || target, canonicalWrite: 'explicit_prepared' };
      }
      rawSetItem(EVIDENCE, JSON.stringify({ ...store, evidence, target: currentTarget(), spatial_id: currentTarget() }));
      persistViewsFrom(evidence);
      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-synced', { detail: { source: 'spatial-evidence-writer', count: pending.length, spatial_id: currentTarget() } }));
    } catch (error) {
      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-write-failed', { detail: { error: String(error?.message || error) } }));
      console.warn('[Twin] canonical prepared evidence write failed', error);
    } finally { syncing = false; }
  }

  window.__testhpSyncPreparedEvidence = syncPreparedEvidence;
  window.addEventListener('testhp:evidence-attached', () => setTimeout(syncPreparedEvidence, 0));
  window.addEventListener('testhp:evidence-ux-refresh', () => setTimeout(syncPreparedEvidence, 0));
  window.addEventListener('testhp:spatial-layer-changed', () => setTimeout(syncPreparedEvidence, 0));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncPreparedEvidence, { once: true });
  else setTimeout(syncPreparedEvidence, 0);
})();
