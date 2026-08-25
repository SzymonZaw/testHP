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
      schema: 'surface-projection-v2', target: s.spatial_id, views, coverage,
      method: 'registered-view-projection', calibrated: false,
      status: views.length >= 1 ? 'ready' : 'incomplete',
      quality: coverage >= 80 ? 'good' : coverage >= 20 ? 'partial' : 'insufficient',
      generatedAt: new Date().toISOString(),
      boundary: 'Research visualization only; projection does not infer clinical anatomy.'
    };
  }

  function savePlan(s) {
    const plan = buildPlan(s);
    write(PLAN_KEY, plan);
    const surface = read(SURFACE_KEY) || { geometry: {} };
    const mappings = (s.evidence || []).filter(x => x.registration?.status === 'registered' && x.prepared_asset).map(x => ({
      spatialTarget: s.spatial_id, view: x.registration.view, assetId: x.asset_id,
      preparedAssetId: x.prepared_asset.prepared_asset_id, quality: Number(x.registration.quality || 1),
      method: 'registered-view-projection', registeredAt: x.registration.registered_at
    }));
    surface.mappings = mappings;
    surface.projection = plan;
    surface.appliedToModel = false;
    surface.surfaceAssetId = s.reconstruction?.reconstruction_id || null;
    surface.twinPackage = {
      schema: 'hand-surface-package-v1', spatial_id: s.spatial_id,
      reconstruction_id: s.reconstruction?.reconstruction_id || null,
      registered_views: plan.views, coverage: plan.coverage, quality: plan.quality,
      mapping_count: mappings.length, calibrated: false,
      status: plan.status, generatedAt: plan.generatedAt
    };
    surface.geometry = surface.geometry || {};
    const previousParameters = surface.geometry[s.spatial_id]?.parameters || {};
    surface.geometry[s.spatial_id] = {
      schema: 'hand-surface-geometry-v1', spatial_id: s.spatial_id,
      status: 'available', source: 'photo-registration', method: 'registered-view-projection',
      calibrated: false, clinical_claim: false, coordinate_system: 'hand-surface-v1',
      parameters: previousParameters,
      evidence_boundary: 'Geometry is a research visualization until calibrated; it does not infer anatomy.'
    };
    write(SURFACE_KEY, surface);
    window.dispatchEvent(new CustomEvent('testhp:surface-projection-plan-changed', { detail: plan }));
    return plan;
  }

  async function ensureBuild() {
    let s = await state();
    // One prepared view is sufficient. If it has not yet been registered,
    // register it automatically so projection does not retain the old
    // two-view gate as an implicit UI requirement.
    if ((s.registered_count || 0) < 1 && (s.prepared_count || 0) >= 1) {
      const r = await fetch(`${API}/register`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({subject_id:'own_cohort',timepoint:'T0',spatial_id:s.spatial_id})
      });
      const registered = await r.json();
      if (!r.ok) throw new Error(registered.detail || 'Nie udało się zarejestrować przygotowanego widoku.');
      s = registered;
    }
    if ((s.registered_count || 0) < 1) return null;
    let plan = read(PLAN_KEY);
    if (!plan || normalize(plan.target) !== normalize(s.spatial_id) || plan.views?.length !== s.registered_count) {
      const r = await fetch(`${API}/build`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({subject_id:'own_cohort',timepoint:'T0',spatial_id:s.spatial_id,min_views:1}) });
      const built = await r.json();
      if (!r.ok) throw new Error(built.detail || 'Nie udało się utworzyć powierzchni.');
      plan = savePlan(built);
    }
    return { state: s, plan };
  }

  function renderStatus(surface, plan) {
    const host = document.getElementById('hand-surface-unified-status');
    if (!host || !plan) return;
    let el = document.getElementById('photo-projection-status');
    if (!el) { el = document.createElement('span'); el.id = 'photo-projection-status'; el.style.cssText = 'display:block;margin-top:5px;font-size:11px'; host.appendChild(el); }
    const applied = !!surface?.appliedToModel;
    el.textContent = applied
      ? `✓ Zdjęcia nałożone na model · ${plan.views.length}/5 widoków · pokrycie ${plan.coverage}% · jakość ${plan.quality === 'good' ? 'dobra' : 'częściowa'}`
      : `Rejestracja gotowa · ${plan.views.length}/5 widoków · pokrycie ${plan.coverage}% · oczekiwanie na zastosowanie na modelu`;
  }

  function findTargetMesh(root, spatialTarget) {
    const leaf = normalize(spatialTarget).split('/').filter(Boolean).pop() || 'hand';
    const aliases = new Set([leaf, `skin:${leaf}`, `skin_${leaf}`, `${leaf}_mesh`, `${leaf}-mesh`]);
    let exact = null;
    let fuzzy = null;
    root.traverse?.(object => {
      if (!object?.isMesh) return;
      const name = normalize(object.name);
      if (aliases.has(name) || name === `skin:${leaf}`) exact = exact || object;
      else if (!fuzzy && (name.includes(leaf) || name.includes(`skin:${leaf}`))) fuzzy = object;
    });
    return exact || fuzzy || (leaf === 'hand' ? root.getObjectByName('hand') : null);
  }

  function meshBounds(mesh, THREE) {
    const box = new THREE.Box3().setFromObject(mesh);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    return { box, size, center };
  }

  function projectionPlacement(view, bounds, THREE) {
    const { center, size } = bounds;
    const depth = Math.max(size.x, size.y, size.z) * 0.12;
    const width = Math.max(size.x, size.y) * 0.92;
    const height = Math.max(size.x, size.y) * 0.72;
    const placements = {
      front: { position: new THREE.Vector3(center.x, center.y, bounds.box.max.z + depth), rotation: new THREE.Euler(0, 0, 0) },
      back: { position: new THREE.Vector3(center.x, center.y, bounds.box.min.z - depth), rotation: new THREE.Euler(0, Math.PI, 0) },
      side_left: { position: new THREE.Vector3(bounds.box.min.x - depth, center.y, center.z), rotation: new THREE.Euler(0, -Math.PI / 2, 0) },
      side_right: { position: new THREE.Vector3(bounds.box.max.x + depth, center.y, center.z), rotation: new THREE.Euler(0, Math.PI / 2, 0) },
      thumb: { position: new THREE.Vector3(center.x - size.x * 0.32, center.y + size.y * 0.08, center.z + size.z * 0.08), rotation: new THREE.Euler(0, -0.65, 0) }
    };
    const placement = placements[view] || placements.front;
    return { ...placement, scale: new THREE.Vector3(view === 'thumb' ? width * 0.45 : width, view === 'thumb' ? height * 0.55 : height, Math.max(depth * 8, 0.2)) };
  }

  async function applyOverlay(ctx) {
    if (!ctx || !window.spatialViewportManager?.active?.scene) return false;
    const THREE = await import('three');
    const { DecalGeometry } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/geometries/DecalGeometry.js');
    const manager = window.spatialViewportManager;
    const root = manager.active.scene;
    const spatialTarget = normalize(ctx.plan?.target || target());
    const targetMesh = findTargetMesh(root, spatialTarget);
    window.__testhpSpatialProjectionDiagnostics = {
      target: spatialTarget,
      managerVersion: manager.version || null,
      activeKey: manager.activeKey || null,
      scene: !!root,
      targetMesh: targetMesh?.name || null,
      targetMeshFound: !!targetMesh
    };
    if (!targetMesh?.isMesh) return false;

    root.getObjectByName('__photo_surface_projection__')?.removeFromParent();
    const group = new THREE.Group();
    group.name = '__photo_surface_projection__';
    const views = ctx.plan.views || [];
    const records = ctx.state.evidence || [];
    const bounds = meshBounds(targetMesh, THREE);
    const applied = [];

    for (const view of views) {
      const record = records.find(x => x.registration?.view === view && x.prepared_asset);
      if (!record) continue;
      const imageUrl = `/api/spatial/preview/${encodeURIComponent(record.asset_id)}?max_width=1400&max_height=1000`;
      try {
        const texture = await new THREE.TextureLoader().loadAsync(imageUrl);
        texture.colorSpace = THREE.SRGBColorSpace;
        const material = new THREE.MeshBasicMaterial({ map:texture, transparent:true, opacity:0.62, depthWrite:false, polygonOffset:true, polygonOffsetFactor:-1 });
        const placement = projectionPlacement(view, bounds, THREE);
        const decal = new THREE.Mesh(new DecalGeometry(targetMesh, placement.position, placement.rotation, placement.scale), material);
        decal.name = `photo-projection:${view}`;
        group.add(decal);
        applied.push(view);
      } catch (e) { console.warn('[photo-surface-projection]', view, e); }
    }

    if (!group.children.length) {
      window.__testhpSpatialProjectionDiagnostics.reason = 'no-registered-prepared-evidence';
      return false;
    }
    root.add(group);
    const surface = read(SURFACE_KEY) || {};
    surface.appliedToModel = true;
    surface.appliedViews = applied;
    surface.appliedTarget = spatialTarget;
    surface.appliedAt = new Date().toISOString();
    write(SURFACE_KEY, surface);
    window.__testhpSpatialProjectionDiagnostics.appliedViews = applied;
    window.__testhpSpatialProjectionDiagnostics.reason = 'applied';
    renderStatus(surface, ctx.plan);
    try { manager.render?.(); } catch {}
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-ready', { detail: { applied: true, views: applied, target: spatialTarget } }));
    return true;
  }

  async function sync() {
    try {
      const ctx = await ensureBuild();
      if (ctx) {
        const surface = read(SURFACE_KEY) || {};
        renderStatus(surface, ctx.plan);
        await applyOverlay(ctx);
      } else {
        window.__testhpSpatialProjectionDiagnostics = {
          target: target(),
          reason: 'no-registered-views',
          applied: false
        };
      }
    } catch (e) {
      window.__testhpSpatialProjectionDiagnostics = { target: target(), reason: 'projection-error', message: e?.message || String(e), applied: false };
      console.warn('[photo-surface-projection]', e);
    }
  }

  window.testhpPhotoSurfaceProjection = { sync, buildPlan, getPlan: () => read(PLAN_KEY), getSurface: () => read(SURFACE_KEY), getDiagnostics: () => window.__testhpSpatialProjectionDiagnostics || null };
  window.addEventListener('testhp:evidence-registry-synced', () => setTimeout(sync, 150));
  window.addEventListener('testhp:spatial-contract-changed', () => setTimeout(sync, 150));
  window.addEventListener('testhp:viewport-manager-ready', () => setTimeout(sync, 150));
  window.addEventListener('testhp:spatial-target-changed', () => setTimeout(sync, 150));
  window.addEventListener('testhp:hand-surface-ready', () => setTimeout(() => { const p=read(PLAN_KEY), s=read(SURFACE_KEY); if(p) renderStatus(s,p); }, 0));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(sync, 600), { once:true }); else setTimeout(sync, 600);
})();
