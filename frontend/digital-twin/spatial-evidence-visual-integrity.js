(() => {
  const API = '/api/hand/photo-reconstruction';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const target = () => String(window.testhpSpatialContract?.getTarget?.()?.spatial_id || window.selectedSpatialNode || window.spatialEvidenceTarget || 'hand').replace(/^\/+|\/+$/g, '').toLowerCase();

  async function state() {
    const spatialId = target();
    const r = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0&spatial_id=${encodeURIComponent(spatialId)}`);
    if (!r.ok) throw new Error(`photo state ${r.status}`);
    return r.json();
  }

  function stage5Quality(s) {
    const inputs = Array.isArray(s.inputs) ? s.inputs : [];
    const assigned = inputs.filter(x => VIEWS.includes(x.view));
    const prepared = assigned.filter(x => x.prepared);
    const registered = assigned.filter(x => x.registration?.status === 'registered');
    const distinctViews = new Set(assigned.map(x => x.view));
    const duplicates = VIEWS.filter(v => assigned.filter(x => x.view === v).length > 1);
    return {
      stage: 5,
      name: 'multi-view-quality',
      passed: prepared.length >= 2 && distinctViews.size >= 2,
      counts: { inputs: inputs.length, assigned: assigned.length, prepared: prepared.length, registered: registered.length, distinct_views: distinctViews.size },
      missing_views: VIEWS.filter(v => !distinctViews.has(v)),
      duplicate_views: duplicates,
      checks: {
        at_least_two_views: distinctViews.size >= 2,
        at_least_two_prepared: prepared.length >= 2,
        no_duplicate_view_assignment: duplicates.length === 0
      }
    };
  }

  function stage6Projection(s) {
    const projection = window.testhpPhotoSurfaceProjection?.getPlan?.() || null;
    const diag = window.testhpSpatialProjectionDiagnostics || window.testhpPhotoSurfaceProjection?.getDiagnostics?.() || null;
    const registered = Number(s.registered_count || 0);
    const appliedViews = Array.isArray(diag?.appliedViews) ? diag.appliedViews : [];
    const targetOk = !diag?.target || diag.target === target();
    return {
      stage: 6,
      name: 'projection-integrity',
      passed: !!projection && registered >= 1 && targetOk && appliedViews.length >= 1,
      target: target(),
      registered_count: registered,
      plan_views: projection?.views || [],
      applied_views: appliedViews,
      target_ok: targetOk,
      diagnostics: diag || null
    };
  }

  function stage7Package(s, q, p) {
    const surface = window.testhpPhotoSurfaceProjection?.getSurface?.() || null;
    const packageState = surface?.twinPackage || null;
    const coherentTarget = [s.spatial_id, p.target, surface?.appliedTarget].filter(Boolean).every(v => v === target());
    const ready = q.passed && p.passed && !!packageState && coherentTarget;
    return {
      stage: 7,
      name: 'twin-package-integrity',
      passed: ready,
      target: target(),
      coherent_target: coherentTarget,
      package: packageState,
      applied_to_model: !!surface?.appliedToModel,
      boundary: 'Research visualization only; no clinical anatomy inference.'
    };
  }

  async function run() {
    try {
      const s = await state();
      const q = stage5Quality(s);
      const p = stage6Projection(s);
      const pkg = stage7Package(s, q, p);
      const result = { target: target(), stage5: q, stage6: p, stage7: pkg, generatedAt: new Date().toISOString() };
      window.__testhpSpatialVisualIntegrity = result;
      window.dispatchEvent(new CustomEvent('testhp:spatial-visual-integrity', { detail: result }));
      render(result);
      return result;
    } catch (e) {
      const result = { target: target(), error: e?.message || String(e), generatedAt: new Date().toISOString() };
      window.__testhpSpatialVisualIntegrity = result;
      render(result);
      return result;
    }
  }

  function render(result) {
    const host = document.getElementById('hand-surface-unified-status');
    if (!host) return;
    let el = document.getElementById('spatial-visual-integrity-status');
    if (!el) {
      el = document.createElement('div');
      el.id = 'spatial-visual-integrity-status';
      el.style.cssText = 'margin-top:8px;padding:8px 10px;border:1px solid var(--border,#d8dee8);border-radius:8px;font-size:11px;line-height:1.45';
      host.appendChild(el);
    }
    if (result.error) { el.textContent = `Integralność wizualna: błąd odczytu (${result.error})`; return; }
    const ok = n => result[`stage${n}`]?.passed ? '✓' : '○';
    el.innerHTML = `<strong>Integralność wizualna</strong><br>${ok(5)} Etap 5: jakość widoków · ${ok(6)} Etap 6: projekcja · ${ok(7)} Etap 7: pakiet bliźniaka`;
  }

  window.testhpSpatialVisualIntegrity = { run, getDiagnostics: () => window.__testhpSpatialVisualIntegrity || null };
  window.addEventListener('testhp:hand-surface-ready', () => setTimeout(run, 250));
  window.addEventListener('testhp:evidence-registry-synced', () => setTimeout(run, 250));
  window.addEventListener('testhp:spatial-contract-changed', () => setTimeout(run, 250));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(run, 900), { once: true });
  else setTimeout(run, 900);
})();
