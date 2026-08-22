(() => {
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const VIEWS = ['front','back','side_left','side_right','thumb'];
  const readJson = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };
  const writeJson = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const spatialIdOf = value => {
    if (!value) return null;
    if (typeof value === 'string') return value;
    return value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
  };
  const surfaceTarget = () => String(window.spatialEvidenceTarget || spatialIdOf(window.selectedSpatialNode) || document.body.dataset.spatialTarget || 'hand');

  // Stage 13 is a visualization contract, not measured anatomy. Generate a
  // procedural manifest for the active spatial target, including tissue and
  // cellular descendants, instead of silently falling back to hand/palm.
  function ensureGeometryContract() {
    const target = surfaceTarget();
    if (!target.startsWith('hand/palm')) return;
    const surface = readJson(SURFACE_KEY, { geometry: {}, prepared: null, mappings: [], selectedView: 'front', geometryTargets: {} });
    surface.geometry ||= {};
    surface.geometryTargets ||= {};
    const current = surface.geometryTargets[target] || surface.geometry?.[target] || surface.geometry?.['hand/palm'] || {};
    const scalar = key => Number.isFinite(Number(current.parameters?.[key] ?? current[key] ?? surface.geometry[key])) ? Number(current.parameters?.[key] ?? current[key] ?? surface.geometry[key]) : 1;
    const manifest = {
      schema: 'hand-surface-geometry-v1', spatial_id: target, status: 'available',
      source: 'procedural-surface-fallback', method: 'procedural-surface-v1', calibrated: false,
      clinical_claim: false, coordinate_system: 'hand-surface-v1',
      parameters: { palmLength: scalar('palmLength'), palmWidth: scalar('palmWidth'), fingerSpread: scalar('fingerSpread'), thumbAngle: scalar('thumbAngle'), taper: scalar('taper'), thickness: scalar('thickness') },
      evidence_boundary: 'Geometry is a procedural visualization until measured/photo registration is supplied; it does not infer anatomy.',
      updatedAt: new Date().toISOString()
    };
    surface.geometryTargets[target] = manifest;
    if (target === 'hand/palm') {
      Object.assign(surface.geometry, manifest.parameters);
      surface.geometry[target] = manifest;
      surface.geometryManifest = manifest;
    }
    writeJson(SURFACE_KEY, surface);
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-geometry-ready', { detail: manifest }));
    return manifest;
  }

  function ensurePanel() {
    if (document.getElementById('hand-surface-stages-20-22')) return;
    const studio = document.getElementById('hand-surface-studio'); if (!studio) return;
    const panel = document.createElement('section'); panel.id='hand-surface-stages-20-22';
    panel.style.cssText='margin-top:14px;border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)';
    panel.innerHTML='<div style="display:flex;justify-content:space-between;gap:10px;align-items:center"><strong>STAGES 20–22 · Projection package</strong><span id="hss2022-status" style="font-size:11px;font-weight:700;text-transform:uppercase;color:#667085">WAITING</span></div><div id="hss2022-body" style="margin-top:10px;font-size:13px"></div>';
    studio.appendChild(panel); renderPanel();
  }
  function renderPanel() {
    const body=document.getElementById('hss2022-body'), status=document.getElementById('hss2022-status'); if(!body||!status)return;
    const target=surfaceTarget();
    if(!target.startsWith('hand/palm')) { status.textContent='WAITING'; body.textContent='Projection remains attached to a supported hand spatial target.'; return; }
    const surface=readJson(SURFACE_KEY,{geometry:{},mappings:[],geometryTargets:{}}), manifest=surface.geometryTargets?.[target]||surface.geometry?.[target];
    const mappings=Array.isArray(surface.mappings)?surface.mappings.filter(m=>m?.spatialTarget===target):[];
    const registered=VIEWS.filter(v=>mappings.some(m=>m?.view===v&&Number(m?.quality||0)>0)).length;
    const plan=readJson(PLAN_KEY,null), planReady=plan?.schema==='surface-projection-v2'&&plan?.target===target;
    status.textContent=planReady?'READY':manifest?'GEOMETRY READY':'WAITING';
    body.innerHTML=`<div>Cel: <code>${target}</code></div><div style="margin-top:6px">Geometria: <b>${manifest?'GOTOWA':'BRAK'}</b> · źródło: <code>${manifest?.source||'—'}</code> · kalibracja: <b>${manifest?.calibrated?'TAK':'NIE'}</b></div><div style="margin-top:6px">Rejestracja: <b>${registered}/5</b> widoków · plan projekcji: <b>${planReady?'TAK':'NIE'}</b></div><div style="margin-top:8px;font-size:12px;color:#667085">Proceduralna geometria odblokowuje kontrakt etapu 13, ale nie tworzy sztucznych zdjęć ani rejestracji.</div>`;
  }
  function boot(){ ensureGeometryContract(); ensurePanel(); renderPanel(); window.addEventListener('testhp:spatial-target-changed',()=>{ensureGeometryContract();ensurePanel();renderPanel()}); window.addEventListener('testhp:spatial-layer-changed',()=>{ensureGeometryContract();renderPanel()}); window.addEventListener('testhp:hand-surface-geometry-changed',()=>{ensureGeometryContract();renderPanel()}); window.addEventListener('testhp:evidence-attached',renderPanel); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
})();