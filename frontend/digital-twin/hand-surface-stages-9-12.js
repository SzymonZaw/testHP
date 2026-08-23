(() => {
  const API = '/api/hand/photo-reconstruction';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const LABELS = {front:'Front',back:'Tył',side_left:'Lewa strona',side_right:'Prawa strona',thumb:'Kciuk'};
  const SCOPE = 'digitalTwinPhotoSpatialScope.v1';
  const $ = id => document.getElementById(id);
  const esc = v => String(v ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const canonical = value => {
    const raw = typeof value === 'string' ? value : value?.spatial_id || value?.spatialId || value?.target || value?.spatialTarget || null;
    if (!raw) return 'hand';
    const fn = window.testhpSpatialContract?.canonicalTargetId;
    return typeof fn === 'function' ? (fn(raw) || 'hand') : String(raw).replace(/^\/+|\/+$/g, '').toLowerCase();
  };
  const target = () => canonical(window.testhpSpatialContract?.getTarget?.() || window.spatialEvidenceTarget || window.selectedSpatialNode || document.body?.dataset?.spatialTarget || 'hand');
  const readScope = () => { try { return JSON.parse(localStorage.getItem(SCOPE) || '{}'); } catch { return {}; } };
  const scoped = (item, id) => canonical(item?.spatial_id || item?.spatialId || item?.target || readScope()[item?.asset_id] || 'hand') === id;
  async function request(path, options) {
    const r = await fetch(`${API}${path}`, options);
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(body.detail || `Request failed (${r.status})`);
    return body;
  }
  function installCss() {
    if ($('hs912-css')) return;
    const s = document.createElement('style'); s.id = 'hs912-css';
    s.textContent = `.hs912{margin-top:16px}.hs912-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.hs912-tabs button{border:1px solid var(--border,#d8dee8);background:transparent;border-radius:999px;padding:6px 10px;cursor:pointer}.hs912-tabs button.active{background:#172033;color:#fff}.hs912-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}.hs912-card{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}.hs912-list{display:grid;gap:7px}.hs912-row{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:8px 10px;border:1px solid var(--border,#d8dee8);border-radius:9px}.hs912-good{color:#1f6b45}.hs912-warn{color:#9a6700}.hs912-muted{font-size:12px;color:#667085}.hs912-meter{height:8px;background:#e8edf3;border-radius:999px;overflow:hidden}.hs912-meter i{display:block;height:100%;width:0;background:#4f6f8f}.hs912-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}@media(max-width:800px){.hs912-grid{grid-template-columns:1fr}}`;
    document.head.appendChild(s);
  }
  function ensurePanel() {
    if ($('hand-surface-stages-9-12')) return;
    const panel = document.createElement('section'); panel.id='hand-surface-stages-9-12'; panel.className='panel hs912';
    panel.innerHTML = `<div class="panel-title"><div><span class="section-kicker">HAND SURFACE · NEXT STEPS</span><strong>STAGES 9–12</strong></div><span class="muted">kalibracja → rekonstrukcja → jakość → manifest</span></div><div class="hs912-tabs"><button data-tab="calibration" class="active">9 · Kalibracja</button><button data-tab="reconstruction">10 · Rekonstrukcja</button><button data-tab="quality">11 · Jakość</button><button data-tab="manifest">12 · Manifest</button></div><div id="hs912-content"></div>`;
    document.querySelector('.timeline')?.before(panel); panel.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{panel.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));render(b.dataset.tab);}); render('calibration');
  }
  async function getState() {
    const id=target();
    try { const state=await request(`/state?subject_id=own_cohort&timepoint=T0`); state.inputs=(state.inputs||[]).filter(x=>scoped(x,id)); return state; }
    catch { return {inputs:[],views:{},prepared_count:0,registered_count:0,reconstruction:null}; }
  }
  async function render(tab) {
    const c=$('hs912-content'); if(!c)return;
    const id=target(); const state=await getState();
    const inputs=state.inputs||[];
    const prepared=inputs.filter(x=>x.prepared&&x.view).length;
    const registered=inputs.filter(x=>x.registration?.status==='registered').length;
    const unique=new Set(inputs.filter(x=>x.view).map(x=>x.view));
    if(tab==='calibration') {
      const missing=VIEWS.filter(v=>!unique.has(v));
      c.innerHTML=`<div class="hs912-grid"><div class="hs912-card"><strong>Etap 9 · Kalibracja celu</strong><p class="hs912-muted">Kalibracja jest jawna i przypisana do dokładnego <code>${esc(id)}</code>. Brak danych kalibracyjnych nie jest zastępowany pozorną geometrią kliniczną.</p><div class="hs912-list">${VIEWS.map(v=>`<div class="hs912-row"><span>${LABELS[v]}</span><strong class="${unique.has(v)?'hs912-good':'hs912-warn'}">${unique.has(v)?'OK':'BRAK'}</strong></div>`).join('')}</div><div class="hs912-actions"><button id="hs912-register" class="primary" ${prepared<2?'disabled':''}>Sprawdź rejestrację</button></div></div><div class="hs912-card"><strong>Warunek wejścia</strong><p class="hs912-muted">Minimum 2 przygotowane widoki. Docelowo pełna kalibracja wymaga parametrów kamery i punktów odpowiadających.</p><p>${prepared}/5 przygotowanych · ${registered}/5 zarejestrowanych</p>${missing.length?`<p class="hs912-warn">Brak widoków: ${missing.map(v=>LABELS[v]).join(', ')}</p>`:'<p class="hs912-good">Wszystkie 5 widoków ma przypisanie.</p>'}</div></div>`;
      $('hs912-register')?.addEventListener('click',async()=>{try{await request(`/register?subject_id=own_cohort&timepoint=T0`,{method:'POST'});render('calibration');}catch(e){alert(e.message)}});
    } else if(tab==='reconstruction') {
      const recon=state.reconstruction;
      c.innerHTML=`<div class="hs912-grid"><div class="hs912-card"><strong>Etap 10 · Rekonstrukcja powierzchni</strong><p class="hs912-muted">Rekonstrukcja może korzystać wyłącznie z danych przypisanych do aktywnego celu. Wynik zachowuje status metody i nie jest przedstawiany jako klinicznie skalibrowany model.</p><div class="hs912-actions"><button id="hs912-build" class="primary" ${prepared<2?'disabled':''}>Zbuduj rekonstrukcję</button><button id="hs912-clear" ${recon?'':'disabled'}>Wyczyść wynik</button></div><div id="hs912-recon-status" style="margin-top:10px">${recon?`Gotowa · ${recon.mesh?.vertex_count||0} wierzchołków · ${recon.mesh?.face_count||0} ścian`:'Brak rekonstrukcji dla tego celu.'}</div></div><div class="hs912-card"><strong>Granica evidence</strong><ul><li>target: <code>${esc(id)}</code></li><li>prepared views: ${prepared}/5</li><li>registered views: ${registered}/5</li><li>metoda: ${esc(recon?.method||'silhouette-envelope-v1')}</li></ul></div></div>`;
      $('hs912-build')?.addEventListener('click',async()=>{const b=$('hs912-build');b.disabled=true;try{await request('/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subject_id:'own_cohort',timepoint:'T0'})});render('reconstruction');}catch(e){alert(e.message);b.disabled=false;}});
      $('hs912-clear')?.addEventListener('click',async()=>{await request('/clear',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subject_id:'own_cohort',timepoint:'T0'})});render('reconstruction');});
    } else if(tab==='quality') {
      const viewScore=prepared/VIEWS.length, registrationScore=registered/VIEWS.length, coverage=Math.min(1,unique.size/VIEWS.length);
      const score=Math.round((viewScore*.45+registrationScore*.35+coverage*.20)*100);
      c.innerHTML=`<div class="hs912-grid"><div class="hs912-card"><strong>Etap 11 · Jakość i niepewność</strong><p class="hs912-muted">Wynik jest wskaźnikiem kompletności procesu, nie oceną jakości medycznej zdjęcia.</p><div class="hs912-meter"><i style="width:${score}%"></i></div><p><strong>${score}%</strong> gotowości technicznej dla <code>${esc(id)}</code></p><div class="hs912-list"><div class="hs912-row"><span>Przygotowanie</span><strong>${prepared}/5</strong></div><div class="hs912-row"><span>Rejestracja</span><strong>${registered}/5</strong></div><div class="hs912-row"><span>Pokrycie widoków</span><strong>${unique.size}/5</strong></div></div></div><div class="hs912-card"><strong>Niepewność</strong><p class="hs912-muted">Niepełne widoki, brak intrinsics/extrinsics lub fallback proceduralny zwiększają niepewność. System nie zamienia tych braków na pewność.</p><p class="${score>=80?'hs912-good':'hs912-warn'}">${score>=80?'Dobra gotowość techniczna':'Wymaga uzupełnienia danych'}</p></div></div>`;
    } else {
      const manifest={schema:'hand-surface-manifest-v1',subject_id:'own_cohort',timepoint:'T0',spatial_id:id,generated_at:new Date().toISOString(),views:{prepared,registered,assigned:[...unique]},reconstruction:state.reconstruction?{id:state.reconstruction.reconstruction_id||null,method:state.reconstruction.method||'silhouette-envelope-v1',vertices:state.reconstruction.mesh?.vertex_count||0,faces:state.reconstruction.mesh?.face_count||0}:null,evidence_boundary:'Manifest opisuje stan techniczny rekonstrukcji; nie jest diagnozą ani kliniczną oceną anatomii.'};
      c.innerHTML=`<div class="hs912-card"><strong>Etap 12 · Manifest i przenośność</strong><p class="hs912-muted">Manifest zapisuje target, kompletność widoków, metodę i granice evidence. Nie kopiuje zdjęć ani nie zmienia ich źródłowej proweniencji.</p><pre style="white-space:pre-wrap;max-height:260px;overflow:auto;background:#f6f8fa;padding:10px;border-radius:8px">${esc(JSON.stringify(manifest,null,2))}</pre><div class="hs912-actions"><button id="hs912-download" class="primary">Eksportuj manifest JSON</button></div></div>`;
      $('hs912-download').onclick=()=>{const blob=new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`hand-surface-${id.replace(/\//g,'_')}-manifest.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
    }
  }
  const boot=()=>{installCss();ensurePanel();window.addEventListener('testhp:spatial-layer-changed',()=>render(document.querySelector('#hand-surface-stages-9-12 [data-tab].active')?.dataset.tab||'calibration'));window.addEventListener('testhp:spatial-contract-changed',()=>render(document.querySelector('#hand-surface-stages-9-12 [data-tab].active')?.dataset.tab||'calibration'));};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
