import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

(() => {
  const viewport = document.getElementById('twin-viewport');
  const view = window.handSurfaceView;
  if (!viewport || !view) return;

  const state = {
    assets: [],
    textures: new Map(),
    registration: 'calibrated-fallback',
    scaffoldVisible: false,
    skinOpacity: 1,
  };
  view.surfaceStageState = state;

  const panel = document.createElement('div');
  panel.id = 'hand-surface-stages-3-5';
  Object.assign(panel.style, { position:'absolute', left:'18px', top:'18px', zIndex:'35', display:'none', gap:'6px', flexWrap:'wrap', maxWidth:'430px' });
  viewport.appendChild(panel);
  const button = (label, title, fn) => { const b=document.createElement('button'); b.type='button'; b.textContent=label; b.title=title; Object.assign(b.style,{padding:'7px 10px',borderRadius:'9px',border:'1px solid rgba(155,216,196,.35)',background:'rgba(13,25,24,.92)',color:'#dcece6',font:'800 11px system-ui',cursor:'pointer'}); b.onclick=fn; panel.appendChild(b); return b; };
  button('MULTI-VIEW','Use all registered hand views',()=>loadAssets(true));
  button('SCAFFOLD','Toggle anatomical skeleton reference',()=>toggleScaffold());
  button('SKIN −','Reduce skin opacity',()=>setSkin(Math.max(.2,state.skinOpacity-.1)));
  button('SKIN +','Increase skin opacity',()=>setSkin(Math.min(1,state.skinOpacity+.1)));
  const status=document.createElement('span'); Object.assign(status.style,{padding:'7px 10px',borderRadius:'9px',background:'rgba(13,25,24,.75)',color:'#b8ccc5',font:'700 10px system-ui'}); panel.appendChild(status);

  function updateStatus(){ status.textContent=`${state.assets.length} views · ${state.registration} · scaffold ${state.scaffoldVisible?'ON':'OFF'}`; }
  function setSkin(value){ state.skinOpacity=value; view.handShell?.traverse(o=>{if(o.isMesh&&o.material){o.material.transparent=value<1;o.material.opacity=value;}}); updateStatus(); }

  async function loadAssets(multi=false){
    try {
      const r=await fetch('/api/hand/analysis?subject_id=own_cohort&timepoint=T0');
      const data=await r.json();
      const assets=(data.assets||[]).filter(a=>a.modality==='hand'&&['ready','available'].includes(String(a.status||'').toLowerCase()));
      state.assets=assets.filter(a=>['front','back','left','right','side_left','side_right','thumb'].includes(String(a.view||'').toLowerCase()));
      state.registration=state.assets.length>=2?'calibrated-fallback':'unavailable';
      if(multi) await Promise.all(state.assets.map(loadTexture));
      updateStatus();
      installMultiProjection();
    }catch(e){state.registration='unavailable';updateStatus();}
  }
  function loadTexture(asset){
    return new Promise(resolve=>{ const image=new Image(); image.crossOrigin='anonymous'; image.onload=()=>{const t=new THREE.Texture(image);t.colorSpace=THREE.SRGBColorSpace;t.needsUpdate=true;state.textures.set(String(asset.view).toLowerCase(),t);resolve();}; image.onerror=resolve; image.src=`/api/hand/evidence/${encodeURIComponent(asset.asset_id)}`; });
  }

  function installMultiProjection(){
    if(!state.textures.size||!view.handShell)return;
    view.handShell.traverse(o=>{
      if(!o.isMesh||!o.material?.isMeshStandardMaterial)return;
      const material=o.material;
      material.onBeforeCompile=shader=>{
        const uniforms={};
        const entries=[...state.textures.entries()];
        entries.forEach(([key,tex],i)=>uniforms['photo'+i]={value:tex});
        shader.uniforms={...shader.uniforms,...uniforms};
        shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 hsPos; varying vec3 hsNormal;');
        shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nhsPos=(modelMatrix*vec4(transformed,1.0)).xyz; hsNormal=normalize(mat3(modelMatrix)*objectNormal);');
        shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 hsPos; varying vec3 hsNormal;');
        entries.forEach(([key],i)=>{shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`uniform sampler2D photo${i};\n#include <common>`);});
        const front=entries.findIndex(([k])=>k==='front'); const back=entries.findIndex(([k])=>k==='back'); const left=entries.findIndex(([k])=>k==='left'||k==='side_left'); const right=entries.findIndex(([k])=>k==='right'||k==='side_right');
        let sample='vec3 projected=diffuseColor.rgb; float weight=0.0;';
        const add=(idx,expr)=>{if(idx>=0)sample+=`{float w=${expr}; vec2 uv=vec2(hsPos.x/4.4+0.5,1.0-(hsPos.y/5.7+0.5)); projected=mix(projected,texture2D(photo${idx},clamp(uv,0.001,0.999)).rgb,w); weight=max(weight,w);}`;};
        add(front,'smoothstep(0.35,0.82,max(hsNormal.z,0.0))'); add(back,'smoothstep(0.35,0.82,max(-hsNormal.z,0.0))'); add(right,'smoothstep(0.45,0.9,max(hsNormal.x,0.0))'); add(left,'smoothstep(0.45,0.9,max(-hsNormal.x,0.0))');
        shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',`${sample} diffuseColor.rgb=projected;`);
      }; material.needsUpdate=true;
    });
  }

  function toggleScaffold(){
    if(!view.root)return;
    if(!view.anatomicalScaffold){
      const g=new THREE.Group(); g.name='AnatomicalScaffold';
      const bone=new THREE.MeshStandardMaterial({color:0xd8c9aa,roughness:.65,transparent:true,opacity:.88});
      const addBone=(a,b,r=.13)=>{const av=new THREE.Vector3(...a),bv=new THREE.Vector3(...b),d=bv.clone().sub(av),m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,d.length,12),bone);m.position.copy(av).add(bv).multiplyScalar(.5);m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());g.add(m);};
      addBone([0,-1.2,-.15],[0,1.0,-.15],.2); addBone([0,-1.2,-.15],[0,-2.5,-.12],.18);
      [-1.1,-.38,.38,1.1].forEach(x=>addBone([x,1.0,-.16],[x,3.0,-.16],.12));
      addBone([-1.15,.3,-.18],[-1.85,1.25,-.16],.14);
      view.root.add(g); view.anatomicalScaffold=g;
    }
    state.scaffoldVisible=!state.scaffoldVisible; view.anatomicalScaffold.visible=state.scaffoldVisible; updateStatus();
  }

  const originalShow=view.show.bind(view);
  view.show=(visible)=>{originalShow(visible);panel.style.display=visible?'flex':'none';updateStatus();};
  const originalReset=view.reset.bind(view); view.reset=()=>{originalReset();setSkin(1);if(view.anatomicalScaffold)view.anatomicalScaffold.visible=false;state.scaffoldVisible=false;};

  const originalDebug=window.__handSurfaceDebug;
  window.__handSurfaceDebug=()=>({ stage:'3-5', viewCount:state.assets.length, views:state.assets.map(a=>a.view), registration:state.registration, scaffoldVisible:state.scaffoldVisible, skinOpacity:state.skinOpacity, viewportOwner:view.visible?'HandSurfaceView':'base/deep' });

  loadAssets(false);
})();
