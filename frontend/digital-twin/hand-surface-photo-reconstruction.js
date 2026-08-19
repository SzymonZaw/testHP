import * as THREE from 'three';

(() => {
  const EVIDENCE = 'digitalTwinEvidenceUX.v2';
  const SURFACE = 'digitalTwinHandSurface.v1';
  const VIEWS = ['front','back','side_left','side_right','thumb'];
  const $ = id => document.getElementById(id);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const read = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };
  const evidence = () => { const x = read(EVIDENCE, {evidence:[]}); return Array.isArray(x.evidence) ? x.evidence.filter(e => !e.archived) : []; };
  const inferView = e => {
    const explicit = String(e?.view || e?.preparedAsset?.view || '').toLowerCase();
    if (VIEWS.includes(explicit)) return explicit;
    const name = String(e?.filename || e?.preparedAsset?.name || '').toLowerCase().replace(/[- ]/g,'_');
    return VIEWS.find(v => name.includes(v)) || null;
  };
  const preparedFor = view => evidence().find(e => e.sourceType === 'prepared-image' && e.prepared && inferView(e) === view) || null;
  const state = { renderer:null, scene:null, camera:null, mesh:null, atlas:null, running:false, yaw:.25, pitch:.08, distance:3.8 };

  function css(){ if($('photo-reconstruction-css')) return; const s=document.createElement('style'); s.id='photo-reconstruction-css'; s.textContent=`
    #photo-3d-reconstruction{margin-top:16px}.p3r-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}.p3r-card{border:1px solid var(--border,#d8dee8);border-radius:12px;padding:14px;background:var(--panel,#fff)}.p3r-canvas{height:430px;border-radius:10px;background:#eef2f6;overflow:hidden;position:relative}.p3r-canvas canvas{display:block;width:100%;height:100%}.p3r-head,.p3r-actions{display:flex;align-items:center;justify-content:space-between;gap:8px}.p3r-actions{justify-content:flex-start;flex-wrap:wrap}.p3r-list{display:grid;gap:7px;margin-top:10px}.p3r-item{border:1px solid var(--border,#d8dee8);border-radius:9px;padding:9px}.p3r-badge{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}.p3r-good{color:#1f6b45}.p3r-warn{color:#9a6700}.p3r-bad{color:#a33a3a}.p3r-note{font-size:12px;color:#667085}.p3r-status{padding:9px 10px;border-radius:9px;background:rgba(79,111,143,.08);font-size:12px}.p3r-meter{height:8px;background:#e8edf3;border-radius:999px;overflow:hidden}.p3r-meter i{display:block;height:100%;width:0;background:#4f6f8f}.p3r-code{font:11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:#f6f8fa;border-radius:9px;padding:10px;max-height:220px;overflow:auto;white-space:pre-wrap}@media(max-width:800px){.p3r-grid{grid-template-columns:1fr}}
  `; document.head.appendChild(s); }

  function panel(){
    if($('photo-3d-reconstruction')) return;
    const p=document.createElement('section'); p.id='photo-3d-reconstruction'; p.className='panel';
    p.innerHTML=`<div class="panel-title"><div><span class="section-kicker">PHOTO 3D RECONSTRUCTION</span><strong>REAL PHOTOGRAPHS → 3D HAND</strong></div><span class="muted">visual hull + multi-view surface texture</span></div><div class="p3r-grid"><div class="p3r-card"><div id="p3r-stage" class="p3r-canvas"><div class="viewer-loading">Add prepared photos to build the reconstruction.</div></div><div class="p3r-actions" style="margin-top:10px"><button id="p3r-build" class="primary">Build 3D reconstruction</button><button id="p3r-clear">Clear reconstruction</button></div></div><div class="p3r-card"><div class="p3r-head"><strong>Photo inputs</strong><span id="p3r-score" class="p3r-badge">0 / 5</span></div><p class="p3r-note">Uses foreground-separated photographs. View assignment can come from explicit metadata or a filename containing front, back, side_left, side_right or thumb.</p><div id="p3r-inputs" class="p3r-list"></div><div class="p3r-meter" style="margin-top:10px"><i id="p3r-meter"></i></div><div id="p3r-status" class="p3r-status" style="margin-top:10px">Waiting for prepared photographs.</div><pre id="p3r-meta" class="p3r-code" style="margin-top:10px">No reconstruction yet.</pre></div></div>`;
    document.querySelector('#hand-surface-studio')?.after(p) || document.querySelector('.timeline')?.before(p); renderInputs();
  }

  function renderInputs(){
    const c=$('p3r-inputs'); if(!c)return; let ready=0;
    c.innerHTML=VIEWS.map(v=>{const e=preparedFor(v); if(e)ready++; return `<div class="p3r-item"><div class="p3r-head"><strong>${esc(v.replaceAll('_',' '))}</strong><span class="p3r-badge ${e?'p3r-good':'p3r-bad'}">${e?'READY':'MISSING'}</span></div><small>${e?esc(e.filename||e.preparedAsset?.name||'prepared image'):'prepare and save this view in Stage 12'}</small></div>`}).join('');
    $('p3r-score').textContent=`${ready} / ${VIEWS.length}`; $('p3r-meter').style.width=`${Math.round(ready/VIEWS.length*100)}%`; $('p3r-build').disabled=ready<2; $('p3r-status').textContent=ready<2?'At least two prepared views are required.':'Ready for silhouette reconstruction.';
  }

  function loadImage(dataUrl){ return new Promise((resolve,reject)=>{const img=new Image(); img.onload=()=>resolve(img); img.onerror=reject; img.src=dataUrl;}); }
  function alphaAt(img,u,v){
    if(!img)return 0;
    const c=img.__maskCanvas || (()=>{const cv=document.createElement('canvas'); const size=192; cv.width=size; cv.height=size; cv.getContext('2d').drawImage(img,0,0,size,size); img.__maskCanvas=cv; return cv;})();
    const x=c.getContext('2d'); const px=x.getImageData(Math.max(0,Math.min(c.width-1,Math.round(u*(c.width-1)))),Math.max(0,Math.min(c.height-1,Math.round((1-v)*(c.height-1)))),1,1); return px.data[3];
  }
  function project(view,p){
    if(view==='front') return {u:(p.x+1)/2,v:(p.y+1)/2,depth:p.z};
    if(view==='back') return {u:(1-p.x)/2,v:(p.y+1)/2,depth:-p.z};
    if(view==='side_left') return {u:(p.z+1)/2,v:(p.y+1)/2,depth:p.x};
    if(view==='side_right') return {u:(1-p.z)/2,v:(p.y+1)/2,depth:-p.x};
    return {u:(p.x+1)/2,v:(p.z+1)/2,depth:p.y};
  }
  function normalForView(view){ return ({front:new THREE.Vector3(0,0,1),back:new THREE.Vector3(0,0,-1),side_left:new THREE.Vector3(-1,0,0),side_right:new THREE.Vector3(1,0,0),thumb:new THREE.Vector3(0,1,0)})[view]; }
  function bestView(p,n,available){ let best=available[0],score=-Infinity; for(const v of available){const s=n.dot(normalForView(v))-Math.abs(project(v,p).depth)*.12;if(s>score){score=s;best=v;}} return best; }

  function buildVoxelMesh(images,resolution=34){
    const occupied=new Uint8Array(resolution*resolution*resolution), idx=(x,y,z)=>x+resolution*(y+resolution*z), available=VIEWS.filter(v=>images[v]); let count=0;
    for(let z=0;z<resolution;z++)for(let y=0;y<resolution;y++)for(let x=0;x<resolution;x++){
      const p={x:x/(resolution-1)*2-1,y:y/(resolution-1)*2-1,z:z/(resolution-1)*2-1}; let inside=true;
      for(const v of available){const q=project(v,p);if(q.u<0||q.u>1||q.v<0||q.v>1||alphaAt(images[v],q.u,q.v)<24){inside=false;break;}}
      if(inside){occupied[idx(x,y,z)]=1;count++;}
    }
    const positions=[],uvs=[],indices=[];let vi=0;
    const dirs=[[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1]];
    const corners=[[[0,0,0],[0,0,1],[0,1,1],[0,1,0]],[[1,0,0],[1,1,0],[1,1,1],[1,0,1]],[[0,0,0],[1,0,0],[1,0,1],[0,0,1]],[[0,1,0],[0,1,1],[1,1,1],[1,1,0]],[[0,0,0],[0,1,0],[1,1,0],[1,0,0]],[[0,0,1],[1,0,1],[1,1,1],[0,1,1]]];
    const tile={front:0,back:1,side_left:2,side_right:3,thumb:4};
    for(let z=0;z<resolution;z++)for(let y=0;y<resolution;y++)for(let x=0;x<resolution;x++)if(occupied[idx(x,y,z)])for(let f=0;f<6;f++){
      const nx=x+dirs[f][0],ny=y+dirs[f][1],nz=z+dirs[f][2]; if(nx>=0&&ny>=0&&nz>=0&&nx<resolution&&ny<resolution&&nz<resolution&&occupied[idx(nx,ny,nz)])continue;
      const pts=corners[f].map(c=>({x:(x+c[0])/(resolution-1)*2-1,y:(y+c[1])/(resolution-1)*2-1,z:(z+c[2])/(resolution-1)*2-1})); const n=new THREE.Vector3(...dirs[f]); const view=bestView(pts[0],n,available); const t=tile[view],bu=(t%3)/3,bv=Math.floor(t/3)/2;
      for(const p of pts){const q=project(view,p);positions.push(p.x,p.y,p.z);uvs.push(bu+Math.max(0,Math.min(1,q.u))/3,bv+(1-Math.max(0,Math.min(1,q.v)))/2);} indices.push(vi,vi+1,vi+2,vi,vi+2,vi+3);vi+=4;
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));g.setIndex(indices);g.computeVertexNormals();return {geometry:g,voxelCount:count,available};
  }

  async function makeAtlas(images){
    const canvas=document.createElement('canvas');canvas.width=1536;canvas.height=1024;const ctx=canvas.getContext('2d');ctx.fillStyle='#f3f4f6';ctx.fillRect(0,0,canvas.width,canvas.height);
    for(let i=0;i<VIEWS.length;i++){const img=images[VIEWS[i]];if(!img)continue;const x=i%3*512,y=Math.floor(i/3)*512,scale=Math.min(512/img.naturalWidth,512/img.naturalHeight),w=img.naturalWidth*scale,h=img.naturalHeight*scale;ctx.drawImage(img,x+(512-w)/2,y+(512-h)/2,w,h);}
    const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;tex.needsUpdate=true;return tex;
  }

  function mountRenderer(){
    if(state.renderer)return; const host=$('p3r-stage');const r=new THREE.WebGLRenderer({antialias:true,alpha:true});r.setPixelRatio(Math.min(devicePixelRatio||1,2));r.setSize(host.clientWidth,host.clientHeight,false);r.outputColorSpace=THREE.SRGBColorSpace;host.innerHTML='';host.appendChild(r.domElement);
    const scene=new THREE.Scene();scene.background=new THREE.Color(0xf1f4f7);const camera=new THREE.PerspectiveCamera(35,host.clientWidth/host.clientHeight,.01,20);camera.position.set(0,0,state.distance);scene.add(new THREE.HemisphereLight(0xffffff,0x8892a0,2));state.renderer=r;state.scene=scene;state.camera=camera;
    const resize=()=>{camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();r.setSize(host.clientWidth,host.clientHeight,false);render()};new ResizeObserver(resize).observe(host);
    let down=null;host.onpointerdown=e=>{down={x:e.clientX,y:e.clientY,yaw:state.yaw,pitch:state.pitch};host.setPointerCapture?.(e.pointerId)};host.onpointermove=e=>{if(!down)return;state.yaw=down.yaw+(e.clientX-down.x)*.008;state.pitch=Math.max(-1.1,Math.min(1.1,down.pitch+(e.clientY-down.y)*.006));render()};host.onpointerup=()=>down=null;host.onwheel=e=>{e.preventDefault();state.distance=Math.max(2.2,Math.min(7,state.distance+e.deltaY*.0025));render()};
  }
  function render(){if(!state.renderer)return;const r=state.renderer,c=state.camera;c.position.set(Math.sin(state.yaw)*state.distance,Math.sin(state.pitch)*state.distance,Math.cos(state.yaw)*state.distance);c.lookAt(0,0,0);r.render(state.scene,c);}

  async function build(){
    if(state.running)return;state.running=true;$('p3r-build').disabled=true;$('p3r-status').textContent='Loading prepared photographs…';const images={};
    try{
      for(const v of VIEWS){const e=preparedFor(v),url=e?.preparedAsset?.dataUrl;if(url)images[v]=await loadImage(url);}const available=VIEWS.filter(v=>images[v]);if(available.length<2)throw new Error('At least two prepared photographs are required.');
      $('p3r-status').textContent=`Carving visual hull from ${available.length} views…`;const built=buildVoxelMesh(images,34);if(built.voxelCount<40)throw new Error('The silhouettes do not overlap enough to form a stable volume.');
      const atlas=await makeAtlas(images);mountRenderer();if(state.mesh){state.scene.remove(state.mesh);state.mesh.geometry.dispose();state.mesh.material.dispose();}const mat=new THREE.MeshStandardMaterial({map:atlas,roughness:.78,metalness:0});state.mesh=new THREE.Mesh(built.geometry,mat);state.scene.add(state.mesh);state.atlas=atlas;render();
      localStorage.setItem('digitalTwinPhotoReconstruction.v1',JSON.stringify({schema:'photo-reconstruction-v1',method:'multi-view-visual-hull',views:available,resolution:34,voxelCount:built.voxelCount,textureProjection:'normal-weighted-view-selection',generatedAt:new Date().toISOString(),target:window.spatialEvidenceTarget||'hand'}));
      $('p3r-status').textContent='3D reconstruction ready. Drag to inspect the reconstructed surface.';$('p3r-meta').textContent=JSON.stringify({method:'multi-view-visual-hull',views:available,resolution:34,voxelCount:built.voxelCount,textureProjection:'normal-weighted-view-selection',note:'Silhouette-based reconstruction; not calibrated photogrammetry.'},null,2);
    }catch(e){$('p3r-status').textContent=e.message||'Reconstruction failed.';}finally{state.running=false;$('p3r-build').disabled=VIEWS.filter(v=>preparedFor(v)).length<2;}
  }
  function clear(){if(state.mesh){state.scene.remove(state.mesh);state.mesh.geometry.dispose();state.mesh.material.dispose();state.mesh=null;}if(state.atlas){state.atlas.dispose();state.atlas=null;}$('p3r-meta').textContent='No reconstruction yet.';$('p3r-status').textContent='Reconstruction cleared.';}
  function boot(){css();panel();$('p3r-build').onclick=build;$('p3r-clear').onclick=clear;window.addEventListener('testhp:evidence-attached',renderInputs);window.addEventListener('resize',render);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
