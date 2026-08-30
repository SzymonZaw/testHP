import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

(() => {
  'use strict';
  if (window.__testhpDigitalTwin3D) return;
  window.__testhpDigitalTwin3D = true;

  const REGIONS = ['wrist', 'palm', 'thumb', 'index', 'middle', 'ring', 'little'];
  const LABELS = { wrist:'Wrist', palm:'Palm', thumb:'Thumb', index:'Index', middle:'Middle', ring:'Ring', little:'Little' };
  let host, canvas, renderer, scene, camera, controls, handRoot, raycaster, resizeObserver;
  let regionMeshes = new Map();
  let current = { region:'palm', tissue:null, cell:null };
  let assetKey = null;

  const css = `.dt3d-host{position:relative;width:100%;height:100%;min-height:420px;overflow:hidden;background:radial-gradient(circle at 50% 42%,#17202d 0,#0d1117 66%);border-radius:16px}.dt3d-host canvas{display:block;width:100%;height:100%;touch-action:none}.dt3d-controls{position:absolute;right:12px;top:12px;z-index:3}.dt3d-reset{border:1px solid rgba(255,255,255,.16);background:rgba(13,17,23,.78);color:#e6edf3;border-radius:8px;padding:7px 10px;font:600 12px/1 system-ui;cursor:pointer}.dt3d-badge{position:absolute;left:12px;top:12px;padding:7px 9px;border-radius:8px;background:rgba(13,17,23,.72);border:1px solid rgba(255,255,255,.10);color:#dce5ee;font:700 11px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;pointer-events:none}.dt3d-hint{position:absolute;left:12px;bottom:12px;padding:7px 9px;border-radius:8px;background:rgba(13,17,23,.72);border:1px solid rgba(255,255,255,.10);color:#9da7b5;font:500 11px/1.35 system-ui;pointer-events:none}.dt3d-empty{position:absolute;inset:50px;display:grid;place-content:center;text-align:center;color:#9da7b5;pointer-events:none}.dt3d-empty strong{color:#e6edf3;font-size:14px}.dt3d-empty span{margin-top:6px;font-size:12px}`;
  const style=document.createElement('style'); style.textContent=css; document.head.appendChild(style);

  const canonical = () => { try { return window.TestHPCanonicalState?.get?.() || null; } catch { return null; } };
  const selectionFromCanonical = state => {
    const s=state || {};
    current={ region:s.region || s.selection?.region || 'palm', tissue:s.tissue ?? s.selection?.tissue ?? null, cell:s.cell ?? s.selection?.cell ?? null };
  };
  const findViewport=()=>document.getElementById('twin-viewport') || document.querySelector('[data-twin-viewport]') || document.querySelector('.twin-viewport');
  const readyAsset=a=>['ready','available','verified','usable'].includes(String(a?.status??'').toLowerCase());
  const assetUrl=a=>a?.url ?? a?.uri ?? a?.asset_url ?? a?.assetUrl ?? a?.source_url ?? null;
  const hand3dAsset=state=>{
    const assets=Array.isArray(state?.assets)?state.assets:[];
    return assets.find(a=>readyAsset(a) && ['hand_3d','3d','mesh','gltf','glb'].includes(String(a.modality??'').toLowerCase()) && assetUrl(a)) || null;
  };
  const material=()=>new THREE.MeshStandardMaterial({color:0xc98f77,roughness:.62,metalness:.02});
  const selectMaterial=()=>new THREE.MeshStandardMaterial({color:0x68b5ff,roughness:.58,emissive:0x0b2745,emissiveIntensity:.32});

  function disposeGroup(group){
    if(!group)return;
    for(const obj of [...group.children]){obj.traverse(n=>{if(!n.isMesh)return;n.geometry?.dispose?.();if(Array.isArray(n.material))n.material.forEach(m=>m.dispose?.());else n.material?.dispose?.();});group.remove(obj);}
  }
  function clearEmptyMessage(){host?.querySelector('.dt3d-empty')?.remove();}
  function showEmpty(title,detail){clearEmptyMessage();const e=document.createElement('div');e.className='dt3d-empty';e.innerHTML=`<strong>${title}</strong><span>${detail}</span>`;host.appendChild(e);}
  function indexBackendRegions(state){
    regionMeshes.clear();
    const regions=Array.isArray(state?.anatomy?.regions)?state.anatomy.regions:[];
    regions.forEach(region=>{
      const id=String(region?.region_id ?? region?.regionId ?? region?.id ?? '').toLowerCase();
      if(!REGIONS.includes(id))return;
      regionMeshes.set(id,[]);
    });
    handRoot?.traverse(node=>{
      if(!node.isMesh)return;
      const raw=node.userData?.region ?? node.userData?.region_id ?? node.name;
      const id=String(raw??'').toLowerCase();
      const match=REGIONS.find(r=>id===r || id.includes(r));
      if(match){if(!regionMeshes.has(match))regionMeshes.set(match,[]);regionMeshes.get(match).push(node);}
    });
  }
  function highlight(){
    for(const [id,meshes] of regionMeshes){for(const mesh of meshes){mesh.material?.color?.setHex(id===current.region?0x68b5ff:0xc98f77);if(mesh.material?.emissive){mesh.material.emissive.setHex(id===current.region?0x0b2745:0);mesh.material.emissiveIntensity=id===current.region?.32:0;}}}
    setBadge(current.cell?`CELL ${String(current.cell).toUpperCase()}`:current.tissue?'TISSUE FIELD':`${LABELS[current.region]||current.region} · 3D HAND`);
  }
  function setBadge(text){const el=host?.querySelector('.dt3d-badge');if(el)el.textContent=text;}
  function resize(){if(!renderer||!camera||!host)return;const w=Math.max(1,host.clientWidth),h=Math.max(1,host.clientHeight);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  function reset(){camera.position.set(0,.45,8.6);controls.target.set(0,.1,0);controls.update();}
  function selectRegion(region){window.TestHPCanonicalState?.updateSelection?.({region});}
  function selectCell(cell){window.TestHPCanonicalState?.updateSelection?.({cell});}
  function onPointer(event){
    if(!canvas||!camera)return;const r=canvas.getBoundingClientRect();const p=new THREE.Vector2(((event.clientX-r.left)/r.width)*2-1,-((event.clientY-r.top)/r.height)*2+1);raycaster.setFromCamera(p,camera);
    const objects=[...regionMeshes.values()].flat();const hit=raycaster.intersectObjects(objects,true)[0];if(!hit)return;let obj=hit.object;
    while(obj && obj.parent && !obj.userData?.region && !obj.userData?.region_id && !obj.userData?.cell_id && !obj.userData?.cell) obj=obj.parent;
    const region=obj?.userData?.region ?? obj?.userData?.region_id;const cell=obj?.userData?.cell_id ?? obj?.userData?.cell;
    if(region)selectRegion(String(region));else if(cell)selectCell(String(cell));
  }
  async function loadBackendAsset(state){
    disposeGroup(handRoot); regionMeshes.clear(); clearEmptyMessage();
    const asset=hand3dAsset(state); const url=assetUrl(asset);
    if(!url){showEmpty('No 3D asset supplied','The backend has not supplied a ready hand 3D asset for this state. No anatomy is generated by the frontend.');setBadge('3D · NOT ESTABLISHED');assetKey=null;return;}
    const key=String(url);if(assetKey===key && handRoot.children.length){highlight();return;}assetKey=key;
    const loader=new GLTFLoader();
    try{
      const gltf=await loader.loadAsync(url);handRoot.add(gltf.scene);gltf.scene.traverse(n=>{if(n.isMesh && !n.material)n.material=material();});indexBackendRegions(state);highlight();
    }catch(error){assetKey=null;showEmpty('3D asset unavailable','The supplied 3D asset could not be loaded. The frontend does not substitute fictional anatomy.');setBadge('3D · UNAVAILABLE');window.dispatchEvent(new CustomEvent('testhp:3d-asset-error',{detail:{message:String(error)}}));}
  }
  function mount(){
    const next=findViewport();if(!next || (next===host&&canvas?.isConnected))return;host=next;host.innerHTML='';host.classList.add('dt3d-host');
    canvas=document.createElement('canvas');canvas.setAttribute('aria-label','Interactive 3D hand viewport');host.appendChild(canvas);
    const badge=document.createElement('div');badge.className='dt3d-badge';host.appendChild(badge);
    const controlsEl=document.createElement('div');controlsEl.className='dt3d-controls';const resetButton=document.createElement('button');resetButton.className='dt3d-reset';resetButton.type='button';resetButton.textContent='Reset view';resetButton.onclick=reset;controlsEl.appendChild(resetButton);host.appendChild(controlsEl);
    const hint=document.createElement('div');hint.className='dt3d-hint';hint.textContent='Drag to rotate · wheel/pinch to zoom · click a supplied region';host.appendChild(hint);
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
    scene=new THREE.Scene();scene.background=new THREE.Color(0x0d1117);camera=new THREE.PerspectiveCamera(32,1,.1,100);camera.position.set(0,.45,8.6);
    controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=true;controls.minDistance=4;controls.maxDistance=15;controls.target.set(0,.1,0);
    scene.add(new THREE.HemisphereLight(0xffffff,0x172033,2.1));const key=new THREE.DirectionalLight(0xffffff,2.7);key.position.set(4,6,7);scene.add(key);const fill=new THREE.DirectionalLight(0x8bb8ff,1);fill.position.set(-5,2,-4);scene.add(fill);
    handRoot=new THREE.Group();scene.add(handRoot);raycaster=new THREE.Raycaster();canvas.addEventListener('click',onPointer);resize();if(resizeObserver)resizeObserver.disconnect();resizeObserver=new ResizeObserver(resize);resizeObserver.observe(host);
    loadBackendAsset(canonical());
  }
  async function sync(){selectionFromCanonical(canonical());if(!host?.isConnected){mount();return;}highlight();await loadBackendAsset(canonical());}
  window.addEventListener('testhp:canonical-state-changed',sync);window.addEventListener('testhp:spatial-layer-changed',sync);
  const observer=new MutationObserver(()=>{if(findViewport()&&(!host?.isConnected||!host.querySelector('canvas')))mount();});observer.observe(document.body,{childList:true,subtree:true});
  selectionFromCanonical(canonical());const initial=setInterval(()=>{if(findViewport()){clearInterval(initial);mount();}},100);setTimeout(()=>clearInterval(initial),15000);
})();
