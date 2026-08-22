(() => {
  if (window.__testhpSpatialEvidenceWriterInstalled) return;
  window.__testhpSpatialEvidenceWriterInstalled = true;

  const EVIDENCE = 'digitalTwinEvidenceUX.v2';
  const SURFACE = 'digitalTwinHandSurface.v1';
  let syncing = false;

  const canonical = value => {
    if (!value) return null;
    const raw = typeof value === 'string'
      ? value
      : value.spatial_node_id || value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
    const aliases = {
      'hand/palm/thenar-eminence': 'hand/palm/thenar',
      'hand/palm/hypothenar-eminence': 'hand/palm/hypothenar',
      'hand/palm/central-palm-eminence': 'hand/palm/central-palm'
    };
    return aliases[String(raw).replace(/^\/+|\/+$/g, '')] || String(raw).replace(/^\/+|\/+$/g, '') || null;
  };

  const currentTarget = () => canonical(
    window.spatialViewportManager?.state?.spatialTarget ||
    window.spatialViewportManager?.active?.spatial_id ||
    window.testhpSpatialContract?.getTarget?.()?.spatial_id ||
    window.spatialEvidenceTarget ||
    window.selectedSpatialNode ||
    'hand'
  ) || 'hand';

  const levelFor = id => {
    const depth = id.split('/').filter(Boolean).length;
    return depth <= 2 ? 'macro' : depth === 3 ? 'tissue' : depth === 4 ? 'cellular' : 'cell';
  };

  const read = key => {
    try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch { return {}; }
  };

  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));

  // Stage 13 keeps its working state in one object. Make the persistence
  // boundary target-scoped, rather than allowing geometry from one target to
  // masquerade as geometry for another target.
  const originalSetItem = localStorage.setItem.bind(localStorage);
  localStorage.setItem = (key, value) => {
    if (key === SURFACE) {
      try {
        const state = JSON.parse(value || '{}');
        if (state && typeof state === 'object') {
          state.spatial_id = currentTarget();
          value = JSON.stringify(state);
        }
      } catch {}
    }
    return originalSetItem(key, value);
  };

  const dataUrlToBlob = async dataUrl => {
    const response = await fetch(dataUrl);
    return response.blob();
  };

  async function syncPreparedEvidence() {
    if (syncing) return;
    const store = read(EVIDENCE);
    const evidence = Array.isArray(store.evidence) ? store.evidence : [];
    const pending = evidence.filter(x => !x.archived && x.prepared && x.fileData === '' && !x.backendAssetId && x.preparedAsset?.dataUrl);
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
        const evidenceIndex = evidence.findIndex(x => x.id === item.id);
        if (evidenceIndex >= 0) {
          evidence[evidenceIndex] = {
            ...evidence[evidenceIndex],
            backendAssetId: payload.evidence?.asset_id || null,
            backendEvidenceId: payload.evidence?.evidence_id || null,
            canonicalSpatialId: payload.evidence?.spatial_node_id || target,
            canonicalWrite: 'explicit_prepared'
          };
        }
      }
      write(EVIDENCE, { ...store, evidence, target: currentTarget() });
      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-synced', { detail: { source: 'spatial-evidence-writer', count: pending.length } }));
    } catch (error) {
      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-write-failed', { detail: { error: String(error?.message || error) } }));
      console.warn('[Twin] canonical prepared evidence write failed', error);
    } finally {
      syncing = false;
    }
  }

  window.__testhpSyncPreparedEvidence = syncPreparedEvidence;
  window.addEventListener('testhp:evidence-attached', () => setTimeout(syncPreparedEvidence, 0));
  window.addEventListener('testhp:evidence-ux-refresh', () => setTimeout(syncPreparedEvidence, 0));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncPreparedEvidence, { once: true });
  else setTimeout(syncPreparedEvidence, 0);
})();
