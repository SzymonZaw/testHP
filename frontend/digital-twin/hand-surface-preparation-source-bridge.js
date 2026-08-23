(() => {
  'use strict';

  const API = '/api/hand/photo-reconstruction';
  const REGISTRY = '/api/spatial/registry';
  const VIEWS = { front:'Przód', back:'Tył', side_left:'Lewa strona', side_right:'Prawa strona', thumb:'Kciuk' };
  const EVIDENCE_KEY = 'digitalTwinEvidenceUX.v2';
  let observer;
  let selected = null;
  let prepared = null;

  const canonical = value => {
    const raw = typeof value === 'string' ? value : value?.spatial_id || value?.spatialId || value?.spatial_node_id || value?.actual_spatial_node_id || value?.target || value?.spatialTarget || 'hand';
    const fn = window.testhpSpatialContract?.canonicalTargetId;
    const aliases = {
      'palm':'hand/palm', 'śródręcze':'hand/palm', 'srodrecze':'hand/palm',
      'thenar eminence':'hand/palm/thenar', 'kłąb kciuka':'hand/palm/thenar', 'klab kciuka':'hand/palm/thenar',
      'hypothenar eminence':'hand/palm/hypothenar', 'kłębik dłoni':'hand/palm/hypothenar', 'klebik dloni':'hand/palm/hypothenar',
      'central palm':'hand/palm/central-palm', 'centralna część dłoni':'hand/palm/central-palm', 'centralna czesc dloni':'hand/palm/central-palm'
    };
    const normalized = String(raw).trim().replace(/^\/+|\/+$/g, '').toLowerCase();
    return String(typeof fn === 'function' ? (fn(normalized) || aliases[normalized] || normalized) : (aliases[normalized] || normalized));
  };
  const target = () => canonical(window.testhpSpatialContract?.getTarget?.() || window.spatialEvidenceTarget || document.body?.dataset?.spatialTarget || 'hand');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const readEvidence = () => { try { const x=JSON.parse(localStorage.getItem(EVIDENCE_KEY)||'{}'); return Array.isArray(x.evidence) ? x.evidence : []; } catch { return []; } };
  const request = async (url, options) => { const r=await fetch(url,options); const b=await r.json().catch(()=>({})); if(!r.ok) throw new Error(b.detail || `Request failed (${r.status})`); return b; };

  async function sourcesForTarget() {
    const t = target();
    const result = [];
    const add = item => {
      const id = item.asset_id || item.id || item.backendAssetId || item.sourceAssetId || item.evidence_id;
      if (!id || item.archived) return;
      const spatial = canonical(item.spatial_id || item.spatialId || item.spatial_node_id || item.actual_spatial_node_id || item.target || item.expected_spatial_node_id || 'hand');
      if (spatial !== t || result.some(x => x.asset_id === id)) return;
      result.push({ ...item, asset_id:id, spatial_id:spatial, filename:item.filename || item.name || id, timepoint:item.timepoint || 'T0' });
    };

    // Registry diagnostics are the source of truth for eligibility.
    // Only ACCEPT decisions with an exact canonical target enter preparation.
    try {
      const payload = await request(`${REGISTRY}?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodeURIComponent(t)}&debug=true`, { cache:'no-store' });
      const decisions = Array.isArray(payload.debug?.decisions) ? payload.debug.decisions : [];
      if (decisions.length) {
        decisions.filter(x => x.matched === true).forEach(add);
      } else if (Array.isArray(payload.items)) {
        payload.items.forEach(add);
      }
    } catch {}

    // Keep the photo-reconstruction manifest as a secondary source for assets
    // that have already entered the preparation workflow.
    try {
      const state = await request(`${API}/state?subject_id=own_cohort&timepoint=T0`, { cache:'no-store' });
      for (const item of (state.inputs || [])) add(item);
    } catch {}

    // Include explicitly saved UX evidence only when it is target-exact.
    for (const item of readEvidence()) add({
      asset_id:item.sourceAssetId || item.asset_id || item.assetId,
      filename:item.filename || item.name,
      view:item.view || '', timepoint:item.timepoint || 'T0', spatial_id:item.spatial_id || item.target,
      prepared:!!item.prepared, prepared_asset_id:item.preparedAssetId || item.prepared_asset_id
    });
    return result;
  }

  function css() {
    if (document.getElementById('hs-prep-source-bridge-css')) return;
    const s=document.createElement('style'); s.id='hs-prep-source-bridge-css';
    s.textContent='.hspsb{display:grid;grid-template-columns:1fr 1fr;gap:14px}.hspsb-box{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}.hspsb-select{width:100%;padding:8px;border:1px solid var(--border,#d8dee8);border-radius:8px;background:var(--panel,#fff);color:inherit}.hspsb-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.hspsb-preview{margin-top:10px;min-height:180px;border:1px dashed var(--border,#d8dee8);border-radius:10px;display:grid;place-items:center;overflow:hidden;background:#f7f8fa}.hspsb-preview img{max-width:100%;max-height:300px;object-fit:contain}.hspsb-pair{display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%}.hspsb-pair figure{margin:0}.hspsb-pair img{width:100%;height:220px;object-fit:contain;background:#f7f8fa;border-radius:8px}.hspsb-pair figcaption{font-size:11px;color:#667085;margin-top:4px}.hspsb-meta{font-size:12px;color:#667085;line-height:1.5;margin-top:8px}.hspsb-status{font-size:12px;margin-top:9px}.hspsb-good{color:#1f6b45}.hspsb-warn{color:#9a6700}.hspsb-upload input{display:none}@media(max-width:800px){.hspsb{grid-template-columns:1fr}.hspsb-pair{grid-template-columns:1fr}}';
    document.head.appendChild(s);
  }

  async function render() {
    const content=document.getElementById('hss-content');
    const active=document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;
    if(!content || active!=='prepare') return;
    css();
    const token=target();
    content.dataset.sourceBridge='1';
    const items=await sourcesForTarget();
    content.innerHTML=`<div class="hspsb">
      <div class="hspsb-box">
        <strong>Zdjęcie źródłowe</strong>
        <p class="hss-note">Wybierz zdjęcie z „Zdjęcia / źródła” przypisane dokładnie do aktualnego celu: <code>${esc(token)}</code>.</p>
        <select id="hspsb-source" class="hspsb-select"><option value="">${items.length ? 'Wybierz zapisane zdjęcie…' : 'Brak zaakceptowanych zdjęć dla tego celu…'}</option>${items.map(x=>`<option value="${esc(x.asset_id)}">${esc(x.filename||x.asset_id)} · ${esc(VIEWS[x.view]||x.view||'widok nieprzypisany')}</option>`).join('')}</select>
        <div id="hspsb-meta" class="hspsb-meta"></div>
        <div class="hspsb-actions"><button id="hspsb-add" type="button" class="primary">＋ Dodaj nowe zdjęcie</button><input id="hspsb-file" type="file" accept="image/jpeg,image/png,image/webp,image/tiff" multiple></div>
        <div id="hspsb-preview" class="hspsb-preview"><span class="hss-note">Wybierz zdjęcie, aby rozpocząć.</span></div>
        <div class="hspsb-actions"><button id="hspsb-run" type="button" class="primary" disabled>Przygotuj zdjęcie</button></div>
      </div>
      <div class="hspsb-box">
        <strong>Przygotowanie</strong>
        <p class="hss-note">System automatycznie usuwa tło, tworzy miękką maskę, przycina pusty obszar i zachowuje informacje potrzebne do późniejszej rejestracji. Oryginał pozostaje niezmieniony.</p>
        <div id="hspsb-result" class="hspsb-meta">Brak przygotowanego wyniku.</div>
        <details><summary>Opcje zaawansowane</summary><label>Tolerancja tła <input id="hspsb-tol" type="number" min="4" max="80" value="28"></label><label>Maksymalny wymiar <input id="hspsb-max" type="number" min="1024" max="8192" value="4096"></label></details>
        <div class="hspsb-actions"><button id="hspsb-save" type="button" disabled>Zapisz przygotowane zdjęcie</button></div>
        <div id="hspsb-status" class="hspsb-status" role="status"></div>
      </div>
    </div>`;

    const select=document.getElementById('hspsb-source'); const meta=document.getElementById('hspsb-meta'); const preview=document.getElementById('hspsb-preview'); const run=document.getElementById('hspsb-run'); const save=document.getElementById('hspsb-save'); const status=document.getElementById('hspsb-status');
    const getItem=()=>items.find(x=>x.asset_id===select.value);
    const update=()=>{ selected=getItem(); run.disabled=!selected; prepared=null; save.disabled=true; if(!selected){meta.textContent='';preview.innerHTML='<span class="hss-note">Wybierz zdjęcie, aby rozpocząć.</span>';return;} meta.innerHTML=`<strong>Cel:</strong> <code>${esc(selected.spatial_id)}</code> · <strong>Widok:</strong> ${esc(VIEWS[selected.view]||selected.view||'nieprzypisany')} · <strong>Czas:</strong> ${esc(selected.timepoint||'T0')}`; preview.innerHTML='<span class="hss-note">Gotowe do przygotowania.</span>';};
    select.addEventListener('change',update);
    document.getElementById('hspsb-add').onclick=()=>document.getElementById('hspsb-file').click();
    document.getElementById('hspsb-file').onchange=async e=>{const files=[...e.target.files||[]];if(!files.length)return;status.textContent=`Dodawanie ${files.length} ${files.length===1?'zdjęcia':'zdjęć'} dla ${token}…`;try{for(const file of files){const form=new FormData();form.append('file',file);form.append('subject_id','own_cohort');form.append('timepoint','T0');form.append('spatial_node_id',token);await request(`${API}/upload`,{method:'POST',body:form});}status.textContent='✓ Zdjęcia dodane. Lista zostanie odświeżona.';window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));setTimeout(render,100);}catch(e){status.textContent=e.message||'Nie udało się dodać zdjęć.';status.className='hspsb-status hspsb-warn';}e.target.value='';};
    run.onclick=async()=>{if(!selected)return;run.disabled=true;status.className='hspsb-status';status.textContent='Przygotowywanie…';try{prepared=await request(`${API}/prepare/${encodeURIComponent(selected.asset_id)}`,{method:'POST'});const id=prepared.prepared_asset_id;if(!id)throw new Error('Brak identyfikatora przygotowanego pliku.');preview.innerHTML=`<div class="hspsb-pair"><figure><img src="${API}/file/source/${encodeURIComponent(selected.asset_id)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(id)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;document.getElementById('hspsb-result').innerHTML=`<span class="hspsb-good">✓ Przygotowane</span><br>${prepared.prepared_width||'?'} × ${prepared.prepared_height||'?'} px · maska + crop + transformacja zachowane`;save.disabled=false;status.textContent='✓ Gotowe. Oryginał pozostał niezmieniony.';status.className='hspsb-status hspsb-good';}catch(e){status.textContent=e.message||'Nie udało się przygotować zdjęcia.';status.className='hspsb-status hspsb-warn';run.disabled=false;}};
    save.onclick=()=>{if(!selected||!prepared)return;try{const raw=JSON.parse(localStorage.getItem(EVIDENCE_KEY)||'{}');const evidence=Array.isArray(raw.evidence)?raw.evidence:[];if(!evidence.some(x=>(x.sourceAssetId||x.asset_id)===selected.asset_id&&x.preparedAssetId===prepared.prepared_asset_id))evidence.unshift({id:`prepared-${prepared.prepared_asset_id}`,type:'Macro',sourceType:'prepared-image',target:token,spatial_id:token,timepoint:selected.timepoint||'T0',view:selected.view,filename:selected.filename,sourceAssetId:selected.asset_id,preparedAssetId:prepared.prepared_asset_id,prepared:true,quality:prepared.quality,crop:prepared.crop,provenance:{sourceAssetId:selected.asset_id,preparation:'photo-reconstruction/prepare',originalUnchanged:true},archived:false,history:[{at:new Date().toISOString(),action:'prepared image saved'}]});localStorage.setItem(EVIDENCE_KEY,JSON.stringify({...raw,evidence,target:token}));}catch{}status.textContent='✓ Przygotowane zdjęcie zapisane i gotowe do rejestracji.';status.className='hspsb-status hspsb-good';window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));};
    update();
  }

  function boot(){const active=document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;if(active==='prepare')render();}
  const schedule=()=>setTimeout(boot,0);
  window.addEventListener('testhp:spatial-contract-changed',schedule);window.addEventListener('testhp:spatial-layer-changed',schedule);window.addEventListener('testhp:evidence-attached',schedule);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',schedule,{once:true});else schedule();
  observer=new MutationObserver(()=>{const content=document.getElementById('hss-content');const active=document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;if(active==='prepare'&&content&&!content.dataset.sourceBridge)render();});
  if(document.body)observer.observe(document.body,{childList:true,subtree:true});
})();
