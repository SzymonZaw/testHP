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
const regionMeshes=new Map();

const REGION_LABELS={wrist:'Wrist',palm:'Palm',thumb:'Thumb',index:'Index finger',middle:'Middle finger',ring:'Ring finger',little:'Little finger'};
const PALM_VIEWS=new Set(['front','back','side_left','side_right']);

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
const key=new THREE.DirectionalLight(0xffffff,2.8); key.position.set(4,6,7); scene.add(key);
const fill=new THREE.DirectionalLight(0x8bb8ff,1); fill.position.set(-5,2,-4); scene.add(fill);
const root=new THREE.Group(); root.rotation.x=-.18; scene.add(root);

const normal=new THREE.MeshStandardMaterial({color:0xc68b72,roughness:.72});
const selected=new THREE.MeshStandardMaterial({color:0x66b3ff,roughness:.58,emissive:0x0b2745,emissiveIntensity:.35});
const review=new THREE.MeshStandardMaterial({color:0xd6a64f,roughness:.68});
const unavailable=new THREE.MeshStandardMaterial({color:0x586174,roughness:.9});

function capsule(name,p,r,l,rot=[0,0,0]){
  const m=new THREE.Mesh(new THREE.CapsuleGeometry(r,l,8,16),normal.clone());
  m.name=name; m.position.set(...p); m.rotation.set(...rot); root.add(m); regionMeshes.set(name,m); return m;
}
capsule('wrist',[0,-2.15,0],.72,1.25);
capsule('palm',[0,-.35,0],1.55,2.25);
capsule('thumb',[-1.45,0,.02],.48,1.45,[0,0,-.82]);
capsule('index',[-1.05,1.95,0],.43,2.15);
capsule('middle',[-.35,2.25,0],.46,2.55);
capsule('ring',[.42,2.12,0],.45,2.32);
capsule('little',[1.12,1.86,0],.40,1.95,[0,0,.08]);

function availableAssets(){return (analysis?.assets||[]).filter(x=>x.status==='available');}
function handAssets(){return availableAssets().filter(x=>x.modality==='hand');}
function assetView(asset){return String(asset.view||'unknown').toLowerCase();}
function regionEvidence(region){
  const assets=handAssets();
  if(region==='palm') return assets.filter(x=>PALM_VIEWS.has(assetView(x)));
  if(region==='thumb') return assets.filter(x=>assetView(x)==='thumb' || x.zone_id==='thumb');
  return assets.filter(x=>x.zone_id===region);
}
function tissueEvidence(region){
  return availableAssets().filter(x=>x.modality==='wsi' && x.region_id===region && x.subject_id===subjectId && x.timepoint===timepoint);
}
function molecularEvidence(region){
  return availableAssets().filter(x=>x.modality==='rna' && x.region_id===region && x.subject_id===subjectId && x.timepoint===timepoint);
}
function cellularEvidence(region){
  return availableAssets().filter(x=>['microscopy','cellular'].includes(String(x.modality).toLowerCase()) && x.region_id===region && x.subject_id===subjectId && x.timepoint===timepoint);
}
function status(region){
  const macro=regionEvidence(region), tissue=tissueEvidence(region), cellular=cellularEvidence(region), molecular=molecularEvidence(region);
  return {macro:macro.length>0,macroCount:macro.length,tissue:tissue.length>0,tissueCount:tissue.length,cellular:cellular.length>0,cellularCount:cellular.length,molecular:molecular.length>0,molecularCount:molecular.length};
}
function mat(region){
  const s=status(region);
  if(!s.macro&&!s.tissue&&!s.cellular&&!s.molecular) return unavailable.clone();
  if(!s.macro||s.tissue||s.cellular||s.molecular) return review.clone();
  return normal.clone();
}
function setEvidenceStatus(id,label){const el=document.getElementById(id);if(el)el.textContent=label;}
function setText(id,value){const el=document.getElementById(id);if(el)el.textContent=value;}
function renderMacroEvidence(region){
  const items=regionEvidence(region);
  const preview=document.getElementById('macro-preview');
  const image=document.getElementById('macro-image');
  const filename=document.getElementById('macro-filename');
  const view=document.getElementById('macro-view');
  if(!items.length){preview.hidden=true;image.removeAttribute('src');return;}
  selectedMacroIndex=Math.min(selectedMacroIndex,items.length-1);
  const item=items[selectedMacroIndex];
  image.src=`/api/hand/evidence/${encodeURIComponent(item.asset_id)}`;
  image.alt=`Macro evidence · ${item.view||item.filename}`;
  filename.textContent=item.filename||'hand image';
  view.textContent=(item.view||'view').replaceAll('_',' ');
  preview.hidden=false;
}
function renderMacroGallery(region){
  const items=regionEvidence(region);
  const preview=document.getElementById('macro-preview');
  if(!preview)return;
  let nav=document.getElementById('macro-gallery');
  if(!items.length){if(nav)nav.remove();return;}
  if(!nav){nav=document.createElement('div');nav.id='macro-gallery';nav.className='macro-gallery';preview.parentElement.appendChild(nav);}
  nav.replaceChildren();
  items.forEach((item,index)=>{
    const button=document.createElement('button'); button.type='button'; button.textContent=(item.view||item.filename||`View ${index+1}`).replaceAll('_',' '); button.className=index===selectedMacroIndex?'active':'';
    button.onclick=()=>{selectedMacroIndex=index;renderMacroEvidence(region);renderMacroGallery(region);}; nav.appendChild(button);
  });
}
function renderMacro(region){renderMacroEvidence(region);renderMacroGallery(region);}
function selectRegion(region,focus=true){
  if(!regionMeshes.has(region))return;
  selectedRegion=region; selectedMacroIndex=0;
  for(const[id,m]of regionMeshes)m.material=id===region?selected.clone():mat(id);
  setText('zone-label',region); setText('region-title',REGION_LABELS[region]||region); setText('form-region',region);
  const s=status(region);
  setText('macro-state',s.macro?`${s.macroCount} view${s.macroCount===1?'':'s'} available`:'No evidence');
  setText('macro-detail',s.macro?'Registered hand images are available for this region. Use the view selector to inspect each one.':'No explicitly region-relevant hand image is currently available.');
  setEvidenceStatus('macro-status',s.macro?'OBSERVED':'NONE'); renderMacro(region);
  setText('tissue-state',s.tissue?`${s.tissueCount} linked item${s.tissueCount===1?'':'s'}`:'Unavailable');
  setText('tissue-detail',s.tissue?'Tissue-level evidence is explicitly linked to this region.':'No tissue / WSI evidence is explicitly linked to this region.');
  setEvidenceStatus('tissue-status',s.tissue?'LINKED':'NONE');
  setText('cellular-state',s.cellular?`${s.cellularCount} linked item${s.cellularCount===1?'':'s'}`:'Unavailable');
  setText('cellular-detail',s.cellular?'Cellular evidence is explicitly linked to this region.':'Cellular conclusions require microscopy / cellular data explicitly linked to this region.');
  setEvidenceStatus('cellular-status',s.cellular?'LINKED':'NONE');
  setText('molecular-state',s.molecular?`${s.molecularCount} linked item${s.molecularCount===1?'':'s'}`:'Unavailable');
  setText('molecular-detail',s.molecular?'Molecular measurements are explicitly linked to this region.':'No molecular measurements are explicitly linked to this region.');
  setEvidenceStatus('molecular-status',s.molecular?'LINKED':'NONE');
  const availableLayers=[s.macro,s.tissue,s.cellular,s.molecular].filter(Boolean).length;
  setText('confidence-state',availableLayers?'Observed evidence':'No evidence');
  setText('evidence-level',availableLayers?`${availableLayers}/4 evidence layers available`:'Availability only');
  if(focus){controls.target.set(0,region==='wrist'?-1.2:region==='palm'?-0.35:1.3,0);controls.update();}
}
function updateGlobalCoverage(){
  const assets=availableAssets();
  const hand=assets.filter(x=>x.modality==='hand');
  const tissue=assets.filter(x=>x.modality==='wsi');
  const cellular=assets.filter(x=>['microscopy','cellular'].includes(String(x.modality).toLowerCase()));
  const molecular=assets.filter(x=>x.modality==='rna');
  setText('coverage-macro',`Macro ${hand.length?100:0}%`);
  setText('coverage-micro',`Tissue ${tissue.length?100:0}%`);
  setText('coverage-cellular',`Cellular ${cellular.length?100:0}%`);
  setText('coverage-molecular',`Molecular ${molecular.length?100:0}%`);
}
async function refresh(){
  try{
    const r=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`);
    if(!r.ok)throw Error('Evidence request failed');
    analysis=await r.json(); updateGlobalCoverage();
    setText('twin-status',`${handAssets().length} macro observation${handAssets().length===1?'':'s'} loaded`);
    selectRegion(selectedRegion,false);
  }catch(error){setText('twin-status','Evidence unavailable');console.error(error);}
  finally{loading.remove();}
}
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();
canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect();pointer.x=(e.clientX-r.left)/r.width*2-1;pointer.y=-(e.clientY-r.top)/r.height*2+1;ray.setFromCamera(pointer,camera);const hits=ray.intersectObjects([...regionMeshes.values()],false);if(hits.length)selectRegion(hits[0].object.name)});
function reset(){camera.position.set(0,1.5,8.5);controls.target.set(0,.4,0);root.rotation.y=0;controls.update();setText('zoom-label','100%');}
document.getElementById('reset-view').onclick=reset;
document.getElementById('rotate-left').onclick=()=>root.rotation.y-=Math.PI/9;
document.getElementById('rotate-right').onclick=()=>root.rotation.y+=Math.PI/9;
document.getElementById('zoom-in').onclick=()=>{camera.position.multiplyScalar(.86);controls.update();};
document.getElementById('zoom-out').onclick=()=>{camera.position.multiplyScalar(1.16);controls.update();};
document.getElementById('zoom-region').onclick=()=>{camera.position.multiplyScalar(.84);controls.update();};
document.getElementById('deep-analysis').onclick=()=>{
  const s=status(selectedRegion);
  const layers=[s.macro&&'Macro',s.tissue&&'Tissue',s.cellular&&'Cellular',s.molecular&&'Molecular'].filter(Boolean);
  const message=layers.length?`Deep analysis · ${REGION_LABELS[selectedRegion]||selectedRegion}\n\nAvailable evidence layers: ${layers.join(', ')}.\n\nNo biological inference is generated automatically. Evidence must remain explicitly linked to this region.`:`Deep analysis · ${REGION_LABELS[selectedRegion]||selectedRegion}\n\nNo linked evidence is currently available. The system will not invent tissue, cellular or molecular findings.`;
  alert(message);
};
document.getElementById('add-observation').onclick=()=>dialog.showModal();
document.querySelector('.close').onclick=()=>dialog.close();
document.getElementById('register-observation').onclick=async e=>{
  e.preventDefault(); const file=document.getElementById('observation-file').files[0]; if(!file)return;
  const modality=document.getElementById('form-modality').value;
  const endpoint={Photo:'hand',Video:'video',Microscopy:'wsi',Measurements:'metadata','Molecular data':'rna'}[modality];
  const body=new FormData(); body.append('file',file); body.append('subject_id',subjectId); body.append('timepoint',timepoint); body.append('view',selectedRegion);
  const b=e.currentTarget; b.disabled=true; b.textContent='Registering…';
  try{const r=await fetch(`/api/upload/${endpoint}`,{method:'POST',body}),j=await r.json();if(!r.ok)throw Error(j.detail||'Upload failed');dialog.close();await refresh();alert(`Observation registered for ${selectedRegion}. Biological inference is not established automatically.`);}
  catch(err){alert(err.message);}
  finally{b.disabled=false;b.textContent='Register observation';}
};
function resize(){const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
window.addEventListener('resize',resize);
function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);}
resize(); animate(); selectRegion('palm',false); refresh();
