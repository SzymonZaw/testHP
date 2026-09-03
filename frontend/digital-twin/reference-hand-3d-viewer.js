(() => {
  'use strict';
  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const NIH_ENTRY_URL = 'https://3d.nih.gov/entries/3DPX-017237';
  const NIH_GLB_URL = 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511847';
  const PROXY_URL = '/api/hand/photo-reconstruction/reference-glb';
  const VIEWER_VERSION = 'reference-glb-safe-29';
  const LOCAL_SPATIAL_URL = '/api/reference/tissue/human-skin-spatial-census/cells/preview?region=forearm&limit=100';

  let observer = null;
  let retryTimer = null;
  let loadPollTimer = null;
  let bootToken = 0;
  let loadingPromise = null;
  let activeModel = null;
  let spatialPreviewPromise = null;

  function state(p = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({
      installed:true, version:VIEWER_VERSION, active:false, loading:false, loaded:false,
      sourceId:SOURCE_ID, entryUrl:NIH_ENTRY_URL, assetUrl:NIH_GLB_URL, proxyUrl:PROXY_URL,
      assetFormat:'glb', provenance:'public_reference', ownership:'reference', userHealthData:false,
      regionId:window.__testhpReferenceHandState?.regionId || 'palm', error:null, ...p
    });
    return window.__testhpReferenceHand3DViewerState;
  }
  function host(){return document.getElementById('testhp-end-user-layer');}
  function mountPoint(){const h=host();if(!h)return null;return h.querySelector('#twin-viewport')||h.querySelector('.dt-viewport')||h.querySelector('.center .viewport')||h.querySelector('.viewport')||h;}
  function styles(){
    if(document.getElementById('testhp-reference-hand-3d-style'))return;
    const s=document.createElement('style');
    s.id='testhp-reference-hand-3d-style';
    s.textContent='.dt-reference-3d-card{position:relative;min-height:520px;width:100%;margin:16px 0;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;box-sizing:border-box}.dt-reference-3d-model{display:block;width:100%;height:520px;border:0;background:#0b1118}.dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}.dt-reference-3d-title,.dt-reference-3d-source,.dt-reference-3d-status,.dt-reference-3d-mapping{position:absolute;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}.dt-reference-3d-title{left:16px;top:14px;color:#dce7f2}.dt-reference-3d-source{right:16px;top:14px}.dt-reference-3d-status{left:16px;bottom:14px}.dt-reference-3d-mapping{right:16px;bottom:14px}.dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:#0b1118;z-index:3}.dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}.dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}.dt-reference-spatial-card{width:100%;margin:16px 0;border:1px solid #263545;border-radius:16px;background:#0b1118;box-sizing:border-box;padding:16px;color:#dce7f2}.dt-reference-spatial-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:10px}.dt-reference-spatial-title{font:800 12px/1.3 system-ui,sans-serif;letter-spacing:.05em}.dt-reference-spatial-sub{font:600 10px/1.4 system-ui,sans-serif;color:#8fa2b6}.dt-reference-spatial-status{font:700 10px/1.4 system-ui,sans-serif;color:#9fb0c2;text-align:right}.dt-reference-spatial-canvas{display:block;width:100%;height:320px;border:1px solid #263545;border-radius:12px;background:#071016}.dt-reference-spatial-note{margin-top:9px;font:600 10px/1.5 system-ui,sans-serif;color:#8fa2b6}.dt-reference-spatial-error{color:#d6a64f}.dt-reference-spatial-meta{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font:600 10px/1.4 system-ui,sans-serif;color:#9fb0c2}.dt-reference-spatial-pill{padding:5px 7px;border-radius:8px;background:#0d151e;border:1px solid #263545}';
    document.head.appendChild(s)
  }
  function card(m){if(!m)return null;let c=m.querySelector(':scope > .dt-reference-3d-card');if(c)return c;c=document.createElement('section');c.className='dt-reference-3d-card';c.setAttribute('aria-label','NIH 3D reference hand');c.innerHTML='<model-viewer class="dt-reference-3d-model" alt="NIH 3D healthy adult human hand reference template" loading="eager" reveal="auto" camera-controls touch-action="pan-y" interaction-prompt="none" shadow-intensity="0" exposure="0.95" camera-orbit="0deg 75deg 105%"></model-viewer><div class="dt-reference-3d-overlay"><div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div><div class="dt-reference-3d-source">GLB · PUBLIC REFERENCE</div><div class="dt-reference-3d-status">Loading NIH 3D reference geometry…</div><div class="dt-reference-3d-mapping">Region geometry mapping · NOT ESTABLISHED</div></div>';m.appendChild(c);return c}
  function stopTimers(){if(observer){observer.disconnect();observer=null}if(retryTimer){clearInterval(retryTimer);retryTimer=null}if(loadPollTimer){clearInterval(loadPollTimer);loadPollTimer=null}}
  function markLoaded(token,model,c){if(token!==bootToken||!model||!model.loaded)return;stopTimers();activeModel=model;state({active:true,loading:false,loaded:true,error:null,loadMethod:'same_origin_fastapi'});const st=c.querySelector('.dt-reference-3d-status');if(st)st.textContent='Loaded NIH GLB · public reference geometry · not user health data';mountLocalSpatialPreview(c.parentElement||mountPoint())}
  function fallback(c,msg){const viewer=c?.querySelector('.dt-reference-3d-model');if(!viewer)return;const st=c.querySelector('.dt-reference-3d-status');if(st)st.textContent=msg;viewer.removeAttribute('src');if(!c.querySelector('.dt-reference-3d-fallback')){const f=document.createElement('div');f.className='dt-reference-3d-fallback';f.innerHTML='<div><strong>Reference 3D viewer unavailable</strong><br><a href="'+NIH_ENTRY_URL+'" target="_blank" rel="noopener noreferrer">Open NIH 3D reference on NIH 3D</a></div>';c.appendChild(f)}}

  function drawSpatial(canvas, cells){
    const ctx=canvas.getContext('2d');
    if(!ctx)return;
    const dpr=window.devicePixelRatio||1;
    const cssW=Math.max(320, canvas.clientWidth||640);
    const cssH=Math.max(220, canvas.clientHeight||320);
    canvas.width=Math.round(cssW*dpr); canvas.height=Math.round(cssH*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,cssW,cssH);
    if(!cells.length)return;
    const points=cells.map(c=>Array.isArray(c.spatial)?c.spatial:null).filter(p=>p&&p.length>=2&&Number.isFinite(Number(p[0]))&&Number.isFinite(Number(p[1]))).map(p=>[Number(p[0]),Number(p[1])]);
    if(!points.length)return;
    const xs=points.map(p=>p[0]), ys=points.map(p=>p[1]);
    const minX=Math.min(...xs), maxX=Math.max(...xs), minY=Math.min(...ys), maxY=Math.max(...ys);
    const pad=22, spanX=Math.max(maxX-minX,1), spanY=Math.max(maxY-minY,1);
    ctx.strokeStyle='#263545'; ctx.lineWidth=1; ctx.strokeRect(.5,.5,cssW-1,cssH-1);
    ctx.font='600 9px system-ui,sans-serif'; ctx.fillStyle='#8fa2b6';
    ctx.fillText('sample-local X', 10, cssH-9);
    ctx.save(); ctx.translate(10,cssH-30); ctx.rotate(-Math.PI/2); ctx.fillText('sample-local Y',0,0); ctx.restore();
    for(const [x,y] of points){
      const px=pad+(x-minX)/spanX*(cssW-pad*2);
      const py=pad+(1-(y-minY)/spanY)*(cssH-pad*2);
      ctx.beginPath(); ctx.arc(px,py,2.6,0,Math.PI*2); ctx.fillStyle='#9bd8c4'; ctx.fill();
    }
  }

  async function mountLocalSpatialPreview(parent){
    if(!parent || parent.__testhpLocalSpatialMounted || spatialPreviewPromise)return;
    parent.__testhpLocalSpatialMounted=true;
    styles();
    const section=document.createElement('section'); section.className='dt-reference-spatial-card'; section.setAttribute('aria-label','MERFISH local spatial extract');
    section.innerHTML='<div class="dt-reference-spatial-head"><div><div class="dt-reference-spatial-title">MERFISH · LOCAL SPATIAL EXTRACT</div><div class="dt-reference-spatial-sub">FOREARM · SAMPLE-LOCAL · REAL CELLS</div></div><div class="dt-reference-spatial-status">Loading local extract…</div></div><canvas class="dt-reference-spatial-canvas"></canvas><div class="dt-reference-spatial-meta"></div><div class="dt-reference-spatial-note">These coordinates come from the local MERFISH extract. They are not transformed onto the NIH hand mesh and are not claimed to represent palm/hand geometry.</div>';
    parent.appendChild(section);
    const statusEl=section.querySelector('.dt-reference-spatial-status'), canvas=section.querySelector('canvas'), meta=section.querySelector('.dt-reference-spatial-meta');
    spatialPreviewPromise=(async()=>{
      try{
        const response=await fetch(LOCAL_SPATIAL_URL,{cache:'no-store',credentials:'same-origin'});
        const data=await response.json();
        if(!response.ok)throw new Error(data?.detail||`Preview unavailable (${response.status})`);
        const cells=Array.isArray(data?.cells)?data.cells:[];
        if(data?.status!=='bounded_local_cell_preview' || !cells.length){
          statusEl.textContent='No local cell preview available';
          statusEl.classList.add('dt-reference-spatial-error');
          canvas.remove();
          const note=section.querySelector('.dt-reference-spatial-note');
          note.textContent=data?.note||'The local extract is not materialized for this region.';
          return;
        }
        drawSpatial(canvas,cells);
        statusEl.textContent=`${cells.length} cells shown`;
        const sampleIds=[...new Set(cells.map(c=>c.sampleId).filter(Boolean))];
        const sites=[...new Set(cells.map(c=>c.anatomicSite).filter(Boolean))];
        meta.innerHTML=`<span class="dt-reference-spatial-pill">Site: ${sites.join(', ')||'unknown'}</span><span class="dt-reference-spatial-pill">Sample IDs: ${sampleIds.length}</span><span class="dt-reference-spatial-pill">Source cells: ${Number(data.sourceCellCount||0).toLocaleString()}</span><span class="dt-reference-spatial-pill">Matrix loaded: no</span>`;
      }catch(error){
        statusEl.textContent='Local extract unavailable';
        statusEl.classList.add('dt-reference-spatial-error');
        canvas.remove();
        const note=section.querySelector('.dt-reference-spatial-note'); note.textContent=`Could not load the bounded local extract: ${error?.message||error}`;
      }
    })().finally(()=>{spatialPreviewPromise=null});
  }

  async function load(token,model,c){
    try{
      state({active:true,loading:true,loaded:false,error:null,loadMethod:'same_origin_fastapi'});
      if(window.customElements?.whenDefined)await window.customElements.whenDefined('model-viewer');
      if(token!==bootToken)return;
      const onLoad=()=>markLoaded(token,model,c);
      const onError=()=>{
        if(token!==bootToken)return;
        stopTimers();
        state({active:true,loading:false,loaded:false,error:'GLB returned by FastAPI endpoint could not be decoded',loadMethod:'same_origin_fastapi'});
        fallback(c,'The verified NIH GLB could not be decoded by model-viewer.');
      };
      model.addEventListener('load',onLoad,{once:true});
      model.addEventListener('error',onError,{once:true});
      model.setAttribute('src',PROXY_URL);
      let checks=0;
      loadPollTimer=setInterval(()=>{
        checks++;
        if(model.loaded)markLoaded(token,model,c);
        else if(checks>=120){
          stopTimers();
          if(token===bootToken){
            state({active:true,loading:false,loaded:false,error:'Timed out waiting for model-viewer to finish loading',loadMethod:'same_origin_fastapi'});
            fallback(c,'The verified NIH GLB did not finish loading in the allotted time.');
          }
        }
      },250);
    }catch(e){
      if(token!==bootToken)return;
      stopTimers();
      state({active:true,loading:false,loaded:false,error:e?.message||'Reference GLB endpoint failed',loadMethod:'same_origin_fastapi'});
      fallback(c,e?.message||'The same-origin reference asset endpoint could not load the verified NIH GLB.');
    }finally{loadingPromise=null}
  }
  function mount(token){
    const m=mountPoint();if(!m)return false;
    let c=m.querySelector(':scope > .dt-reference-3d-card');
    if(!c&&activeModel&&activeModel.isConnected===false){const oldCard=activeModel.closest('.dt-reference-3d-card');if(oldCard){m.appendChild(oldCard);c=oldCard}}
    if(!c)c=card(m);
    const model=c?.querySelector('.dt-reference-3d-model');if(!model)return false;
    if(model.loaded){markLoaded(token,model,c);return true}
    if(model.getAttribute('src')||loadingPromise)return true;
    loadingPromise=load(token,model,c);return true;
  }
  function boot(){
    styles();
    const current=window.__testhpReferenceHand3DViewerState;
    const existing=activeModel||document.querySelector('.dt-reference-3d-model');
    if(current?.active&&current?.loaded&&existing?.loaded){mountLocalSpatialPreview(existing.closest('.dt-reference-3d-card')?.parentElement||mountPoint());return}
    if(loadingPromise){return}
    const token=++bootToken;
    stopTimers();
    if(activeModel&&!document.contains(activeModel))activeModel=null;
    state({active:true,loading:true,loaded:false,error:null,loadMethod:'same_origin_fastapi',assetFormat:'glb',assetUrl:NIH_GLB_URL});
    if(mount(token))return;
    observer=new MutationObserver(()=>{if(mount(token)){observer.disconnect();observer=null}});
    observer.observe(document.documentElement||document,{childList:true,subtree:true});
    let attempts=0;
    retryTimer=setInterval(()=>{attempts++;if(mount(token)||attempts>=30){clearInterval(retryTimer);retryTimer=null}},250)
  }
  window.testhpReferenceHand3D=Object.freeze({version:VIEWER_VERSION,sourceId:SOURCE_ID,entryUrl:NIH_ENTRY_URL,assetUrl:NIH_GLB_URL,proxyUrl:PROXY_URL,assetFormat:'glb',activate:boot,getState:()=>window.__testhpReferenceHand3DViewerState});
  state();window.addEventListener('testhp:reference-hand-activated',boot);window.addEventListener('DOMContentLoaded',()=>{if(window.__testhpReferenceHandState?.active)boot()},{once:true});if(window.__testhpReferenceHandState?.active)boot();
})();
