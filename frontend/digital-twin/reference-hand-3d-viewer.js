(() => {
  'use strict';
  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const NIH_ENTRY_URL = 'https://3d.nih.gov/entries/3DPX-017237';
  const NIH_GLB_URL = 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511847';
  const PROXY_URL = '/api/hand/photo-reconstruction/reference-glb';
  const VIEWER_VERSION = 'reference-glb-safe-21';

  function state(p = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({
      installed: true, version: VIEWER_VERSION, active: false, loading: false, loaded: false,
      sourceId: SOURCE_ID, entryUrl: NIH_ENTRY_URL, assetUrl: NIH_GLB_URL, proxyUrl: PROXY_URL,
      assetFormat: 'glb', provenance: 'public_reference', ownership: 'reference',
      userHealthData: false, regionId: window.__testhpReferenceHandState?.regionId || 'palm', error: null,
      ...p,
    });
    return window.__testhpReferenceHand3DViewerState;
  }
  function host() { return document.getElementById('testhp-end-user-layer'); }
  function mountPoint() { const h = host(); return h && (h.querySelector('.center .viewport') || h.querySelector('.viewport') || h); }
  function styles() {
    if (document.getElementById('testhp-reference-hand-3d-style')) return;
    const s = document.createElement('style'); s.id='testhp-reference-hand-3d-style';
    s.textContent='.dt-reference-3d-card{position:relative;min-height:520px;width:100%;margin:16px 0;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;box-sizing:border-box}.dt-reference-3d-model{display:block;width:100%;height:520px;border:0;background:#0b1118}.dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}.dt-reference-3d-title,.dt-reference-3d-source,.dt-reference-3d-status,.dt-reference-3d-mapping{position:absolute;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}.dt-reference-3d-title{left:16px;top:14px;color:#dce7f2}.dt-reference-3d-source{right:16px;top:14px}.dt-reference-3d-status{left:16px;bottom:14px}.dt-reference-3d-mapping{right:16px;bottom:14px}.dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:#0b1118;z-index:3}.dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}.dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}';
    document.head.appendChild(s);
  }
  function card(m) {
    if (!m) return null;
    let c=m.querySelector(':scope > .dt-reference-3d-card'); if(c) return c;
    c=document.createElement('section'); c.className='dt-reference-3d-card'; c.setAttribute('aria-label','NIH 3D reference hand');
    c.innerHTML='<model-viewer class="dt-reference-3d-model" alt="NIH 3D healthy adult human hand reference template" loading="eager" reveal="auto" camera-controls touch-action="pan-y" interaction-prompt="none" shadow-intensity="0.22" exposure="0.95" camera-orbit="0deg 75deg 105%" ar ar-modes="webxr scene-viewer quick-look"></model-viewer><div class="dt-reference-3d-overlay"><div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div><div class="dt-reference-3d-source">GLB · PUBLIC REFERENCE</div><div class="dt-reference-3d-status">Loading NIH 3D reference geometry…</div><div class="dt-reference-3d-mapping">Region geometry mapping · NOT ESTABLISHED</div></div>';
    m.appendChild(c); return c;
  }
  function fallback(c,msg){const viewer=c?.querySelector('.dt-reference-3d-model');if(!viewer)return;const status=c.querySelector('.dt-reference-3d-status');if(status)status.textContent=msg;viewer.removeAttribute('src');if(!c.querySelector('.dt-reference-3d-fallback')){const f=document.createElement('div');f.className='dt-reference-3d-fallback';f.innerHTML='<div><strong>Reference 3D viewer unavailable</strong><br><a href="'+NIH_ENTRY_URL+'" target="_blank" rel="noopener noreferrer">Open NIH 3D reference on NIH 3D</a></div>';c.appendChild(f);}}
  let observer=null,retryTimer=null,bootToken=0,loadingPromise=null;
  async function load(token,model,c){try{state({active:true,loading:true,loaded:false,error:null,loadMethod:'same_origin_fastapi'});if(window.customElements?.whenDefined)await window.customElements.whenDefined('model-viewer');if(token!==bootToken)return;await Promise.resolve();const r=await fetch(PROXY_URL,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw new Error(`Reference GLB endpoint unavailable (${r.status})`);const ct=r.headers.get('content-type')||'';if(!ct.includes('model/gltf-binary')&&!ct.includes('application/octet-stream'))throw new Error(`Reference GLB endpoint returned ${ct||'unknown content type'}`);const buf=new Uint8Array(await r.arrayBuffer());if(buf.length<4||String.fromCharCode(...buf.slice(0,4))!=='glTF')throw new Error('Reference asset is not a valid GLB');if(token!==bootToken)return;const url=URL.createObjectURL(new Blob([buf],{type:'model/gltf-binary'}));const onLoad=()=>{URL.revokeObjectURL(url);if(token!==bootToken)return;if(observer){observer.disconnect();observer=null}if(retryTimer){clearInterval(retryTimer);retryTimer=null}state({active:true,loading:false,loaded:true,error:null,loadMethod:'same_origin_fastapi'});const st=c.querySelector('.dt-reference-3d-status');if(st)st.textContent='Loaded NIH GLB · public reference geometry · not user health data';};const onError=()=>{URL.revokeObjectURL(url);if(token!==bootToken)return;state({active:true,loading:false,loaded:false,error:'GLB returned by FastAPI endpoint could not be decoded',loadMethod:'same_origin_fastapi'});fallback(c,'The verified NIH GLB was fetched but could not be decoded by model-viewer.');};model.addEventListener('load',onLoad,{once:true});model.addEventListener('error',onError,{once:true});model.setAttribute('src',url);}catch(e){if(token!==bootToken)return;state({active:true,loading:false,loaded:false,error:e?.message||'Reference GLB endpoint failed',loadMethod:'same_origin_fastapi'});fallback(c,e?.message||'The same-origin reference asset endpoint could not load the verified NIH GLB.');}}
  function mount(token){const m=mountPoint();if(!m)return false;const c=card(m);const model=c?.querySelector('.dt-reference-3d-model');if(!model)return false;if(model.getAttribute('src')||loadingPromise)return true;loadingPromise=load(token,model,c).finally(()=>{loadingPromise=null});return true;}
  function boot(){styles();const token=++bootToken;if(observer)observer.disconnect();if(retryTimer)clearInterval(retryTimer);loadingPromise=null;state({active:true,loading:true,loaded:false,error:null,loadMethod:'same_origin_fastapi',assetFormat:'glb',assetUrl:NIH_GLB_URL});if(mount(token))return;observer=new MutationObserver(()=>{if(mount(token)){observer.disconnect();observer=null}});observer.observe(document.documentElement||document,{childList:true,subtree:true});let attempts=0;retryTimer=setInterval(()=>{attempts++;if(mount(token)||attempts>=30){clearInterval(retryTimer);retryTimer=null}},250);}
  window.testhpReferenceHand3D=Object.freeze({version:VIEWER_VERSION,sourceId:SOURCE_ID,entryUrl:NIH_ENTRY_URL,assetUrl:NIH_GLB_URL,proxyUrl:PROXY_URL,assetFormat:'glb',activate:boot,getState:()=>window.__testhpReferenceHand3DViewerState});
  state();window.addEventListener('testhp:reference-hand-activated',boot);window.addEventListener('DOMContentLoaded',()=>{if(window.__testhpReferenceHandState?.active)boot()},{once:true});if(window.__testhpReferenceHandState?.active)boot();
})();
