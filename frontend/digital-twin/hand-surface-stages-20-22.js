(() => {
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];

  const readJson = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; }
    catch { return fallback; }
  };
  const writeJson = (key, value) => localStorage.setItem(key, JSON.stringify(value));

  const spatialIdOf = value => {
    if (!value) return null;
    if (typeof value === 'string') return value;
    return value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
  };
  const surfaceTarget = () => {
    const raw = String(window.spatialEvidenceTarget || spatialIdOf(window.selectedSpatialNode) || document.body.dataset.spatialTarget || 'hand');
    return raw === 'hand/palm' || raw.startsWith('hand/palm/') ? 'hand/palm' : raw;
  };

  // Stage 13 needs a durable geometry contract, not just renderer-local mesh state.
  // The fallback is explicitly marked procedural so it cannot be mistaken for
  // measured or clinically reconstructed anatomy.
  function ensureGeometryContract() {
    const target = surfaceTarget();
    if (target !== 'hand/palm') return;

    const surface = readJson(SURFACE_KEY, { geometry: {}, prepared: null, mappings: [], selectedView: 'front' });
    surface.geometry ||= {};

    const current = surface.geometry;
    const scalar = key => Number.isFinite(Number(current[key])) ? Number(current[key]) : 1;
    const manifest = {
      schema: 'hand-surface-geometry-v1',
      spatial_id: 'hand/palm',
      status: 'available',
      source: 'procedural-surface-fallback',
      method: 'procedural-surface-v1',
      calibrated: false,
      clinical_claim: false,
      coordinate_system: 'hand-surface-v1',
      parameters: {
        palmLength: scalar('palmLength'),
        palmWidth: scalar('palmWidth'),
        fingerSpread: scalar('fingerSpread'),
        thumbAngle: scalar('thumbAngle'),
        taper: scalar('taper'),
        thickness: scalar('thickness')
      },
      evidence_boundary: 'Geometry is a procedural visualization until measured/photo registration is supplied; it does not infer anatomy.',
      updatedAt: new Date().toISOString()
    };

    // Keep the legacy scalar controls for the 13 UI while also publishing the
    // target-scoped manifest consumed by the diagnostics/pipeline.
    Object.assign(surface.geometry, manifest.parameters);
    surface.geometry['hand/palm'] = manifest;
    surface.geometryTargets ||= {};
    surface.geometryTargets['hand/palm'] = manifest;
    surface.geometryManifest = manifest;
    writeJson(SURFACE_KEY, surface);
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-geometry-ready', { detail: manifest }));
  }

  function ensurePanel() {
    if (document.getElementById('hand-surface-stages-20-22')) return;
    const studio = document.getElementById('hand-surface-studio');
    if (!studio) return;
    const panel = document.createElement('section');
    panel.id = 'hand-surface-stages-20-22';
    panel.style.cssText = 'margin-top:14px;border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)';
    panel.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center">
        <strong>STAGES 20–22 · Projection package</strong>
        <span id="hss2022-status" style="font-size:11px;font-weight:700;text-transform:uppercase;color:#667085">WAITING</span>
      </div>
      <div id="hss2022-body" style="margin-top:10px;font-size:13px"></div>`;
    studio.appendChild(panel);
    renderPanel();
  }

  function renderPanel() {
    const body = document.getElementById('hss2022-body');
    const status = document.getElementById('hss2022-status');
    if (!body || !status) return;
    const target = surfaceTarget();
    if (target !== 'hand/palm') {
      status.textContent = 'WAITING';
      body.textContent = 'Projection remains attached to the nearest supported hand surface.';
      return;
    }
    const surface = readJson(SURFACE_KEY, { geometry: {}, mappings: [] });
    const manifest = surface.geometryTargets?.['hand/palm'] || surface.geometry?.['hand/palm'];
    const mappings = Array.isArray(surface.mappings) ? surface.mappings : [];
    const registered = VIEWS.filter(v => mappings.some(m => m?.view === v && Number(m?.quality || 0) > 0)).length;
    const plan = readJson(PLAN_KEY, null);
    const planReady = plan?.schema === 'surface-projection-v2' && plan?.target === 'hand/palm';

    status.textContent = planReady ? 'READY' : manifest ? 'GEOMETRY READY' : 'WAITING';
    body.innerHTML = `
      <div>Cel: <code>hand/palm</code></div>
      <div style="margin-top:6px">Geometria: <b>${manifest ? 'GOTOWA' : 'BRAK'}</b> · źródło: <code>${manifest?.source || '—'}</code> · kalibracja: <b>${manifest?.calibrated ? 'TAK' : 'NIE'}</b></div>
      <div style="margin-top:6px">Rejestracja: <b>${registered}/5</b> widoków · plan projekcji: <b>${planReady ? 'TAK' : 'NIE'}</b></div>
      <div style="margin-top:8px;font-size:12px;color:#667085">Proceduralna geometria odblokowuje kontrakt etapu 13, ale nie tworzy sztucznych zdjęć ani rejestracji.</div>`;
  }

  function boot() {
    ensureGeometryContract();
    ensurePanel();
    renderPanel();
    window.addEventListener('testhp:spatial-target-changed', () => { ensureGeometryContract(); ensurePanel(); renderPanel(); });
    window.addEventListener('testhp:spatial-layer-changed', () => { ensureGeometryContract(); renderPanel(); });
    window.addEventListener('testhp:hand-surface-geometry-changed', () => { ensureGeometryContract(); renderPanel(); });
    window.addEventListener('testhp:evidence-attached', renderPanel);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
