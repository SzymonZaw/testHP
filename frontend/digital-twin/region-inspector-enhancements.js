(() => {
  const STORAGE = 'digitalTwinEvidenceUX.v2';
  const PHOTO_STORAGE = 'digitalTwinRegionPhotos.v1';
  const style = document.createElement('style');
  style.textContent = `
    .region-inspector-tools{display:flex;align-items:center;gap:6px;margin-top:-6px;margin-bottom:10px;flex-wrap:wrap}
    .region-inspector-tools button{border:1px solid #d5dde2;background:#fff;color:#53616c;border-radius:8px;padding:6px 9px;font-size:9px;font-weight:750;cursor:pointer}
    .region-inspector-tools button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
    .ri-help{display:none;margin:0 0 12px;padding:10px 11px;border:1px solid #dbe5e1;border-radius:10px;background:#f7fbf9;color:#66747d;font-size:9px;line-height:1.55}
    .ri-help.open{display:block}.ri-help strong{display:block;margin-bottom:4px;color:#26343e;font-size:10px}
    .ri-evidence-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin:0 0 12px}
    .ri-evidence-chip{padding:7px 6px;border:1px solid #e1e6ea;border-radius:8px;background:#fafbfc;text-align:center}
    .ri-evidence-chip strong{display:block;font-size:10px;color:#26343e}.ri-evidence-chip span{display:block;margin-top:3px;font-size:7px;color:#8a969f;text-transform:uppercase;letter-spacing:.06em}
    .ri-evidence-chip.available{border-color:#cfe5dc;background:#f4faf7}.ri-evidence-chip.available span{color:#146b55}
    .ri-workflow{margin-top:10px;padding:9px 10px;border:1px dashed #cfd8de;border-radius:9px;background:#fff;color:#788690;font-size:8px;line-height:1.5}.ri-workflow strong{color:#53616c}
    .ri-action-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}.ri-action-row button{border:1px solid #d5dde2;background:#fff;color:#45525d;border-radius:8px;padding:7px 8px;font-size:9px;font-weight:700;cursor:pointer}.ri-action-row button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
    .ri-photo-tools{display:flex;justify-content:space-between;align-items:center;gap:6px;margin-top:8px}.ri-photo-tools button,.ri-photo-card button{border:1px solid #d5dde2;background:#fff;color:#53616c;border-radius:7px;padding:5px 7px;font-size:8px;font-weight:700;cursor:pointer}.ri-photo-tools button:hover,.ri-photo-card button:hover{border-color:#9fc5b8;background:#e9f4f0;color:#146b55}
    .ri-photo-gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin-top:8px}.ri-photo-card{position:relative;border:1px solid #e1e6ea;border-radius:8px;background:#fff;overflow:hidden}.ri-photo-card img{display:block;width:100%;height:92px;object-fit:cover;background:#f1f4f5;cursor:zoom-in}.ri-photo-card img:hover{opacity:.9}.ri-photo-card-body{padding:6px}.ri-photo-name{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:8px;font-weight:750;color:#34424c}.ri-photo-meta{display:block;margin-top:2px;font-size:7px;color:#8a969f}.ri-photo-actions{display:flex;gap:4px;margin-top:5px}.ri-photo-actions button{flex:1}.ri-photo-empty{grid-column:1/-1;padding:12px;text-align:center;border:1px dashed #d5dde2;border-radius:8px;color:#8a969f;font-size:8px}
    .ri-photo-dialog{width:min(430px,calc(100vw - 28px));border:1px solid #d5dde2;border-radius:12px;padding:0;box-shadow:0 18px 60px rgba(24,38,48,.2)}.ri-photo-dialog::backdrop{background:rgba(20,30,35,.28)}.ri-photo-form{padding:15px}.ri-photo-form h3{margin:0 0 12px;font-size:13px;color:#26343e}.ri-photo-form label{display:block;margin:8px 0 4px;font-size:8px;font-weight:750;color:#53616c}.ri-photo-form input,.ri-photo-form select{box-sizing:border-box;width:100%;padding:8px;border:1px solid #d5dde2;border-radius:7px;background:#fff;font-size:9px}.ri-photo-form .ri-form-actions{display:flex;justify-content:flex-end;gap:6px;margin-top:12px}.ri-photo-form button{border:1px solid #d5dde2;background:#fff;border-radius:7px;padding:7px 10px;font-size:9px;font-weight:750;cursor:pointer}.ri-photo-form button.primary{background:#146b55;border-color:#146b55;color:#fff}
    .ri-photo-viewer{width:min(1100px,calc(100vw - 28px));height:min(90vh,860px);border:1px solid #d5dde2;border-radius:12px;padding:0;overflow:hidden;background:#111;box-shadow:0 22px 80px rgba(0,0,0,.35)}
    .ri-photo-viewer::backdrop{background:rgba(10,16,20,.72)}
    .ri-photo-viewer-shell{height:100%;display:flex;flex-direction:column;min-height:0}
    .ri-photo-viewer-bar{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;background:#fff;color:#26343e;font-size:10px}
    .ri-photo-viewer-actions{display:flex;gap:5px;align-items:center}.ri-photo-viewer-actions button{border:1px solid #d5dde2;background:#fff;color:#45525d;border-radius:7px;padding:5px 8px;font-size:9px;font-weight:750;cursor:pointer}.ri-photo-viewer-actions button:hover{background:#f1f5f4}
    .ri-photo-stage{position:relative;flex:1;min-height:0;overflow:hidden;display:flex;align-items:center;justify-content:center;touch-action:none;cursor:grab;background:#111}
    .ri-photo-stage.dragging{cursor:grabbing}.ri-photo-stage img{display:block;max-width:none;max-height:none;user-select:none;-webkit-user-drag:none;transform-origin:center center;will-change:transform}
    .ri-photo-hint{position:absolute;left:10px;bottom:10px;padding:5px 7px;border-radius:6px;background:rgba(0,0,0,.55);color:#fff;font-size:8px;pointer-events:none}
    @media(max-width:700px){.ri-evidence-summary{grid-template-columns:repeat(2,1fr)}.ri-photo-viewer{height:86vh}}
  `;
  document.head.appendChild(style);

  const get = id => document.getElementById(id);
  function spatialTarget() { return window.selectedSpatialNode || window.spatialEvidenceTarget || get('zone-label')?.textContent || 'hand'; }
  function targetKey() { const t=spatialTarget(); return typeof t === 'string' ? t : (t.id || t.spatial_id || t.regionId || 'hand'); }
  function targetLabel() { const node=window.selectedSpatialNode; if(node?.label)return node.label; return String(spatialTarget()).replace(/^hand\//,'').replace(/[-_]+/g,' ').replace(/\b\w/g,x=>x.toUpperCase())||'Wybrany region'; }

  function readPhotos(){ try { const v=JSON.parse(localStorage.getItem(PHOTO_STORAGE)||'{}'); return Array.isArray(v.items)?v.items:[]; } catch { return []; } }
  function writePhotos(items){ localStorage.setItem(PHOTO_STORAGE,JSON.stringify({version:1,items})); window.dispatchEvent(new CustomEvent('testhp:region-photos-changed',{detail:{target:targetKey()}})); }
  function regionPhotos(){ const key=targetKey(); return readPhotos().filter(p=>p.target===key); }
  function escapeHtml(value){ return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

  function ensurePhotoDialog(){
    if(get('ri-photo-dialog')) return get('ri-photo-dialog');
    const dialog=document.createElement('dialog'); dialog.id='ri-photo-dialog'; dialog.className='ri-photo-dialog';
    dialog.innerHTML=`<form class="ri-photo-form" id="ri-photo-form"><h3 id="ri-photo-dialog-title">Dodaj zdjęcie</h3><input id="ri-photo-id" type="hidden"><label for="ri-photo-file">Zdjęcie</label><input id="ri-photo-file" type="file" accept="image/*"><label for="ri-photo-name">Nazwa / opis</label><input id="ri-photo-name" type="text" placeholder="np. Widok boczny Śródręcza"><label for="ri-photo-view">Widok</label><select id="ri-photo-view"><option value="back">back</option><option value="front">front</option><option value="side left">side left</option><option value="side right">side right</option><option value="custom">własny</option></select><div class="ri-form-actions"><button type="button" id="ri-photo-cancel">Anuluj</button><button type="submit" class="primary">Zapisz</button></div></form>`;
    document.body.appendChild(dialog);
    get('ri-photo-cancel').onclick=()=>dialog.close();
    get('ri-photo-form').onsubmit=async e=>{ e.preventDefault(); const id=get('ri-photo-id').value; const file=get('ri-photo-file').files[0]; const name=get('ri-photo-name').value.trim()||file?.name||'Zdjęcie'; const view=get('ri-photo-view').value; const items=readPhotos(); const old=items.find(p=>p.id===id);
      if(!file && !old){ alert('Wybierz zdjęcie.'); return; }
      let data=old?.data||''; if(file) data=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(file);});
      const item={id:id||`photo-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,target:targetKey(),name,view,data,updatedAt:new Date().toISOString()};
      const next=id?items.map(p=>p.id===id?{...p,...item}:p):[...items,item]; writePhotos(next); dialog.close(); renderPhotoGallery();
    };
    return dialog;
  }

  function openPhotoEditor(photo){ const d=ensurePhotoDialog(); get('ri-photo-dialog-title').textContent=photo?'Edytuj zdjęcie':'Dodaj zdjęcie'; get('ri-photo-id').value=photo?.id||''; get('ri-photo-name').value=photo?.name||''; get('ri-photo-view').value=photo?.view||'custom'; get('ri-photo-file').value=''; d.showModal(); }

  const viewerState={photo:null,scale:1,min:0.1,max:6,x:0,y:0,dragging:false,lastX:0,lastY:0};
  function ensurePhotoViewer(){
    if(get('ri-photo-viewer')) return get('ri-photo-viewer');
    const d=document.createElement('dialog'); d.id='ri-photo-viewer'; d.className='ri-photo-viewer';
    d.innerHTML=`<div class="ri-photo-viewer-shell"><div class="ri-photo-viewer-bar"><strong id="ri-photo-viewer-title">Podgląd zdjęcia</strong><div class="ri-photo-viewer-actions"><button type="button" id="ri-photo-zoom-out">−</button><button type="button" id="ri-photo-zoom-reset">100%</button><button type="button" id="ri-photo-zoom-in">＋</button><button type="button" id="ri-photo-viewer-close">Zamknij</button></div></div><div id="ri-photo-stage" class="ri-photo-stage"><img id="ri-photo-viewer-img" alt=""><span class="ri-photo-hint">Kółko myszy: zoom · przeciągnij: przesuwanie</span></div></div>`;
    document.body.appendChild(d);
    get('ri-photo-viewer-close').onclick=()=>d.close();
    get('ri-photo-zoom-in').onclick=()=>setPhotoZoom(viewerState.scale*1.25);
    get('ri-photo-zoom-out').onclick=()=>setPhotoZoom(viewerState.scale/1.25);
    get('ri-photo-zoom-reset').onclick=()=>resetPhotoZoom();
    const stage=get('ri-photo-stage');
    stage.addEventListener('wheel',e=>{e.preventDefault();setPhotoZoom(viewerState.scale*(e.deltaY<0?1.15:1/1.15));},{passive:false});
    stage.addEventListener('pointerdown',e=>{viewerState.dragging=true;viewerState.lastX=e.clientX;viewerState.lastY=e.clientY;stage.classList.add('dragging');stage.setPointerCapture?.(e.pointerId);});
    stage.addEventListener('pointermove',e=>{if(!viewerState.dragging)return;viewerState.x+=e.clientX-viewerState.lastX;viewerState.y+=e.clientY-viewerState.lastY;viewerState.lastX=e.clientX;viewerState.lastY=e.clientY;applyPhotoTransform();});
    const stop=e=>{viewerState.dragging=false;stage.classList.remove('dragging');try{stage.releasePointerCapture?.(e.pointerId);}catch{}};
    stage.addEventListener('pointerup',stop);stage.addEventListener('pointercancel',stop);
    d.addEventListener('close',()=>{viewerState.photo=null;});
    return d;
  }
  function applyPhotoTransform(){const img=get('ri-photo-viewer-img');if(img)img.style.transform=`translate(${viewerState.x}px,${viewerState.y}px) scale(${viewerState.scale})`;const b=get('ri-photo-zoom-reset');if(b)b.textContent=`${Math.round(viewerState.scale*100)}%`;}
  function setPhotoZoom(value){viewerState.scale=Math.max(viewerState.min,Math.min(viewerState.max,value));applyPhotoTransform();}
  function resetPhotoZoom(){viewerState.scale=1;viewerState.x=0;viewerState.y=0;applyPhotoTransform();}
  function openPhotoViewer(photo){
    if(!photo?.data)return;
    const d=ensurePhotoViewer();viewerState.photo=photo;resetPhotoZoom();get('ri-photo-viewer-title').textContent=photo.name||'Podgląd zdjęcia';const img=get('ri-photo-viewer-img');img.src=photo.data;img.alt=photo.name||'Zdjęcie regionu';d.showModal();
  }

  function renderPhotoGallery(){
    const host=get('ri-photo-gallery'); if(!host)return; const photos=regionPhotos();
    host.innerHTML=photos.length?photos.map(p=>`<article class="ri-photo-card" data-photo-id="${escapeHtml(p.id)}"><img src="${p.data}" alt="${escapeHtml(p.name)}" title="Kliknij, aby powiększyć"><div class="ri-photo-card-body"><span class="ri-photo-name">${escapeHtml(p.name)}</span><span class="ri-photo-meta">${escapeHtml(p.view||'własny')}</span><div class="ri-photo-actions"><button type="button" data-photo-zoom="${escapeHtml(p.id)}">Powiększ</button><button type="button" data-photo-edit="${escapeHtml(p.id)}">Edytuj</button><button type="button" data-photo-delete="${escapeHtml(p.id)}">Usuń</button></div></div></article>`).join(''):'<div class="ri-photo-empty">Brak własnych zdjęć dla tego regionu. Dodaj pierwsze zdjęcie.</div>';
    host.querySelectorAll('img[data-noop]').forEach(()=>{});
    host.querySelectorAll('.ri-photo-card img').forEach(img=>img.onclick=()=>{const p=readPhotos().find(x=>x.id===img.closest('.ri-photo-card')?.dataset.photoId);if(p)openPhotoViewer(p);});
    host.querySelectorAll('[data-photo-zoom]').forEach(b=>b.onclick=()=>{const p=readPhotos().find(x=>x.id===b.dataset.photoZoom);if(p)openPhotoViewer(p);});
    host.querySelectorAll('[data-photo-edit]').forEach(b=>b.onclick=()=>{const p=readPhotos().find(x=>x.id===b.dataset.photoEdit);if(p)openPhotoEditor(p);});
    host.querySelectorAll('[data-photo-delete]').forEach(b=>b.onclick=()=>{if(!confirm('Usunąć to zdjęcie z tego regionu?'))return;writePhotos(readPhotos().filter(x=>x.id!==b.dataset.photoDelete));renderPhotoGallery();});
  }

  function ensurePhotoGallery(){
    const row=document.querySelector('.macro-row'); if(!row||get('ri-photo-gallery'))return;
    const box=document.createElement('div'); box.innerHTML=`<div class="ri-photo-tools"><strong style="font-size:8px;color:#53616c">Zdjęcia regionu</strong><button type="button" id="ri-photo-add">＋ Dodaj zdjęcie</button></div><div id="ri-photo-gallery" class="ri-photo-gallery"></div>`;
    row.appendChild(box); get('ri-photo-add').onclick=()=>openPhotoEditor(null); renderPhotoGallery();
  }

  function openObservationWizard(){ const target=spatialTarget(); window.spatialEvidenceTarget=typeof target==='string'?target:(target.id||target.spatial_id||target.regionId||'hand'); window.dispatchEvent(new CustomEvent('testhp:region-observation-requested',{detail:{target:window.spatialEvidenceTarget,label:targetLabel()}})); const add=get('evidence-add'); if(add){add.click();return;} const legacy=get('register-observation')||get('add-biological-observation'); if(legacy)legacy.click(); else document.querySelector('[data-action="add-observation"]')?.click(); }

  function ensureTools(){
    const inspector=document.querySelector('.inspector'), title=inspector?.querySelector('.panel-title'); if(!inspector||!title||get('region-inspector-tools'))return;
    const tools=document.createElement('div'); tools.id='region-inspector-tools'; tools.className='region-inspector-tools'; tools.innerHTML='<button type="button" id="ri-help-toggle">ⓘ Jak to działa?</button>'; title.after(tools);
    const help=document.createElement('div'); help.id='ri-help'; help.className='ri-help'; help.innerHTML='<strong>Wybrany region</strong>Ten panel pokazuje dane przypisane bezpośrednio do zaznaczonego miejsca. Makro oznacza fotografie powierzchni, tkanka — dane WSI, komórkowe — mikroskopię, a molekularne — pomiary molekularne. Dodanie obserwacji otwiera formularz i automatycznie ustawia bieżący cel przestrzenny.'; tools.after(help); get('ri-help-toggle').onclick=()=>{help.classList.toggle('open');get('ri-help-toggle').textContent=help.classList.contains('open')?'ⓘ Ukryj instrukcję':'ⓘ Jak to działa?';};
    const summary=document.createElement('div'); summary.id='ri-evidence-summary'; summary.className='ri-evidence-summary'; summary.innerHTML=[['macro','Makro'],['tissue','Tkanka'],['cellular','Komórkowe'],['molecular','Molekularne']].map(([key,label])=>`<div class="ri-evidence-chip" data-ri-chip="${key}"><strong>—</strong><span>${label}</span></div>`).join(''); help.after(summary);
    const workflow=document.createElement('div'); workflow.id='ri-workflow'; workflow.className='ri-workflow'; workflow.innerHTML='<strong>Przepływ danych</strong><br>przypisane → przygotowane → zarejestrowane → gotowe do projekcji 3D'; summary.after(workflow);
    const actions=document.createElement('div'); actions.id='ri-action-row'; actions.className='ri-action-row'; actions.innerHTML='<button type="button" id="ri-add">＋ Dodaj obserwację</button><button type="button" id="ri-manage">Zarządzaj obserwacjami</button>'; workflow.after(actions);
    get('ri-add').onclick=openObservationWizard; get('ri-manage').onclick=()=>{const target=document.querySelector('.evidence-management,[data-section="evidence-management"],#evidence-workspace');if(target)target.scrollIntoView({behavior:'smooth',block:'center'});else window.dispatchEvent(new CustomEvent('testhp:region-inspector-manage',{detail:{region:spatialTarget()}}));};
  }

  function readStoredEvidence(){try{const parsed=JSON.parse(localStorage.getItem(STORAGE)||'{}');return Array.isArray(parsed.evidence)?parsed.evidence:[];}catch{return[];}}
  function classify(e){const type=String(e.type||'').toLowerCase();if(type==='tissue')return'tissue';if(type==='cellular')return'cellular';if(type==='molecular')return'molecular';if(type==='macro')return'macro';return null;}
  function isForTarget(e,target){const eTarget=e.target||e.spatialNodeId||e.regionId||'';return eTarget===target||eTarget===get('zone-label')?.textContent||String(target).startsWith(String(eTarget)+'/');}
  function updateSummary(){
    const values={macro:get('macro-state')?.textContent||'—',tissue:get('tissue-state')?.textContent||'—',cellular:get('cellular-state')?.textContent||'—',molecular:get('molecular-state')?.textContent||'—'}; const target=spatialTarget(); const local=readStoredEvidence().filter(e=>isForTarget(e,target)); const localCounts={macro:0,tissue:0,cellular:0,molecular:0}; local.forEach(e=>{const key=classify(e);if(key)localCounts[key]++;});
    Object.entries(values).forEach(([key,value])=>{const chip=document.querySelector(`[data-ri-chip="${key}"]`);if(!chip)return;const strong=chip.querySelector('strong'),count=localCounts[key];if(count){strong.textContent=`${count} dostępne${count===1?'':' dane'}`;chip.classList.add('available');return;}if(strong)strong.textContent=value;const available=!/niedostępne|brak danych|nie pokazano|tylko dane nadrzędne|—/i.test(value);chip.classList.toggle('available',available);});
    ensurePhotoGallery(); renderPhotoGallery();
  }

  window.addEventListener('testhp:spatial-layer-changed',event=>{const d=event.detail||{};if(d.spatial_id)window.spatialEvidenceTarget=d.spatial_id;else if(d.id)window.spatialEvidenceTarget=d.id;setTimeout(updateSummary,0);});
  window.addEventListener('testhp:evidence-ux-refresh',()=>setTimeout(updateSummary,0));
  window.addEventListener('testhp:evidence-registry-synced',()=>setTimeout(updateSummary,0));
  window.addEventListener('testhp:region-photos-changed',()=>setTimeout(updateSummary,0));

  let scheduled=false,running=false; const observer=new MutationObserver(()=>{if(running||scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;if(running)return;running=true;observer.disconnect();try{ensureTools();updateSummary();}finally{const inspector=document.querySelector('.inspector');if(inspector)observer.observe(inspector,{subtree:true,childList:true,characterData:true});running=false;}});});
  const start=()=>{ensureTools();updateSummary();const inspector=document.querySelector('.inspector');if(inspector)observer.observe(inspector,{subtree:true,childList:true,characterData:true});};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();