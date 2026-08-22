(() => {
  const start = () => {
    const panel = document.getElementById('twin-debug-panel');
    if (!panel || document.getElementById('hand-surface-debug-flow')) return false;
    const box = document.createElement('section');
    box.id = 'hand-surface-debug-flow';
    box.style.cssText = 'margin:12px 0;padding:12px;border:1px solid #52647a;border-radius:10px;background:#0d1420;color:#dbe7f5;font:12px/1.45 system-ui,sans-serif;';
    box.innerHTML = '<div style="font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">HAND SURFACE · DEBUG FLOW</div><div id="hsd-target" style="margin-bottom:10px"></div><div id="hsd-flow" style="display:grid;gap:6px"></div><div id="hsd-details" style="margin-top:10px;color:#aebed0;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace"></div>';
    panel.appendChild(box);
    const esc = v => String(v ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
    const target = () => { const t=window.testhpSpatialContract?.getTarget?.()||window.selectedSpatialNode||window.spatialEvidenceTarget||'hand'; return typeof t==='object'?{label:t.label||t.path?.join(' > ')||t.spatial_id||t.id||'Bieżący cel',id:t.spatial_id||t.spatialId||t.id||'hand'}:{label:String(t),id:String(t)}; };
    const evidence = () => { try { const x=JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2')||'{}'); return Array.isArray(x.evidence)?x.evidence.filter(x=>!x.archived):[]; } catch { return []; } };
    const geometry = () => { try { return JSON.parse(localStorage.getItem('digitalTwinHandSurface.v1')||'{}'); } catch { return {}; } };
    const targetId = x => String(x?.spatial_id||x?.spatialId||x?.target?.spatial_id||x?.target?.spatialId||x?.target||'');
    const targetItems = (items,id) => items.filter(x => targetId(x) === id);
    const targetGeometry = (g,id) => targetId(g)===id ? g : {};
    const stage = (name,status,detail) => `<div style="display:grid;grid-template-columns:150px 90px 1fr;gap:8px;align-items:center;padding:7px 9px;border:1px solid #26364b;border-radius:7px;background:#111b29"><strong>${esc(name)}</strong><span style="font-weight:800">${esc(status)}</span><span>${esc(detail)}</span></div>`;
    const render = () => { const t=target(),all=evidence(),items=targetItems(all,t.id),g=targetGeometry(geometry(),t.id); const views=['front','back','side_left','side_right','thumb']; const present=views.filter(v=>items.some(x=>{const name=String(x.filename||x.name||'').toLowerCase(); return name.includes(v)||String(x.view||'').toLowerCase()===v;})); const preparedCount=items.filter(x=>x.prepared===true||x.preparedAssetId).length; const regReady=present.length===5&&preparedCount>0; const projectionReady=!!g.projectionPlan; const packageReady=!!g.twinPackage; document.getElementById('hsd-target').innerHTML=`<strong>Aktualny cel:</strong> ${esc(t.label)} <code style="color:#9fc4e8">${esc(t.id)}</code>`; document.getElementById('hsd-flow').innerHTML=[stage('ŹRÓDŁA · 11',items.length?'READY':'EMPTY',`${items.length} rekordów dla celu`),stage('PRZYGOTOWANIE · 12',preparedCount?'READY':'BLOCKED',preparedCount?`${preparedCount} prepared asset dla celu`:'brak prepared asset dla celu'),stage('GEOMETRIA · 13',Object.keys(g).length?'READY':'EMPTY',Object.keys(g).length?'geometria dla celu':'brak geometrii dla celu'),stage('REJESTRACJA · 14',regReady?'READY':present.length?'PARTIAL':'BLOCKED',`${present.length}/5 widoków dla celu`),stage('WORKFLOW · 15',regReady?'READY':'WAITING',regReady?'można kontynuować':'oczekuje na dane celu'),stage('PROJEKCJA · 21',projectionReady?'READY':'WAITING',projectionReady?'plan dla celu':'plan nieutworzony dla celu'),stage('PAKIET · 22',packageReady?'READY':'WAITING',packageReady?'pakiet dla celu':'pakiet nieutworzony dla celu')].join('<div style="text-align:center;color:#71849b">↓</div>'); document.getElementById('hsd-details').textContent=`TARGET: ${t.id}\nEVIDENCE: ${all.length} total | ${items.length} target-linked | prepared=${preparedCount}\nVIEWS: ${present.length}/5 target-scoped\nRENDERER: ${window.spatialViewportManager?.active?.constructor?.name||'unknown'} | manager=${window.spatialViewportManager?'present':'missing'}`; };
    render();
    let scheduled=false; const schedule=()=>{ if(scheduled)return; scheduled=true; requestAnimationFrame(()=>{scheduled=false;render();}); };
    ['testhp:spatial-layer-changed','testhp:spatial-contract-changed','testhp:evidence-attached','testhp:hand-surface-ready','testhp:surface-projection-plan-changed'].forEach(e=>window.addEventListener(e,schedule));
    return true;
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start,{once:true}); else start();
})();
