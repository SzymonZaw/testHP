// Canonical Evidence Registry bridge.
(() => {
  const STORAGE = 'digitalTwinEvidenceUX.v2';
  const BOOTSTRAP = 'digitalTwinCanonicalEvidenceBootstrap.v1';
  const CANONICAL_DEEP_IDS = new Map([
    ['hand/palm/thenar-eminence', 'hand/palm/thenar'],
    ['hand/palm/hypothenar-eminence', 'hand/palm/hypothenar'],
    ['hand/palm/central-palm-eminence', 'hand/palm/central-palm']
  ]);
  const canonicalSpatialId = value => {
    if (!value) return null;
    const raw = typeof value === 'string' ? value : value.spatial_node_id || value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
    if (!raw || typeof raw !== 'string') return raw;
    return CANONICAL_DEEP_IDS.get(raw) || raw;
  };
  const syncManagerTarget = target => {
    const canonical = canonicalSpatialId(target);
    const manager = window.spatialViewportManager;
    if (canonical && manager?.state && typeof manager.state === 'object') manager.state.spatialTarget = canonical;
    return canonical;
  };
  const registryCandidates = target => {
    const canonical = canonicalSpatialId(target); if (!canonical) return [];
    const aliases = [...CANONICAL_DEEP_IDS.entries()].filter(([, value]) => value === canonical).map(([key]) => key);
    return [...new Set([canonical, ...aliases])];
  };
  const toUX = item => ({ id: item.asset_id || item.evidence_id, evidenceId: item.evidence_id || '', backendAssetId: item.asset_id || '', type: item.spatial_level === 'tissue' ? 'Tissue' : item.spatial_level === 'cellular' || item.spatial_level === 'cell' ? 'Cellular' : item.modality === 'rna' ? 'Molecular' : 'Macro', sourceType: item.source === 'upload' ? 'upload' : 'dataset', target: canonicalSpatialId(item.spatial_node_id || item.spatial_id || item.target) || 'hand', spatial_id: canonicalSpatialId(item.spatial_node_id || item.spatial_id || item.target) || 'hand', subject: item.subject_id || 'own_cohort', timepoint: item.timepoint || 'T0', date: item.created_at ? String(item.created_at).slice(0, 10) : '', modality: item.modality || '', resolution: item.resolution || '', operator: item.operator || '', filename: item.filename || 'Registered observation', fileData: '', signals: Object.entries(item.signals || {}).map(([name, value]) => ({ name, value, unit: '' })), annotations: item.spatially_localized === false ? 'Registered at anatomical root; no deeper spatial localization has been asserted.' : '', comments: item.interpretation_boundary || '', archived: false, history: [{ at: item.created_at || new Date().toISOString(), action: item.attachment_status === 'explicit' ? 'spatially attached' : 'registered from ingestion registry' }], spatiallyLocalized: item.spatially_localized !== false });

  function renderDiagnostics(d) {
    const studio = document.getElementById('hand-surface-studio'); if (!studio) return;
    let panel = document.getElementById('testhp-registry-debug-panel');
    if (!panel) { panel = document.createElement('section'); panel.id = 'testhp-registry-debug-panel'; panel.style.cssText = 'margin-top:14px;border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff);font-size:13px'; studio.appendChild(panel); }
    const rejected = d.matchDebug?.rejected || [], accepted = d.matchDebug?.accepted || [];
    const rows = (d.matchDebug?.decisions || []).map(x => `<tr><td style="padding:5px 7px;font-weight:700">${x.matched ? 'ACCEPT' : 'REJECT'}</td><td style="padding:5px 7px"><code>${canonicalSpatialId(x.actual_spatial_node_id) || 'NULL'}</code></td><td style="padding:5px 7px"><code>${canonicalSpatialId(x.expected_spatial_node_id) || 'NULL'}</code></td><td style="padding:5px 7px">${x.reason || '—'}</td><td style="padding:5px 7px">${x.attachment_status || '—'}</td><td style="padding:5px 7px">${x.filename || x.evidence_id || '—'}</td></tr>`).join('');
    const sourceWarning = d.matchDebug?.sourceWarning ? `<div style="margin-top:8px;padding:8px;border:1px dashed var(--border,#d8dee8)">${d.matchDebug.sourceWarning}</div>` : '';
    panel.innerHTML = `<div style="display:flex;justify-content:space-between;gap:10px;align-items:center"><strong>REGISTRY / CACHE MISMATCH DIAGNOSTICS</strong><span style="font-size:11px;font-weight:700">${d.ok ? 'READY' : 'ERROR'}</span></div><div style="margin-top:8px">Target: <code>${d.requestedTarget || '—'}</code> · scoped: <b>${d.total}</b> · accepted: <b>${accepted.length}</b> · rejected: <b>${rejected.length}</b> · target-linked: <b>${d.targetLinked}</b></div>${sourceWarning}${d.error ? `<div style="margin-top:8px">${d.error.name}: ${d.error.message}</div>` : `<div style="margin-top:10px;overflow:auto"><table style="width:100%;border-collapse:collapse"><thead><tr><th align="left">Decision</th><th align="left">Actual</th><th align="left">Expected</th><th align="left">Reason</th><th align="left">Attachment</th><th align="left">Evidence</th></tr></thead><tbody>${rows || '<tr><td colspan="6" style="padding:8px">No records in subject/timepoint scope.</td></tr>'}</tbody></table></div>`}`;
  }

  const summarize = item => ({ evidence_id: item.evidence_id || null, asset_id: item.asset_id || null, spatial_node_id: canonicalSpatialId(item.spatial_node_id) || null, spatial_id: canonicalSpatialId(item.spatial_id) || null, target: canonicalSpatialId(item.target) || null, spatial_level: item.spatial_level || null, attachment_status: item.attachment_status || null, spatially_localized: item.spatially_localized ?? null, source: item.source || null, modality: item.modality || null, filename: item.filename || null, prepared: !!(item.prepared || item.prepared_asset || item.prepared_asset_id), prepared_asset_id: item.prepared_asset_id || item.prepared_asset?.id || null });
  const localDecision = (item, target) => { const actual = canonicalSpatialId(item.spatial_node_id); const expected = canonicalSpatialId(target); const matched = actual === expected; let reason = 'SPATIAL_ID_MISMATCH'; if (matched) reason = 'EXACT_SPATIAL_ID_MATCH'; else if (actual === 'hand' && String(expected).startsWith('hand/')) reason = 'ROOT_ONLY_REGISTERED_ASSET_NOT_DEEP_ATTACHED'; else if (!actual) reason = 'MISSING_SPATIAL_NODE_ID'; return { ...summarize(item), expected_spatial_node_id: expected, actual_spatial_node_id: actual, matched, reason }; };

  async function collectRegistryDiagnostics(target = resolveCanonicalTarget()) {
    target = syncManagerTarget(target) || 'hand'; window.spatialEvidenceTarget = target;
    const candidates = registryCandidates(target); const encodedTarget = encodeURIComponent(String(target));
    const endpoint = `/api/spatial/registry?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodedTarget}&debug=true`;
    const diagnostics = { requestedTarget: target, endpoint, fetchedAt: new Date().toISOString(), ok: false, status: null, total: 0, targetLinked: 0, prepared: 0, targetRecords: [], allRecords: [], matchDebug: null, error: null };
    try {
      let response = await fetch(endpoint, { cache: 'no-store' }); diagnostics.status = response.status; if (!response.ok) throw new Error(`registry HTTP ${response.status}`);
      let payload = await response.json(); let items = Array.isArray(payload.items) ? payload.items : []; let decisions = Array.isArray(payload.debug?.decisions) ? payload.debug.decisions : []; let aliasUsed = null;
      if (!items.length && candidates.length > 1) {
        for (const candidate of candidates.slice(1)) {
          const aliasEndpoint = `/api/spatial/registry?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodeURIComponent(candidate)}&debug=true`;
          const aliasResponse = await fetch(aliasEndpoint, { cache: 'no-store' }); if (!aliasResponse.ok) continue;
          const aliasPayload = await aliasResponse.json(); const aliasItems = Array.isArray(aliasPayload.items) ? aliasPayload.items : [];
          if (aliasItems.length) { items = aliasItems; decisions = aliasItems.map(item => localDecision(item, target)); aliasUsed = candidate; break; }
        }
      }
      if (!payload.debug || !Array.isArray(payload.debug.decisions)) {
        const fallbackEndpoint = '/api/spatial/registry?subject_id=own_cohort&timepoint=T0'; const fallbackResponse = await fetch(fallbackEndpoint, { cache: 'no-store' });
        if (fallbackResponse.ok) { const fallbackPayload = await fallbackResponse.json(); const scopedItems = Array.isArray(fallbackPayload.items) ? fallbackPayload.items : []; decisions = scopedItems.map(item => localDecision(item, target)); diagnostics.matchDebug = { sourceWarning: 'SERVER DEBUG PAYLOAD UNAVAILABLE — decisions reconstructed locally from the unfiltered canonical registry. Deploy/restart the backend branch to get server-side decision tracing.', fallbackEndpoint }; }
        else diagnostics.matchDebug = { sourceWarning: `SERVER DEBUG PAYLOAD UNAVAILABLE and fallback registry request failed (HTTP ${fallbackResponse.status}).` };
      }
      diagnostics.total = payload.debug?.scoped_count ?? decisions.length; diagnostics.allRecords = decisions.map(summarize); diagnostics.targetRecords = items.map(summarize); diagnostics.targetLinked = diagnostics.targetRecords.length; diagnostics.prepared = diagnostics.targetRecords.filter(item => item.prepared).length;
      diagnostics.matchDebug = { ...(diagnostics.matchDebug || {}), ...(payload.debug || {}), decisions, accepted: decisions.filter(d => d.matched), rejected: decisions.filter(d => !d.matched), rejectedCount: decisions.filter(d => !d.matched).length, target, aliasUsed }; diagnostics.total = Math.max(diagnostics.total, decisions.length); diagnostics.ok = true;
    } catch (error) { diagnostics.error = { name: error.name || 'Error', message: error.message || String(error) }; }
    window.__testhpTwinRegistryDiagnostics = diagnostics; renderDiagnostics(diagnostics); window.dispatchEvent(new CustomEvent('testhp:evidence-registry-debug', { detail: diagnostics })); return diagnostics;
  }

  function resolveCanonicalTarget() {
    const manager = window.spatialViewportManager, activeKey = manager?.activeKey || '', managerState = manager?.state || {}, active = manager?.active || {};
    const managerTarget = canonicalSpatialId(active?.spatial_id || active?.spatialId || managerState?.spatial_id || managerState?.spatialId || managerState?.target?.spatial_id || managerState?.target?.spatialId);
    const contractTarget = canonicalSpatialId(window.testhpSpatialContract?.current?.spatial_id || window.testhpSpatialContract?.current?.spatialId);
    const explicitViewportTarget = canonicalSpatialId(window.__testhpSpatialState?.spatial_id || window.__testhpSpatialState?.spatialId || window.__testhpDiagnostics?.spatial_id);
    const legacyTarget = canonicalSpatialId(window.spatialEvidenceTarget || window.selectedSpatialNode);
    if (managerTarget) return managerTarget; if (contractTarget) return contractTarget; if (explicitViewportTarget) return explicitViewportTarget;
    if (activeKey) { const match = activeKey.match(/^(?:macro|tissue|cell|cellular)\|(.+)$/); if (match?.[1]) return canonicalSpatialId(match[1].includes('/') ? match[1] : null); }
    return legacyTarget || 'hand';
  }

  window.__testhpCollectRegistryDiagnostics = collectRegistryDiagnostics; window.__testhpResolveCanonicalRegistryTarget = resolveCanonicalTarget;
  const debugCurrentTarget = () => collectRegistryDiagnostics(resolveCanonicalTarget()).then(d => { console.groupCollapsed(`[Twin Registry Debug] ${d.requestedTarget}`); console.log('summary', { total: d.total, targetLinked: d.targetLinked, prepared: d.prepared, rejected: d.matchDebug?.rejectedCount ?? 0, status: d.status, endpoint: d.endpoint, aliasUsed: d.matchDebug?.aliasUsed || null }); console.table(d.matchDebug?.decisions || d.targetRecords); console.log('accepted', d.matchDebug?.accepted || []); console.log('rejected', d.matchDebug?.rejected || []); console.groupEnd(); });
  const onSpatialChange = event => { const detail = event?.detail || {}; const target = syncManagerTarget(detail.spatial_id || detail.spatialId || detail.target?.spatial_id || detail.target?.spatialId || resolveCanonicalTarget()); if (target) { window.spatialEvidenceTarget = target; collectRegistryDiagnostics(target).then(d => { console.groupCollapsed(`[Twin Registry Debug] ${target}`); console.log('summary', { total: d.total, targetLinked: d.targetLinked, prepared: d.prepared, rejected: d.matchDebug?.rejectedCount ?? 0, status: d.status, aliasUsed: d.matchDebug?.aliasUsed || null }); console.table(d.matchDebug?.decisions || d.targetRecords); console.log('accepted', d.matchDebug?.accepted || []); console.log('rejected', d.matchDebug?.rejected || []); console.groupEnd(); }); } };
  window.addEventListener('testhp:spatial-layer-changed', onSpatialChange); window.addEventListener('testhp:spatial-target-changed', onSpatialChange);

  async function syncCanonical() { try { const response = await fetch('/api/spatial/registry?subject_id=own_cohort&timepoint=T0', { cache: 'no-store' }); if (!response.ok) return; const payload = await response.json(); const canonical = Array.isArray(payload.items) ? payload.items : []; if (!canonical.length) return; let current = {}; try { current = JSON.parse(localStorage.getItem(STORAGE) || '{}'); } catch {} const existing = Array.isArray(current.evidence) ? current.evidence : []; const canonicalUX = canonical.map(toUX); const canonicalIds = new Set(canonicalUX.map(x => x.backendAssetId || x.id)); const manual = existing.filter(x => !canonicalIds.has(x.backendAssetId || x.id)); localStorage.setItem(STORAGE, JSON.stringify({ evidence: [...canonicalUX, ...manual], target: canonicalSpatialId(current.target || resolveCanonicalTarget()) || 'hand' })); window.dispatchEvent(new CustomEvent('testhp:evidence-registry-synced', { detail: { count: canonical.length, evidence: canonicalUX, canonical: true } })); if (!sessionStorage.getItem(BOOTSTRAP)) { sessionStorage.setItem(BOOTSTRAP, '1'); window.location.reload(); } } catch (error) { console.warn('Canonical evidence registry sync failed', error); } }
  window.addEventListener('testhp:evidence-registry-synced', event => window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh', { detail: event.detail || {} })));
  const bootDebug = () => setTimeout(debugCurrentTarget, 0);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => { syncCanonical(); syncManagerTarget(resolveCanonicalTarget()); window.spatialEvidenceTarget = resolveCanonicalTarget(); bootDebug(); }, { once: true }); else { syncCanonical(); syncManagerTarget(resolveCanonicalTarget()); window.spatialEvidenceTarget = resolveCanonicalTarget(); bootDebug(); }
  window.addEventListener('load', bootDebug, { once: true });
})();
