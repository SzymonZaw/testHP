(() => {
  import('./spatial-target-drift-debug-fix.js?v=authoritative-target-1').catch(error => console.error('[Twin diagnostics] authoritative target debug failed to load', error));
  // Stage 1-5: canonical spatial identity is owned by spatial-contract.js.
  const contract = () => window.testhpSpatialContract;
  const canonical = value => {
    const api = contract();
    if (api?.normalizeId) return api.normalizeId(value);
    const raw = String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
    return ({palm:'hand/palm','śródręcze':'hand/palm',srodrecze:'hand/palm'})[raw] || raw;
  };
  const canonicalizeTarget = target => {
    if (!target || typeof target !== 'object') return target;
    const next = { ...target };
    const id = canonical(next.spatial_id || next.spatialId || next.spatial_node_id || next.targetSpatialId || next.id);
    if (id) Object.assign(next,{spatial_id:id,spatialId:id,spatial_node_id:id,targetSpatialId:id});
    return next;
  };

  // The viewport manager can expose a display label through `spatialTarget`
  // even when the active navigation node already carries the real canonical
  // spatial_id. Resolve that authoritative ID before considering any label.
  const activeViewportSpatialId = manager => {
    const diagnostics = window.__testhpDiagnostics || {};
    const navigation = diagnostics.lastNavigation || diagnostics.lastNavigationRoute;
    const navigationId = navigation?.spatial_id || navigation?.spatialId;
    if (typeof navigationId === 'string' && navigationId.includes('/')) return canonical(navigationId);

    const clickButton = diagnostics.lastClickRoute?.button;
    const clickId = clickButton?.spatialId || clickButton?.spatial_id || clickButton?.spatial_node_id;
    if (typeof clickId === 'string' && clickId.includes('/')) return canonical(clickId);

    const direct = manager?.active?.spatial_node_id || manager?.active?.spatial_id || manager?.active?.spatialId;
    if (typeof direct === 'string' && direct) return canonical(direct);

    const state = manager?.state || {};
    const stateId = state.spatial_node_id || state.spatial_id || state.spatialId;
    if (typeof stateId === 'string' && stateId && stateId.includes('/')) return canonical(stateId);

    const activeKey = typeof manager?.activeKey === 'string' ? manager.activeKey : '';
    const leaf = activeKey.includes('|') ? activeKey.slice(activeKey.indexOf('|') + 1) : '';
    if (!leaf) return '';

    // Navigation buttons expose `spatialId` as an own property in the live
    // viewport. Prefer an exact leaf match so a human-readable target label
    // can never become the registry key.
    const nodes = document.querySelectorAll('button,[role="button"]');
    for (const node of nodes) {
      const candidates = [
        node.spatialId,
        node.spatial_id,
        node.spatialNodeId,
        node.dataset?.spatialId,
        node.dataset?.spatial_id,
        node.getAttribute?.('data-spatial-id'),
        node.getAttribute?.('data-spatial_id')
      ].filter(value => typeof value === 'string' && value);
      const match = candidates.find(value => value === leaf || value.endsWith(`/${leaf}`));
      if (match) return canonical(match);
    }

    return '';
  };

  const reconcile = () => {
    const api = contract();
    if (api?.reconcile) api.reconcile();
    const manager = window.spatialViewportManager;
    if (!manager || typeof manager !== 'object') return;

    // Authoritative order: explicit navigation ID -> active node ID -> state ID
    // -> object target ID. A concrete activeKey must never fall back to the
    // display-label string exposed by manager.spatialTarget.
    const activeId = activeViewportSpatialId(manager);
    const state = manager.state || {};
    const stateTarget = state.target && typeof state.target === 'object'
      ? (state.target.spatial_node_id || state.target.spatial_id || state.target.spatialId || state.target.id)
      : '';
    const objectTarget = manager.spatialTarget && typeof manager.spatialTarget === 'object'
      ? (manager.spatialTarget.spatial_node_id || manager.spatialTarget.spatial_id || manager.spatialTarget.spatialId || manager.spatialTarget.id)
      : '';
    const activeKeyPresent = typeof manager.activeKey === 'string' && manager.activeKey.includes('|');
    const fallback = stateTarget || objectTarget || (!activeKeyPresent && typeof manager.spatialTarget === 'string' ? manager.spatialTarget : '') || (!activeKeyPresent && typeof state.spatialTarget === 'string' ? state.spatialTarget : '');
    const id = canonical(activeId || stateTarget || objectTarget || fallback);
    if (!id) return;

    if (manager.state && typeof manager.state === 'object') Object.assign(manager.state,{spatial_id:id,spatialId:id,spatialTarget:id});
    manager.spatialTarget = id;
    // Keep legacy globals on the same canonical identity. The debug surface
    // compares these values with the viewport-manager target; aliases such as
    // `palm` must not be reported as TARGET DRIFT when they mean hand/palm.
    if (window.selectedSpatialNode) window.selectedSpatialNode = canonical(window.selectedSpatialNode);
    if (window.spatialEvidenceTarget) window.spatialEvidenceTarget = canonical(window.spatialEvidenceTarget);
  };
  const repairPhotoShell = () => {
    const root = document.getElementById('photo-3d-reconstruction');
    if (!root) return;
    const ensure = (id, tag, cls='') => {
      let el = document.getElementById(id);
      if (!el) { el=document.createElement(tag); el.id=id; if(cls) el.className=cls; root.appendChild(el); }
      return el;
    };
    ensure('p3r-inputs','div','p3r-list');
    ensure('p3r-score','span','p3r-badge');
    ensure('p3r-meter','i');
    ensure('p3r-status','div','p3r-status');
    ensure('p3r-meta','pre','p3r-code');
    ensure('p3r-stage','div','p3r-canvas');
    ensure('p3r-build','button','primary');
    ensure('p3r-clear','button');
  };
  const install = () => {
    reconcile();
    repairPhotoShell();
    const manager = window.spatialViewportManager;
    if (!manager || manager.__testhpSpatialCanonicalizerInstalled) return;
    const original = manager.setSpatialTarget;
    if (typeof original !== 'function') return;
    manager.__testhpSpatialCanonicalizerInstalled = true;
    manager.setSpatialTarget = function(target,...args){ const result=original.call(this,canonicalizeTarget(target),...args); reconcile(); return result; };
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-canonicalizer-ready',{detail:{source:'spatial-contract',canonical:true}}));
  };
  install();
  window.addEventListener('testhp:spatial-contract-changed',reconcile);
  window.addEventListener('testhp:spatial-layer-changed',reconcile);
  window.addEventListener('testhp:spatial-target-changed',reconcile);
  window.addEventListener('testhp:viewport-manager-ready',install);
  const observer = new MutationObserver(() => { repairPhotoShell(); reconcile(); });
  if (document.documentElement) observer.observe(document.documentElement,{childList:true,subtree:true});
})();
