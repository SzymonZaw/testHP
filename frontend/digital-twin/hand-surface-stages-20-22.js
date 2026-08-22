(() => {
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const VIEWS = ['front','back','side_left','side_right','thumb'];
  const TARGET_ROOT = 'hand/palm';
  const CANONICAL_DEEP_IDS = new Map([
    ['hand/palm/thenar-eminence', 'hand/palm/thenar'],
    ['hand/palm/hypothenar-eminence', 'hand/palm/hypothenar'],
    ['hand/palm/central-palm-eminence', 'hand/palm/central-palm']
  ]);
  const canonicalSpatialId = value => {
    if (!value) return null;
    const raw = typeof value === 'string' ? value : value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
    if (!raw || typeof raw !== 'string') return raw;
    return CANONICAL_DEEP_IDS.get(raw) || raw;
  };
  const readJson = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; }
    catch { return fallback; }
  };
  const writeJson = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const spatialIdOf = value => canonicalSpatialId(value);

  // Keep the last canonical navigation event locally. The evidence cache can
  // legitimately point at a different target, so it must never win over the
  // current viewport selection. This also fixes the boot-order case where the
  // selected node is represented by the manager/event stream rather than a
  // window global.
  let lastSpatialTarget = null;
  const rememberSpatialTarget = detail => {
    const id = spatialIdOf(detail);
    if (id && typeof id === 'string' && id.startsWith(TARGET_ROOT)) lastSpatialTarget = id;
  };

  window.addEventListener('testhp:spatial-target-changed', event => rememberSpatialTarget(event.detail));
  window.addEventListener('testhp:spatial-layer-changed', event => rememberSpatialTarget(event.detail));

  const managerTarget = () => {
    const manager = window.spatialViewportManager;
    const candidates = [
      manager?.state?.spatialTarget,
      manager?.state?.spatial_id,
      manager?.state?.spatialId,
      manager?.state?.targetSpatialId,
      manager?.active?.spatial_id,
      manager?.active?.spatialId,
      manager?.active?.targetSpatialId,
      manager?.active?.target
    ];
    return candidates.map(spatialIdOf).find(id => typeof id === 'string' && id.startsWith(TARGET_ROOT)) || null;
  };

  const surfaceTarget = () => {
    // Priority is intentional: canonical viewport navigation > manager state
    // > selected-node compatibility globals > evidence-cache target.
    const value = lastSpatialTarget
      || managerTarget()
      || spatialIdOf(window.selectedSpatialNode)
      || canonicalSpatialId(document.body.dataset.spatialTarget)
      || spatialIdOf(window.spatialEvidenceTarget)
      || TARGET_ROOT;
    return String(canonicalSpatialId(value) || TARGET_ROOT);
  };

  function isSupportedTarget(target) {
    return target === TARGET_ROOT || target.startsWith(`${TARGET_ROOT}/`);
  }

  function ensureGeometryContract() {
    const target = surfaceTarget();
    if (!isSupportedTarget(target)) return null;

    const surface = readJson(SURFACE_KEY, {
      geometry: {}, prepared: null, mappings: [], selectedView: 'front', geometryTargets: {}
    });
    surface.geometry ||= {};
    surface.geometryTargets ||= {};

    const existing = surface.geometryTargets[target];
    const scalar = key => {
      const raw = existing?.parameters?.[key] ?? existing?.[key];
      return Number.isFinite(Number(raw)) ? Number(raw) : 1;
    };

    const manifest = existing?.schema === 'hand-surface-geometry-v1'
      ? { ...existing, updatedAt: new Date().toISOString() }
      : {
          schema: 'hand-surface-geometry-v1',
          spatial_id: target,
          status: 'available',
          source: 'procedural-surface-fallback',
          method: 'procedural-surface-v1',
          calibrated: false,
          clinical_claim: false,
          coordinate_system: 'hand-surface-v1',
          parameters: {
            palmLength: scalar('palmLength'), palmWidth: scalar('palmWidth'),
            fingerSpread: scalar('fingerSpread'), thumbAngle: scalar('thumbAngle'),
            taper: scalar('taper'), thickness: scalar('thickness')
          },
          evidence_boundary: 'Geometry is a procedural visualization until measured/photo registration is supplied; it does not infer anatomy.',
          updatedAt: new Date().toISOString()
        };

    surface.geometryTargets[target] = manifest;
    if (target === TARGET_ROOT) {
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
    const studio = document.getElementById('hand-surface-studio');
    if (!studio) return;
    const panel = document.createElement('section');
    panel.id = 'hand-surface-stages-20-22';
    panel.style.cssText = 'margin-top:14px;border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)';
    panel.innerHTML = '<div style="display:flex;justify-content:space-between;gap:10px;align-items:center"><strong>STAGES 20–22 · Projection package</strong><span id="hss2022-status" style="font-size:11px;font-weight:700;text-transform:uppercase;color:#667085">WAITING</span></div><div id="hss2022-body" style="margin-top:10px;font-size:13px"></div>';
    studio.appendChild(panel);
    renderPanel();
  }

  function renderPanel() {
    const body = document.getElementById('hss2022-body');
    const status = document.getElementById('hss2022-status');
    if (!body || !status) return;
    const target = surfaceTarget();
    if (!isSupportedTarget(target)) {
      status.textContent = 'WAITING';
      body.textContent = 'Projection remains attached to a supported hand spatial target.';
      return;
    }
    const surface = readJson(SURFACE_KEY, { geometry: {}, mappings: [], geometryTargets: {} });
    const manifest = surface.geometryTargets?.[target] || surface.geometry?.[target];
    const mappings = Array.isArray(surface.mappings) ? surface.mappings.filter(m => canonicalSpatialId(m?.spatialTarget) === target) : [];
    const registered = VIEWS.filter(v => mappings.some(m => m?.view === v && Number(m?.quality || 0) > 0)).length;
    const plan = readJson(PLAN_KEY, null);
    const planReady = plan?.schema === 'surface-projection-v2' && canonicalSpatialId(plan?.target) === target;
    status.textContent = planReady ? 'READY' : manifest ? 'GEOMETRY READY' : 'WAITING';
    body.innerHTML = `<div>Cel: <code>${target}</code></div><div style="margin-top:6px">Geometria: <b>${manifest ? 'GOTOWA' : 'BRAK'}</b> · źródło: <code>${manifest?.source || '—'}</code> · kalibracja: <b>${manifest?.calibrated ? 'TAK' : 'NIE'}</b></div><div style="margin-top:6px">Rejestracja: <b>${registered}/5</b> widoków · plan projekcji: <b>${planReady ? 'TAK' : 'NIE'}</b></div><div style="margin-top:8px;font-size:12px;color:#667085">Proceduralna geometria odblokowuje kontrakt etapu 13, ale nie tworzy sztucznych zdjęć ani rejestracji.</div>`;
  }

  let reconcileTimer = null;
  function reconcile() {
    ensureGeometryContract();
    ensurePanel();
    renderPanel();
  }
  function scheduleReconcile() {
    if (reconcileTimer) return;
    reconcileTimer = window.setTimeout(() => { reconcileTimer = null; reconcile(); }, 0);
  }

  function boot() {
    reconcile();
    scheduleReconcile();
    window.addEventListener('testhp:spatial-target-changed', event => { rememberSpatialTarget(event.detail); scheduleReconcile(); });
    window.addEventListener('testhp:spatial-layer-changed', event => { rememberSpatialTarget(event.detail); scheduleReconcile(); });
    window.addEventListener('testhp:hand-surface-geometry-changed', scheduleReconcile);
    window.addEventListener('testhp:evidence-attached', scheduleReconcile);
    window.addEventListener('testhp:surface-projection-plan-changed', scheduleReconcile);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
