(() => {
  'use strict';
  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const NIH_ENTRY_URL = 'https://3d.nih.gov/entries/3DPX-017237';
  const NIH_GLB_URL = 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811';
  const PROXY_URL = `/digital-twin/reference-hand-glb-proxy.php?url=${encodeURIComponent(NIH_GLB_URL)}`;
  const VIEWER_VERSION = 'reference-glb-safe-13';
  let observer = null;
  let retryTimer = null;
  let bootToken = 0;

  function setState(patch = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({
      installed: true, version: VIEWER_VERSION, active: false, loading: false, loaded: false,
      sourceId: SOURCE_ID, entryUrl: NIH_ENTRY_URL, assetUrl: NIH_GLB_URL, proxyUrl: PROXY_URL,
      assetFormat: 'glb', provenance: 'public_reference', ownership: 'reference', userHealthData: false,
      regionId: window.__testhpReferenceHandState?.regionId || 'palm', error: null, ...patch
    });
    return window.__testhpReferenceHand3DViewerState;
  }

  function installStyles() {
    if (document.getElementById('testhp-reference-hand-3d-style')) return;
    const s = document.createElement('style'); s.id = 'testhp-reference-hand-3d-style';
    s.textContent = `.dt-reference-3d-card{position:relative;min-height:520px;width:100%;margin:16px 0;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;isolation:isolate;box-sizing:border-box}.dt-reference-3d-model{display:block;width:100%;height:520px;background:#0b1118;--poster-color:#0b1118;--progress-bar-color:#79bce9;--progress-mask:transparent}.dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}.dt-reference-3d-title{position:absolute;left:16px;top:14px;padding:8px 10px;border:1px solid #344456;border-radius:10px;background:#0d151ee8;color:#dce7f2;font:700 11px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase}.dt-reference-3d-status{position:absolute;left:16px;bottom:14px;max-width:80%;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}.dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:#0b1118;z-index:3}.dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}.dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}.dt-reference-3d-source{position:absolute;right:16px;top:14px;padding:6px 8px;border:1px solid #2e3d4c;border-radius:8px;background:#0d151ee8;color:#9fb0c2;font:600 10px/1.2 system-ui,sans-serif}.dt-reference-3d-mapping{position:absolute;right:16px;bottom:14px;padding:6px 8px;border:1px solid #2e3d4c;border-radius:8px;background:#0d151ee8;color:#8495a6;font:600 10px/1.2 system-ui,sans-serif}`;
    document.head.appendChild(s);
  }
  function getHost(){return document.getElementById('testhp-end-user-layer');}
  function findMount(){const h=getHost();return h?(h.querySelector('.center .viewport')||h.querySelector('.viewport')||h):null;}
  function ensureCard(mount){
    if(!mount)return null; let card=mount.querySelector(':scope > .dt-reference-3d-card'); if(card)return card;
    card=document.createElement('section'); card.className='dt-reference-3d-card'; card.setAttribute('aria-label','NIH 3D reference hand');
    card.innerHTML=`<model-viewer class="dt-reference-3d-model" alt="NIH 3D healthy adult human hand reference template" loading="eager" reveal="auto" camera-controls touch-action="pan-y" interaction-prompt="none" shadow-intensity="0.22" exposure="0.95" camera-orbit="0deg 75deg 105%" ar ar-modes="webxr scene-viewer quick-look"></model-viewer><div class="dt-reference-3d-overlay"><div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div><div class="dt-reference-3d-source">GLB · public reference</div><div class="dt-reference-3d-status">Loading NIH 3D reference geometry…</div><div class="dt-reference-3d-mapping">Region geometry mapping · NOT ESTABLISHED</div></div>`;
    card.style.display='block'; card.style.position='relative'; if(mount===getHost())mount.prepend(card);else mount.appendChild(card); return card;
  }
  function showFallback(card,message){if(!card)return;let f=card.querySelector('.dt-reference-3d-fallback');if(!f){f=document.createElement('div');f.className='dt-reference-3d-fallback';f.innerHTML=`<div><strong>Reference 3D viewer unavailable</strong><span></span><br><a href="${NIH_ENTRY_URL}" target="_blank" rel="noopener noreferrer">Open NIH 3D reference</a></div>`;card.appendChild(f);}const sp=f.querySelector('span');if(sp)sp.textContent=message;}
  function stopWaiting(){if(observer){observer.disconnect();observer=null;}if(retryTimer){clearInterval(retryTimer);retryTimer=null;}}

  async function loadProxy(model,card,token){
    try{
      setState({active:true,loading:true,loaded:false,error:null,loadMethod:'same_origin_proxy'});
      const r=await fetch(PROXY_URL,{credentials:'same-origin',cache:'no-store'});
      if(!r.ok)throw new Error(`Reference GLB proxy unavailable (${r.status})`);
      const blob=await r.blob(); if(!blob.size)throw new Error('Reference GLB proxy returned an empty asset');
      if(token!==bootToken)return;
      const objectUrl=URL.createObjectURL(blob);
      model.addEventListener('load',()=>{URL.revokeObjectURL(objectUrl);if(token!==bootToken)return;stopWaiting();setState({active:true,loading:false,loaded:true,error:null,loadMethod:'same_origin_proxy'});const st=card.querySelector('.dt-reference-3d-status');if(st)st.textContent='Loaded NIH GLB · public reference geometry · not user health data';},{once:true});
      model.addEventListener('error',()=>{URL.revokeObjectURL(objectUrl);if(token!==bootToken)return;stopWaiting();setState({active:true,loading:false,loaded:false,error:'GLB returned by same-origin proxy could not be decoded'});showFallback(card,'The local proxy returned an asset that the 3D viewer could not decode.');},{once:true});
      model.src=objectUrl;
    }catch(e){if(token!==bootToken)return;stopWaiting();setState({active:true,loading:false,loaded:false,error:e?.message||'Reference GLB proxy failed',loadMethod:'same_origin_proxy'});showFallback(card,e?.message||'The local reference asset proxy could not load the public NIH GLB.');}
  }
  function mount(token){const m=findMount();if(!m)return false;const c=ensureCard(m);const v=c?.querySelector('.dt-reference-3d-model');if(!v)return false;loadProxy(v,c,token);return true;}
  function boot(){
    installStyles(); const token=++bootToken; stopWaiting(); setState({active:true,loading:true,loaded:false,error:null});
    if(mount(token))return;
    const root=document.documentElement||document; observer=new MutationObserver(()=>{if(mount(token))stopWaiting();}); observer.observe(root,{childList:true,subtree:true});
    let attempts=0; retryTimer=setInterval(()=>{attempts++;if(mount(token)){stopWaiting();return;}if(attempts>=30){stopWaiting();setState({active:true,loading:false,loaded:false,error:'Reference viewer host is not available'});}},250);
  }
  window.testhpReferenceHand3D=Object.freeze({version:VIEWER_VERSION,sourceId:SOURCE_ID,entryUrl:NIH_ENTRY_URL,assetUrl:NIH_GLB_URL,proxyUrl:PROXY_URL,assetFormat:'glb',activate:boot,getState:()=>window.__testhpReferenceHand3DViewerState});
  setState(); window.addEventListener('testhp:reference-hand-activated',boot); window.addEventListener('DOMContentLoaded',()=>{if(window.__testhpReferenceHandState?.active)boot();},{once:true}); if(window.__testhpReferenceHandState?.active)boot();
})();