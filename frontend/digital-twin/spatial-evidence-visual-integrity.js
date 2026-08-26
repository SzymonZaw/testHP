(() => {
  // The spatial UI has several read-only consumers (registry, preparation,
  // projection and integrity diagnostics). They can react to the same state
  // event at nearly the same time. Keep one short-lived cache/in-flight request
  // per exact endpoint so an event storm cannot become an HTTP polling loop.
  if (!window.__testhpSpatialRequestGuardInstalled) {
    window.__testhpSpatialRequestGuardInstalled = true;
    const originalFetch = window.fetch.bind(window);
    const cache = new Map();
    const inflight = new Map();
    const TTL_MS = 5000;
    const isTracked = url => /\/api\/(?:spatial\/(?:registry|state)|hand\/photo-reconstruction\/state)(?:\?|$)/.test(url);
    const keyFor = (url, options) => {
      const method = String(options?.method || 'GET').toUpperCase();
      if (method !== 'GET') return null;
      const parsed = new URL(url, location.href);
      if (!isTracked(parsed.pathname + parsed.search)) return null;
      return `${method} ${parsed.pathname}${parsed.search}`;
    };
    const invalidate = () => { cache.clear(); };

    window.fetch = async (input, options = {}) => {
      const url = typeof input === 'string' ? input : input?.url || '';
      const method = String(options?.method || (typeof input !== 'string' ? input?.method : '') || 'GET').toUpperCase();
      if (method !== 'GET') {
        const response = await originalFetch(input, options);
        if (/^\/api\/(?:spatial\/|hand\/photo-reconstruction\/)/.test(new URL(url, location.href).pathname)) invalidate();
        return response;
      }

      const key = keyFor(url, options);
      if (!key) return originalFetch(input, options);

      const now = Date.now();
      const cached = cache.get(key);
      if (cached && now - cached.at < TTL_MS) return cached.response.clone();

      if (inflight.has(key)) {
        const response = await inflight.get(key);
        return response.clone();
      }

      const promise = originalFetch(input, options).then(response => {
        if (response.ok) cache.set(key, { at: Date.now(), response: response.clone() });
        return response;
      }).finally(() => inflight.delete(key));
      inflight.set(key, promise);
      return (await promise).clone();
    };

    window.__testhpSpatialRequestGuard = {
      ttlMs: TTL_MS,
      clear: invalidate,
      stats: () => ({ cacheEntries: cache.size, inflight: inflight.size })
    };
  }

  const API = '/api/hand/photo-reconstruction';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const normalize = v => String(v ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
  const target = () => normalize(window.testhpSpatialContract?.getTarget?.()?.spatial_id || window.selectedSpatialNode?.spatial_id || window.spatialEvidenceTarget || 'hand');
  const isDescendantOf = (child, parent) => { const c=normalize(child), p=normalize(parent); return !!p && (c===p || c.startsWith(`${p}/`)); };

  async function fetchState(spatialId) {
    const r = await fetch(`${API}/state?subject_id=own_cohort&timepoint=T0&spatial_id=${encodeURIComponent(spatialId)}`);
    if (!r.ok) throw new Error(`photo state ${r.status}`);
    return r.json();
  }

  async function state() {
    const t = target();
    const direct = await fetchState(t);
    if (t === 'hand' || direct.registered_count > 0 || direct.prepared_count > 0 || direct.reconstruction) return direct;
    const ancestor = await fetchState('hand');
    if (ancestor.registered_count > 0 || ancestor.prepared_count > 0 || ancestor.reconstruction) {
      return { ...ancestor, spatial_id:t, source_spatial_id:'hand', evidence_scope:'inherited', projection_target:t };
    }
    return direct;
  }

  function stage5Quality(s) {
    const inputs = Array.isArray(s.evidence) ? s.evidence : (Array.isArray(s.inputs) ? s.inputs : []);
    const assigned = inputs.filter(x => VIEWS.includes(x.view || x.registration?.view));
    const byView = new Map();
    for (const x of assigned) {
      const view = x.view || x.registration?.view;
      const previous = byView.get(view);
      const score = (x.registration?.status === 'registered' ? 4 : 0) + (x.prepared ? 2 : x.prepared_asset ? 1 : 0);
      const previousScore = previous ? ((previous.registration?.status === 'registered' ? 4 : 0) + (previous.prepared ? 2 : previous.prepared_asset ? 1 : 0)) : -1;
      if (!previous || score > previousScore) byView.set(view, x);
    }
    const uniqueAssigned = [...byView.values()];
    const prepared = uniqueAssigned.filter(x => x.prepared || x.prepared_asset);
    const registered = uniqueAssigned.filter(x => x.registration?.status === 'registered');
    const distinctViews = new Set(byView.keys());
    return {
      stage:5, name:'multi-view-quality', passed:prepared.length >= 2 && distinctViews.size >= 2,
      counts:{inputs:inputs.length,assigned:uniqueAssigned.length,prepared:prepared.length,registered:registered.length,distinct_views:distinctViews.size},
      missing_views:VIEWS.filter(v=>!distinctViews.has(v)), duplicate_views:[],
      checks:{at_least_two_views:distinctViews.size>=2,at_least_two_prepared:prepared.length>=2,no_duplicate_view_assignment:true}
    };
  }

  function stage6Projection(s) {
    const projection = window.testhpPhotoSurfaceProjection?.getPlan?.() || null;
    const diag = window.__testhpSpatialProjectionDiagnostics || window.testhpPhotoSurfaceProjection?.getDiagnostics?.() || null;
    const registered = Number(s.registered_count || 0);
    const appliedViews = Array.isArray(diag?.appliedViews) ? diag.appliedViews : [];
    const targetOk = !diag?.target || diag.target === target();
    const applied = diag?.reason === 'applied' && appliedViews.length >= 1 && diag?.targetMeshFound === true;
    return {stage:6,name:'projection-integrity',passed:!!projection&&registered>=1&&targetOk&&applied,target:target(),registered_count:registered,plan_views:projection?.views||[],applied_views:appliedViews,target_ok:targetOk,diagnostics:diag||null};
  }

  function stage7Package(s,q,p) {
    const surface = window.testhpPhotoSurfaceProjection?.getSurface?.() || null;
    const packageState = surface?.twinPackage || null;
    const packageScope = packageState?.spatial_id || surface?.projection?.source_spatial_id || null;
    const coherentTarget = !!packageScope && isDescendantOf(target(), packageScope) && (!surface?.appliedTarget || surface.appliedTarget === target());
    const ready = q.passed && p.passed && !!packageState && coherentTarget && !!surface?.appliedToModel;
    return {stage:7,name:'twin-package-integrity',passed:ready,target:target(),coherent_target:coherentTarget,package:packageState,applied_to_model:!!surface?.appliedToModel,boundary:'Research visualization only; no clinical anatomy inference.'};
  }

  async function run() {
    try {
      const s=await state();
      const q=stage5Quality(s), p=stage6Projection(s), pkg=stage7Package(s,q,p);
      const result={target:target(),stage5:q,stage6:p,stage7:pkg,generatedAt:new Date().toISOString()};
      window.__testhpSpatialVisualIntegrity=result;
      window.dispatchEvent(new CustomEvent('testhp:spatial-visual-integrity',{detail:result}));
      render(result); return result;
    } catch(e) {
      const result={target:target(),error:e?.message||String(e),generatedAt:new Date().toISOString()};
      window.__testhpSpatialVisualIntegrity=result; render(result); return result;
    }
  }

  function render(result) {
    const host=document.getElementById('hand-surface-unified-status'); if(!host)return;
    let el=document.getElementById('spatial-visual-integrity-status');
    if(!el){el=document.createElement('div');el.id='spatial-visual-integrity-status';el.style.cssText='margin-top:8px;padding:8px 10px;border:1px solid var(--border,#d8dee8);border-radius:8px;font-size:11px;line-height:1.45';host.appendChild(el);}
    if(result.error){el.textContent=`Integralność wizualna: błąd odczytu (${result.error})`;return;}
    const ok=n=>result[`stage${n}`]?.passed?'✓':'○';
    el.innerHTML=`<strong>Integralność wizualna</strong><br>${ok(5)} Etap 5: jakość widoków · ${ok(6)} Etap 6: projekcja · ${ok(7)} Etap 7: pakiet bliźniaka`;
  }

  // Coalesce noisy bootstrap events. This observer must not run on every
  // registry/state event: a quiet period is enough to refresh diagnostics,
  // and a minimum gap prevents repeated API reads during event storms.
  let scheduledRun = null;
  let running = false;
  let rerunRequested = false;
  let lastRunAt = 0;
  const DEBOUNCE_MS = 2000;
  const MIN_RUN_GAP_MS = 5000;

  function scheduleRun(delay=DEBOUNCE_MS) {
    if (running) {
      rerunRequested = true;
      return;
    }
    if (scheduledRun !== null) return;

    const wait = Math.max(delay, MIN_RUN_GAP_MS - (Date.now() - lastRunAt));
    scheduledRun = setTimeout(async () => {
      scheduledRun = null;
      if (running) { rerunRequested = true; return; }
      running = true;
      try {
        lastRunAt = Date.now();
        await run();
      } finally {
        running = false;
        if (rerunRequested) {
          rerunRequested = false;
          scheduleRun(DEBOUNCE_MS);
        }
      }
    }, wait);
  }

  window.testhpSpatialVisualIntegrity={run,getDiagnostics:()=>window.__testhpSpatialVisualIntegrity||null};
  window.addEventListener('testhp:hand-surface-ready',()=>scheduleRun());
  window.addEventListener('testhp:evidence-registry-synced',()=>scheduleRun());
  window.addEventListener('testhp:spatial-contract-changed',()=>scheduleRun());
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>scheduleRun(900),{once:true});else scheduleRun(900);
})();
