(() => {
  const ID='visual-integrity-ux-10-13';
  const $=(s,r=document)=>r.querySelector(s);
  const install=()=>{
    if($('#'+ID)) return $('#'+ID);
    const anchor=$('#visual-integrity-workflow-5-9')||$('#twin-viewport')?.parentElement;
    if(!anchor?.parentElement)return null;
    const el=document.createElement('section');el.id=ID;el.className='panel';
    el.innerHTML=`<header><strong>MODEL 3D</strong><h2>Praca z modelem</h2><p>Najważniejsze działania są tutaj. Szczegóły techniczne pozostają w tle.</p></header><div class="viux-meta" id="viux-meta"></div><div class="viux-actions"><button type="button" class="primary" data-viux="focus">Pokaż wybrane miejsce</button><button type="button" data-viux="surface">Pokaż zdjęcia na modelu</button></div><p class="viux-mobile-note">Na telefonie możesz przewijać sekcje kolejno: model → miejsce → dane.</p>`;
    anchor.parentElement.insertBefore(el,anchor.nextSibling);refresh(el);return el;
  };
  const refresh=el=>{const mode=window.testhpHandGeometryMode?.getMode?.()||'classic',node=window.selectedSpatialNode||window.spatialEvidenceTarget||'brak wybranego miejsca',g=window.spatialViewportManager?.active?.scene,projection=g?.getObjectByName('__spatial_registry_evidence_projection__');$('#viux-meta',el).innerHTML=`<span class="viux-badge">Model: <b>${mode==='real'?'Dopasowany do rzeczywistej dłoni':'Klasyczny'}</b></span><span class="viux-badge">Miejsce: <b>${node}</b></span><span class="viux-badge ${projection?.children?.length?'ok':''}">Zdjęcia powierzchni: <b>${projection?.children?.length||0}</b></span>`};
  const bind=el=>{el.querySelector('[data-viux="focus"]').onclick=()=>{$('#twin-viewport')?.scrollIntoView({behavior:'smooth',block:'center'});refresh(el)};el.querySelector('[data-viux="surface"]').onclick=()=>{window.testhpPhotoSurfaceProjection?.sync?.().then(()=>{refresh(el);$('#twin-viewport')?.scrollIntoView({behavior:'smooth',block:'center'})})}};
  const boot=()=>{const el=install();if(el)bind(el);else new MutationObserver((_,o)=>{const x=install();if(x){bind(x);o.disconnect()}}).observe(document.body,{childList:true,subtree:true})};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();