(()=>{
  const KEY='testhp.handGeometryCapture.v1';
  const VIEWS=['front','back','side_left','side_right','thumb'];
  const DEFAULT={
    session:'session-001',
    scaleMm:0,
    scalePx:0,
    measurements:{
      palmLength:0,palmWidth:0,handThickness:0,
      indexLength:0,middleLength:0,ringLength:0,littleLength:0,
      thumbLength:0,thumbAngle:0
    },
    captured:{front:null,back:null,side_left:null,side_right:null,thumb:null}
  };
  let state=(()=>{try{return {...DEFAULT,...JSON.parse(localStorage.getItem(KEY)||'{}'),measurements:{...DEFAULT.measurements,...(JSON.parse(localStorage.getItem(KEY)||'{}').measurements||{})},captured:{...DEFAULT.captured,...(JSON.parse(localStorage.getItem(KEY)||'{}').captured||{})}}}catch{return structuredClone(DEFAULT)}})();
  const save=()=>localStorage.setItem(KEY,JSON.stringify(state));
  const n=v=>Math.max(0,Number(v)||0);
  const ratio=(v,base)=>base>0?n(v)/base:1;
  const fit=()=>{
    const m=state.measurements;
    const ref=state.scaleMm>0&&state.scalePx>0?state.scaleMm/state.scalePx:0;
    const width=m.palmWidth, length=m.palmLength, thickness=m.handThickness;
    if(!width||!length)return null;
    const fingers=[m.indexLength,m.middleLength,m.ringLength,m.littleLength].filter(Boolean);
    const meanFinger=fingers.length?fingers.reduce((a,b)=>a+b,0)/fingers.length:Math.max(1,length*.42);
    const spread=((m.indexLength&&m.littleLength)?Math.abs(m.indexLength-m.littleLength)/meanFinger:0);
    const params={
      palmLength:Math.min(1.25,Math.max(.75,length/18.5)),
      palmWidth:Math.min(1.25,Math.max(.75,width/8.2)),
      thickness:Math.min(1.25,Math.max(.75,(thickness||2.0)/2.0)),
      fingerSpread:Math.min(1.3,Math.max(.7,1+spread*.55)),
      taper:1,
      thumbAngle:Math.min(1.3,Math.max(.7,1+(n(m.thumbAngle)-35)/70))
    };
    const scaleInfo=ref?{mmPerPx:ref,scaleReferenceMm:state.scaleMm,scaleReferencePx:state.scalePx}:null;
    return {params,scaleInfo,meanFingerLength:meanFinger,referenceQuality:ref?'scaled':'proportion-only'};
  };
  const apply=()=>{
    const result=fit();
    if(!result)return {applied:false,reason:'missing-palm-measurements'};
    const api=window.__testhpPermanentGeometry;
    if(!api?.setState)return {applied:false,reason:'geometry-editor-not-ready',result};
    api.setState(result.params);
    return {applied:true,result};
  };
  const style=`<style id="hand-geometry-capture-css">#hand-geometry-capture{margin:16px 0;border:1px solid var(--border,#d8dee8);border-radius:14px;background:var(--panel,#fff);overflow:hidden}#hand-geometry-capture .hgc-head{padding:16px 18px;border-bottom:1px solid #d8dee8}#hand-geometry-capture .hgc-kicker{font-size:10px;font-weight:800;letter-spacing:.08em;color:#667085;text-transform:uppercase}#hand-geometry-capture h3{margin:3px 0;font-size:18px}#hand-geometry-capture p{font-size:12px;color:#667085}#hand-geometry-capture .hgc-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:12px 18px;border-bottom:1px solid #d8dee8}#hand-geometry-capture .hgc-step{padding:8px;border:1px solid #d8dee8;border-radius:9px;font-size:11px}#hand-geometry-capture .hgc-step.active{border-color:#526f8d;background:rgba(82,111,141,.07)}#hand-geometry-capture .hgc-body{padding:14px 18px}.hgc-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.hgc-grid label{font-size:11px;font-weight:700}.hgc-grid input{display:block;width:100%;box-sizing:border-box;margin-top:4px;padding:7px;border:1px solid #d8dee8;border-radius:7px}.hgc-views{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px}.hgc-view{padding:9px;border:1px dashed #b9c1cb;border-radius:8px;text-align:center;font-size:10px}.hgc-view.ok{border-style:solid;background:rgba(2,122,72,.05)}.hgc-actions{display:flex;gap:8px;align-items:center;margin-top:12px;flex-wrap:wrap}.hgc-actions button{padding:8px 11px}.hgc-result{margin-top:12px;padding:10px;border-radius:8px;background:#f7f8fa;font:11px ui-monospace,monospace;white-space:pre-wrap}@media(max-width:760px){#hand-geometry-capture .hgc-steps,.hgc-grid{grid-template-columns:1fr 1fr}.hgc-views{grid-template-columns:1fr 1fr}.hgc-steps .hgc-step:last-child{grid-column:span 2}}@media(max-width:520px){#hand-geometry-capture .hgc-steps,.hgc-grid{grid-template-columns:1fr}.hgc-steps .hgc-step:last-child{grid-column:auto}}</style>`;
  const render=()=>{
    if(document.getElementById('hand-geometry-capture'))return;
    document.head.insertAdjacentHTML('beforeend',style);
    const el=document.createElement('section');el.id='hand-geometry-capture';el.className='panel';
    el.innerHTML=`<div class="hgc-head"><span class="hgc-kicker">DOPASOWANIE DO RZECZYWISTEJ DŁONI</span><h3>Pomiar → geometria 3D</h3><p>Etapy 1–4 prowadzą od zebrania pięciu widoków do przeliczenia pomiarów na istniejący edytor geometrii. Nie usuwają ani nie zmieniają evidence.</p></div><div class="hgc-steps"><div class="hgc-step active"><b>1. Zdjęcia</b><br>5 kontrolowanych widoków</div><div class="hgc-step"><b>2. Skala</b><br>mm + piksele wzorca</div><div class="hgc-step"><b>3. Pomiary</b><br>proporcje dłoni</div><div class="hgc-step"><b>4. Dopasowanie</b><br>parametry modelu</div></div><div class="hgc-body"><div id="hgc-stage"></div><div class="hgc-actions"><button type="button" data-hgc="back">← Wstecz</button><button type="button" data-hgc="next">Dalej →</button><button type="button" data-hgc="apply">Zastosuj do modelu 3D</button><button type="button" data-hgc="reset">Wyczyść formularz</button><span id="hgc-status" aria-live="polite"></span></div><div id="hgc-result" class="hgc-result" hidden></div></div>`;
    const anchor=document.getElementById('hand-geometry-permanent')||document.querySelector('.timeline')||document.querySelector('.state-panel');
    anchor?.before(el);
    let stage=1;
    const stageEl=el.querySelector('#hgc-stage'),resultEl=el.querySelector('#hgc-result'),statusEl=el.querySelector('#hgc-status');
    const set=(path,value)=>{const [a,b]=path.split('.');state[a][b]=value;save();renderStage()};
    const renderStage=()=>{
      el.querySelectorAll('.hgc-step').forEach((x,i)=>x.classList.toggle('active',i===stage-1));
      if(stage===1){stageEl.innerHTML=`<p><b>Ustawienie zdjęć:</b> dłoń nieruchomo, aparat możliwie prostopadle do powierzchni, stała odległość. Najlepiej dodać prosty wzorzec długości w kadrze.</p><div class="hgc-views">${VIEWS.map(v=>`<label class="hgc-view ${state.captured[v]?'ok':''}"><b>${v}</b><input type="file" accept="image/*" data-view="${v}" style="display:block;width:100%;margin-top:6px"></label>`).join('')}</div><p>Pliki są używane tu jako manifest lokalnej sesji; istniejące API evidence pozostaje bez zmian.</p>`;stageEl.querySelectorAll('input[data-view]').forEach(i=>i.onchange=()=>{state.captured[i.dataset.view]=i.files?.[0]?.name||null;save();renderStage()})}
      if(stage===2){stageEl.innerHTML=`<p>Wzorzec skali powinien leżeć w tej samej płaszczyźnie co dłoń. Wpisz jego znaną długość oraz długość w pikselach na zdjęciu referencyjnym.</p><div class="hgc-grid"><label>Długość wzorca [mm]<input type="number" min="0" step=".1" data-m="scaleMm" value="${state.scaleMm||''}"></label><label>Długość wzorca [px]<input type="number" min="0" step="1" data-m="scalePx" value="${state.scalePx||''}"></label></div>`;stageEl.querySelectorAll('[data-m]').forEach(i=>i.oninput=()=>{state[i.dataset.m]=n(i.value);save()})}
      if(stage===3){const m=state.measurements;stageEl.innerHTML=`<p>Podaj pomiary w mm. Jeśli nie masz suwmiarki, zacznij od długości/szerokości dłoni i później uzupełnij resztę.</p><div class="hgc-grid">${[['palmLength','Długość dłoni'],['palmWidth','Szerokość dłoni'],['handThickness','Grubość dłoni'],['indexLength','Wskazujący'],['middleLength','Środkowy'],['ringLength','Serdeczny'],['littleLength','Mały'],['thumbLength','Kciuk'],['thumbAngle','Kąt kciuka [°]']].map(([k,l])=>`<label>${l} [${k==='thumbAngle'?'°':'mm'}]<input type="number" min="0" step=".1" data-m="${k}" value="${m[k]||''}"></label>`).join('')}</div>`;stageEl.querySelectorAll('[data-m]').forEach(i=>i.oninput=()=>{state.measurements[i.dataset.m]=n(i.value);save()})}
      if(stage===4){const r=fit();stageEl.innerHTML=r?`<p><b>Gotowe do dopasowania.</b> Wynik jest deterministycznym przeliczeniem pomiarów na zakresy istniejącego edytora.</p><pre>${JSON.stringify(r,null,2)}</pre>`:`<p>Brakuje co najmniej długości i szerokości dłoni.</p>`}
      el.querySelector('[data-hgc="back"]').disabled=stage===1;el.querySelector('[data-hgc="next"]').disabled=stage===4;
    };
    el.querySelector('[data-hgc="back"]').onclick=()=>{stage=Math.max(1,stage-1);renderStage()};
    el.querySelector('[data-hgc="next"]').onclick=()=>{stage=Math.min(4,stage+1);renderStage()};
    el.querySelector('[data-hgc="apply"]').onclick=()=>{const r=apply();statusEl.textContent=r.applied?'✓ Zastosowano pomiary do modelu 3D':`⚠ ${r.reason}`;resultEl.hidden=false;resultEl.textContent=JSON.stringify(r,null,2)};
    el.querySelector('[data-hgc="reset"]').onclick=()=>{state=structuredClone(DEFAULT);save();stage=1;statusEl.textContent='Wyczyszczono formularz';renderStage()};
    renderStage();
    window.testhpHandGeometryCapture={getState:()=>structuredClone(state),fit,apply,goTo:n=>{stage=Math.min(4,Math.max(1,n));renderStage()}};
  };
  const boot=()=>{if(window.__testhpHandGeometryCaptureBooted)return;window.__testhpHandGeometryCaptureBooted=true;render()};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();