(() => {
  'use strict';

  const API = '/api/hand/photo-reconstruction';
  const REGISTRY = '/api/spatial/registry';
  const EVIDENCE = 'digitalTwinEvidenceUX.v2';
  const VIEW_STORE = 'digitalTwinEvidenceUX.views.v1';
  const VIEWS = {front:'Przód',back:'Tył',side_left:'Lewa strona',side_right:'Prawa strona',thumb:'Kciuk'};
  let observer;
  let state = {inputs:[]};
  let prepared = null;

  const esc = v => String(v ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const canonical = value => {
    const raw = typeof value === 'string' ? value : value?.spatial_id || value?.spatialId || value?.actual_spatial_node_id || value?.spatial_node_id || value?.target || value?.spatialTarget || 'hand';
    const fn = window.testhpSpatialContract?.canonicalTargetId;
    const aliases = {'palm':'hand/palm','śródręcze':'hand/palm','srodrecze':'hand/palm','thenar eminence':'hand/palm/thenar','kłąb kciuka':'hand/palm/thenar','klab kciuka':'hand/palm/thenar','hypothenar eminence':'hand/palm/hypothenar','kłębik dłoni':'hand/palm/hypothenar','klebik dloni':'hand/palm/hypothenar','central palm':'hand/palm/central-palm','centralna część dłoni':'hand/palm/central-palm','centralna czesc dloni':'hand/palm/central-palm'};
    const normalized = String(raw).trim().replace(/^\/+|\/+$/g,'').toLowerCase();
    return String(typeof fn === 'function' ? (fn(normalized) || aliases[normalized] || normalized) : (aliases[normalized] || normalized));
  };
  const target = () => canonical(window.testhpSpatialContract?.getTarget?.() || window.spatialEvidenceTarget || document.body?.dataset?.spatialTarget || 'hand');
  const request = async (url, options) => { const r = await fetch(url, options); const body = await r.json().catch(() => ({})); if(!r.ok) throw new Error(body.detail || `Request failed (${r.status})`); return body; };

  function normalizeItem(item) {
    const id = item?.asset_id || item?.id || item?.backendAssetId || item?.sourceAssetId || item?.evidence_id;
    if(!id || item?.archived) return null;
    const spatial = canonical(item.spatial_id || item.spatialId || item.actual_spatial_node_id || item.spatial_node_id || item.target || item.expected_spatial_node_id);
    if(spatial !== target()) return null;
    return {...item, asset_id:id, spatial_id:spatial, filename:item.filename || item.name || id, timepoint:item.timepoint || 'T0'};
  }

  const readViewStore = () => {
    try {
      const value = JSON.parse(localStorage.getItem(VIEW_STORE) || '{}');
      return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    } catch { return {}; }
  };

  const savedViewFor = item => {
    if (!item) return null;
    const saved = readViewStore();
    return saved[item.asset_id] || saved[item.id] || saved[item.sourceAssetId] || null;
  };

  const withSavedView = item => {
    if (!item) return item;
    const view = item.view || savedViewFor(item);
    return view ? {...item, view} : item;
  };

  async function loadSources() {
    const t = target();
    const byId = new Map();
    try {
      const payload = await request(`${REGISTRY}?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodeURIComponent(t)}&debug=true`, {cache:'no-store'});
      const accepted = Array.isArray(payload.debug?.decisions) ? payload.debug.decisions.filter(x => x.matched === true) : [];
      for(const raw of accepted) { const item = normalizeItem({...raw, spatial_id:raw.actual_spatial_node_id}); if(item) byId.set(item.asset_id,item); }
      if(!accepted.length && Array.isArray(payload.items)) for(const raw of payload.items) { const item=normalizeItem(raw); if(item) byId.set(item.asset_id,item); }
    } catch {}
    try {
      const saved = await request(`${API}/state?subject_id=own_cohort&timepoint=T0`, {cache:'no-store'});
      for(const raw of (saved.inputs || saved.evidence || [])) {
        const item=withSavedView(normalizeItem(raw));
        if(item) byId.set(item.asset_id,item);
      }
    } catch {}
    try {
      const raw = JSON.parse(localStorage.getItem(EVIDENCE) || '{}');
      for(const source of (Array.isArray(raw.evidence) ? raw.evidence : [])) {
        const sourceId = source.sourceAssetId || source.asset_id || source.id || source.backendAssetId;
        const savedView = source.view || savedViewFor({asset_id:sourceId, id:source.id, sourceAssetId:source.sourceAssetId});
        const item = normalizeItem({asset_id:sourceId, id:source.id, filename:source.filename, spatial_id:source.spatial_id || source.target, view:savedView, timepoint:source.timepoint, prepared:source.prepared, prepared_asset_id:source.preparedAssetId || source.prepared_asset_id});
        if(item) {
          const existing = byId.get(item.asset_id) || {};
          const localFields = Object.fromEntries(Object.entries(item).filter(([,value]) => value !== undefined && value !== null && value !== ''));
          const merged = {...existing, ...localFields};
          if (existing.prepared === true && existing.prepared_asset_id) {
            merged.prepared = true;
            merged.prepared_asset_id = existing.prepared_asset_id;
            if (existing.prepared_asset) merged.prepared_asset = existing.prepared_asset;
            if (existing.prepared_path) merged.prepared_path = existing.prepared_path;
          }
          byId.set(item.asset_id,{...merged,view:merged.view || savedViewFor(merged)});
        }
      }
    } catch {}
    state.inputs = [...byId.values()].map(withSavedView);
  }

  async function refreshSelectedFromServer(assetId) {
    if (!assetId) return;
    try {
      const saved = await request(`${API}/state?subject_id=own_cohort&timepoint=T0`, {cache:'no-store'});
      const records = saved.inputs || saved.evidence || [];
      const current = state.inputs.find(x => x.asset_id === assetId);
      const raw = records.find(x => x.asset_id === assetId || (current?.filename && x.filename === current.filename));
      if (!raw) return;

      // The preparation state endpoint can legitimately describe a source at
      // the registered root (`hand`) while the UI source is scoped to the
      // active child target (`hand/palm`). Do not pass this record through
      // normalizeItem here: doing so discarded the exact prepared state that
      // the server had already persisted.
      const serverFields = {
        prepared: raw.prepared === true,
        prepared_asset_id: raw.prepared_asset_id || raw.preparedAssetId,
        prepared_asset: raw.prepared_asset,
        prepared_path: raw.prepared_path,
        preparation: raw.preparation,
        view: raw.view
      };
      const merged = {...current, ...Object.fromEntries(Object.entries(serverFields).filter(([,v]) => v !== undefined && v !== null && v !== ''))};
      const index = state.inputs.findIndex(x => x.asset_id === assetId);
      if (index < 0) state.inputs.push(withSavedView({...merged, asset_id:assetId}));
      else state.inputs[index] = withSavedView(merged);
    } catch {}
  }

  function styles() {
    if(document.getElementById('hs-prep-clean-css')) return;
    const s=document.createElement('style'); s.id='hs-prep-clean-css'; s.textContent='.hs-prep-clean{display:grid;grid-template-columns:1.1fr .9fr;gap:14px}.hs-prep-box{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}.hs-prep-select{width:100%;padding:8px;border:1px solid var(--border,#d8dee8);border-radius:8px;background:var(--panel,#fff);color:inherit}.hs-prep-preview{margin-top:10px;min-height:220px;border:1px dashed var(--border,#d8dee8);border-radius:10px;display:grid;place-items:center;overflow:hidden;background:#f7f8fa}.hs-prep-preview img{max-width:100%;max-height:320px;object-fit:contain}.hs-prep-pair{display:grid;grid-template-columns:1fr 1fr;gap:8px}.hs-prep-pair figure{margin:0}.hs-prep-pair img{width:100%;height:220px;object-fit:contain;background:#f7f8fa;border-radius:8px}.hs-prep-meta,.hs-prep-status{font-size:12px;color:#667085;line-height:1.5;margin-top:8px}.hs-prep-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.hs-prep-good{color:#1f6b45}.hs-prep-warn{color:#9a6700}.hs-prep-clean details{margin-top:12px}.hs-prep-clean details label{display:block;margin:8px 0;font-size:12px}.hs-prep-clean input{max-width:140px}@media(max-width:800px){.hs-prep-clean,.hs-prep-pair{grid-template-columns:1fr}}'; document.head.appendChild(s);
  }

  function render() {
    const content=document.getElementById('hss-content');
    const active=document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;
    if(!content || active!=='prepare') return;
    styles();
    const t=target();
    content.dataset.cleanPreparation='1';
    content.innerHTML=`<div class="hs-prep-clean"><div class="hs-prep-box"><strong>Zdjęcie źródłowe</strong><p class="hss-note">Wybierz zdjęcie zapisane wcześniej w „Zdjęcia / źródła”. Oryginał nie zostanie zmieniony.</p><select id="hs-prep-source" class="hs-prep-select"><option value="">${state.inputs.length?'Wybierz zapisane zdjęcie…':'Brak zaakceptowanych zdjęć dla tego celu…'}</option>${state.inputs.map(x=>`<option value="${esc(x.asset_id)}">${esc(x.filename)} · ${esc(VIEWS[x.view]||x.view||'widok nieprzypisany')}</option>`).join('')}</select><div id="hs-prep-meta" class="hs-prep-meta"></div><div id="hs-prep-preview" class="hs-prep-preview"><span class="hss-note">Wybierz zdjęcie, aby rozpocząć.</span></div><div class="hs-prep-actions"><button id="hs-prep-run" class="primary" type="button" disabled>Przygotuj zdjęcie</button></div></div><div class="hs-prep-box"><strong>Przygotowanie</strong><p class="hss-note">System automatycznie usuwa tło, tworzy miękką maskę, przycina pusty obszar i zachowuje informacje potrzebne do późniejszej rejestracji. Oryginał pozostaje niezmieniony.</p><div id="hs-prep-result" class="hs-prep-meta">Brak przygotowanego wyniku.</div><details><summary>Opcje zaawansowane</summary><label>Tolerancja tła <input id="hs-prep-tol" type="number" min="4" max="80" value="28"></label><label>Maksymalny wymiar <input id="hs-prep-max" type="number" min="1024" max="8192" value="4096"></label></details><div class="hs-prep-actions"><button id="hs-prep-save" type="button" disabled>Zapisz przygotowane zdjęcie</button></div><div id="hs-prep-status" class="hs-prep-status" role="status"></div></div></div>`;
    const select=document.getElementById('hs-prep-source'), meta=document.getElementById('hs-prep-meta'), preview=document.getElementById('hs-prep-preview'), run=document.getElementById('hs-prep-run'), save=document.getElementById('hs-prep-save'), result=document.getElementById('hs-prep-result'), status=document.getElementById('hs-prep-status');
    const selected=()=>state.inputs.find(x=>x.asset_id===select.value);
    const showPrepared = item => {
      if(!item?.prepared || !item.prepared_asset_id) return false;
      const id=item.prepared_asset_id;
      prepared=item.prepared_asset || {prepared_asset_id:id, quality:item.quality, crop:item.crop};
      preview.innerHTML=`<div class="hs-prep-pair"><figure><img src="${API}/file/source/${encodeURIComponent(item.asset_id)}" alt="Oryginał"><figcaption>Oryginał</figcaption></figure><figure><img src="${API}/file/prepared/${encodeURIComponent(id)}" alt="Przygotowane"><figcaption>Po przygotowaniu</figcaption></figure></div>`;
      result.innerHTML=`<span class="hs-prep-good">✓ Przygotowane</span><br>${prepared.prepared_width||prepared.width||'?'} × ${prepared.prepared_height||prepared.height||'?'} px · wynik zapisany po stronie serwera`;
      save.disabled=false; save.dataset.id=id; save.dataset.source=item.asset_id;
      run.disabled=true;
      status.textContent='✓ Zdjęcie jest już przygotowane.'; status.className='hs-prep-status hs-prep-good';
      return true;
    };
    const update=()=>{const item=selected();prepared=null;save.disabled=true;save.dataset.id='';save.dataset.source='';if(!item){run.disabled=true;meta.textContent='';preview.innerHTML='<span class="hss-note">Wybierz zdjęcie, aby rozpocząć.</span>';result.textContent='Brak przygotowanego wyniku.';status.textContent='';return;}const hasSupportedView=Object.prototype.hasOwnProperty.call(VIEWS,item.view);const view=VIEWS[item.view]||item.view||'nieprzypisany';meta.innerHTML=`<strong>Cel:</strong> <code>${esc(item.spatial_id)}</code> · <strong>Widok:</strong> ${esc(view)} · <strong>Czas:</strong> ${esc(item.timepoint||'T0')}`;if(showPrepared(item))return;if(!hasSupportedView){preview.innerHTML='<span class="hss-note hs-prep-warn">⚠️ Przed przygotowaniem przypisz zdjęciu obsługiwany widok w „Zdjęcia / źródła”.</span>';result.textContent='Brak przygotowanego wyniku.';status.textContent='Przygotowanie jest zablokowane, dopóki zdjęcie nie ma przypisanego widoku.';status.className='hs-prep-status hs-prep-warn';run.disabled=true;return;}run.disabled=false;preview.innerHTML='<span class="hss-note">Gotowe do przygotowania.</span>';result.textContent='Brak przygotowanego wyniku.';status.textContent='';status.className='hs-prep-status';};
    select.onchange=async()=>{const assetId=select.value;run.disabled=true;status.textContent='';await refreshSelectedFromServer(assetId);update();};
    run.onclick=async()=>{const item=selected();if(!item)return;if(!Object.prototype.hasOwnProperty.call(VIEWS,item.view)){update();return;}run.disabled=true;status.textContent='Przygotowywanie…';status.className='hs-prep-status';try{
      const savedView = item.view;
      await request(`${API}/assign`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({asset_id:item.asset_id, view:savedView})});
      const response=await request(`${API}/prepare/${encodeURIComponent(item.asset_id)}`,{method:'POST'});
      prepared=response.prepared_asset || response;
      const id=response.prepared_asset_id || prepared.prepared_asset_id;
      if(!id)throw new Error('Brak identyfikatora przygotowanego pliku.');
      item.prepared=true; item.prepared_asset_id=id; item.prepared_asset=prepared; item.view=savedView;
      state.inputs = state.inputs.map(x=>x.asset_id===item.asset_id ? {...x,...item} : x);
      showPrepared(item);
      status.textContent='✓ Gotowe. Oryginał pozostał niezmieniony.'; status.className='hs-prep-status hs-prep-good';
      await loadSources();
      const refreshed=state.inputs.find(x=>x.asset_id===item.asset_id); if(refreshed) { item.prepared=refreshed.prepared; item.prepared_asset_id=refreshed.prepared_asset_id; item.prepared_asset=refreshed.prepared_asset; }
    }catch(err){status.textContent=err.message||'Nie udało się przygotować zdjęcia.';status.className='hs-prep-status hs-prep-warn';run.disabled=false;}};
    save.onclick=()=>{const item=selected();if(!item||!prepared)return;try{const raw=JSON.parse(localStorage.getItem(EVIDENCE)||'{}');const evidence=Array.isArray(raw.evidence)?raw.evidence:[];if(!evidence.some(x=>x.sourceAssetId===item.asset_id&&x.preparedAssetId===prepared.prepared_asset_id))evidence.unshift({id:`prepared-${prepared.prepared_asset_id}`,type:'Macro',sourceType:'prepared-image',target:t,spatial_id:t,timepoint:item.timepoint||'T0',view:item.view,filename:item.filename,sourceAssetId:item.asset_id,preparedAssetId:prepared.prepared_asset_id,prepared:true,quality:prepared.quality,crop:prepared.crop,provenance:{sourceAssetId:item.asset_id,preparation:'photo-reconstruction/prepare',originalUnchanged:true},archived:false,history:[{at:new Date().toISOString(),action:'prepared image saved'}]});localStorage.setItem(EVIDENCE,JSON.stringify({...raw,evidence,target:t}));}catch{}status.textContent='✓ Przygotowane zdjęcie zapisane i gotowe do rejestracji.';status.className='hs-prep-status hs-prep-good';window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));};
    update();
  }

  async function boot(){const active=document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;if(active!=='prepare')return;await loadSources();render();}
  const schedule=()=>setTimeout(()=>boot(),0);
  window.addEventListener('testhp:spatial-contract-changed',schedule);window.addEventListener('testhp:spatial-layer-changed',schedule);window.addEventListener('testhp:evidence-attached',schedule);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',schedule,{once:true});else schedule();
  observer=new MutationObserver(()=>{const active=document.querySelector('#hand-surface-studio .hss-tabs button.active')?.dataset.tab;const content=document.getElementById('hss-content');if(active==='prepare'&&content&&!content.dataset.cleanPreparation)boot();});
  if(document.body)observer.observe(document.body,{childList:true,subtree:true});
})();