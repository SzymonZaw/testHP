import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport=document.getElementById('twin-viewport');
const baseCanvas=document.getElementById('twin-canvas');
const controls=document.querySelector('.viewer-controls');
const hint=document.querySelector('.viewer-hint');
const loading=document.getElementById('viewer-loading');
const badge=document.getElementById('spatial-level-badge');
const node=document.getElementById('spatial-node');
const children=document.getElementById('spatial-children');
if(!viewport||!badge||!node||!children){
  console.warn('Spatial layer viewport: required Digital Twin elements are missing.');
} else {
const layerCanvas=document.createElement('canvas');
layerCanvas.id='spatial-layer-canvas';
Object.assign(layerCanvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',zIndex:'3',display:'none',cursor:'grab'});
viewport.appendChild(layerCanvas);
const labels=document.createElement('div');
Object.assign(labels.style,{position:'absolute',inset:'0',zIndex:'4',pointerEvents:'none',display:'none'});
viewport.appendChild(labels);

const renderer=new THREE.WebGLRenderer({canvas:layerCanvas,antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x0b1518);
const camera=new THREE.PerspectiveCamera(35,1,.1,100);camera.position.set(0,0,8);
scene.add(new THREE.HemisphereLight(0xffffff,0x10201d,2.2));
const keyLight=new THREE.DirectionalLight(0xffffff,2.4);keyLight.position.set(4,5,7);scene.add(keyLight);
const root=new THREE.Group();scene.add(root);
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let clickable=[];let last='';
const COLORS={tissue:0x4f8f7d,cellular:0x5fae98,cell:0x8bc7b0,accent:0x9bd8c4,grid:0x4f9b86};

function level(){const b=String(badge.textContent||'').trim().toUpperCase();if(b.includes('SINGLE'))return'cell';if(b.includes('CELLULAR'))return'cellular';if(b.includes('TISSUE'))return'tissue';return'macro'}
function title(){return node.querySelector('strong')?.textContent?.trim()||'Spatial target'}
function path(){return [...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean)}
function targetElements(){return [...children.querySelectorAll('.spatial-target')].filter(x=>x.querySelector('strong'))}
function targetText(el){return el.querySelector('strong').textContent.trim()}
function clear(){while(root.children.length){const o=root.children.pop();o.traverse?.(c=>{c.geometry?.dispose?.();if(c.material)c.material.dispose?.()})}clickable=[];labels.replaceChildren()}
function addLabel(text,x,y,target){const b=document.createElement('button');b.type='button';b.textContent=text;Object.assign(b.style,{position:'absolute',left:`${x}%`,top:`${y}%`,transform:'translate(-50%,-50%)',pointerEvents:'auto',padding:'10px 13px',borderRadius:'12px',border:'1px solid #78bca866',background:'#12221fe6',color:'#dcece6',font:'700 12px system-ui,sans-serif',cursor:'pointer',backdropFilter:'blur(6px)'});b.onclick=()=>target.click();labels.appendChild(b)}
function mesh(geometry,position,target,color){const m=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.62,metalness:.05,emissive:0x071c17,emissiveIntensity:.22}));m.position.set(...position);m.userData.target=target;root.add(m);clickable.push(m);return m}
function renderTissue(){const plate=new THREE.Mesh(new THREE.BoxGeometry(6.5,3.8,.32),new THREE.MeshStandardMaterial({color:0x18322d,roughness:.85}));plate.position.z=-.35;root.add(plate);const pos=[[-2.05,.45,.25],[0,-.25,.45],[2.05,.5,.25]];targetElements().forEach((t,i)=>{mesh(new THREE.BoxGeometry(1.55,1.25,.38),pos[i%3],t,COLORS.tissue);addLabel(targetText(t),24+i*26,58-(i%2)*18,t)})}
function renderCellular(){const plate=new THREE.Mesh(new THREE.BoxGeometry(7,4.2,.18),new THREE.MeshStandardMaterial({color:0x101f20,roughness:.9}));plate.position.z=-.45;root.add(plate);for(let x=-3;x<=3;x++)for(let y=-2;y<=2;y++){const c=new THREE.Mesh(new THREE.CircleGeometry(.13,20),new THREE.MeshBasicMaterial({color:COLORS.grid,transparent:true,opacity:.5}));c.position.set(x+(y%2)*.35,y*.7,-.1);root.add(c)}const pos=[[-2,.75,.2],[0,-.55,.3],[2,.8,.2]];targetElements().forEach((t,i)=>{const m=mesh(new THREE.SphereGeometry(.62,32,20),pos[i%3],t,COLORS.cellular);m.scale.set(1,.72,.35);addLabel(targetText(t),25+i*25,54-(i%2)*17,t)})}
function renderCell(){const t=targetElements()[0];const outer=new THREE.Mesh(new THREE.SphereGeometry(1.45,48,32),new THREE.MeshStandardMaterial({color:COLORS.cell,roughness:.55,transparent:true,opacity:.82,emissive:0x0b3026,emissiveIntensity:.35}));outer.position.z=.1;if(t){outer.userData.target=t;clickable.push(outer)}root.add(outer);const nucleus=new THREE.Mesh(new THREE.SphereGeometry(.55,40,24),new THREE.MeshStandardMaterial({color:0x315e51,roughness:.45,emissive:0x183b31,emissiveIntensity:.45}));nucleus.position.set(-.2,.1,1.05);root.add(nucleus);const ring=new THREE.Mesh(new THREE.TorusGeometry(2,.025,8,96),new THREE.MeshBasicMaterial({color:COLORS.accent,transparent:true,opacity:.55}));root.add(ring);if(t)addLabel(targetText(t),50,82,t)}
function syncBoundary(deep){const inspector=document.querySelector('.inspector');const statePanel=document.querySelector('.state-panel');[inspector,statePanel].forEach(e=>{if(e)e.style.setProperty('display',deep?'none':'','important')});document.body.classList.toggle('spatial-deep',deep)}
function render(){const l=level(),t=title(),p=path(),k=`${l}:${t}:${p.join('/')}`,deep=l!=='macro';syncBoundary(deep);layerCanvas.style.display=deep?'block':'none';labels.style.display=deep?'block':'none';if(baseCanvas)baseCanvas.style.visibility=deep?'hidden':'visible';if(controls)controls.style.visibility=deep?'hidden':'visible';if(hint)hint.style.visibility=deep?'hidden':'visible';if(loading)loading.style.visibility=deep?'hidden':'visible';if(!deep||k===last){if(deep)resize();return}last=k;clear();camera.position.set(0,0,8);camera.lookAt(0,0,0);if(l==='tissue')renderTissue();else if(l==='cellular')renderCellular();else renderCell();resize()}
function resize(){const r=viewport.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
function animate(){requestAnimationFrame(animate);if(layerCanvas.style.display!=='none'){root.rotation.y+=.0025;renderer.render(scene,camera)}}
layerCanvas.addEventListener('pointerdown',e=>{const r=layerCanvas.getBoundingClientRect();pointer.x=((e.clientX-r.left)/r.width)*2-1;pointer.y=-((e.clientY-r.top)/r.height)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(clickable,false)[0];if(hit?.object?.userData?.target)hit.object.userData.target.click()});

const layerSwitcher=document.createElement('div');
layerSwitcher.id='spatial-layer-switcher';
Object.assign(layerSwitcher.style,{display:'flex',flexWrap:'wrap',gap:'6px',alignItems:'center',margin:'10px 0 12px'});
const layerNames={macro:'Macro anatomy',tissue:'Tissue field',cellular:'Cellular field',cell:'Single cell'};
const layerOrder=['macro','tissue','cellular','cell'];
function renderLayerSwitcher(){
  layerSwitcher.replaceChildren();
  const label=document.createElement('span');label.textContent='VISUALIZATION LAYER';
  Object.assign(label.style,{font:'700 10px system-ui,sans-serif',letterSpacing:'.12em',opacity:'.65',marginRight:'4px'});layerSwitcher.appendChild(label);
  const buttons=[...document.querySelectorAll('#spatial-breadcrumb button')];
  const current=level();
  const currentIndex=layerOrder.indexOf(current);
  layerOrder.forEach((layer)=>{
    const b=document.createElement('button');b.type='button';b.textContent=layerNames[layer];
    Object.assign(b.style,{padding:'7px 10px',borderRadius:'9px',border:'1px solid #36544e',background:layer===current?'#23463e':'#101b1a',color:'#dcece6',font:'600 11px system-ui,sans-serif',cursor:'pointer'});
    const idx=layerOrder.indexOf(layer);
    const available=idx<=currentIndex && buttons.length>idx;
    b.disabled=!available;b.style.opacity=available?'1':'.35';
    if(available){
      let breadcrumbIndex=idx;
      if(layer==='macro'&&buttons.length>1)breadcrumbIndex=1;
      b.onclick=()=>buttons[breadcrumbIndex]?.click();
    }
    layerSwitcher.appendChild(b);
  });
}
const navigator=document.querySelector('.spatial-navigator');
const breadcrumb=document.getElementById('spatial-breadcrumb');
if(navigator&&breadcrumb)navigator.insertBefore(layerSwitcher,breadcrumb);

new MutationObserver(render).observe(badge,{childList:true,characterData:true,subtree:true});new MutationObserver(render).observe(node,{childList:true,characterData:true,subtree:true});new MutationObserver(render).observe(children,{childList:true,characterData:true,subtree:true});new MutationObserver(render).observe(document.getElementById('spatial-breadcrumb'),{childList:true,subtree:true});new MutationObserver(renderLayerSwitcher).observe(document.getElementById('spatial-breadcrumb'),{childList:true,subtree:true,characterData:true});new MutationObserver(renderLayerSwitcher).observe(badge,{childList:true,characterData:true,subtree:true});window.addEventListener('resize',resize);render();renderLayerSwitcher();animate();
}
