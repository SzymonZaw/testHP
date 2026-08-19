(() => {
  const STORAGE = 'digitalTwinEvidenceUX.v2';
  const DATA_STORAGE = 'digitalTwinRegionData.v1';
  const TYPES = {
    tissue: { label: 'TKANKA', title: 'Tkanka', empty: 'Brak danych tkankowych / WSI jawnie przypisanych do tego regionu.' },
    cellular: { label: 'KOMÓRKOWE', title: 'Komórkowe', empty: 'Dane komórkowe wymagają jawnie przypisanych danych mikroskopowych.' },
    molecular: { label: 'MOLEKULARNE', title: 'Molekularne', empty: 'Brak pomiarów molekularnych jawnie przypisanych do tego regionu.' }
  };
  const STATUSES = ['przypisane', 'przygotowane', 'zarejestrowane', 'gotowe do projekcji 3D'];
  const get = id => document.getElementById(id);

  const style = document.createElement('style');
  style.textContent = `
    .ri-data-tools{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}
    .ri-data-tools button,.ri-data-card button{border:1px solid #d5dde2;background:#fff;color:#53616c;border-radius:7px;padding:5px 7px;font-size:8px;font-weight:750;cursor:pointer}
    .ri-data-tools button:hover,.ri-data-card button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
    .ri-data-list{display:grid;gap:5px;margin-top:8px}
    .ri-data-card{border:1px solid #e1e6ea;border-radius:8px;background:#fafbfc;padding:7px}
    .ri-data-card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:6px}
    .ri-data-card-title{font-size:8px;font-weight:800;color:#34424c;overflow:hidden;text-overflow:ellipsis}
    .ri-data-card-status{font-size:7px;color:#146b55;white-space:nowrap}
    .ri-data-card-meta{display:block;margin-top:3px;font-size:7px;color:#8a969f;line-height:1.45}
    .ri-data-card-actions{display:flex;gap:4px;margin-top:5px}.ri-data-card-actions button{flex:1}
    .ri-data-empty{margin-top:8px;padding:8px;border:1px dashed #d5dde2;border-radius:8px;color:#8a969f;font-size:8px}
    .ri-data-dialog{width:min(470px,calc(100vw - 28px));border:1px solid #d5dde2;border-radius:12px;padding:0;box-shadow:0 18px 60px rgba(24,38,48,.2)}
    .ri-data-dialog::backdrop{background:rgba(20,30,35,.28)}
    .ri-data-form{padding:15px}.ri-data-form h3{margin:0 0 12px;font-size:13px;color:#26343e}
    .ri-data-form label{display:block;margin:8px 0 4px;font-size:8px;font-weight:750;color:#53616c}
    .ri-data-form input,.ri-data-form select,.ri-data-form textarea{box-sizing:border-box;width:100%;padding:8px;border:1px solid #d5dde2;border-radius:7px;background:#fff;font-size:9px}
    .ri-data-form textarea{min-height:64px;resize:vertical}.ri-data-form small{display:block;margin-top:4px;color:#8a969f;font-size:7px;line-height:1.4}
    .ri-data-form-actions{display:flex;justify-content:flex-end;gap:6px;margin-top:12px}.ri-data-form-actions button{border:1px solid #d5dde2;background:#fff;border-radius:7px;padding:7px 10px;font-size:9px;font-weight:750;cursor:pointer}.ri-data-form-actions .primary{background:#146b55;border-color:#146b55;color:#fff}
  `;
  document.head.appendChild(style);

  function readData(){ try { const v=JSON.parse(localStorage.getItem(DATA_STORAGE)||'{}'); return Array.isArray(v.items)?v.items:[]; } catch { return []; } }
  function writeData(items){
    localStorage.setItem(DATA_STORAGE, JSON.stringify({version:1,items}));
    try {
      const evidence=JSON.parse(localStorage.getItem(STORAGE)||'{}');
      evidence.evidence=Array.isArray(evidence.evidence)?evidence.evidence:[];
      const managedIds=new Set(items.map(x=>x.evidenceId));
      evidence.evidence=evidence.filter(e=>!String(e.id||'').startsWith('ri-data-') || managedIds.has(e.id));
      items.forEach(item=>{
        const e={id:item.evidenceId,type:item.type,target:item.target,title:item.name,status:item.status,source:item.source||'frontend',createdAt:item.createdAt,updatedAt:item.updatedAt};
        const i=evidence.evidence.findIndex(x=>x.id===e.id); if(i>=0)evidence.evidence[i]=e; else evidence.evidence.push(e);
      });
      localStorage.setItem(STORAGE,JSON.stringify(evidence));
    } catch {}
    window.dispatchEvent(new CustomEvent('testhp:evidence-ux-refresh'));
    window.dispatchEvent(new CustomEvent('testhp:region-data-changed',{detail:{target:currentTarget()}}));
  }

  function currentTarget(){
    const n=window.selectedSpatialNode;
    if(n) return n.spatial_id||n.id||n.regionId||'hand';
    const t=window.spatialEvidenceTarget||get('zone-label')?.textContent||'hand';
    return typeof t==='string'?t:(t.id||t.spatial_id||t.regionId||'hand');
  }
  function currentLabel(){
    const n=window.selectedSpatialNode;
    return n?.label || get('region-title')?.textContent || String(currentTarget()).split('/').pop() || 'Wybrany region';
  }
  function forTarget(item){ return item.target===currentTarget(); }
  function typeItems(type){ return readData().filter(x=>x.type===type&&forTarget(x)); }
  function statusLabel(status){ return status==='gotowe do projekcji 3D'?'gotowe do projekcji 3D':status; }

  function ensureDialog(){
    if(get('ri-data-dialog')) return get('ri-data-dialog');
    const d=document.createElement('dialog'); d.id='ri-data-dialog'; d.className='ri-data-dialog';
    d.innerHTML=`<form class="ri-data-form" id="ri-data-form"><h3 id="ri-data-dialog-title">Dodaj dane</h3><input id="ri-data-id" type="hidden"><label for="ri-data-type">Typ danych</label><select id="ri-data-type"><option value="tissue">Tkanka</option><option value="cellular">Komórkowe</option><option value="molecular">Molekularne</option></select><label for="ri-data-name">Nazwa / opis</label><input id="ri-data-name" type="text" placeholder="np. WSI Śródręcza · preparat 01" required><label for="ri-data-status">Status przepływu</label><select id="ri-data-status">${STATUSES.map(s=>`<option value="${s}">${s}</option>`).join('')}</select><label for="ri-data-source">Źródło / identyfikator</label><input id="ri-data-source" type="text" placeholder="np. WSI-001 / mikroskop M2"><label for="ri-data-file">Plik źródłowy (opcjonalnie)</label><input id="ri-data-file" type="file"><small>Rejestr zapisuje nazwę, typ i metadane pliku. Sam duży plik nie jest kopiowany do localStorage.</small><label for="ri-data-notes">Notatka</label><textarea id="ri-data-notes" placeholder="Dodatkowe informacje o danych…"></textarea><div class="ri-data-form-actions"><button type="button" id="ri-data-cancel">Anuluj</button><button type="submit" class="primary">Zapisz dane</button></div></form>`;
    document.body.appendChild(d);
    get('ri-data-cancel').onclick=()=>d.close();
    get('ri-data-form').onsubmit=e=>{
      e.preventDefault();
      const id=get('ri-data-id').value;
      const old=readData().find(x=>x.id===id);
      const file=get('ri-data-file').files[0];
      const now=new Date().toISOString();
      const item={
        id:id||`ri-data-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
        evidenceId:id?old?.evidenceId||`ri-data-${id}`:`ri-data-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
        target:currentTarget(),
        type:get('ri-data-type').value,
        name:get('ri-data-name').value.trim(),
        status:get('ri-data-status').value,
        source:get('ri-data-source').value.trim(),
        notes:get('ri-data-notes').value.trim(),
        fileName:file?.name||old?.fileName||'',
        fileSize:file?.size||old?.fileSize||0,
        fileType:file?.type||old?.fileType||'',
        createdAt:old?.createdAt||now,
        updatedAt:now
      };
      if(!item.name){alert('Podaj nazwę danych.');return;}
      const all=readData(); const next=id?all.map(x=>x.id===id?item:x):[...all,item]; writeData(next); d.close(); render();
    };
    return d;
  }

  function openEditor(item,type){
    const d=ensureDialog();
    get('ri-data-dialog-title').textContent=item?'Edytuj dane':'Dodaj dane';
    get('ri-data-id').value=item?.id||'';
    get('ri-data-type').value=item?.type||type||'tissue';
    get('ri-data-name').value=item?.name||'';
    get('ri-data-status').value=item?.status||'przypisane';
    get('ri-data-source').value=item?.source||'';
    get('ri-data-notes').value=item?.notes||'';
    get('ri-data-file').value='';
    d.showModal();
  }

  function renderType(type){
    const row=document.querySelector(`.evidence-row[data-ri-type="${type}"]`); if(!row)return;
    const items=typeItems(type); const state=row.querySelector(`#${type}-state`); const status=row.querySelector(`#${type}-status`); const detail=row.querySelector(`#${type}-detail`);
    if(state) state.textContent=items.length?`${items.length} dostępne ${items.length===1?'dane':'dane'}`:'Niedostępne';
    if(status) status.textContent=items.length?items.map(x=>statusLabel(x.status)).join(' · '):'—';
    if(detail) detail.textContent=items.length?`${items.length} ${TYPES[type].title.toLowerCase()} ${items.length===1?'dane':'danych'} jawnie przypisano do tego regionu.`:TYPES[type].empty;
    let list=row.querySelector('.ri-data-list'); if(!list){list=document.createElement('div');list.className='ri-data-list';row.appendChild(list);}
    list.innerHTML=items.length?items.map(x=>`<article class="ri-data-card" data-ri-data-id="${escapeHtml(x.id)}"><div class="ri-data-card-head"><span class="ri-data-card-title">${escapeHtml(x.name)}</span><span class="ri-data-card-status">${escapeHtml(x.status)}</span></div><span class="ri-data-card-meta">${escapeHtml(x.source||'bez źródła')}${x.fileName?' · '+escapeHtml(x.fileName):''}${x.notes?' · '+escapeHtml(x.notes):''}</span><div class="ri-data-card-actions"><button type="button" data-ri-edit="${escapeHtml(x.id)}">Edytuj</button><button type="button" data-ri-delete="${escapeHtml(x.id)}">Usuń</button></div></article>`).join(''):`<div class="ri-data-empty">${escapeHtml(TYPES[type].empty)}</div>`;
    list.querySelectorAll('[data-ri-edit]').forEach(b=>b.onclick=()=>openEditor(readData().find(x=>x.id===b.dataset.riEdit)));
    list.querySelectorAll('[data-ri-delete]').forEach(b=>b.onclick=()=>{const item=readData().find(x=>x.id===b.dataset.riDelete);if(!item||!confirm(`Usunąć dane „${item.name}”?`))return;writeData(readData().filter(x=>x.id!==item.id));render();});
  }

  function ensureRows(){
    Object.keys(TYPES).forEach(type=>{
      const id=`${type}-state`; const state=get(id); if(!state)return; const row=state.closest('.evidence-row'); if(!row)return;
      row.dataset.riType=type;
      if(row.querySelector('.ri-data-tools'))return;
      const tools=document.createElement('div');tools.className='ri-data-tools';tools.innerHTML=`<button type="button" data-ri-add-type="${type}">＋ Dodaj dane</button>`;
      row.appendChild(tools);tools.querySelector('button').onclick=()=>openEditor(null,type);
    });
  }

  function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function render(){ensureRows();Object.keys(TYPES).forEach(renderType);}
  window.addEventListener('testhp:spatial-layer-changed',()=>setTimeout(render,0));
  window.addEventListener('testhp:region-photos-changed',()=>setTimeout(render,0));
  const boot=()=>{render();const inspector=document.querySelector('.inspector');if(inspector)new MutationObserver(()=>render()).observe(inspector,{subtree:true,childList:true,characterData:true});};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
