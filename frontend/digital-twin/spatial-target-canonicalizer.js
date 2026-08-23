(() => {
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
  const reconcile = () => {
    const api = contract();
    if (api?.reconcile) api.reconcile();
    const manager = window.spatialViewportManager;
    if (!manager || typeof manager !== 'object') return;
    // Prefer the actual active node ID. A display label such as Palm must not win.
    const id = canonical(manager?.active?.spatial_id || manager?.active?.spatialId || manager?.state?.spatial_id || manager?.state?.spatialId || (typeof manager?.spatialTarget === 'string' ? manager.spatialTarget : '') || manager?.state?.spatialTarget);
    if (!id) return;
    if (manager.state && typeof manager.state === 'object') Object.assign(manager.state,{spatial_id:id,spatialId:id,spatialTarget:id});
    manager.spatialTarget = id;
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