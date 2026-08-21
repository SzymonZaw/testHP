(() => {
  const loading = document.getElementById('viewer-loading');
  const canvas = document.getElementById('twin-canvas');
  const viewport = document.getElementById('twin-viewport');
  const status = document.getElementById('twin-status');
  if (!loading || !canvas || !viewport) return;

  // app.js is the sole owner of the canonical Three.js renderer. This boot
  // module only verifies readiness; it must never call render() or dispatch
  // synthetic resize events because both can recursively trigger renderer
  // observers during startup.
  const progress = (step, detail = '') => window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step, detail } }));
  const isCanonical = manager => !!(manager && manager.version === 'canonical-three-1' && manager.active?.scene && manager.active?.camera && manager.deepRenderer);
  const safe = value => { try { return JSON.stringify(value); } catch { return String(value); } };
  const stack = () => (new Error().stack || '').split('\n').slice(2, 7).join(' <- ');

  let lastNavSnapshot = '';
  let diagnosticsInstalled = false;
  let biologicalDiagnosticsRunning = false;
  let lastBiologicalSignature = '';

  const readNavigation = () => {
    const crumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(el => el.textContent.trim()).filter(Boolean);
    const node = document.getElementById('spatial-node');
    const children = [...document.querySelectorAll('#spatial-children .spatial-target')].map(el => ({
      label: el.querySelector('strong')?.textContent?.trim() || '(missing label)',
      meta: el.querySelector('span')?.textContent?.trim() || '(missing level)',
      disabled: !!el.disabled,
      connected: el.isConnected,
      id: el.dataset?.spatialId || el.getAttribute('data-spatial-id') || null
    }));
    const level = document.getElementById('spatial-level-badge')?.textContent?.trim() || '?';
    const target = node?.querySelector('strong')?.textContent?.trim() || '?';
    return { crumbs, node, children, level, target };
  };

  const navigationDiagnostics = () => {
    const nav = readNavigation();
    const manager = window.spatialViewportManager;
    const active = manager?.active;
    const evidenceTarget = window.spatialEvidenceTarget || '?';
    const selectedTarget = window.selectedSpatialNode || '?';
    const expectedHandMacro = ['Śródręcze','Mały palec','Palec serdeczny','Palec środkowy','Palec wskazujący','Kciuk','Nadgarstek'];
    const actualLabels = nav.children.map(x => x.label);
    const isHandMacro = nav.crumbs.length === 1 && /^dłoń$/i.test(nav.crumbs[0]) && /macro/i.test(nav.level);
    const fallbackRegionalField = isHandMacro && actualLabels.length === 1 && /^regional field$/i.test(actualLabels[0]);
    const missingExpected = isHandMacro ? expectedHandMacro.filter(label => !actualLabels.includes(label)) : [];
    const diagnostics = {
      path: nav.crumbs.join(' > ') || '(root)', level: nav.level, target: nav.target,
      evidenceTarget, selectedTarget, children: actualLabels, childCount: nav.children.length,
      childMeta: nav.children, expectedHandMacro, missingExpected, fallbackRegionalField,
      managerPresent: !!manager, managerVersion: manager?.version || 'missing',
      activeKey: manager?.activeKey || 'none', activeLayer: manager?.activeLayer || active?.activeLayer || 'none',
      activeRenderer: active?.constructor?.name || 'none', activeScene: !!active?.scene,
      activeCamera: !!active?.camera, deepRenderer: !!manager?.deepRenderer,
      managerSetSpatialTarget: typeof manager?.setSpatialTarget === 'function',
      managerRender: typeof manager?.render === 'function'
    };
    const detail = [
      `path=${diagnostics.path}`, `level=${diagnostics.level}`, `target=${diagnostics.target}`,
      `spatialEvidenceTarget=${diagnostics.evidenceTarget}`, `selectedSpatialNode=${diagnostics.selectedTarget}`,
      `children=${actualLabels.length ? actualLabels.join(' | ') : '(none)'}`,
      `manager=${diagnostics.managerPresent ? 'present' : 'MISSING'}`,
      `manager.version=${diagnostics.managerVersion}`, `manager.activeKey=${diagnostics.activeKey}`,
      `manager.activeLayer=${diagnostics.activeLayer}`, `active.scene=${diagnostics.activeScene ? 'yes' : 'NO'}`,
      `active.camera=${diagnostics.activeCamera ? 'yes' : 'NO'}`, `deepRenderer=${diagnostics.deepRenderer ? 'present' : 'missing'}`,
      `setSpatialTarget=${diagnostics.managerSetSpatialTarget ? 'yes' : 'NO'}`, `render=${diagnostics.managerRender ? 'yes' : 'NO'}`
    ];
    if (fallbackRegionalField) {
      detail.push('NAVIGATION DEFECT: Hand/Macro exposes only "Regional field" instead of the 7 expected hand macro regions.');
      detail.push(`missing expected: ${missingExpected.join(' | ')}`);
    } else if (isHandMacro && missingExpected.length) {
      detail.push(`NAVIGATION WARNING: Hand/Macro children differ from expected list; missing=${missingExpected.join(' | ')}`);
    } else if (isHandMacro) {
      detail.push('NAVIGATION OK: Hand/Macro exposes all 7 expected macro regions.');
    }
    progress('navigation-diagnostics', detail.join('; '));
    window.__testhpSpatialNavigationDiagnostics = diagnostics;
    return diagnostics;
  };

  // Evidence diagnostics intentionally read both APIs. This distinguishes the
  // three states that previously looked identical in the UI:
  // 1) no observation exists, 2) observation exists but has no evidence_id,
  // 3) evidence exists but is outside the requested spatial scope.
  const biologicalEvidenceDiagnostics = async (detail = {}) => {
    if (biologicalDiagnosticsRunning) return;
    const spatialId = detail?.spatial_id || detail?.id || window.spatialEvidenceTarget || window.selectedSpatialNode || 'hand/palm';
    if (!spatialId || spatialId === '?') return;
    biologicalDiagnosticsRunning = true;
    const signature = String(spatialId);
    try {
      const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: spatialId, include_descendants: 'true' });
      const [stateResponse, scopedResponse, globalResponse] = await Promise.all([
        fetch(`/api/biological-state?${params.toString()}`, { cache: 'no-store' }),
        fetch(`/api/observations?subject_id=own_cohort&timepoint=T0&spatial_id=${encodeURIComponent(spatialId)}&include_archived=false`, { cache: 'no-store' }),
        fetch('/api/observations?subject_id=own_cohort&timepoint=T0&include_archived=false', { cache: 'no-store' })
      ]);
      const statePayload = stateResponse.ok ? await stateResponse.json() : null;
      const scopedPayload = scopedResponse.ok ? await scopedResponse.json() : null;
      const globalPayload = globalResponse.ok ? await globalResponse.json() : null;
      const state = statePayload?.state || {};
      const summary = statePayload?.summary || {};
      const scoped = Array.isArray(scopedPayload?.observations) ? scopedPayload.observations : [];
      const global = Array.isArray(globalPayload?.observations) ? globalPayload.observations : [];
      const matchingGlobal = global.filter(item => String(item.spatial_id || '') === String(spatialId));
      const missingEvidence = matchingGlobal.filter(item => !item.evidence_id).map(item => ({
        id: item.id, name: item.name, biological_level: item.biological_level,
        modality: item.modality, spatial_id: item.spatial_id, parent_id: item.parent_id || null,
        evidence_id: null, status: item.status, version: item.version
      }));
      const evidenceBacked = matchingGlobal.filter(item => item.evidence_id).map(item => ({
        id: item.id, name: item.name, biological_level: item.biological_level,
        spatial_id: item.spatial_id, parent_id: item.parent_id || null, evidence_id: item.evidence_id,
        evidence_confidence: item.evidence_confidence ?? null, status: item.status, version: item.version
      }));
      const returnedEvidenceIds = Array.isArray(state.evidence_ids) ? state.evidence_ids : [];
      const locations = Array.isArray(summary.by_location) ? summary.by_location : [];
      const diagnostic = {
        spatial_id: spatialId,
        request: `/api/biological-state?${params.toString()}`,
        state_http: stateResponse.status,
        observations_scoped_http: scopedResponse.status,
        observations_global_http: globalResponse.status,
        state_evidence_count: Number(state.evidence_count || 0),
        state_evidence_ids: returnedEvidenceIds,
        summary: {
          observations: Number(summary.observations || 0),
          explicit_evidence: Number(summary.explicit_evidence || 0),
          direct_evidence: Number(summary.direct_evidence || 0),
          descendant_evidence: Number(summary.descendant_evidence || 0),
          by_location: locations
        },
        observations_in_scope: scoped.length,
        matching_global_observations: matchingGlobal.length,
        evidence_backed_observations: evidenceBacked,
        observations_missing_evidence_id: missingEvidence,
        evidence_ids_from_observations: evidenceBacked.map(item => item.evidence_id),
        scope_match: matchingGlobal.length > 0,
        evidence_pipeline_ok: Number(state.evidence_count || 0) > 0,
        likely_cause: missingEvidence.length
          ? 'OBSERVATION_HAS_NO_EVIDENCE_ID'
          : matchingGlobal.length && !Number(state.evidence_count || 0)
            ? 'EVIDENCE_EXISTS_BUT_WAS_NOT_INCLUDED_IN_SCOPE'
            : !matchingGlobal.length
              ? 'NO_OBSERVATION_FOR_SELECTED_SPATIAL_ID'
              : 'NO_OBVIOUS_EVIDENCE_SCOPE_DEFECT'
      };
      window.__testhpBiologicalEvidenceDiagnostics = diagnostic;
      const compact = [
        `spatial_id=${spatialId}`,
        `stateHTTP=${stateResponse.status}`,
        `observationsScoped=${scoped.length}`,
        `observationsGlobalMatch=${matchingGlobal.length}`,
        `evidenceBacked=${evidenceBacked.length}`,
        `missingEvidenceId=${missingEvidence.length}`,
        `state.evidence_count=${diagnostic.state_evidence_count}`,
        `direct=${diagnostic.summary.direct_evidence}`,
        `descendants=${diagnostic.summary.descendant_evidence}`,
        `evidenceIds=${returnedEvidenceIds.length ? returnedEvidenceIds.join('|') : '(none)'}`,
        `likelyCause=${diagnostic.likely_cause}`
      ];
      if (missingEvidence.length) compact.push(`missingEvidenceObservations=${missingEvidence.map(item => `${item.id}:${item.name}`).join(' | ')}`);
      if (evidenceBacked.length) compact.push(`backedObservations=${evidenceBacked.map(item => `${item.id}:${item.evidence_id}`).join(' | ')}`);
      if (locations.length) compact.push(`byLocation=${locations.map(item => `${item.spatial_id}:${item.count}`).join(' | ')}`);
      if (signature !== lastBiologicalSignature || diagnostic.likely_cause !== 'NO_OBVIOUS_EVIDENCE_SCOPE_DEFECT') {
        progress('BIOLOGICAL EVIDENCE DIAGNOSTICS', compact.join('; '));
        lastBiologicalSignature = signature;
      }
    } catch (error) {
      progress('BIOLOGICAL EVIDENCE DIAGNOSTICS ERROR', `${error?.message || error}; stack=${error?.stack || 'none'}`);
    } finally {
      biologicalDiagnosticsRunning = false;
    }
  };

  const installMutationDiagnostics = () => {
    if (diagnosticsInstalled) return;
    diagnosticsInstalled = true;
    const container = document.getElementById('spatial-children');
    if (!container) return;

    const snapshot = () => safe(readNavigation().children.map(x => x.label));
    const emitChange = (kind, extra = '') => {
      const after = snapshot();
      if (after === lastNavSnapshot && !extra) return;
      const before = lastNavSnapshot || '(unknown)';
      lastNavSnapshot = after;
      progress('NAV DOM WRITE', `kind=${kind}; before=${before}; after=${after}; ${extra} stack=${stack()}`);
      navigationDiagnostics();
    };

    lastNavSnapshot = snapshot();
    const methods = ['appendChild','prepend','insertBefore','replaceChild','removeChild','replaceChildren'];
    methods.forEach(name => {
      const original = container[name];
      if (typeof original !== 'function') return;
      container[name] = function(...args) {
        const result = original.apply(this, args);
        emitChange(name);
        return result;
      };
    });

    const observer = new MutationObserver(records => {
      const summary = records.map(record => ({
        type: record.type,
        added: record.addedNodes?.length || 0,
        removed: record.removedNodes?.length || 0,
        attribute: record.attributeName || null
      }));
      progress('NAV MUTATION OBSERVED', `records=${safe(summary)}; current=${snapshot()}`);
      navigationDiagnostics();
    });
    observer.observe(container, { childList:true, subtree:true, characterData:true, attributes:true });
    window.addEventListener('beforeunload', () => observer.disconnect(), { once:true });
  };

  const installManagerDiagnostics = manager => {
    if (!manager || manager.__testhpDiagnosticsInstalled) return;
    manager.__testhpDiagnosticsInstalled = true;
    ['render','setSpatialTarget'].forEach(name => {
      const original = manager[name];
      if (typeof original !== 'function') return;
      manager[name] = function(...args) {
        const before = readNavigation();
        progress('MANAGER CALL', `method=${name}; args=${safe(args)}; beforePath=${before.crumbs.join(' > ')}; beforeTarget=${before.target}; beforeChildren=${safe(before.children.map(x => x.label))}; stack=${stack()}`);
        const result = original.apply(this, args);
        const after = readNavigation();
        progress('MANAGER RESULT', `method=${name}; afterPath=${after.crumbs.join(' > ')}; afterTarget=${after.target}; afterChildren=${safe(after.children.map(x => x.label))}`);
        return result;
      };
    });
  };

  const managerValidationDiagnostics = manager => {
    if (!manager) return;
    const checks = {
      exists: true,
      versionExpected: manager.version === 'canonical-three-1',
      scene: !!manager.active?.scene,
      camera: !!manager.active?.camera,
      deepRenderer: !!manager.deepRenderer,
      setSpatialTarget: typeof manager.setSpatialTarget === 'function',
      render: typeof manager.render === 'function'
    };
    const failed = Object.entries(checks).filter(([, ok]) => !ok).map(([key]) => key);
    progress('MANAGER VALIDATION', `checks=${safe(checks)}; failed=${failed.length ? failed.join(' | ') : '(none)'}; version=${manager.version || 'missing'}; activeKey=${manager.activeKey || 'none'}; activeLayer=${manager.activeLayer || manager.active?.activeLayer || 'none'}; activeType=${manager.active?.constructor?.name || 'none'}`);
    if (failed.length) progress('MANAGER REJECTION REASON', `failed=${failed.join(' | ')}; expected=version canonical-three-1 + active.scene + active.camera + deepRenderer`);
  };

  const hideLoading = (message = 'Digital Twin ready') => {
    loading.hidden = true;
    loading.setAttribute('aria-hidden', 'true');
    loading.style.display = 'none';
    loading.classList.remove('viewer-loading-error');
    if (status && (!status.textContent || /starting|building/i.test(status.textContent))) status.textContent = message;
    window.__testhpTwinReady = true;
    window.dispatchEvent(new CustomEvent('testhp:twin-ready', { detail: { width: canvas.width, height: canvas.height, renderer: 'WebGL' } }));
  };

  const showFailure = message => {
    loading.hidden = false;
    loading.style.display = 'grid';
    loading.textContent = message;
    loading.classList.add('viewer-loading-error');
    if (status) status.textContent = 'Twin Viewport error';
    window.dispatchEvent(new CustomEvent('testhp:twin-error', { detail: { error: new Error(message) } }));
  };

  const report = () => {
    try {
      progress('canvas-check');
      if (!canvas.isConnected) throw new Error('Twin canvas is not connected to the DOM');
      installMutationDiagnostics();
      navigationDiagnostics();
      progress('manager-check');
      const manager = window.spatialViewportManager;
      if (!manager) { progress('MANAGER MISSING', 'window.spatialViewportManager is not available'); return false; }
      installManagerDiagnostics(manager);
      managerValidationDiagnostics(manager);
      if (!isCanonical(manager)) {
        progress('manager-rejected', `version=${manager.version || 'unknown'}; waiting for canonical-three-1`);
        return false;
      }
      progress('webgl-check');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) {
        showFailure('3D rendering is unavailable. Check WebGL support in the browser.');
        return true;
      }
      progress('ready');
      hideLoading();
      biologicalEvidenceDiagnostics({ spatial_id: window.spatialEvidenceTarget || window.selectedSpatialNode || 'hand/palm' });
      return true;
    } catch (error) {
      console.error('[Twin Viewport] bootstrap failed', error);
      progress('BOOTSTRAP EXCEPTION', `${error?.message || error}; stack=${error?.stack || 'none'}`);
      showFailure(`Twin Viewport initialization failed: ${error?.message || error}`);
      return true;
    }
  };

  window.addEventListener('error', event => { if (event?.message) progress('WINDOW ERROR', `${event.message} | ${event.filename || ''}:${event.lineno || ''}`); });
  window.addEventListener('unhandledrejection', event => progress('UNHANDLED PROMISE', String(event.reason?.stack || event.reason || 'unknown')));
  window.addEventListener('testhp:viewport-manager-ready', () => report());
  window.addEventListener('testhp:twin-error', event => console.error('[Twin Viewport]', event.detail));
  window.addEventListener('testhp:spatial-layer-changed', event => { progress('SPATIAL LAYER CHANGED', JSON.stringify(event.detail || {})); biologicalEvidenceDiagnostics(event.detail || {}); });
  window.addEventListener('testhp:spatial-target-changed', event => { progress('SPATIAL TARGET CHANGED', JSON.stringify(event.detail || {})); biologicalEvidenceDiagnostics(event.detail || {}); });
  window.addEventListener('testhp:observation-updated', event => biologicalEvidenceDiagnostics(event.detail?.observation || event.detail || {}));

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    const done = report();
    if (done || attempts >= 40) {
      clearInterval(timer);
      if (!done && !window.__testhpTwinReady) showFailure('Twin Viewport initialization timed out after 10 seconds. Open DEBUG for diagnostics.');
    }
  }, 250);

  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
})();