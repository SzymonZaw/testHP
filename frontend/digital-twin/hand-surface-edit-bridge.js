(() => {
  const STORAGE='digitalTwinEvidenceUX.v2';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const read=()=>{try{const x=JSON.parse(localStorage.getItem(STORAGE)||'{}');return Array.isArray(x.evidence)?x.evidence:[]}catch{return[]}};
  const write=e=>localStorage.setItem(STORAGE,JSON.stringify({evidence:e,target:window.spatialEvidenceTarget||'hand'}));
  function open(item){
    const d=document.createElement('dialog');d.style.cssText='border:0;border-radius:16px;padding:0;max-width:560px;width:92vw';
    d.innerHTML=`<form method="dialog" style="padding:20px"><h2 style="margin-top:0">Edit observation</h2><label style="display:block;margin:10px 0">Type<select id="he-type" style="width:100%;padding:8px"><option>Macro</option><option>Tissue</option><option>Cellular</option><option>Molecular</option><option>Clinical</option></select></label><label style="display:block;margin:10px 0">Timepoint<select id="he-time" style="width:100%;padding:8px"><option>T0</option><option>T1</option><option>T2</option><option>T3</option></select></label><label style="display:block;margin:10px 0">Modality<input id="he-modality" style="width:100%;padding:8px" value="${esc(item.modality)}"></label><label style="display:block;margin:10px 0">Spatial target<input id="he-target" style="width:100%;padding:8px" value="${esc(item.target)}"></label><label style="display:block;margin:10px 0">Comments<textarea id="he-comments" style="width:100%;min-height:90px;padding:8px">${esc(item.comments)}</textarea></label><div style="display:flex;justify-content:flex-end;gap:8px"><button value="cancel">Cancel</button><button id="he-save" value="default" class="primary">Save changes</button></div></form>`;
    document.body.appendChild(d);d.showModal();
    d.querySelector('#he-type').value=item.type||'Macro';d.querySelector('#he-time').value=item.timepoint||'T0';
    d.querySelector('#he-save').onclick=()=>{const all=read(),i=all.findIndex(x=>x.id===item.id);if(i<0)return;const next={...all[i],type:d.querySelector('#he-type').value,timepoint:d.querySelector('#he-time').value,modality:d.querySelector('#he-modality').value,target:d.querySelector('#he-target').value,comments:d.querySelector('#he-comments').value,history:[...(all[i].history||[]),{at:new Date().toISOString(),action:'edited'}]};all[i]=next;write(all);window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));d.close();setTimeout(()=>d.remove(),0)};
    d.addEventListener('close',()=>d.remove(),{once:true});
  }
  window.addEventListener('testhp:edit-evidence',e=>{if(e.detail?.item)open(e.detail.item)});
  const loadStages20to22=()=>{if(document.querySelector('script[data-stages-20-22]'))return;const s=document.createElement('script');s.src='/digital-twin/hand-surface-stages-20-22.js?v=stages-20-22-1';s.dataset.stages20To22='1';document.body.appendChild(s)};
  const loadSimpleUi=()=>{if(document.querySelector('script[data-hand-surface-simple-ui]'))return;const s=document.createElement('script');s.src='/digital-twin/hand-surface-simple-ui.js?v=simple-ui-2';s.dataset.handSurfaceSimpleUi='1';document.body.appendChild(s)};
  const loadHandSurfaceDebug=()=>{if(document.querySelector('script[data-hand-surface-debug]'))return;const s=document.createElement('script');s.src='/digital-twin/hand-surface-debug.js?v=hand-surface-debug-1';s.dataset.handSurfaceDebug='1';document.body.appendChild(s)};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{loadStages20to22();loadSimpleUi();loadHandSurfaceDebug()},{once:true});else{loadStages20to22();loadSimpleUi();loadHandSurfaceDebug()}
})();
