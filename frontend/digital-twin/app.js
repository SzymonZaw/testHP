import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const subjectId='own_cohort';
const timepoint='T0';
const viewport=document.getElementById('twin-viewport');
const canvas=document.getElementById('twin-canvas');
const loading=document.getElementById('viewer-loading');
const dialog=document.getElementById('observation-dialog');
let analysis=null;
let selectedRegion='palm';
let selectedMacroIndex=0;
let spatialPath=[{id:'hand',label:'Hand',level:'macro',type:'root'}];
const regionMeshes=new Map();

const REGION_LABELS={wrist:'Wrist',palm:'Palm',thumb:'Thumb',index:'Index finger',middle:'Middle finger',ring:'Ring finger',little:'Little finger'};
const PALM_VIEWS=new Set(['front','back','side_left','side_right']);
const SCALE_LABELS={macro:'Macro anatomy',tissue:'Tissue field',cellular:'Cellular field',cell:'Single cell'};

const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x0d1117);
const camera=new THREE.PerspectiveCamera(32,1,.1,100);
camera.position.set(0,1.5,8.5);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;
controls.enablePan=true;
controls.minDistance=4;
controls.maxDistance=15;
controls.target.set(0,.4,0);
scene.add(new THREE.HemisphereLight(0xffffff,0x172033,2.2));
const key=new THREE.DirectionalLight(0xffffff,2.8);key.position.set(4,6,7);scene.add(key);
const fill=new THREE.DirectionalLight(0x8bb8ff,1);fill.position.set(-5,2,-4);scene.add(fill);
const root=new THREE.Group();root.rotation.x=-.18;scene.add(root);

const normal=new THREE.MeshStandardMaterial({color:0xc68b72,roughness:.72});
const selected=new THREE.MeshStandardMaterial({color:0x66b3ff,roughness:.58,emissive:0x0b2745,emissiveIntensity:.35});
const review=new THREE.MeshStandardMaterial({color:0xd6a64f,roughness:.68});
const unavailable=new THREE.MeshStandardMaterial({color:0x586174,roughness:.9});

function capsule(name,p,r,l,rot=[0,0,0]){const m=new THREE.Mesh(new THREE.CapsuleGeometry(r,l,8,16),normal.clone());m.name=name;m.position.set(...p);m.rotation.set(...rot);root.add(m);regionMeshes.set(name,m);return m;}
capsule('wrist',[0,-2.15,0],.72,1.25);capsule('palm',[0,-.35,0],1.55,2.25);capsule('thumb',[-1.45,0,.02],.48,1.45,[0,0,-.82]);capsule('index',[-1.05,1.95,0],.43,2.15);capsule('middle',[-.35,2.25,0],.46,2.55);capsule('ring',[.42,2.12,0],.45,2.32);capsule('little',[1.12,1.86,0],.40,1.95,[0,0,.08]);

function availableAssets(){return (analysis?.assets||[]).filter(x=>['ready','available'].includes(String(x.status||'').toLowerCase()));}
function handAssets(){return availableAssets().filter(x=>x.modality==='hand');}
function assetView(asset){return String(asset.view||'unknown').toLowerCase();}
function regionEvidence(region){const assets=handAssets();if(region==='palm')return assets.filter(x=>PALM_VIEWS.has(assetView(x)));if(region==='thumb')return assets.filter(x=>assetView(x)==='thumb'||x.zone_id==='thumb');return assets.filter(x=>x.zone_id===region);}
function tissueEvidence(region){return availableAssets().filter(x=>x.modality==='wsi'&&x.region_id===region&&x.subject_id===subjectId&&x.timepoint===timepoint);}
function molecularEvidence(region){return availableAssets().filter(x=>x.modality==='rna'&&x.region_id===region&&x.subject_id===subjectId&&x.timepoint===timepoint);}
function cellularEvidence(region){return availableAssets().filter(x=>['microscopy','cellular'].includes(String(x.modality).toLowerCase())&&x.region_id===region&&x.subject_id===subjectId&&x.timepoint===timepoint);}
function status(region){const macro=regionEvidence(region),tissue=tissueEvidence(region),cellular=cellularEvidence(region),molecular=molecularEvidence(region);return{macro:macro.length>0,macroCount:macro.length,tissue:tissue.length>0,tissueCount:tissue.length,cellular:cellular.length>0,cellularCount:cellular.length,molecular:molecular.length>0,molecularCount:molecular.length};}
function mat(region){const s=status(region);if(!s.macro&&!s.tissue&&!s.cellular&&!s.molecular)return unavailable.clone();if(!s.macro||s.tissue||s.cellular||s.molecular)return review.clone();return normal.clone();}
function setEvidenceStatus(id,label){const el=document.getElementById(id);if(el)el.textContent=label;}
function setText(id,value){const el=document.getElementById(id);if(el)el.textContent=value;}
function setValue(id,value){const el=document.getElementById(id);if(el)el.value=value;}

function spatialNodeLabel(node){return node.label;}
function currentSpatial(){return spatialPath[spatialPath.length-1];}
function spatialRegion(){return spatialPath.findLast(x=>x.regionId)?.regionId||selectedRegion;}
function childTargets(node){
  if(node.level==='macro'){
    if(node.regionId==='palm') return [
      {id:'thenar',label:'Thenar eminence',level:'tissue',regionId:'palm'},
      {id:'hypothenar',label:'Hypothenar eminence',level:'tissue',regionId:'palm'},
      {id:'central-palm',label:'Central palm',level:'tissue',regionId:'palm'}
    ];
    if(['index','middle','ring','little'].includes(node.regionId)) return [
      {id:`${node.regionId}-proximal`,label:'Proximal segment',level:'tissue',regionId:node.regionId},
      {id:`${node.regionId}-middle`,label:'Middle segment',level:'tissue',regionId:node.regionId},
      {id:`${node.regionId}-distal`,label:'Distal segment',level:'tissue',regionId:node.regionId}
    ];
    if(node.regionId==='thumb') return [
      {id:'thumb-proximal',label:'Proximal segment',level:'tissue',regionId:'thumb'},
      {id:'thumb-distal',label:'Distal segment',level:'tissue',regionId:'thumb'}
    ];
    return [{id:'regional-field',label:'Regional field',level:'tissue',regionId:node.regionId}];
  }
  if(node.level==='tissue') return [
    {id:`${node.id}-field-a`,label:'Microscopy field A',level:'cellular',regionId:node.regionId},
    {id:`${node.id}-field-b`,label:'Microscopy field B',level:'cellular',regionId:node.regionId},
    {id:`${node.id}-field-c`,label:'Microscopy field C',level:'cellular',regionId:node.regionId}
  ];
  if(node.level==='cellular') return [
    {id:`${node.id}-cell-1`,label:'Cell target 1',level:'cell',regionId:node.regionId},
    {id:`${node.id}-cell-2`,label:'Cell target 2',level:'cell',regionId:node.regionId},
    {id:`${node.id}-cell-3`,label:'Cell target 3',level:'cell',regionId:node.regionId}
  ];
  return [];
}
function renderSpatialNavigator(){
  const current=currentSpatial();
  setText('spatial-level-badge',(SCALE_LABELS[current.level]||current.level).toUpperCase());
  const breadcrumb=document.getElementById('spatial-breadcrumb');breadcrumb.replaceChildren();
  spatialPath.forEach((node,index)=>{const b=document.createElement('button');b.type='button';b.textContent=spatialNodeLabel(node);b.className=index===spatialPath.length-1?'current':'';b.onclick=()=>{spatialPath=spatialPath.slice(0,index+1);applySpatialNode();};breadcrumb.appendChild(b);if(index<spatialPath.length-1){const sep=document.createElement('span');sep.textContent='›';breadcrumb.appendChild(sep);}});
  const node=document.getElementById('spatial-node');node.replaceChildren();
  const title=document.createElement('strong');title.textContent=current.label;node.appendChild(title);
  const meta=document.createElement('span');meta.textContent=`${SCALE_LABELS[current.level]||current.level} · ${current.level==='cell'?'navigation only':'spatial target'}`;node.appendChild(meta);
  const children=document.getElementById('spatial-children');children.replaceChildren();
  const targets=childTargets(current);
  if(!targets.length){const empty=document.createElement('div');empty.className='spatial-empty';empty.innerHTML='<strong>Finest spatial target</strong><span>No deeper target is defined here. Deeper biological resolution requires explicitly linked evidence.</span>';children.appendChild(empty);return;}
  targets.forEach(target=>{const button=document.createElement('button');button.type='button';button.className='spatial-target';const t=document.createElement('strong');t.textContent=target.label;const s=document.createElement('span');s.textContent=SCALE_LABELS[target.level];button.append(t,s);button.onclick=()=>{spatialPath.push(target);applySpatialNode();};children.appendChild(button);});
}
function applySpatialNode(){
  const current=currentSpatial();
  if(current.regionId){selectedRegion=current.regionId;selectedMacroIndex=0;}
  renderSpatialNavigator();
  updateInspectorForSpatial(current);
}
function updateInspectorForSpatial(node){const region=node.regionId||selectedRegion;const s=status(region);setText('zone-label',region);setText('region-title',node.label||REGION_LABELS[region]||region);setText('region-context',`Hand · ${timepoint} · ${SCALE_LABELS[node.level]||node.level}`);const macroVisible=node.level==='macro';const preview=document.getElementById('macro-preview');if(macroVisible){setText('macro-state',s.macro?`${s.macroCount} view${s.macroCount===1?'':'s'} available`:'No evidence');setText('macro-detail',s.macro?'Registered hand images are available for this region. Use the view selector to inspect each one.':'No explicitly region-relevant hand image is currently available.');setEvidenceStatus('macro-status',s.macro?'OBSERVED':'NONE');renderMacro(region);preview.closest('.evidence-row').hidden=false;}else{preview.hidden=true;preview.closest('.evidence-row').hidden=false;setText('macro-state','Not shown at this resolution');setText('macro-detail','Macro evidence remains attached to the parent spatial region; it is not presented as evidence for this deeper target.');setEvidenceStatus('macro-status','PARENT');const nav=document.getElementById('macro-gallery');if(nav)nav.remove();}const tissueHere=node.level==='tissue'?s.tissue:false;const cellularHere=node.level==='cellular'?s.cellular:false;const molecularHere=s.molecular;setText('tissue-state',node.level==='tissue'?(tissueHere?`${s.tissueCount} linked item${s.tissueCount===1?'':'s'}`:'No evidence at this resolution'):(node.level==='macro'?(s.tissue?`${s.tissueCount} linked item${s.tissueCount===1?'':'s'}`:'Unavailable'):'Parent evidence only'));setText('tissue-detail',node.level==='tissue'?(tissueHere?'Tissue / WSI evidence is explicitly linked to this spatial target.':'No tissue / WSI evidence is linked to this target. The node remains navigation only.'):(s.tissue?'Tissue evidence exists on this region but is not automatically inherited by this target.':'No tissue / WSI evidence is explicitly linked to this region.'));setEvidenceStatus('tissue-status',node.level==='tissue'?(tissueHere?'LINKED':'NONE'):(s.tissue?'REGION':'NONE'));setText('cellular-state',node.level==='cellular'?(cellularHere?`${s.cellularCount} linked item${s.cellularCount===1?'':'s'}`:'No evidence at this resolution'):(s.cellular?'Linked evidence':'Unavailable'));setText('cellular-detail',node.level==='cellular'?(cellularHere?'Cellular microscopy evidence is explicitly linked to this field.':'No cellular evidence is linked to this field. The visualization is a navigation target only.'):(s.cellular?'Cellular evidence exists but is not automatically inherited by this node.':'Cellular evidence requires explicitly linked microscopy data.'));setEvidenceStatus('cellular-status',node.level==='cellular'?(cellularHere?'LINKED':'NONE'):(s.cellular?'REGION':'NONE'));setText('molecular-state',molecularHere?`${s.molecularCount} linked item${s.molecularCount===1?'':'s'}`:'Unavailable');setText('molecular-detail',molecularHere?'Molecular measurements are explicitly linked to this region.':'No molecular measurements are explicitly linked to this region.');setEvidenceStatus('molecular-status',molecularHere?'LINKED':'NONE');const evidenceAtLevel=node.level==='macro'?s.macro:node.level==='tissue'?s.tissue:node.level==='cellular'?s.cellular:false;setText('confidence-state',evidenceAtLevel?'Observed evidence':'Navigation only');setText('evidence-level',evidenceAtLevel?`Evidence linked at ${SCALE_LABELS[node.level]}`:`No evidence at ${SCALE_LABELS[node.level]}`);}
function renderMacroEvidence(region){const items=regionEvidence(region),preview=document.getElementById('macro-preview'),image=document.getElementById('macro-image'),filename=document.getElementById('macro-filename'),view=document.getElementById('macro-view');if(!items.length){preview.hidden=true;image.removeAttribute('src');return;}selectedMacroIndex=Math.min(selectedMacroIndex,items.length-1);const item=items[selectedMacroIndex];image.src=`/api/hand/evidence/${encodeURIComponent(item.asset_id)}`;image.alt=`Macro evidence · ${item.view||item.filename}`;filename.textContent=item.filename||'hand image';view.textContent=(item.view||'view').replaceAll('_',' ');preview.hidden=false;}
function renderMacroGallery(region){const items=regionEvidence(region),preview=document.getElementById('macro-preview');if(!preview)return;let nav=document.getElementById('macro-gallery');if(!items.length){if(nav)nav.remove();return;}if(!nav){nav=document.createElement('div');nav.id='macro-gallery';nav.className='macro-gallery';preview.parentElement.appendChild(nav);}nav.replaceChildren();items.forEach((item,index)=>{const button=document.createElement('button');button.type='button';button.textContent=(item.view||item.filename||`View ${index+1}`).replaceAll('_',' ');button.className=index===selectedMacroIndex?'active':'';button.onclick=()=>{selectedMacroIndex=index;renderMacroEvidence(region);renderMacroGallery(region);};nav.appendChild(button);});}
function renderMacro(region){renderMacroEvidence(region);renderMacroGallery(region);}
function selectRegion(region,focus=true){if(!regionMeshes.has(region))return;selectedRegion=region;selectedMacroIndex=0;spatialPath=[{id:'hand',label:'Hand',level:'macro',type:'root'},{id:region,label:REGION_LABELS[region]||region,level:'macro',regionId:region}];for(const[id,m]of regionMeshes)m.material=id===region?selected.clone():mat(id);setValue('form-region',region);if(focus){controls.target.set(0,region==='wrist'?-1.2:region==='palm'?-0.35:1.3,0);controls.update();}applySpatialNode();}
function updateGlobalCoverage(){const assets=availableAssets(),hand=assets.filter(x=>x.modality==='hand'),tissue=assets.filter(x=>x.modality==='wsi'),cellular=assets.filter(x=>['microscopy','cellular'].includes(String(x.modality).toLowerCase())),molecular=assets.filter(x=>x.modality==='rna');setText('coverage-macro',`Macro ${hand.length?100:0}%`);setText('coverage-micro',`Tissue ${tissue.length?100:0}%`);setText('coverage-cellular',`Cellular ${cellular.length?100:0}%`);setText('coverage-molecular',`Molecular ${molecular.length?100:0}%`);}
async function refresh(){try{const r=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`);if(!r.ok)throw Error('Evidence request failed');analysis=await r.json();updateGlobalCoverage();setText('twin-status',`${handAssets().length} macro observation${handAssets().length===1?'':'s'} loaded`);selectRegion(selectedRegion,false);}catch(error){setText('twin-status','Evidence unavailable');console.error(error);}finally{if(loading?.isConnected){loading.hidden=true;loading.setAttribute('aria-hidden','true');}window.dispatchEvent(new CustomEvent('testhp:twin-progress',{detail:{step:'evidence-ready',detail:'Evidence refresh completed'}}));}}
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();
canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect();pointer.x=(e.clientX-r.left)/r.width*2-1;pointer.y=-(e.clientY-r.top)/r.height*2+1;ray.setFromCamera(pointer,camera);const hits=ray.intersectObjects([...regionMeshes.values()],false);if(hits.length)selectRegion(hits[0].object.name);});
function reset(){camera.position.set(0,1.5,8.5);controls.target.set(0,.4,0);root.rotation.y=0;controls.update();setText('zoom-label','100%');}
document.getElementById('reset-view').onclick=reset;document.getElementById('rotate-left').onclick=()=>root.rotation.y-=Math.PI/9;document.getElementById('rotate-right').onclick=()=>root.rotation.y+=Math.PI/9;document.getElementById('zoom-in').onclick=()=>{camera.position.multiplyScalar(.86);controls.update();};document.getElementById('zoom-out').onclick=()=>{camera.position.multiplyScalar(1.16);controls.update();};document.getElementById('zoom-region').onclick=()=>{camera.position.multiplyScalar(.84);controls.update();};
document.getElementById('deep-analysis').onclick=()=>{const current=currentSpatial();const message=current.level==='cell'?`Spatial target · ${current.label}\n\nNo single-cell evidence is linked. This node is a navigation target only; the macro photograph from the parent region is intentionally not presented as cell evidence.`:`Spatial target · ${current.label}\n\nResolution: ${SCALE_LABELS[current.level]}.\n\nEvidence is shown only when explicitly linked at this resolution.`;alert(message);};
const addObservation=document.getElementById('add-observation');
if(addObservation && dialog){addObservation.onclick=()=>dialog.showModal();}
const closeDialog=document.querySelector('.close');
if(closeDialog && dialog)closeDialog.onclick=()=>dialog.close();
const registerObservation=document.getElementById('register-observation');
if(registerObservation){registerObservation.onclick=async e=>{e.preventDefault();const file=document.getElementById('observation-file')?.files?.[0];if(!file)return;const modality=document.getElementById('form-modality')?.value,endpoint={Photo:'hand',Video:'video',Microscopy:'wsi',Measurements:'metadata','Molecular data':'rna'}[modality],body=new FormData();if(!endpoint)return;body.append('file',file);body.append('subject_id',subjectId);body.append('timepoint',timepoint);body.append('view',selectedRegion);const b=e.currentTarget;b.disabled=true;b.textContent='Registering…';try{const r=await fetch(`/api/upload/${endpoint}`,{method:'POST',body}),j=await r.json();if(!r.ok)throw Error(j.detail||'Upload failed');if(dialog)dialog.close();await refresh();alert(`Observation registered for ${selectedRegion}. Biological inference is not established automatically.`);}catch(err){alert(err.message);}finally{b.disabled=false;b.textContent='Register observation';}};}
function resize(){const w=Math.max(1,viewport.clientWidth),h=Math.max(1,viewport.clientHeight);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
window.addEventListener('resize',resize);
function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);}

// Expose the canonical renderer to the Twin Viewport diagnostics. This is the
// real Three.js scene, camera, controls and mesh registry owned by this module;
// no second renderer or fake scene is created.
function publishViewportManager(){
  window.spatialViewportManager={
    version:'canonical-three-1',
    activeKey:`macro|${selectedRegion}`,
    active:{constructor:{name:'ThreeCanvasRenderer'},renderer,scene,root,camera,controls,clickable:[...regionMeshes.values()]},
    deepRenderer:renderer,
    get deep(){return renderer;},
    render(){
      const current=currentSpatial();
      this.activeKey=`${current.level}|${current.id||current.label||'spatial-target'}`;
      this.active={constructor:{name:'ThreeCanvasRenderer'},renderer,scene,root,camera,controls,clickable:[...regionMeshes.values()]};
      resize();
      renderer.render(scene,camera);
      window.dispatchEvent(new CustomEvent('testhp:viewport-rendered',{detail:{level:current.level,target:current.label,path:spatialPath.map(x=>x.label),children:childTargets(current).map(x=>x.label),renderer:'ThreeCanvasRenderer'}}));
    },
    resize,
    get state(){const current=currentSpatial();return{level:current.level,target:current.label,spatial_id:current.regionId||current.id,path:spatialPath.map(x=>x.label),children:childTargets(current).map(x=>x.label)};}
  };
  window.dispatchEvent(new CustomEvent('testhp:viewport-manager-ready',{detail:{renderer:'ThreeCanvasRenderer',sceneChildren:scene.children.length,meshCount:regionMeshes.size}}));
}

resize();
animate();
selectRegion('palm',false);
publishViewportManager();
window.dispatchEvent(new CustomEvent('testhp:twin-progress',{detail:{step:'renderer-ready',detail:'Three.js scene, camera, controls and mesh hierarchy initialized'}}));
window.__testhpTwinReady=true;
window.dispatchEvent(new CustomEvent('testhp:twin-ready',{detail:{renderer:'Three.js',sceneChildren:scene.children.length,meshCount:regionMeshes.size}}));
refresh();