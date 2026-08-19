(() => {
  const SURFACE_KEY = 'digitalTwinHandSurface.v1';
  const EVIDENCE_KEY = 'digitalTwinEvidenceUX.v2';
  const PLAN_KEY = 'digitalTwinSurfaceProjection.v2';
  const VIEWS = ['front','back','side_left','side_right','thumb'];
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  const readJson = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; }
    catch { return fallback; }
  };
  const surface = () => readJson(SURFACE_KEY, {geometry:{}, prepared:null, mappings:[], selectedView:'front'});
  const evidence = () => {
    const value = readJson(EVIDENCE_KEY, {evidence:[]});
    return Array.isArray(value.evidence) ? value.evidence.filter(x => !x.archived) : [];
  };
  const currentTarget = () => window.spatialEvidenceTarget || window.selectedSpatialNode || document.body.dataset.spatialTarget || 'hand';

  const state = {
    tab: 'registration',
    projection: readJson(PLAN_KEY, {
      schema: 'surface-projection-v2', mode: 'weighted-multiview-plan', target: 'hand', confidence: 0, views: {}, savedAt: null
    })
  };

  function installCss() {
    if ($('hand-surface-20-22-css')) return;
    const style = document.createElement('style');
    style.id = 'hand-surface-20-22-css';
    style.textContent = `
      #hand-surface-stages-20-22{margin-top:16px}.hss22-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:14px}.hss22-card{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}
      .hss22-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.hss22-tabs button{border:1px solid var(--border,#d8dee8);background:transparent;border-radius:999px;padding:6px 10px;cursor:pointer}.hss22-tabs button.active{background:#172033;color:#fff}
      .hss22-head,.hss22-actions,.hss22-row{display:flex;align-items:center;gap:8px}.hss22-head{justify-content:space-between}.hss22-actions{flex-wrap:wrap}.hss22-row{justify-content:space-between;margin:9px 0}.hss22-row label{flex:1}.hss22-row input,.hss22-row select{width:100%;box-sizing:border-box}.hss22-list{display:grid;gap:7px}.hss22-item{border:1px solid var(--border,#d8dee8);border-radius:9px;padding:9px}.hss22-note{font-size:12px;color:#667085}.hss22-badge{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#667085}.hss22-status{padding:9px 10px;border-radius:9px;background:rgba(79,111,143,.08);font-size:12px}.hss22-meter{height:8px;background:#e8edf3;border-radius:999px;overflow:hidden}.hss22-meter i{display:block;height:100%;width:0;background:#4f6f8f;transition:width .2s}.hss22-good{color:#1f6b45}.hss22-warn{color:#9a6700}.hss22-bad{color:#a33a3a}.hss22-code{font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;background:#f6f8fa;border-radius:9px;padding:10px;max-height:260px;overflow:auto}
      @media(max-width:800px){.hss22-grid{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function ensurePanel() {
    if ($('hand-surface-stages-20-22')) return;
    const panel = document.createElement('section');
    panel.id = 'hand-surface-stages-20-22';
    panel.className = 'panel';
    panel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">HAND SURFACE PIPELINE</span><strong>STAGES 20–22</strong></div><span class="muted">registration → projection plan → exportable twin package</span></div><div class="hss22-tabs"><button data-tab="registration" class="active">20 · Registration QA</button><button data-tab="projection">21 · Projection plan</button><button data-tab="package">22 · Twin package</button></div><div id="hss22-content"></div>`;
    const studio = $('hand-surface-studio');
    if (studio) studio.after(panel); else document.querySelector('.timeline')?.before(panel);
    panel.querySelectorAll('[data-tab]').forEach(btn => btn.onclick = () => {
      state.tab = btn.dataset.tab;
      panel.querySelectorAll('[data-tab]').forEach(x => x.classList.toggle('active', x === btn));
      render();
    });
    render();
  }

  function mappingFor(view) {
    const maps = Array.isArray(surface().mappings) ? surface().mappings : [];
    return maps.find(x => x.view === view) || null;
  }

  function evidenceFor(view) {
    return evidence().find(x => String(x.view || '').toLowerCase() === view || (String(x.modality || '').toLowerCase() === 'skin_image' && String(x.preparedAsset?.view || '').toLowerCase() === view)) || null;
  }

  function preparedCount() { return evidence().filter(x => x.prepared && x.sourceType === 'prepared-image').length; }

  function registrationScore() {
    const prepared = preparedCount();
    const mapped = VIEWS.filter(v => Number(mappingFor(v)?.quality || 0) > 0).length;
    const quality = VIEWS.reduce((sum, v) => sum + Number(mappingFor(v)?.quality || 0), 0) / VIEWS.length;
    return Math.round(Math.min(100, mapped / VIEWS.length * 55 + prepared / VIEWS.length * 20 + quality * 25));
  }

  function render() {
    const c = $('hss22-content'); if (!c) return;
    if (state.tab === 'registration') renderRegistration(c);
    if (state.tab === 'projection') renderProjection(c);
    if (state.tab === 'package') renderPackage(c);
  }

  function renderRegistration(c) {
    const score = registrationScore();
    c.innerHTML = `<div class="hss22-grid"><div class="hss22-card"><div class="hss22-head"><strong>Stage 20 · Registration QA</strong><span class="hss22-badge">${score}% ready</span></div><p class="hss22-note">Checks the five intended views before any real multi-view projection. This stage does not pretend that registration is clinically accurate.</p><div class="hss22-meter"><i style="width:${score}%"></i></div><div class="hss22-list" style="margin-top:10px">${VIEWS.map(v => {
      const m = mappingFor(v), e = evidenceFor(v), q = Number(m?.quality || 0);
      const status = q >= .8 ? 'READY' : q > 0 ? 'REVIEW' : e ? 'IMAGE ONLY' : 'MISSING';
      const cls = status === 'READY' ? 'hss22-good' : status === 'MISSING' ? 'hss22-bad' : 'hss22-warn';
      return `<div class="hss22-item"><div class="hss22-head"><strong>${esc(v.replaceAll('_',' '))}</strong><span class="hss22-badge ${cls}">${status}</span></div><small>${e ? esc(e.filename || 'prepared image present') : 'no prepared evidence'} · mapping quality ${q.toFixed(2)}</small></div>`;
    }).join('')}</div></div><div class="hss22-card"><strong>Registration contract</strong><ul><li>coordinate space: <b>hand-surface-v1</b></li><li>view IDs are stable: front/back/side_left/side_right/thumb</li><li>quality is explicit and editable</li><li>missing views remain missing; no synthetic evidence is invented</li></ul><div class="hss22-status">Current spatial target: <b>${esc(currentTarget())}</b><br>Prepared assets in registry: <b>${preparedCount()}</b></div><div class="hss22-actions" style="margin-top:10px"><button id="hss22-refresh" class="primary">Recheck</button><button id="hss22-open-mapping">Open Stage 14</button></div></div></div>`;
    $('hss22-refresh').onclick = render;
    $('hss22-open-mapping').onclick = () => document.querySelector('.hss-tabs [data-tab="mapping"]')?.click();
  }

  function computeProjectionPlan() {
    const mappings = Array.isArray(surface().mappings) ? surface().mappings : [];
    const plan = {schema:'surface-projection-v2',mode:'weighted-multiview-plan',target:currentTarget(),views:{},confidence:0,savedAt:new Date().toISOString()};
    let total = 0;
    VIEWS.forEach(view => {
      const q = Math.max(0, Math.min(1, Number(mappings.find(x => x.view === view)?.quality || 0)));
      const hasPrepared = !!evidenceFor(view);
      const source = hasPrepared ? 1 : 0;
      const weight = Number((q * .75 + source * .25).toFixed(3));
      plan.views[view] = {quality:q,prepared:hasPrepared,weight}; total += weight;
    });
    plan.confidence = Number(Math.min(1, total / VIEWS.length).toFixed(3));
    return plan;
  }

  function savePlan(plan) {
    state.projection = plan;
    localStorage.setItem(PLAN_KEY, JSON.stringify(plan));
    window.dispatchEvent(new CustomEvent('testhp:surface-projection-plan-changed',{detail:plan}));
  }

  function renderProjection(c) {
    const plan = state.projection?.schema === 'surface-projection-v2' ? state.projection : computeProjectionPlan();
    const confidence = Math.round(Number(plan.confidence || 0) * 100);
    c.innerHTML = `<div class="hss22-grid"><div class="hss22-card"><div class="hss22-head"><strong>Stage 21 · Projection plan</strong><span class="hss22-badge">${confidence}% source confidence</span></div><p class="hss22-note">Builds a deterministic source-selection plan for the curved hand surface. It is a preparation layer for true texture projection, not a claim that the current browser implementation performs photogrammetry.</p><div class="hss22-list">${VIEWS.map(v => { const x = plan.views[v] || {quality:0,prepared:false,weight:0}; return `<div class="hss22-item"><div class="hss22-head"><strong>${esc(v.replaceAll('_',' '))}</strong><b>${Math.round(x.weight*100)}%</b></div><div class="hss22-meter"><i style="width:${Math.round(x.weight*100)}%"></i></div><small>registration ${Number(x.quality).toFixed(2)} · prepared ${x.prepared?'yes':'no'}</small></div>`; }).join('')}</div></div><div class="hss22-card"><strong>Projection rules</strong><ul><li>prefer registered views over unregistered images</li><li>prefer prepared foreground-separated assets</li><li>keep the source view in the manifest for provenance</li><li>never fill missing surface data with invented biological texture</li></ul><div class="hss22-status">Target: <b>${esc(plan.target)}</b><br>Mode: <b>${esc(plan.mode)}</b></div><div class="hss22-actions" style="margin-top:10px"><button id="hss22-build-plan" class="primary">Rebuild plan</button><button id="hss22-save-plan">Save plan</button></div></div></div>`;
    $('hss22-build-plan').onclick = () => { state.projection = computeProjectionPlan(); render(); };
    $('hss22-save-plan').onclick = () => { savePlan(plan); $('hss22-save-plan').textContent = 'Saved'; };
  }

  function buildManifest() {
    const s = surface();
    const plan = state.projection?.schema === 'surface-projection-v2' ? state.projection : computeProjectionPlan();
    return {
      schema:'digital-twin-hand-surface-package-v1', generatedAt:new Date().toISOString(), subjectId:'own_cohort', timepoint:'T0',
      spatialTarget:currentTarget(), coordinateSpace:'hand-surface-v1', geometry:s.geometry||{}, landmarks:window.handSurfaceEngine?.landmarks||[],
      preparedAsset:s.prepared ? {name:s.prepared.name,originalName:s.prepared.originalName,width:s.prepared.width,height:s.prepared.height,background:s.prepared.background,crop:s.prepared.crop,status:s.prepared.status} : null,
      mappings:Array.isArray(s.mappings)?s.mappings:[], projectionPlan:plan, evidenceIds:evidence().map(x=>x.id).filter(Boolean),
      provenance:{client:'Hand Digital Twin',stageRange:'20-22',nonClinical:true}
    };
  }

  function downloadManifest(manifest) {
    const blob = new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'});
    const url = URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`hand-surface-package-${Date.now()}.json`;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function validateManifest(manifest) {
    const issues=[];
    if(!manifest.preparedAsset) issues.push('No prepared skin image is registered yet.');
    if(!manifest.mappings.length) issues.push('No view registration records exist yet.');
    const mapped=VIEWS.filter(v=>Number(manifest.mappings.find(x=>x.view===v)?.quality||0)>0);
    if(mapped.length<2) issues.push('At least two registered views are recommended before projection testing.');
    if(manifest.projectionPlan.confidence<.5) issues.push('Projection source confidence is below 50%; treat the plan as review-only.');
    return issues;
  }

  function renderPackage(c) {
    const manifest=buildManifest(), issues=validateManifest(manifest);
    c.innerHTML=`<div class="hss22-grid"><div class="hss22-card"><div class="hss22-head"><strong>Stage 22 · Twin package</strong><span class="hss22-badge ${issues.length?'hss22-warn':'hss22-good'}">${issues.length?'REVIEW REQUIRED':'READY FOR TESTING'}</span></div><p class="hss22-note">Creates a portable, auditable description of the hand-surface setup. Original images stay outside this JSON; the package records their prepared metadata, mappings and provenance.</p><div class="hss22-status">${issues.length?issues.map(x=>`• ${esc(x)}`).join('<br>'):'All required structural contracts are present.'}</div><div class="hss22-actions" style="margin-top:10px"><button id="hss22-export" class="primary">Export package JSON</button><button id="hss22-refresh-package">Refresh validation</button></div></div><div class="hss22-card"><strong>Manifest preview</strong><pre class="hss22-code">${esc(JSON.stringify({schema:manifest.schema,spatialTarget:manifest.spatialTarget,coordinateSpace:manifest.coordinateSpace,preparedAsset:manifest.preparedAsset,mappings:manifest.mappings,projectionConfidence:manifest.projectionPlan.confidence},null,2))}</pre></div></div>`;
    $('hss22-export').onclick=()=>downloadManifest(manifest); $('hss22-refresh-package').onclick=render;
  }

  function updateEngineDebug(){const engine=window.handSurfaceEngine;if(engine){engine.stage=Math.max(Number(engine.stage||8),22);engine.updateDebug?.();}}

  function boot(){
    installCss(); ensurePanel(); updateEngineDebug();
    window.addEventListener('testhp:hand-surface-ready',()=>{updateEngineDebug();render();});
    window.addEventListener('testhp:evidence-attached',render);
    window.addEventListener('testhp:surface-projection-plan-changed',render);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
})();
