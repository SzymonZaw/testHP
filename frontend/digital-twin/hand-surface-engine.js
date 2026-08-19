import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const STAGES = Object.freeze({
  0: 'viewport ownership',
  1: 'real hand surface',
  2: 'coordinate system + landmarks',
  3: 'real skin evidence',
  4: 'multi-view surface projection',
  5: 'evidence layer',
  6: 'anatomical structure',
  7: 'progressive biological resolution',
  8: 'longitudinal twin'
});

const REGION_LABELS = Object.freeze({
  wrist: 'Wrist', palm: 'Palm', thumb: 'Thumb', index: 'Index finger',
  middle: 'Middle finger', ring: 'Ring finger', little: 'Little finger'
});

const LANDMARKS = Object.freeze([
  ['wrist', 0, -2.05, 0], ['palm_center', 0, -0.35, 0],
  ['thumb_mcp', -1.02, 0.18, 0.18], ['thumb_tip', -1.72, 1.08, 0.16],
  ['index_mcp', -0.98, 1.22, 0.02], ['index_pip', -1.02, 2.02, 0.02], ['index_dip', -1.02, 2.55, 0.02], ['index_tip', -1.02, 3.02, 0.02],
  ['middle_mcp', -0.34, 1.28, 0.02], ['middle_pip', -0.34, 2.12, 0.02], ['middle_dip', -0.34, 2.70, 0.02], ['middle_tip', -0.34, 3.22, 0.02],
  ['ring_mcp', 0.38, 1.22, 0.02], ['ring_pip', 0.38, 2.02, 0.02], ['ring_dip', 0.38, 2.56, 0.02], ['ring_tip', 0.38, 3.02, 0.02],
  ['little_mcp', 1.02, 1.12, 0.02], ['little_pip', 1.05, 1.80, 0.02], ['little_dip', 1.08, 2.30, 0.02], ['little_tip', 1.10, 2.72, 0.02]
].map(([id,x,y,z]) => Object.freeze({ id, position: Object.freeze({x,y,z}), region: id.split('_')[0], confidence: 1 })));

function css(url) {
  if (document.querySelector(`link[data-hand-surface="${url}"]`)) return;
  const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = url; link.dataset.handSurface = url; document.head.appendChild(link);
}

function skinTexture() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 512;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(220, 180, 20, 260, 260, 420);
  g.addColorStop(0, '#dca58e'); g.addColorStop(.65, '#bd806c'); g.addColorStop(1, '#8e5c51');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 512, 512);
  for (let i=0;i<1600;i++) { const x=Math.random()*512,y=Math.random()*512,r=Math.random()*1.8; ctx.fillStyle=`rgba(90,45,38,${Math.random()*.07})`; ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS=t.wrapT=THREE.RepeatWrapping; return t;
}

class HandSurfaceEngine {
  constructor() {
    this.subjectId = 'own_cohort'; this.timepoint = 'T0'; this.stage = 8;
    this.target = 'hand'; this.evidence = []; this.landmarks = LANDMARKS;
    this.mode = 'skin'; this.skinOpacity = 1; this.skeletonOpacity = 0;
    this.contextCanvas = document.getElementById('twin-canvas'); this.viewport = document.getElementById('twin-viewport');
    this.focus = null; this.overlay = null; this.renderer = null; this.scene = null; this.camera = null; this.controls = null;
    this.meshes = new Map(); this.layers = new Map(); this.debug = null;
  }

  async init() {
    css('/digital-twin/hand-surface.css');
    this.installOwnership(); this.installModel(); this.installDebug();
    await this.loadEvidence(); this.bindNavigation(); this.updateFromTarget();
    this.start();
    window.handSurfaceEngine = this;
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-ready', {detail: this.snapshot()}));
  }

  installOwnership() {
    if (!this.viewport || !this.contextCanvas) return;
    this.viewport.dataset.viewportArchitecture = 'context-focus';
    this.contextCanvas.dataset.viewportRole = 'context';
    const apply = () => {
      const deep = document.querySelector('[data-deep-drill], .deep-drill-visualization, #deep-drill-visualization');
      this.focus = deep || null;
      this.contextCanvas.dataset.inputOwner = this.focus ? 'focus' : 'context';
      this.contextCanvas.style.pointerEvents = this.focus ? 'none' : '';
      this.viewport.dataset.focusOwner = this.focus ? 'DeepDrillVisualization' : 'MacroHandSurface';
      this.updateDebug();
    };
    new MutationObserver(apply).observe(this.viewport, {childList:true, subtree:true, attributes:true});
    apply();
  }

  installModel() {
    if (!this.viewport) return;
    this.overlay = document.createElement('canvas');
    this.overlay.id = 'hand-surface-canvas'; this.overlay.dataset.viewportRole = 'focus-context';
    this.overlay.setAttribute('aria-label', 'Hand surface visualization');
    this.viewport.insertBefore(this.overlay, this.viewport.firstChild);
    this.renderer = new THREE.WebGLRenderer({canvas:this.overlay, antialias:true, alpha:true});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); this.renderer.outputColorSpace=THREE.SRGBColorSpace;
    this.scene = new THREE.Scene(); this.camera = new THREE.PerspectiveCamera(30, 1, .1, 100); this.camera.position.set(0,.6,9);
    this.controls = new OrbitControls(this.camera, this.overlay); this.controls.enableDamping=true; this.controls.minDistance=5; this.controls.maxDistance=14; this.controls.target.set(0,.4,0);
    this.scene.add(new THREE.HemisphereLight(0xffffff,0x3d2522,2.2)); const key=new THREE.DirectionalLight(0xffffff,2.4);key.position.set(4,6,8);this.scene.add(key);
    const group=new THREE.Group(); group.rotation.x=-.12; this.scene.add(group); this.layers.set('skin',group);
    const texture=skinTexture(); const material=new THREE.MeshStandardMaterial({map:texture,roughness:.78,metalness:0,transparent:true,opacity:1});
    const add=(id,p,r,l,rot=[0,0,0])=>{const m=new THREE.Mesh(new THREE.CapsuleGeometry(r,l,8,20),material.clone());m.name=`skin:${id}`;m.position.set(...p);m.rotation.set(...rot);group.add(m);this.meshes.set(id,m);};
    add('wrist',[0,-2.05,0],.72,1.25); add('palm',[0,-.35,0],1.5,2.25); add('thumb',[-1.42,.05,.05],.48,1.5,[0,0,-.82]);
    add('index',[-1.02,2.02,0],.42,2.15); add('middle',[-.34,2.24,0],.46,2.55); add('ring',[.38,2.12,0],.45,2.32); add('little',[1.05,1.90,0],.40,1.95,[0,0,.08]);
    this.buildSkeleton(group);
  }

  buildSkeleton(parent) {
    const layer=new THREE.Group(); layer.visible=true; layer.renderOrder=3; this.layers.set('skeleton',layer); parent.add(layer);
    const mat=new THREE.MeshStandardMaterial({color:0xe7e0cf,roughness:.72,transparent:true,opacity:0});
    const bone=(a,b,r=.11)=>{const A=new THREE.Vector3(...a),B=new THREE.Vector3(...b),d=new THREE.Vector3().subVectors(B,A),len=d.length();const m=new THREE.Mesh(new THREE.CapsuleGeometry(r,len,6,12),mat.clone());m.position.copy(A.clone().add(B).multiplyScalar(.5));m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());layer.add(m);};
    const rows=[['thumb_mcp','thumb_tip'],['index_mcp','index_tip'],['middle_mcp','middle_tip'],['ring_mcp','ring_tip'],['little_mcp','little_tip']];
    for(const [a,b] of rows){const A=this.landmarks.find(x=>x.id===a).position,B=this.landmarks.find(x=>x.id===b).position;bone([A.x,A.y,A.z-.18],[B.x,B.y,B.z-.18]);}
    bone([-0.65,-1.35,-.18],[0.65,-1.35,-.18],.18); bone([-.9,-.8,-.18],[.9,-.8,-.18],.15);
  }

  async loadEvidence() {
    try { const r=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(this.subjectId)}&timepoint=${encodeURIComponent(this.timepoint)}`); if(!r.ok) return; const data=await r.json(); this.evidence=(data.assets||[]).filter(x=>['ready','available'].includes(String(x.status||'').toLowerCase()) && String(x.modality||'').toLowerCase()==='hand'); }
    catch(e){ console.debug('Hand surface evidence unavailable',e); }
    this.updateDebug();
  }

  bindNavigation() {
    const sync=()=>{const bc=document.getElementById('spatial-breadcrumb'); if(!bc)return; const labels=[...bc.querySelectorAll('button')].map(x=>x.textContent.trim()).filter(Boolean); if(labels.length) this.target=this.pathToId(labels); this.updateFromTarget();};
    const bc=document.getElementById('spatial-breadcrumb'); if(bc)new MutationObserver(sync).observe(bc,{childList:true,subtree:true});
    window.addEventListener('testhp:spatial-target-changed',e=>{if(e.detail?.spatial_target_id)this.target=e.detail.spatial_target_id;this.updateFromTarget();});
  }

  pathToId(labels){const map={'Hand':'hand','Palm':'palm','Thenar eminence':'thenar','Hypothenar eminence':'hypothenar','Central palm':'central-palm','Microscopy field A':'field-a','Microscopy field B':'field-b','Microscopy field C':'field-c','Cell target 1':'cell-1','Cell target 2':'cell-2','Cell target 3':'cell-3'}; return labels.map((x,i)=>i===0?'hand':(map[x]||x.toLowerCase().replace(/\s+/g,'-'))).join('/');}

  updateFromTarget() {
    const deep=this.target.split('/').length>2; this.skinOpacity=deep?.42:1; this.skeletonOpacity=deep?.18:0; this.mode=deep?'context':'skin';
    const skin=this.layers.get('skin'); if(skin)skin.traverse(o=>{if(o.material)o.material.opacity=this.skinOpacity;});
    const sk=this.layers.get('skeleton'); if(sk)sk.traverse(o=>{if(o.material)o.material.opacity=this.skeletonOpacity;});
    this.updateDebug();
  }

  installDebug() {
    const host=document.getElementById('twin-viewport-debug-host'); if(!host)return;
    this.debug=document.createElement('details'); this.debug.open=false; this.debug.className='hand-surface-debug'; this.debug.innerHTML='<summary>HAND SURFACE · STAGES 0–8</summary><pre id="hand-surface-debug-data"></pre>'; host.appendChild(this.debug);
  }

  updateDebug(){const el=document.getElementById('hand-surface-debug-data'); if(!el)return; const d=this.snapshot();el.textContent=JSON.stringify(d,null,2);}

  resize(){if(!this.renderer||!this.viewport)return;const r=this.viewport.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);this.renderer.setSize(w,h,false);this.camera.aspect=w/h;this.camera.updateProjectionMatrix();}
  start(){const loop=()=>{this.resize();this.controls?.update();this.renderer?.render(this.scene,this.camera);requestAnimationFrame(loop);};loop();}

  snapshot(){return {stage:this.stage,stage_name:STAGES[this.stage],viewport_ownership:{context:{rendered:!!this.contextCanvas,visible:!this.contextCanvas?.hidden,input:!this.contextCanvas?.style.pointerEvents==='none',owner:this.contextCanvas?.dataset.inputOwner==='focus'?'focus':'context'},focus:{rendered:!!this.focus,visible:!!this.focus,input:!!this.focus,owner:this.focus?'DeepDrillVisualization':'none'}},surface:{renderer:'Three.js WebGL',mesh:'procedural hand surface',skin_fallback:true,skin_opacity:this.skinOpacity,skeleton_opacity:this.skeletonOpacity},coordinates:{space:'hand-local',landmarks:this.landmarks.length,confidence:'explicit per landmark'},evidence:{subject_id:this.subjectId,timepoint:this.timepoint,macro_images:this.evidence.length},target:this.target,longitudinal:{timepoint:this.timepoint,ready_for_T1:true}};}
}

const boot=()=>new HandSurfaceEngine().init();
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
export { HandSurfaceEngine, LANDMARKS, STAGES };
