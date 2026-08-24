(() => {
  const PARAMS = { palmLength: 1, palmWidth: 1, thickness: 1, fingerSpread: 1, taper: 1, thumbAngle: 1 };
  const RANGES = { palmLength: [.75,1.25], palmWidth: [.75,1.25], thickness: [.75,1.25], fingerSpread: [.7,1.3], taper: [.7,1.3], thumbAngle: [.7,1.3] };
  const FINGERS = ['index','middle','ring','little'];
  const KEY = 'digitalTwinHandGeometry.live.v1';
  const clamp = (v,a,b) => Math.min(b,Math.max(a,Number(v)||1));
  const read = () => { try { const x=JSON.parse(localStorage.getItem(KEY)||'null'); return {...PARAMS,...(x?.parameters||x||{})}; } catch { return {...PARAMS}; } };

  let state=read();
  let host=null,canvas=null,renderer=null,scene=null,camera=null,controls=null;
  let previewRoot=null,meshes=new Map(),resizeObserver=null,frame=0,booted=false,previewReady=false;

  const getMain=()=>{
    const active=window.spatialViewportManager?.active;
    const roots=[active?.root,active?.scene].filter(Boolean),out=new Map();
    const visit=o=>{ if(!o||out.size>=6)return; const name=String(o.name||'').replace(/^skin:/,''); if(['palm',...FINGERS,'thumb'].includes(name)&&o.isMesh)out.set(name,o); o.children?.forEach(visit); };
    roots.forEach(visit); return out;
  };
  const bases=new WeakMap();
  const base=mesh=>{ let v=bases.get(mesh); if(!v){v={p:mesh.position.clone(),s:mesh.scale.clone(),rz:mesh.rotation.z};bases.set(mesh,v);} return v; };
  const save=()=>localStorage.setItem(KEY,JSON.stringify({schema:'hand-surface-geometry-live-v4',parameters:state,updatedAt:new Date().toISOString()}));
  const renderMain=()=>{const a=window.spatialViewportManager?.active;if(a?.renderer&&a.scene&&a.camera){try{a.renderer.render(a.scene,a.camera);}catch{}}};

  const updateMain=()=>{
    const mm=getMain(),palm=mm.get('palm'); if(!palm)return mm;
    const pb=base(palm); palm.scale.set(pb.s.x*state.palmWidth,pb.s.y*state.palmLength,pb.s.z*state.thickness);
    FINGERS.forEach((name,index)=>{const m=mm.get(name);if(!m)return;const b=base(m);m.position.x=b.p.x+(index-1.5)*.2*(state.fingerSpread-1);const width=1-.22*(state.taper-1);m.scale.set(b.s.x*width,b.s.y,b.s.z*state.thickness);m.rotation.z=b.rz;});
    const thumb=mm.get('thumb'); if(thumb){const b=base(thumb);thumb.rotation.z=b.rz-.42*(state.thumbAngle-1);thumb.scale.set(b.s.x*(1-.1*(state.taper-1)),b.s.y,b.s.z*state.thickness);}
    renderMain(); return mm;
  };

  const setStatus=text=>{const e=document.querySelector('#hand-geometry-live-preview [data-geometry-preview-status]');if(e)e.textContent=text;};
  const updateUi=()=>{const card=document.getElementById('hand-geometry-live-preview');if(!card)return;const s=card.querySelector('[data-geometry-preview-status]');if(s)s.textContent=previewReady?(Object.values(state).every(v=>Number(v)===1)?'Live · wartości domyślne':'Live · zmieniona geometria'):'Uruchamianie…';const ms=card.querySelector('[data-geometry-main-status]');if(ms){const count=getMain().size;ms.textContent=count>=6?`Połączono z modelem głównym · ${count} elementów geometrii`:'Podgląd działa lokalnie. Model główny jest chwilowo niedostępny.';}};

  const updatePreview=()=>{
    if(!meshes.size)return; const palm=meshes.get('palm'); if(palm)palm.scale.set(state.palmWidth,state.palmLength,state.thickness);
    const xs=[-1.05,-.35,.42,1.12];
    FINGERS.forEach((name,index)=>{const m=meshes.get(name);if(!m)return;m.position.x=xs[index]+(index-1.5)*.2*(state.fingerSpread-1);const width=1-.22*(state.taper-1);m.scale.set(width,1,state.thickness);});
    const thumb=meshes.get('thumb');if(thumb){thumb.rotation.z=-.82-.42*(state.thumbAngle-1);thumb.scale.set(1-.1*(state.taper-1),1,state.thickness);} updateUi();
  };
  const resize=()=>{if(!renderer||!camera||!host)return;const r=host.getBoundingClientRect(),w=Math.max(1,Math.round(r.width)),h=Math.max(1,Math.round(r.height));renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();};
  const framePreview=THREE=>{if(!previewRoot||!camera)return;const box=new THREE.Box3().setFromObject(previewRoot);if(box.isEmpty())return;const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()),maxSize=Math.max(size.x,size.y,size.z),fov=camera.fov*Math.PI/180,distance=(maxSize/2)/Math.tan(fov/2)*1.28;camera.position.set(center.x,center.y+.1,center.z+Math.max(7,distance));camera.near=Math.max(.01,distance/100);camera.far=Math.max(100,distance*8);camera.lookAt(center);camera.updateProjectionMatrix();if(controls){controls.target.copy(center);controls.minDistance=Math.max(4,distance*.45);controls.maxDistance=Math.max(20,distance*2.5);controls.update();}};

  const makePreview=async()=>{
    if(previewReady||!canvas||!canvas.isConnected)return;
    try{
      setStatus('Uruchamianie…');
      const THREE=await import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js');
      const {OrbitControls}=await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js');
      if(!canvas.isConnected)return;
      renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setClearColor(0x0b1220,1);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
      scene=new THREE.Scene();scene.background=new THREE.Color(0x0b1220);camera=new THREE.PerspectiveCamera(30,1,.01,100);controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=true;
      scene.add(new THREE.HemisphereLight(0xffffff,0x334155,2.8));const key=new THREE.DirectionalLight(0xffffff,3.2);key.position.set(4,7,9);scene.add(key);const fill=new THREE.DirectionalLight(0xffd8c2,1.5);fill.position.set(-5,3,5);scene.add(fill);
      previewRoot=new THREE.Group();previewRoot.name='hand-geometry-live-preview-root';previewRoot.rotation.x=-.14;scene.add(previewRoot);
      const add=(id,pos,radius,length,rotation=[0,0,0])=>{const material=new THREE.MeshStandardMaterial({color:0xc68b72,roughness:.64,metalness:0,emissive:0x24130d,emissiveIntensity:.035});const mesh=new THREE.Mesh(new THREE.CapsuleGeometry(radius,length,8,18),material);mesh.name=id;mesh.position.set(...pos);mesh.rotation.set(...rotation);previewRoot.add(mesh);meshes.set(id,mesh);};
      add('wrist',[0,-2.15,0],.72,1.25);add('palm',[0,-.35,0],1.55,2.25);add('thumb',[-1.45,0,.02],.48,1.45,[0,0,-.82]);add('index',[-1.05,1.95,0],.43,2.15);add('middle',[-.35,2.25,0],.46,2.55);add('ring',[.42,2.12,0],.45,2.32);add('little',[1.12,1.86,0],.4,1.95,[0,0,.08]);
      resizeObserver=new ResizeObserver(()=>resize());resizeObserver.observe(host);resize();updatePreview();framePreview(THREE);previewReady=true;updateUi();
      canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();previewReady=false;cancelAnimationFrame(frame);setStatus('Podgląd utracił kontekst WebGL');},{passive:false});
      canvas.addEventListener('webglcontextrestored',()=>{previewReady=true;updatePreview();framePreview(THREE);});
      const render=()=>{if(!renderer||!canvas?.isConnected)return;resize();controls?.update();renderer.render(scene,camera);frame=requestAnimationFrame(render);};render();
    }catch(error){previewReady=false;console.error('[hand-surface-geometry-live] preview boot failed',error);setStatus(`Podgląd niedostępny: ${error?.message||error}`);}
  };

  const geometryRoot=()=>{const title=[...document.querySelectorAll('strong')].find(e=>e.textContent?.trim()==='Geometria dłoni');if(!title)return null;const intro=title.closest('.hss-geometry-intro'),container=intro?.parentElement;return intro&&container?{intro,container}:null;};
  const installUi=()=>{const existing=document.getElementById('hand-geometry-live-preview');if(existing?.isConnected){host=existing.querySelector('[data-geometry-preview-canvas]');canvas=existing.querySelector('canvas');if(host&&canvas)makePreview();return true;}const root=geometryRoot();if(!root)return false;const card=document.createElement('section');card.id='hand-geometry-live-preview';card.style.cssText='margin:14px 0 16px;border:1px solid var(--border,#d8dee8);border-radius:12px;overflow:hidden;background:var(--panel,#fff)';card.innerHTML=`<div style="display:flex;justify-content:space-between;gap:12px;padding:13px 14px;border-bottom:1px solid var(--border,#d8dee8)"><div><strong style="display:block;font-size:14px">Podgląd 3D</strong><span style="display:block;margin-top:3px;font-size:12px;color:#667085">Przesuwaj suwaki i obserwuj dokładnie ten sam efekt w podglądzie.</span></div><span data-geometry-preview-status style="font-size:11px;font-weight:800;color:#027a48">Uruchamianie…</span></div><div data-geometry-preview-canvas style="height:360px;background:#0b1220;position:relative"><canvas aria-label="Podgląd geometrii dłoni" style="width:100%;height:100%;display:block"></canvas><div style="position:absolute;left:12px;bottom:10px;color:#c9d1d9;font-size:11px;background:rgba(13,17,23,.72);padding:6px 8px;border-radius:7px">Przeciągnij · kółko myszy = zoom</div></div><div data-geometry-main-status style="padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid var(--border,#d8dee8)"></div>`;root.container.appendChild(card);host=card.querySelector('[data-geometry-preview-canvas]');canvas=card.querySelector('canvas');makePreview();return true;};
  const bind=()=>{const root=geometryRoot()?.container;if(!root)return;const map=[['palmLength',/długość dłoni/i],['palmWidth',/szerokość dłoni/i],['thickness',/grubość powierzchni/i],['fingerSpread',/rozstaw palców/i],['taper',/zwężenie palców/i],['thumbAngle',/ustawienie kciuka/i]];root.querySelectorAll('input[type="range"]').forEach(input=>{if(input.dataset.geometryLiveBound)return;const text=input.closest('label,div')?.textContent||'',hit=map.find(([,regexp])=>regexp.test(text));if(!hit)return;input.dataset.geometryLiveBound='1';input.value=state[hit[0]];input.addEventListener('input',()=>window.digitalTwinGeometry.setParameter(hit[0],input.value));});};

  const api=window.digitalTwinGeometry||{};api.version='canonical-geometry-4-live';api.__liveBridgeInstalled=true;api.getState=()=>({...state});api.inspect=()=>Object.fromEntries([...getMain()].map(([id,m])=>[id,{position:m.position.toArray(),scale:m.scale.toArray(),rotation:[m.rotation.x,m.rotation.y,m.rotation.z]}]));
  const applyState=next=>{state={...state,...Object.fromEntries(Object.keys(PARAMS).map(key=>[key,clamp(next[key]??state[key],...RANGES[key])]))};save();updateMain();updatePreview();return {...state};};
  api.setParameter=(name,value)=>{if(!(name in PARAMS))return{ok:false,error:`Unknown geometry parameter: ${name}`};applyState({[name]:value});return{ok:true,meshCount:getMain().size,geometry:{...state}};};
  api.setState=next=>{applyState(next||{});return{ok:true,geometry:{...state}};};
  api.reset=()=>api.setState(PARAMS);window.digitalTwinGeometry=api;

  const ensure=()=>{installUi();bind();updateMain();updatePreview();};
  const boot=()=>{if(booted)return;booted=true;ensure();const observer=new MutationObserver(()=>{if(!document.getElementById('hand-geometry-live-preview'))ensure();});observer.observe(document.body,{childList:true,subtree:true});['testhp:deep-3d-active','testhp:viewport-manager-ready','testhp:spatial-layer-changed'].forEach(eventName=>window.addEventListener(eventName,()=>setTimeout(ensure,0)));};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
