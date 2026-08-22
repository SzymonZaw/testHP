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

      // Evidence UX reads its cache during bootstrap. If the cache had to be
      // replaced, perform exactly one bootstrap reload. A persistent session
      // marker prevents the reload loop that previously occurred here.
      if (!sessionStorage.getItem(BOOTSTRAP)) {
        sessionStorage.setItem(BOOTSTRAP, '1');
        window.location.reload();
      }
    } catch (error) {
      console.warn('Canonical evidence registry sync failed', error);
    }
  }

  window.addEventListener('testhp:evidence-registry-synced', (event) => {
    window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh', { detail: event.detail || {} }));
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncCanonical, { once: true });
  } else {
    syncCanonical();
  }
})();
