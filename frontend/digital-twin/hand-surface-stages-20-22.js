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
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const readJson = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };
  const writeJson = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const canonicalSpatialId = value => {
    if (!value) return null;
    const raw = typeof value === 'string' ? value : value.spatial_id || value.spatialId || value.targetSpatialId || value.target || value.spatialTarget || null;
    if (!raw || typeof raw !== 'string') return raw;
    return CANONICAL_DEEP_IDS.get(raw) || raw;
  };
  const spatialIdOf = value => canonicalSpatialId(value);
  let lastSpatialTarget = null;
  const rememberSpatialTarget = detail => { const id = spatialIdOf(detail); if (id?.startsWith(TARGET_ROOT)) lastSpatialTarget = id; };
  const managerTarget = () => {
    const m = window.spatialViewportManager;
    return [m?.state?.spatialTarget,m?.state?.spatial_id,m?.state?.spatialId,m?.state?.targetSpatialId,m?.active?.spatial_id,m?.active?.spatialId,m?.active?.targetSpatialId,m?.active?.target].map(spatialIdOf).find(id => id?.startsWith(TARGET_ROOT)) || null;
  };
  const surfaceTarget = () => String(canonicalSpatialId(lastSpatialTarget || managerTarget() || spatialIdOf(window.selectedSpatialNode) || canonicalSpatialId(document.body.dataset.spatialTarget) || spatialIdOf(window.spatialEvidenceTarget) || TARGET_ROOT) || TARGET_ROOT);
  const supported = target => target === TARGET_ROOT || target.startsWith(`${TARGET_ROOT}/`);
  const surface = () => readJson(SURFACE_KEY, {geometry:{},prepared:null,mappings:[],selectedView:'front',geometryTargets:{}});
  const evidence = () => { const x=readJson('digitalTwinEvidenceUX.v2',{evidence:[]}); return Array.isArray(x.evidence) ? x.evidence.filter(e=>!e.archived) : []; };
  const targetEvidence = target => evidence().filter(e => canonicalSpatialId(e.target || e.spatialTarget) === target);
  const preparedViews = target => targetEvidence(target).filter(e=>e.sourceType==='prepared-image' && e.prepared && VIEWS.includes(String(e.view || e.preparedAsset?.view || '').toLowerCase()) || false);
  const viewOf = e => {
    const explicit=String(e?.view || e?.preparedAsset?.view || '').toLowerCase();
    if(VIEWS.includes(explicit)) return explicit;
    const name=String(e?.filename || e?.preparedAsset?.name || '').toLowerCase().replace(/[- ]/g,'_');
    return VIEWS.find(v=>name.includes(v)) || null;
  };
  const registeredViews = target => {
    const s=surface(); const maps=Array.isArray(s.mappings)?s.mappings.filter(m=>canonicalSpatialId(m?.spatialTarget || m?.target)===target):[];
    return VIEWS.filter(v=>maps.some(m=>m?.view===v && Number(m?.quality||0)>0));
  };
  function ensureGeometryContract(){
    const target=surfaceTarget(); if(!supported(target)) return null;
    const s=surface(); s.geometry ||= {}; s.geometryTargets ||= {};
    const existing=s.geometryTargets[target];
    const scalar=k=>Number.isFinite(Number(existing?.parameters?.[k] ?? existing?.[k]))?Number(existing?.parameters?.[k] ?? existing?.[k]):1;
    const manifest=existing?.schema==='hand-surface-geometry-v1' ? {...existing,updatedAt:new Date().toISOString()} : {
      schema:'hand-surface-geometry-v1',spatial_id:target,status:'available',source:'procedural-surface-fallback',method:'procedural-surface-v1',calibrated:false,clinical_claim:false,coordinate_system:'hand-surface-v1',
      parameters:{palmLength:scalar('palmLength'),palmWidth:scalar('palmWidth'),fingerSpread:scalar('fingerSpread'),thumbAngle:scalar('thumbAngle'),taper:scalar('taper'),thickness:scalar('thickness')},
      evidence_boundary:'Geometry is a procedural visualization until measured/photo registration is supplied; it does not infer anatomy.',updatedAt:new Date().toISOString()
    };
    s.geometryTargets[target]=manifest; if(target===TARGET_ROOT){Object.assign(s.geometry,manifest.parameters);s.geometry[target]=manifest;s.geometryManifest=manifest;}
    writeJson(SURFACE_KEY,s); return manifest;
  }
  function planFor(target){
    const s=surface(), maps=Array.isArray(s.mappings)?s.mappings.filter(m=>canonicalSpatialId(m?.spatialTarget || m?.target)===target && Number(m?.quality||0)>0):[];
    const views=VIEWS.filter(v=>maps.some(m=>m.view===v));
    return {schema:'surface-projection-v2',target,views,coverage:views.length/VIEWS.length,method:'registered-view-projection',generatedAt:new Date().toISOString(),ready:views.length>0};
  }
  function packageState(target){
    const manifest=surface().geometryTargets?.[target] || surface().geometry?.[target];
    const registered=registeredViews(target); const plan=readJson(PLAN_KEY,null); const planReady=plan?.schema==='surface-projection-v2' && canonicalSpatialId(plan.target)===target && Array.isArray(plan.views) && plan.views.length>0;
    const calibrated=!!manifest?.calibrated && manifest.source!=='procedural-surface-fallback';
    return {registered,planReady,calibrated,ready:calibrated && registered.length===VIEWS.length && planReady};
  }
  function ensurePanel(){
    if(document.getElementById('hand-surface-stages-20-22')) return;
    const studio=document.getElementById('hand-surface-studio'); if(!studio) return;
    const panel=document.createElement('section'); panel.id='hand-surface-stages-20-22'; panel.style.cssText='margin-top:14px;border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)';
    panel.innerHTML=`<div class="hsr-head"><div><strong>REJESTRACJA</strong><div class="hsr-note">Sprawdź widoki, przygotuj plan projekcji i zweryfikuj pakiet.</div></div><span id="hss2022-status" class="hsr-badge">NIEGOTOWY</span></div><div class="hsr-tabs" role="tablist"><button data-reg-tab="qc" class="active">Kontrola jakości</button><button data-reg-tab="plan">Plan projekcji</button><button data-reg-tab="package">Pakiet bliźniaka</button></div><div id="hss2022-body"></div>`;
    studio.appendChild(panel);
    panel.querySelectorAll('[data-reg-tab]').forEach(b=>b.onclick=()=>{panel.querySelectorAll('[data-reg-tab]').forEach(x=>x.classList.toggle('active',x===b)); render(b.dataset.regTab);});
    render('qc');
  }
  function render(tab='qc'){
    const body=document.getElementById('hss2022-body'), status=document.getElementById('hss2022-status'); if(!body||!status)return;
    const target=surfaceTarget(); if(!supported(target)){status.textContent='NIEGOTOWY';body.textContent='Wybierz wspierany cel powierzchni dłoni.';return;}
    const ps=packageState(target); status.textContent=ps.ready?'GOTOWY':'NIEGOTOWY';
    if(tab==='qc') renderQC(body,target); else if(tab==='plan') renderPlan(body,target); else renderPackage(body,target);
  }
  function renderQC(body,target){
    const ev=targetEvidence(target); const maps=surface().mappings||[]; const rows=VIEWS.map(v=>{const e=ev.find(x=>viewOf(x)===v && x.sourceType==='prepared-image' && x.prepared);const m=maps.find(x=>canonicalSpatialId(x.spatialTarget||x.target)===target && x.view===v && Number(x.quality||0)>0);return `<div class="hsr-row"><strong>${esc(v.replaceAll('_',' '))}</strong><span>${e?'przygotowane':'brak materiału'} · ${m?'zarejestrowane':'niezarejestrowane'}</span></div>`}).join('');
    const reg=registeredViews(target); body.innerHTML=`<div class="hsr-grid"><div><strong>Widoki</strong><div class="hsr-list">${rows}</div></div><div class="hsr-card"><strong>Wynik kontroli</strong><p>${reg.length}/${VIEWS.length} widoków ma rekord rejestracji.</p><p class="hsr-note">Brak rejestracji nie jest zastępowany przez geometrię proceduralną.</p><button id="hsr-open-mapping" class="primary">Otwórz mapowanie powierzchni</button></div></div>`;
    document.getElementById('hsr-open-mapping').onclick=()=>document.querySelector('#hand-surface-studio [data-tab="mapping"]')?.click();
  }
  function renderPlan(body,target){
    const plan=readJson(PLAN_KEY,null), ps=packageState(target); const current=plan&&canonicalSpatialId(plan.target)===target?plan:null;
    body.innerHTML=`<div class="hsr-card"><strong>Plan projekcji</strong><p class="hsr-note">Plan jest wyliczany wyłącznie z faktycznie zarejestrowanych widoków.</p><div class="hsr-metrics"><div><strong>${ps.registered.length}/5</strong><small>widoków</small></div><div><strong>${Math.round((current?.coverage||0)*100)}%</strong><small>pokrycia</small></div><div><strong>${current?'GOTOWY':'BRAK'}</strong><small>plan</small></div></div><button id="hsr-generate-plan" class="primary">${current?'Odśwież plan':'Utwórz plan'}</button>${current?`<pre class="hsr-code">${esc(JSON.stringify(current,null,2))}</pre>`:''}</div>`;
    document.getElementById('hsr-generate-plan').onclick=()=>{writeJson(PLAN_KEY,planFor(target));window.dispatchEvent(new CustomEvent('testhp:surface-projection-plan-changed',{detail:planFor(target)}));render('plan');};
  }
  function renderPackage(body,target){
    const ps=packageState(target); const manifest=surface().geometryTargets?.[target]||surface().geometry?.[target];
    body.innerHTML=`<div class="hsr-package"><div class="hsr-stage"><strong>WEJŚCIE</strong><span>${ps.registered.length}/5 widoków z rejestracją</span></div><div class="hsr-stage"><strong>PRZETWARZANIE</strong><span>geometria ${ps.calibrated?'skalibrowana':'nieskalibrowana'} · plan ${ps.planReady?'gotowy':'brak'}</span></div><div class="hsr-stage"><strong>WYNIK</strong><span>${ps.ready?'pakiet gotowy':'pakiet niegotowy'}</span></div></div><p class="hsr-note">Cel: <code>${esc(target)}</code></p>${!ps.calibrated?'<div class="hsr-warning">Geometria proceduralna jest tylko wizualizacją. Nie jest rejestracją fotograficzną i nie może sama oznaczać pakietu jako gotowego.</div>':''}${!ps.planReady?'<p class="hsr-note">Plan projekcji utworzysz po przejściu do zakładki „Plan projekcji”.</p>':''}`;
  }
  function installCss(){
    if(document.getElementById('hand-surface-registration-css'))return; const s=document.createElement('style');s.id='hand-surface-registration-css';s.textContent=`.hsr-head{display:flex;justify-content:space-between;gap:10px;align-items:center}.hsr-note{font-size:12px;color:#667085}.hsr-badge{font-size:11px;font-weight:800;letter-spacing:.06em}.hsr-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}.hsr-tabs button{border:1px solid var(--border,#d8dee8);background:transparent;border-radius:9px;padding:8px 11px;cursor:pointer;font-weight:700}.hsr-tabs button.active{background:#172033;color:#fff}.hsr-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:12px}.hsr-card{border:1px solid var(--border,#d8dee8);border-radius:10px;padding:12px}.hsr-list{display:grid;gap:6px;margin-top:8px}.hsr-row{display:flex;justify-content:space-between;gap:10px;padding:8px 10px;border:1px solid var(--border,#d8dee8);border-radius:8px}.hsr-row span{font-size:12px;color:#667085}.hsr-metrics,.hsr-package{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.hsr-metrics>div,.hsr-stage{border:1px solid var(--border,#d8dee8);border-radius:9px;padding:10px}.hsr-metrics strong,.hsr-stage span{display:block;font-size:15px}.hsr-metrics small{color:#667085}.hsr-code{margin-top:10px;background:#f6f8fa;border-radius:8px;padding:9px;font-size:11px;overflow:auto;max-height:220px}.hsr-warning{padding:9px;border-radius:8px;background:#fff7ed;color:#9a3412;font-size:12px}@media(max-width:800px){.hsr-grid,.hsr-metrics,.hsr-package{grid-template-columns:1fr}}`;
    document.head.appendChild(s);
  }
  function reconcile(){ensureGeometryContract();ensurePanel();const active=document.querySelector('#hand-surface-stages-20-22 [data-reg-tab].active')?.dataset.regTab||'qc';render(active);}
  let timer=null;const schedule=()=>{if(timer)return;timer=setTimeout(()=>{timer=null;reconcile()},0)};
  function boot(){installCss();reconcile();window.addEventListener('testhp:spatial-target-changed',e=>{rememberSpatialTarget(e.detail);schedule()});window.addEventListener('testhp:spatial-layer-changed',e=>{rememberSpatialTarget(e.detail);schedule()});['testhp:hand-surface-geometry-changed','testhp:evidence-attached','testhp:surface-projection-plan-changed'].forEach(x=>window.addEventListener(x,schedule));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();