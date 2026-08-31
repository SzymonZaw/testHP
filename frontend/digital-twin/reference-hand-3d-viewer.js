(() => {
  'use strict';
  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const ASSET_URL = '/api/reference-hand/3dpx-017237.glb';
  const VIEWER_VERSION = 'reference-3d-safe-5';
  const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
  const GLTF_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';
  let bootPromise = null;
  let sceneState = null;

  function state(patch = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({installed:true,version:VIEWER_VERSION,active:false,loading:false,loaded:false,sourceId:SOURCE_ID,assetUrl:ASSET_URL,provenance:'public_reference',regionId:window.__testhpReferenceHandState?.regionId || 'palm',error:null,...patch});
    return window.__testhpReferenceHand3DViewerState;
  }

  function styles() {
    if (document.getElementById('testhp-reference-hand-3d-style')) return;
    const s=document.createElement('style'); s.id='testhp-reference-hand-3d-style'; s.textContent=`
      .dt-reference-3d-card{position:relative;min-height:360px;width:100%;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;isolation:isolate}
      .dt-reference-3d-canvas{display:block;width:100%;height:360px;touch-action:none;cursor:grab}.dt-reference-3d-canvas:active{cursor:grabbing}
      .dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}.dt-reference-3d-title{position:absolute;left:16px;top:14px;padding:8px 10px;border:1px solid #344456;border-radius:10px;background:#0d151ee8;color:#dce7f2;font:700 11px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase}.dt-reference-3d-status{position:absolute;left:16px;bottom:14px;max-width:80%;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}
      .dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:#0b1118}.dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}.dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}
    `; document.head.appendChild(s);
  }

  function card() {
    const host=document.getElementById('testhp-end-user-layer'); if(!host) return null;
    let c=host.querySelector('.dt-reference-3d-card'); if(c) return c;
    c=document.createElement('section'); c.className='dt-reference-3d-card'; c.setAttribute('aria-label','NIH 3D reference hand');
    c.innerHTML='<canvas class="dt-reference-3d-canvas" aria-label="Interactive NIH 3D reference hand"></canvas><div class="dt-reference-3d-overlay"><div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div><div class="dt-reference-3d-status">Public reference geometry · not user health data</div></div>';
    const v=host.querySelector('.center .viewport,.viewport'); if(v){v.style.position=v.style.position||'relative';v.style.minHeight=v.style.minHeight||'360px';v.appendChild(c)} else host.appendChild(c); return c;
  }

  function fallback(c,msg){if(!c)return;let f=c.querySelector('.dt-reference-3d-fallback');if(!f){f=document.createElement('div');f.className='dt-reference-3d-fallback';f.innerHTML='<div><strong>Reference 3D viewer unavailable</strong><span></span><br><a href="https://3d.nih.gov/entries/3DPX-017237" target="_blank" rel="noopener noreferrer">Open NIH 3D reference</a></div>';c.appendChild(f)}f.querySelector('span').textContent=msg}

  function normalize(obj,THREE){const box=new THREE.Box3().setFromObject(obj),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3()),max=Math.max(size.x,size.y,size.z)||1,scale=4.8/max;obj.scale.setScalar(scale);obj.position.set(-center.x*scale,-center.y*scale,-center.z*scale)}

  function createScene(c,THREE,GLTFLoader){
    const canvas=c.querySelector('canvas'),renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.75));renderer.setClearColor(0x0b1118,1);renderer.outputColorSpace=THREE.SRGBColorSpace;
    const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(30,1,.01,100);camera.position.set(0,.2,7.5);scene.add(new THREE.HemisphereLight(0xe8f2ff,0x10202b,2.2));const key=new THREE.DirectionalLight(0xffffff,3);key.position.set(4,6,8);scene.add(key);const root=new THREE.Group();scene.add(root);sceneState={renderer,scene,camera,root};
    const resize=()=>{const r=canvas.getBoundingClientRect();renderer.setSize(Math.max(1,r.width),Math.max(1,r.height),false);camera.aspect=Math.max(1,r.width)/Math.max(1,r.height);camera.updateProjectionMatrix()};new ResizeObserver(resize).observe(canvas);resize();
    let drag=false,lx=0,ly=0;canvas.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;ly=e.clientY;canvas.setPointerCapture?.(e.pointerId)});canvas.addEventListener('pointermove',e=>{if(!drag)return;root.rotation.y+=(e.clientX-lx)*.008;root.rotation.x+=(e.clientY-ly)*.006;lx=e.clientX;ly=e.clientY});['pointerup','pointercancel'].forEach(x=>canvas.addEventListener(x,()=>drag=false));canvas.addEventListener('wheel',e=>{e.preventDefault();camera.position.multiplyScalar(e.deltaY>0?1.12:.89);camera.position.clampLength(3.2,14)},{passive:false});
    new GLTFLoader().load(ASSET_URL,g=>{normalize(g.scene,THREE);root.add(g.scene);state({active:true,loading:false,loaded:true,error:null});c.querySelector('.dt-reference-3d-status').textContent='Loaded from NIH 3D · public reference geometry · not user health data'},undefined,e=>{console.warn('[reference-hand-3d] NIH proxy asset failed; keeping UI responsive.',e);state({active:true,loading:false,loaded:false,error:'NIH reference GLB could not be loaded'});fallback(c,'The local NIH proxy could not retrieve the public reference geometry.')});
    const animate=()=>{if(!sceneState||sceneState.renderer!==renderer)return;renderer.render(scene,camera);requestAnimationFrame(animate)};animate();
  }

  async function boot(){if(bootPromise)return bootPromise;bootPromise=(async()=>{styles();state({active:true,loading:true,error:null});const c=card();if(!c){state({active:true,loading:false,error:'Reference viewer host is not available'});return}try{const THREE=await import(THREE_URL);const {GLTFLoader}=await import(GLTF_URL);createScene(c,THREE,GLTFLoader)}catch(e){console.warn('[reference-hand-3d] viewer dependency failed; keeping UI responsive.',e);state({active:true,loading:false,error:'3D viewer dependencies could not be loaded'});fallback(c,'The 3D viewer dependency could not be loaded.')}})();return bootPromise}
  function activate(){state({active:true,regionId:window.__testhpReferenceHandState?.regionId||'palm'});boot()}
  window.testhpReferenceHand3D=Object.freeze({version:VIEWER_VERSION,sourceId:SOURCE_ID,assetUrl:ASSET_URL,activate,getState:()=>window.__testhpReferenceHand3DViewerState});state();window.addEventListener('testhp:reference-hand-activated',activate);if(window.__testhpReferenceHandState?.active)activate();
})();
