// Canonical Evidence Registry bridge.
// Backend /api/spatial/registry is the source of truth. The browser cache is
// only a rendering cache for Evidence UX; it is never the authoritative store.
(() => {
  const STORAGE = 'digitalTwinEvidenceUX.v2';
  const BOOTSTRAP = 'digitalTwinCanonicalEvidenceBootstrap.v1';
  const DEBUG = '[testhp:evidence-target-debug]';
  const ALIASES = new Map([['hypothenar-eminence', 'hypothenar'], ['thenar-eminence', 'thenar'], ['central-palm-region', 'central-palm']]);

  const canonicalTargetId = value => {
    const raw = value == null ? '' : String(value).trim().replace(/^\/+|\/+$/g, '');
    if (!raw) return 'hand';
    const parts = raw.split('/').filter(Boolean).map(part => ALIASES.get(part) || part);
    if (parts[0] !== 'hand') parts.unshift('hand');
    return parts.join('/');
  };

  const debug = (phase, detail = {}) => {
    if (!window.__testhpDiagnosticsInstalled && !window.__testhpSpatialWriterDebugInstalled) return;
    const payload = { phase, t: Math.round(performance.now()), ...detail };
    console.debug(DEBUG, payload);
    window.dispatchEvent(new CustomEvent('testhp:evidence-target-debug', { detail: payload }));
    window.dispatchEvent(new CustomEvent('testhp:diagnostic', { detail: { type: 'evidence-target', ...payload } }));
  };

  const normalizeTarget = value => canonicalTargetId(value);

  const targetMatches = (record, target) => {
    const recordTarget = normalizeTarget(record?.spatial_node_id ?? record?.spatialId ?? record?.target);
    const wanted = normalizeTarget(target);
    const match = !!wanted && recordTarget === wanted;
    debug(match ? 'MATCH' : 'REJECT', {
      target: wanted,
      recordId: record?.evidence_id || record?.asset_id || record?.id || null,
      recordTarget,
      targetFields: { spatial_node_id: record?.spatial_node_id ?? null, spatialId: record?.spatialId ?? null, target: record?.target ?? null },
      reason: !recordTarget ? 'missing-record-target' : !wanted ? 'missing-requested-target' : 'canonical-spatial-target-mismatch',
    });
    return match;
  };

  const toUX = item => ({
    id: item.evidence_id || item.asset_id,
    backendAssetId: item.asset_id || '',
    type: item.spatial_level === 'cellular' ? 'Cellular' : item.spatial_level === 'tissue' ? 'Tissue' : item.spatial_level === 'cell' ? 'Cellular' : item.modality === 'rna' ? 'Molecular' : 'Macro',
    sourceType: item.source === 'upload' ? 'upload' : 'dataset',
    target: item.spatial_node_id || 'hand',
    spatial_node_id: item.spatial_node_id || '',
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
  });

  async function syncCanonical() {
    try {
      const rawTarget = window.spatialEvidenceTarget || window.selectedSpatialNode || document.body.dataset.spatialTarget || 'hand';
      const target = normalizeTarget(rawTarget);
      if (rawTarget !== target) window.spatialEvidenceTarget = target;
      const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', debug: 'true', spatial_node_id: target });
      debug('REGISTRY_MATCH_REQUEST', { rawTarget, target, url: `/api/spatial/registry?${params.toString()}` });
      const response = await fetch(`/api/spatial/registry?${params.toString()}`, { cache: 'no-store' });
      debug('REGISTRY_FETCH', { ok: response.ok, status: response.status, target });
      if (!response.ok) return;
      const payload = await response.json();
      const canonical = Array.isArray(payload.items) ? payload.items : [];
      debug('REGISTRY_PAYLOAD', { count: canonical.length, target, targets: canonical.map(item => ({ id: item.evidence_id || item.asset_id || null, spatial_node_id: item.spatial_node_id || null })) });
      if (payload.debug) {
        debug('REGISTRY_MATCH_DIAGNOSTICS', payload.debug);
        payload.debug.records?.filter(record => !record.matched).forEach(record => debug('REGISTRY_REJECT', record));
      }
      if (!canonical.length) {
        debug('REGISTRY_TARGET_EMPTY', { target, rejected: payload.debug?.rejected ?? null, totalSubjectTimepointRecords: payload.debug?.total_subject_timepoint_records ?? null });
        return;
      }

      let current = {};
      try { current = JSON.parse(localStorage.getItem(STORAGE) || '{}'); } catch {}
      const existing = Array.isArray(current.evidence) ? current.evidence : [];
      const canonicalUX = canonical.map(toUX);
      const canonicalIds = new Set(canonicalUX.map(x => x.backendAssetId || x.id));
      const manual = existing.filter(x => !canonicalIds.has(x.backendAssetId || x.id));
      const merged = [...canonicalUX, ...manual];
      localStorage.setItem(STORAGE, JSON.stringify({ evidence: merged, target }));

      window.dispatchEvent(new CustomEvent('testhp:evidence-registry-synced', { detail: { count: canonical.length, evidence: canonicalUX, canonical: true, target, registryDebug: payload.debug || null } }));

      if (!sessionStorage.getItem(BOOTSTRAP)) {
        sessionStorage.setItem(BOOTSTRAP, '1');
        window.location.reload();
      }
    } catch (error) {
      console.warn('Canonical evidence registry sync failed', error);
      debug('REGISTRY_ERROR', { error: String(error?.stack || error) });
    }
  }

  const installSpatialWriterTrace = () => {
    if (window.__testhpEvidenceTargetWriterTraceInstalled) return true;
    const manager = window.spatialViewportManager;
    if (!manager || typeof manager.setSpatialTarget !== 'function') return false;
    const original = manager.setSpatialTarget;
    manager.setSpatialTarget = function (...args) {
      debug('SPATIAL_WRITER_CALL', { args, before: { activeKey: manager.activeKey, activeLayer: manager.activeLayer, target: manager.state?.target || manager.state?.spatialTarget || null }, stack: new Error('setSpatialTarget writer').stack });
      const result = original.apply(this, args);
      debug('SPATIAL_WRITER_RESULT', { args, after: { activeKey: manager.activeKey, activeLayer: manager.activeLayer, target: manager.state?.target || manager.state?.spatialTarget || null } });
      return result;
    };
    window.__testhpEvidenceTargetWriterTraceInstalled = true;
    debug('WRITER_TRACE_INSTALLED', { managerKeys: Object.keys(manager) });
    return true;
  };

  window.__testhpEvidenceTargetMatches = targetMatches;
  window.__testhpCanonicalSpatialId = canonicalTargetId;
  window.__testhpInstallEvidenceTargetWriterTrace = installSpatialWriterTrace;
  window.addEventListener('testhp:viewport-manager-ready', installSpatialWriterTrace);
  window.addEventListener('testhp:evidence-registry-synced', event => window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh', { detail: event.detail || {} })));

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => { installSpatialWriterTrace(); syncCanonical(); }, { once: true });
  else { installSpatialWriterTrace(); syncCanonical(); }
})();
