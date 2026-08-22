// Canonical Evidence Registry bridge.
// Backend /api/spatial/registry is the source of truth. The browser cache is
// only a rendering cache for Evidence UX; it is never the authoritative store.
(() => {
  const STORAGE = 'digitalTwinEvidenceUX.v2';
  const BOOTSTRAP = 'digitalTwinCanonicalEvidenceBootstrap.v1';

  const toUX = (item) => {
    const spatialId = item.spatial_node_id || item.spatial_id || item.target || 'hand';
    return {
      id: item.evidence_id || item.asset_id,
      backendAssetId: item.asset_id || '',
      type: item.spatial_level === 'cellular' ? 'Cellular' : item.spatial_level === 'tissue' ? 'Tissue' : item.spatial_level === 'cell' ? 'Cellular' : item.modality === 'rna' ? 'Molecular' : 'Macro',
      sourceType: item.source === 'upload' ? 'upload' : 'dataset',
      target: spatialId,
      spatial_id: spatialId,
      subject: item.subject_id || 'own_cohort',
      timepoint: item.timepoint || 'T0',
      date: item.created_at ? String(item.created_at).slice(0, 10) : '',
      modality: item.modality || '',
      resolution: item.resolution || '',
      operator: item.operator || '',
      filename: item.filename || 'Registered observation',
      fileData: '',
      signals: Object.entries(item.signals || {}).map(([name, value]) => ({ name, value, unit: '' })),
      annotations: item.spatially_localized === false ? 'Registered at anatomical root; no deeper spatial localization has been asserted.' : '',
      comments: item.interpretation_boundary || '',
      archived: false,
      history: [{ at: item.created_at || new Date().toISOString(), action: item.attachment_status === 'explicit' ? 'spatially attached' : 'registered from ingestion registry' }],
      spatiallyLocalized: item.spatially_localized !== false,
    };
  };

  // Read-only target-focused registry snapshot for Twin debug.
  async function collectRegistryDiagnostics(target = window.spatialEvidenceTarget || window.selectedSpatialNode || 'hand') {
    const diagnostics = {
      requestedTarget: target,
      endpoint: '/api/spatial/registry?subject_id=own_cohort&timepoint=T0',
      fetchedAt: new Date().toISOString(), ok: false, status: null,
      total: 0, targetLinked: 0, prepared: 0,
      targetRecords: [], allRecords: [], error: null
    };
    try {
      const response = await fetch(diagnostics.endpoint, { cache: 'no-store' });
      diagnostics.status = response.status;
      if (!response.ok) throw new Error(`registry HTTP ${response.status}`);
      const payload = await response.json();
      const items = Array.isArray(payload.items) ? payload.items : [];
      const summarize = item => ({
        evidence_id: item.evidence_id || null,
        asset_id: item.asset_id || null,
        spatial_node_id: item.spatial_node_id || null,
        spatial_id: item.spatial_id || null,
        target: item.target || null,
        spatial_level: item.spatial_level || null,
        attachment_status: item.attachment_status || null,
        spatially_localized: item.spatially_localized ?? null,
        source: item.source || null,
        modality: item.modality || null,
        filename: item.filename || null,
        prepared: !!(item.prepared || item.prepared_asset || item.prepared_asset_id),
        prepared_asset_id: item.prepared_asset_id || item.prepared_asset?.id || null
      });
      diagnostics.total = items.length;
      diagnostics.allRecords = items.map(summarize);
      diagnostics.targetRecords = items.filter(item =>
        (item.spatial_node_id || item.spatial_id || item.target || 'hand') === target
      ).map(summarize);
      diagnostics.targetLinked = diagnostics.targetRecords.length;
      diagnostics.prepared = diagnostics.targetRecords.filter(item => item.prepared).length;
      diagnostics.ok = true;
    } catch (error) {
      diagnostics.error = { name: error.name || 'Error', message: error.message || String(error) };
    }
    window.__testhpTwinRegistryDiagnostics = diagnostics;
    window.dispatchEvent(new CustomEvent('testhp:evidence-registry-debug', { detail: diagnostics }));
    return diagnostics;
  }

  window.__testhpCollectRegistryDiagnostics = collectRegistryDiagnostics;

  // Re-run automatically whenever spatial navigation changes, so the console
  // always contains the exact registry state for the currently selected node.
  window.addEventListener('testhp:spatial-layer-changed', event => {
    const detail = event?.detail || {};
    const target = detail.spatial_id || detail.spatialId || detail.target?.spatial_id || window.spatialEvidenceTarget;
    if (target) collectRegistryDiagnostics(target).then(d => {
      console.groupCollapsed(`[Twin Registry Debug] ${target}`);
      console.log('summary', { total: d.total, targetLinked: d.targetLinked, prepared: d.prepared, status: d.status });
      console.table(d.targetRecords);
      console.log('all registry records', d.allRecords);
      console.groupEnd();
    });
  });

  async function syncCanonical() {
    try {
      const response = await fetch('/api/spatial/registry?subject_id=own_cohort&timepoint=T0', { cache: 'no-store' });
      if (!response.ok) return;
      const payload = await response.json();
      const canonical = Array.isArray(payload.items) ? payload.items : [];
      if (!canonical.length) return;

      let current = {};
      try { current = JSON.parse(localStorage.getItem(STORAGE) || '{}'); } catch {}
      const existing = Array.isArray(current.evidence) ? current.evidence : [];
      const canonicalUX = canonical.map(toUX);
      const canonicalIds = new Set(canonicalUX.map(x => x.backendAssetId || x.id));
      const manual = existing.filter(x => !canonicalIds.has(x.backendAssetId || x.id));
      const merged = [...canonicalUX, ...manual];
      const target = current.target || window.spatialEvidenceTarget || 'hand';
      localStorage.setItem(STORAGE, JSON.stringify({ evidence: merged, target }));

      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-synced', {
        detail: { count: canonical.length, evidence: canonicalUX, canonical: true }
      }));

      if (!sessionStorage.getItem(BOOTSTRAP)) {
        sessionStorage.setItem(BOOTSTRAP, '1');
        window.location.reload();
      }
    } catch (error) {
      console.warn('Canonical evidence registry sync failed', error);
    }
  }

  window.addEventListener('testhp:evidence-registry-synced', event => {
    window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh', { detail: event.detail || {} }));
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncCanonical, { once: true });
  } else {
    syncCanonical();
  }
})();
