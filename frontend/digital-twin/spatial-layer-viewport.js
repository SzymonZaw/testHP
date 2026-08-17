import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport = document.getElementById('twin-viewport');
const canvas = document.getElementById('twin-canvas');
if (!viewport || !canvas) throw new Error('Digital Twin viewport not found');

const style = document.createElement('style');
style.textContent = `
#spatial-layer-scene{position:absolute;inset:0;z-index:12;display:none;background:#0b1116;overflow:hidden;border-radius:inherit}
#spatial-layer-scene.active{display:block}
#spatial-layer-scene .layer-title{position:absolute;top:24px;left:26px;z-index:3;text-transform:uppercase;letter-spacing:.14em;font-size:10px;color:#9bb5ae;font-weight:800}
#spatial-layer-scene .layer-subtitle{position:absolute;top:43px;left:26px;z-index:3;font-size:22px;font-weight:750;color:#e8f0f2}
#spatial-layer-scene .layer-note{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);z-index:3;color:#82949e;font-size:9px;text-align:center;white-space:nowrap}
#spatial-layer-scene .layer-target{position:absolute;z-index:4;border:1px solid #78bca8aa;background:#13251fcc;color:#e8f0f2;border-radius:12px;padding:12px 16px;cursor:pointer;box-shadow:0 10px 30px #0005}
#spatial-layer-scene .layer-target:hover{border-color:#a4d6c2;background:#1a382fcc;transform:translateY(-2px)}
#spatial-layer-scene .tissue-sheet{position:absolute;left:13%;right:13%;top:18%;bottom:15%;border:2px solid #78bca888;border-radius:42% 48% 46% 44%;background:linear-gradient(135deg,#426d6140,#102822b0);box-shadow:inset 0 0 70px #0008,0 0 60px #4caa8b18}
#spatial-layer-scene .tissue-sheet:after{content:'TISSUE SECTION';position:absolute;top:18px;left:22px;color:#9bb5ae;font-size:9px;letter-spacing:.14em;font-weight:800}
#spatial-layer-scene .cell-field{position:absolute;left:9%;right:9%;top:18%;bottom:15%;display:grid;grid-template-columns:repeat(8,1fr);grid-template-rows:repeat(5,1fr);gap:9px;padding:22px;border:1px solid #6da69544;background:#0e1b1e;box-shadow:inset 0 0 80px #0008}
#spatial-layer-scene .cell-field span{border:1px solid #6da69535;border-radius:50%;background:radial-gradient(circle,#78bca833 0 16%,transparent 17% 100%)}
#spatial-layer-scene .cell-field:after{content:'MICROSCOPY FIELD';position:absolute;top:10px;left:14px;color:#9bb5ae;font-size:9px;letter-spacing:.14em;font-weight:800}
#spatial-layer-scene .single-cell{position:absolute;left:50%;top:51%;width:180px;height:180px;transform:translate(-50%,-50%);border-radius:48% 52% 45% 55%;border:3px solid #78bca8;background:radial-gradient(circle at 35% 30%,#a4d6c244,#4d8f7b55 40%,#19382f 75%);box-shadow:0 0 55px #5fb19433}
#spatial-layer-scene .single-cell:before{content:'';position:absolute;left:50%;top:50%;width:68px;height:68px;transform:translate(-50%,-50%);border-radius:50%;border:2px solid #a0d8c288;background:radial-gradient(circle,#8bc7b055,#315e5144 65%,#152a25)}
#spatial-layer-scene .single-cell:after{content:'CELL TARGET';position:absolute;left:50%;bottom:-45px;transform:translateX(-50%);white-space:nowrap;color:#9bb5ae;font-size:9px;letter-spacing:.14em;font-weight:800}
`;
document.head.appendChild(style);

const layer = document.createElement('div');
layer.id = 'spatial-layer-scene';
viewport.appendChild(layer);

let lastKey = '';
let scene = null;
let renderer = null;
let camera = null;
let animationId = 0;

function currentSpatialFromDom(){
  const badge = (document.getElementById('spatial-level-badge')?.textContent || '').toLowerCase();
  const node = document.getElementById('spatial-node');
  const title = node?.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  if (badge.includes('single')) return {level:'cell', title};
  if (badge.includes('cellular')) return {level:'cellular', title};
  if (badge.includes('tissue')) return {level:'tissue', title};
  return {level:'macro', title};
}

function triggerTarget(label){
  const buttons = [...document.querySelectorAll('#spatial-children .spatial-target')];
  const button = buttons.find(b => b.querySelector('strong')?.textContent?.trim() === label);
  if (button) button.click();
}

function makeRenderer(){
  const r = new THREE.WebGLRenderer({antialias:true,alpha:true});
  r.setPixelRatio(Math.min(window.devicePixelRatio || 1,2));
  r.outputColorSpace = THREE.SRGBColorSpace;
  layer.appendChild(r.domElement);
  return r;
}

function clearThree(){
  if (animationId) cancelAnimationFrame(animationId);
  if (renderer) renderer.dispose();
  layer.replaceChildren();
  scene = null; renderer = null; camera = null;
}

function addLabel(text, sub){
  const a=document.createElement('div'); a.className='layer-title'; a.textContent=text; layer.appendChild(a);
  const b=document.createElement('div'); b.className='layer-subtitle'; b.textContent=sub; layer.appendChild(b);
  const n=document.createElement('div'); n.className='layer-note'; n.textContent='Spatial visualization only · no biological evidence is implied'; layer.appendChild(n);
}

function addTarget(label, x, y){
  const b=document.createElement('button'); b.className='layer-target'; b.textContent=label; b.style.left=x; b.style.top=y; b.onclick=()=>triggerTarget(label); layer.appendChild(b);
}

function renderScene(state){
  clearThree();
  if(state.level==='macro'){
    layer.classList.remove('active');
    canvas.style.visibility='visible';
    document.querySelector('.viewer-hint')?.style.removeProperty('visibility');
    document.querySelector('.viewer-controls')?.style.removeProperty('visibility');
    return;
  }
  layer.classList.add('active');
  canvas.style.visibility='hidden';
  document.querySelector('.viewer-hint')?.style.setProperty('visibility','hidden');
  document.querySelector('.viewer-controls')?.style.setProperty('visibility','hidden');
  addLabel(state.level==='tissue'?'TISSUE RESOLUTION':state.level==='cellular'?'CELLULAR RESOLUTION':'CELL RESOLUTION',state.title);

  if(state.level==='tissue'){
    const sheet=document.createElement('div'); sheet.className='tissue-sheet'; layer.appendChild(sheet);
    const buttons=[...document.querySelectorAll('#spatial-children .spatial-target')];
    const positions=[['14%','42%'],['42%','25%'],['69%','47%']];
    buttons.forEach((b,i)=>{const t=b.querySelector('strong')?.textContent?.trim();if(t){addTarget(t,positions[i%3][0],positions[i%3][1]);}});
  } else if(state.level==='cellular'){
    const field=document.createElement('div'); field.className='cell-field';
    for(let i=0;i<40;i++) field.appendChild(document.createElement('span'));
    layer.appendChild(field);
    const buttons=[...document.querySelectorAll('#spatial-children .spatial-target')];
    const positions=[['12%','31%'],['43%','49%'],['70%','27%']];
    buttons.forEach((b,i)=>{const t=b.querySelector('strong')?.textContent?.trim();if(t){addTarget(t,positions[i%3][0],positions[i%3][1]);}});
  } else {
    const cell=document.createElement('div'); cell.className='single-cell'; layer.appendChild(cell);
  }
}

function sync(){
  const state=currentSpatialFromDom();
  const key=`${state.level}:${state.title}`;
  if(key!==lastKey){lastKey=key;renderScene(state);}
}

const observer=new MutationObserver(sync);
observer.observe(document.getElementById('spatial-level-badge'),{childList:true,subtree:true,characterData:true});
observer.observe(document.getElementById('spatial-node'),{childList:true,subtree:true,characterData:true});
observer.observe(document.getElementById('spatial-children'),{childList:true,subtree:true,characterData:true});
observer.observe(document.getElementById('spatial-breadcrumb'),{childList:true,subtree:true});
window.addEventListener('resize',sync);
sync();
