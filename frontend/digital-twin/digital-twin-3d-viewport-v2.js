import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

(() => {
  'use strict';
  if (window.__testhpDigitalTwin3D) return;
  window.__testhpDigitalTwin3D = true;

  const REGIONS = ['wrist', 'palm', 'thumb', 'index', 'middle', 'ring', 'little'];
  const LABELS = { wrist:'Wrist', palm:'Palm', thumb:'Thumb', index:'Index', middle:'Middle', ring:'Ring', little:'Little' };
  const COLORS = { base:0xc98f77, selected:0x68b5ff, unavailable:0x596273, tissue:0x67c7b5, cell:0x8d9cf0 };
  let current = { region:'palm', tissue:null, cell:null };
  let host = null;
  let canvas = null;
  let renderer = null;
  let scene = null;
  let camera = null;
  let controls = null;
  let handRoot = null;
  let deepRoot = null;
  let raycaster = null;
  let pointer = new THREE.Vector2();
  let regionMeshes = new Map();
  let resetButton = null;
  let hint = null;
  let resizeObserver = null;

  const css = `
    .dt3d-host{position:relative;width:100%;height:100%;min-height:420px;overflow:hidden;background:radial-gradient(circle at 50% 42%,#17202d 0,#0d1117 66%);border-radius:16px}
    .dt3d-host canvas{display:block;width:100%;height:100%;touch-action:none}
    .dt3d-controls{position:absolute;right:12px;top:12px;display:flex;gap:7px;z-index:3}
    .dt3d-reset{border:1px solid rgba(255,255,255,.16);background:rgba(13,17,23,.78);color:#e6edf3;border-radius:8px;padding:7px 10px;font:600 12px/1 system-ui;cursor:pointer;backdrop-filter:blur(8px)}
    .dt3d-reset:hover{background:rgba(255,255,255,.10)}
    .dt3d-hint{position:absolute;left:12px;bottom:12px;padding:7px 9px;border-radius:8px;background:rgba(13,17,23,.72);border:1px solid rgba(255,255,255,.10);color:#9da7b5;font:500 11px/1.35 system-ui;pointer-events:none}
    .dt3d-badge{position:absolute;left:12px;top:12px;padding:7px 9px;border-radius:8px;background:rgba(13,17,23,.72);border:1px solid rgba(255,255,255,.10);color:#dce5ee;font:700 11px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;pointer-events:none}
  `;
  const style = document.createElement('style'); style.textContent = css; document.head.appendChild(style);

  function canonical(){
    try { return window.TestHPCanonicalState?.get?.() || null; } catch { return null; }
  }

  function selectionFromCanonical(s){
    const sel = s?.selection || s?.input?.selection || {};
    current = { region: sel.region || 'palm', tissue: sel.tissue || null, cell: sel.cell || null };
  }

  function findViewport(){
    return document.getElementById('twin-viewport') || document.querySelector('[data-twin-viewport]') || document.querySelector('.twin-viewport');
  }

  function material(color, emissive=0x000000, intensity=0){
    return new THREE.MeshStandardMaterial({color, roughness:.62, metalness:.02, emissive, emissiveIntensity:intensity});
  }

  function roundedBox(size, radius, color){
    const g = new THREE.BoxGeometry(...size);
    const m = new THREE.Mesh(g, material(color));
    return m;
  }

  function capsule(radius, length, color){
    return new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 8, 18), material(color));
  }

  function buildHand(){
    handRoot = new THREE.Group(); handRoot.name='interactive-hand';
    handRoot.rotation.x = -0.10;
    scene.add(handRoot);
    regionMeshes.clear();

    const palm = roundedBox([2.45,2.85,.72], .25, COLORS.base);
    palm.position.set(0,-.15,0); palm.rotation.z=-.02; palm.userData.region='palm'; handRoot.add(palm); regionMeshes.set('palm',palm);

    const wrist = roundedBox([1.35,1.55,.68], .22, COLORS.base);
    wrist.position.set(0,-2.15,0); wrist.userData.region='wrist'; handRoot.add(wrist); regionMeshes.set('wrist',wrist);

    const fingers = [
      ['index',-.86,1.75,.43,2.20,-.015],
      ['middle',-.28,2.00,.46,2.60,0],
      ['ring',.34,1.92,.45,2.45,.01],
      ['little',.91,1.72,.39,2.05,.035]
    ];
    for (const [name,x,y,r,l,rz] of fingers){
      const f = capsule(r,l,COLORS.base); f.position.set(x,y,0); f.rotation.z=rz; f.userData.region=name; handRoot.add(f); regionMeshes.set(name,f);
    }
    const thumb = capsule(.49,1.50,COLORS.base);
    thumb.position.set(-1.38,-.05,0); thumb.rotation.z=-.92; thumb.userData.region='thumb'; handRoot.add(thumb); regionMeshes.set('thumb',thumb);
  }

  function disposeGroup(group){
    if(!group) return;
    for(const obj of [...group.children]){
      obj.traverse(n=>{ if(n.isMesh){n.geometry?.dispose?.(); if(Array.isArray(n.material)) n.material.forEach(m=>m.dispose?.()); else n.material?.dispose?.();} });
      group.remove(obj);
    }
  }

  function renderDeep(){
    if(!deepRoot) return;
    disposeGroup(deepRoot);
    const deep = Boolean(current.tissue || current.cell);
    handRoot.visible = !deep;
    deepRoot.visible = deep;
    if(!deep){ setBadge('3D HAND'); return; }

    if(current.cell){
      const shell = new THREE.Mesh(new THREE.SphereGeometry(1.35,48,32), material(COLORS.cell,COLORS.cell,.14));
      shell.scale.set(1.25,.92,1); shell.userData.cell=current.cell; deepRoot.add(shell);
      for(let i=0;i<4;i++){
        const nucleus = new THREE.Mesh(new THREE.SphereGeometry(.16,20,14),material(0xe0e8ff));
        nucleus.position.set((i-1.5)*.38,Math.sin(i*1.7)*.25,.88); deepRoot.add(nucleus);
      }
      setBadge(`CELL ${String(current.cell).toUpperCase()}`); return;
    }

    const names = [];
    document.querySelectorAll('.tree-leaf[data-tissue]').forEach(b=>{ const label=(b.textContent||'').trim(); if(label) names.push(label); });
    const shown = names.slice(0,6);
    if(!shown.length){
      const field = new THREE.Mesh(new THREE.SphereGeometry(1.45,32,20),material(COLORS.tissue,COLORS.tissue,.10));
      field.scale.set(1.7,.75,1); field.userData.navigationOnly=true; deepRoot.add(field);
      setBadge('TISSUE FIELD · NAVIGATION'); return;
    }
    shown.forEach((label,i)=>{
      const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(.45,.85,8,18),material(COLORS.tissue,COLORS.tissue,.08));
      mesh.position.set((i-(shown.length-1)/2)*1.25,0,0); mesh.userData.tissue=label; deepRoot.add(mesh);
    });
    setBadge('TISSUE FIELD');
  }

  function setBadge(text){ const el=host?.querySelector('.dt3d-badge'); if(el) el.textContent=text; }

  function highlight(){
    for(const [name,mesh] of regionMeshes){
      const active = name === current.region;
      mesh.material.color.setHex(active ? COLORS.selected : COLORS.base);
      mesh.material.emissive.setHex(active ? 0x0b2745 : 0x000000);
      mesh.material.emissiveIntensity = active ? .32 : 0;
    }
    setBadge(current.cell ? `CELL ${String(current.cell).toUpperCase()}` : current.tissue ? 'TISSUE FIELD' : `${LABELS[current.region] || current.region} · 3D HAND`);
  }

  function resize(){
    if(!renderer || !camera || !host) return;
    const w=Math.max(1,host.clientWidth), h=Math.max(1,host.clientHeight);
    renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix();
  }

  function reset(){
    camera.position.set(0,.45,8.6); controls.target.set(0,.1,0); controls.update();
  }

  function selectRegion(region){
    const button=document.querySelector(`.tree-region[data-region="${CSS.escape(region)}"]`);
    if(button){ button.click(); return; }
    window.TestHPCanonicalState?.updateSelection?.({region});
  }

  function selectTissue(label){
    const buttons=[...document.querySelectorAll('.tree-leaf[data-tissue]')];
    const b=buttons.find(x=>(x.textContent||'').trim()===label);
    if(b) b.click();
  }

  function onPointer(event){
    if(!canvas || !camera) return;
    const r=canvas.getBoundingClientRect(); pointer.x=((event.clientX-r.left)/r.width)*2-1; pointer.y=-((event.clientY-r.top)/r.height)*2+1;
    raycaster.setFromCamera(pointer,camera);
    const objects=[...regionMeshes.values(),...(deepRoot?.visible?[...deepRoot.children]:[])];
    const hit=raycaster.intersectObjects(objects,true)[0]; if(!hit) return;
    let obj=hit.object; while(obj.parent && !obj.userData.region && !obj.userData.tissue && !obj.userData.cell) obj=obj.parent;
    if(obj.userData.region) selectRegion(obj.userData.region);
    else if(obj.userData.tissue) selectTissue(obj.userData.tissue);
    else if(obj.userData.cell){ window.TestHPCanonicalState?.updateSelection?.({cell:obj.userData.cell}); }
  }

  function mount(){
    const next=findViewport(); if(!next || next===host && canvas?.isConnected) return;
    host=next; host.innerHTML=''; host.classList.add('dt3d-host');
    canvas=document.createElement('canvas'); canvas.setAttribute('aria-label','Interactive 3D hand viewport'); host.appendChild(canvas);
    const badge=document.createElement('div'); badge.className='dt3d-badge'; host.appendChild(badge);
    const controlsEl=document.createElement('div'); controlsEl.className='dt3d-controls';
    resetButton=document.createElement('button'); resetButton.className='dt3d-reset'; resetButton.type='button'; resetButton.textContent='Reset view'; resetButton.onclick=reset; controlsEl.appendChild(resetButton); host.appendChild(controlsEl);
    hint=document.createElement('div'); hint.className='dt3d-hint'; hint.textContent='Drag to rotate · wheel/pinch to zoom · click a region to select'; host.appendChild(hint);

    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true}); renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2)); renderer.outputColorSpace=THREE.SRGBColorSpace;
    scene=new THREE.Scene(); scene.background=new THREE.Color(0x0d1117);
    camera=new THREE.PerspectiveCamera(32,1,.1,100); camera.position.set(0,.45,8.6);
    controls=new OrbitControls(camera,canvas); controls.enableDamping=true; controls.minDistance=4; controls.maxDistance=15; controls.target.set(0,.1,0);
    scene.add(new THREE.HemisphereLight(0xffffff,0x172033,2.1)); const key=new THREE.DirectionalLight(0xffffff,2.7); key.position.set(4,6,7); scene.add(key); const fill=new THREE.DirectionalLight(0x8bb8ff,1); fill.position.set(-5,2,-4); scene.add(fill);
    handRoot=null; deepRoot=new THREE.Group(); deepRoot.name='deep-spatial-layer'; scene.add(deepRoot); raycaster=new THREE.Raycaster(); buildHand();
    canvas.addEventListener('click',onPointer); resize(); highlight(); renderDeep();
    if(resizeObserver) resizeObserver.disconnect(); resizeObserver=new ResizeObserver(resize); resizeObserver.observe(host);
  }

  function sync(){ selectionFromCanonical(canonical()); if(!host?.isConnected){mount(); return;} highlight(); renderDeep(); }

  window.addEventListener('testhp:canonical-state-changed',sync);
  window.addEventListener('testhp:spatial-layer-changed',sync);
  const observer=new MutationObserver(()=>{ if(findViewport() && (!host?.isConnected || !host.querySelector('canvas'))) mount(); });
  observer.observe(document.body,{childList:true,subtree:true});
  selectionFromCanonical(canonical());
  const initial=setInterval(()=>{ if(findViewport()){clearInterval(initial); mount(); sync();} },100);
  setTimeout(()=>clearInterval(initial),15000);
})();
