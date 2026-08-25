(() => {
  const API = '/api/hand/photo-reconstruction';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const normalize = v => String(v ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
  const target = () => normalize(window.testhpSpatialContract?.getTarget?.()?.spatial_id || window.selectedSpatialNode?.spatial_id || window.spatialEvidenceTarget || document.body?.dataset?.spatialTarget || 'hand');
  const read = key => { try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch { return null; } };
  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));

  async function state() {
    const t = target();
    const r = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0&spatial_id=${encodeURIComponent(t)}`);
    if (!r.ok) throw new Error('Nie udało się odczytać stanu rejestracji.');
    return r.json();
  }

  function buildPlan(s) {
    const views = (s.registered_views || []).filter(v => VIEWS.includes(v));
    const coverage = Math.round((views.length / VIEWS.length) * 100);
    return {
      schema: 'surface-projection-v2', target: s.spatial_id, views,
      coverage, method: 'registered-view-projection', calibrated: false,
      status: views.length >= 2 ? 'ready' : 'incomplete',
      quality: coverage >= 80 ? 'good' : coverage >= 40 ? 'partial' : 'insufficient',
      generatedAt: new Date().toISOString(),
      boundary: 'Research visualization only; projection does not infer clinical anatomy.'
    };
  }

  function savePlan(s) {
    const plan = buildPlan(s);
    write(PLAN_KEY, plan);
    const surface = read(SURFACE_KEY) || { geometry: {} };
    surface.mappings = (s.evidence || []).filter(x => x.registration?.status === 'registered' && x.prepared_asset).map(x => ({
      spatialTarget: s.spatial_id, view: x.registration.view, assetId: x.asset_id,
      preparedAssetId: x.prepared_asset.prepared_asset_id, quality: Number(x.registration.quality || 1),
      method: 'registered-view-projection', registeredAt: x.registration.registered_at
    }));
    surface.projection = plan;
    surface.appliedToModel = false;
    surface.surfaceAssetId = s.reconstruction?.reconstruction_id || null;
    surface.geometry = surface.geometry || {};
    surface.geometry[s.spatial_id] = {
      schema: 'hand-surface-geometry-v1', spatial_id: s.spatial_id,
      status: 'available', source: 'photo-registration', method: 'registered-view-projection',
      calibrated: false, clinical_claim: false, coordinate_system: 'hand-surface-v1',
      parameters: read(SURFACE_KEY)?.geometry?.[s.spatial_id]?.parameters || {},
      evidence_boundary: 'Geometry is a research visualization until calibrated; it does not infer anatomy.'
    };
    write(SURFACE_KEY, surface);
    window.dispatchEvent(new CustomEvent('testhp:surface-projection-plan-changed', { detail: plan }));
    return plan;
  }

  async function ensureBuild() {
    const s = await state();
    if ((s.registered_count || 0) < 2) return null;
    let plan = read(PLAN_KEY);
    if (!plan || normalize(plan.target) !== normalize(s.spatial_id) || plan.views?.length !== s.registered_count) {
      const r = await fetch(`${API}/build`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({subject_id:'own_cohort',timepoint:'T0',spatial_id:s.spatial_id,min_views:2}) });
      const built = await r.json();
      if (!r.ok) throw new Error(built.detail || 'Nie udało się utworzyć powierzchni.');
      plan = savePlan(built);
    }
    return { state: s, plan };
  }

  async function applyOverlay(ctx) {
    if (!ctx || !window.spatialViewportManager?.active?.scene) return false;
    const THREE = await import('three');
    const { DecalGeometry } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/geometries/DecalGeometry.js');
    const manager = window.spatialViewportManager;
    const root = manager.active.scene;
    const targetMesh = root.getObjectByName('palm') || root.getObjectByName('skin:palm');
    if (!targetMesh?.isMesh) return false;

    root.getObjectByName('__photo_surface_projection__')?.removeFromParent();
    const group = new THREE.Group(); group.name = '__photo_surface_projection__';
    const views = ctx.plan.views || [];
    const records = ctx.state.evidence || [];
    const positions = { front:[0, -0.35, 1.45], back:[0,-0.35,-1.45], side_left:[-1.35,-0.35,0], side_right:[1.35,-0.35,0], thumb:[-1.15,0.2,0.75] };
    const rotations = { front:[0,0,0], back:[0,Math.PI,0], side_left:[0,-Math.PI/2,0], side_right:[0,Math.PI/2,0], thumb:[0,-0.65,0] };
    for (const view of views) {
      const record = records.find(x => x.registration?.view === view && x.prepared_asset);
      if (!record) continue;
      const src = `${API}/asset/${encodeURIComponent(record.asset_id)}/hand.obj`;
      const imageUrl = `/api/spatial/preview/${encodeURIComponent(record.asset_id)}?max_width=1400&max_height=1000`;
      try {
        const texture = await new THREE.TextureLoader().loadAsync(imageUrl);
        texture.colorSpace = THREE.SRGBColorSpace;
        const material = new THREE.MeshBasicMaterial({ map:texture, transparent:true, opacity:0.62, depthWrite:false, polygonOffset:true, polygonOffsetFactor:-1 });
        const pos = new THREE.Vector3(...positions[view]);
        const rot = new THREE.Euler(...rotations[view]);
        const size = new THREE.Vector3(view === 'thumb' ? 1.2 : 2.55, view === 'thumb' ? 1.5 : 2.2, 1.0);
        const decal = new THREE.Mesh(new DecalGeometry(targetMesh, pos, rot, size), material);
        decal.name = `photo-projection:${view}`;
        group.add(decal);
      } catch (e) { console.warn('[photo-surface-projection]', view, e); }
    }
    root.add(group);
    const surface = read(SURFACE_KEY) || {};
    surface.appliedToModel = group.children.length > 0;
    surface.appliedViews = group.children.map(x => x.name.replace('photo-projection:',''));
    surface.appliedAt = new Date().toISOString();
    write(SURFACE_KEY, surface);
    try { manager.render?.(); } catch {}
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-ready', { detail: { applied: surface.appliedToModel, views: surface.appliedViews } }));
    return surface.appliedToModel;
  }

  async function sync() {
    try {
      const ctx = await ensureBuild();
      if (ctx) await applyOverlay(ctx);
    } catch (e) { console.warn('[photo-surface-projection]', e); }
  }

  window.testhpPhotoSurfaceProjection = { sync, buildPlan, getPlan: () => read(PLAN_KEY) };
  window.addEventListener('testhp:evidence-registry-synced', () => setTimeout(sync, 150));
  window.addEventListener('testhp:spatial-contract-changed', () => setTimeout(sync, 150));
  window.addEventListener('testhp:surface-projection-plan-changed', () => setTimeout(() => applyOverlayFromStored(), 0));
  async function applyOverlayFromStored() { try { const s = await state(); const plan = read(PLAN_KEY); if (plan?.target === s.spatial_id && plan.views?.length) await applyOverlay({state:s,plan}); } catch {} }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(sync, 600), { once:true }); else setTimeout(sync, 600);
})();
