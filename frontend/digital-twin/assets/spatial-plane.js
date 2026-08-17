import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport = document.getElementById('twin-viewport');
const baseCanvas = document.getElementById('twin-canvas');
const controls = document.querySelector('.viewer-controls');
const hint = document.querySelector('.viewer-hint');
const loading = document.getElementById('viewer-loading');
const badge = document.getElementById('spatial-level-badge');
const node = document.getElementById('spatial-node');
const children = document.getElementById('spatial-children');

if (viewport && badge && node && children) {
  const layerCanvas = document.createElement('canvas');
  layerCanvas.id = 'spatial-layer-canvas';
  Object.assign(layerCanvas.style, {position:'absolute',inset:'0',width:'100%',height:'100%',zIndex:'3',display:'none',cursor:'default'});
  viewport.appendChild(layerCanvas);
  const labels=document.createElement('div'); labels.id='spatial-layer-labels'; Object.assign(labels.style,{position:'absolute',inset:'0',zIndex:'4',pointerEvents:'none',display:'none'}); viewport.appendChild(labels);
  const renderer=new THREE.WebGLRenderer({canvas:layerCanvas,antialias:true,alpha:true}); renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2)); renderer.outputColorSpace=THREE.SRGBColorSpace;
  const scene=new THREE.Scene(); scene.background=new THREE.Color(0x0b1518); const camera=new THREE.PerspectiveCamera(35,1,.1,100); camera.position.set(0,0,8); scene.add(new THREE.HemisphereLight(0xffffff,0x10201d,2.2)); const key=new THREE.DirectionalLight(0xffffff,2.4); key.position.set(4,5,7); scene.add(key); const layerRoot=new THREE.Group(); scene.add(layerRoot);
  const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2(); let clickable=[];
  const COLORS={tissue:0x4f8f7d,cellular:0x5fae98,cell:0x8bc7b0,accent:0x9bd8c4,grid:0x4f9b86};
  function level(){return String(badge.textContent||'MACRO').trim().toUpperCase()}
  function targets(){return [...children.querySelectorAll('.spatial-target')]}
  function text(el){return el.querySelector('strong')?.textContent||'Spatial target'}
  function clear(){while(layerRoot.children.length){const o=layerRoot.children.pop();o.traverse?.(c=>{c.geometry?.dispose?.();c.material?.dispose?.()})} clickable=[];labels.replaceChildren()}
  function label(t,x,y,target){const b=document.createElement('button');b.type='button';b.textContent=t;Object.assign(b.style,{position:'absolute',left:`${x}%`,top:`${y}%`,transform:'translate(-50%,-50%)',pointerEvents:'auto',padding:'10px 13px',borderRadius:'12px',border:'1px solid #78bca866',background:'#12221fe6',color:'#dcece6',font:'700 12px system-ui,sans-serif',cursor:'pointer'});b.onclick=()=>target.click();labels.appendChild(b)}
  function mesh(g,p,t,c){const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:c,roughness:.62,metalness:.05,emissive:0x071c17,emissiveIntensity:.22}));m.position.set(...p);m.userData.target=t;layerRoot.add(m);clickable.push(m);return m}
  function tissue(){const ts=targets();const plate=new THREE.Mesh(new THREE.BoxGeometry(6.5,3.8,.32),new THREE.MeshStandardMaterial({color:0x18322d,roughness:.85}));plate.position.z=-.35;layerRoot.add(plate);const p=[[-2.05,.45,.25],[0,-.25,.45],[2.05,.5,.25]];ts.forEach((t,i)=>{mesh(new THREE.BoxGeometry(1.55,1.25,.38),p[i%3],t,COLORS.tissue);label(text(t),24+i*26,58-(i%2)*18,t)})}
  function cellular(){const ts=targets();const plate=new THREE.Mesh(new THREE.BoxGeometry(7,4.2,.18),new THREE.MeshStandardMaterial({color:0x101f20,roughness:.9}));plate.position.z=-.45;layerRoot.add(plate);for(let x=-3;x<=3;x++)for(let y=-2;y<=2;y++){const c=new THREE.Mesh(new THREE.CircleGeometry(.13,20),new THREE.MeshBasicMaterial({color:COLORS.grid,transparent:true,opacity:.5}));c.position.set(x+(y%2)*.35,y*.7,-.1);layerRoot.add(c)}const p=[[-2,.75,.2],[0,-.55,.3],[2,.8,.2]];ts.forEach((t,i)=>{const m=mesh(new THREE.SphereGeometry(.62,32,20),p[i%3],t,COLORS.cellular);m.scale.set(1,.72,.35);label(text(t),25+i*25,54-(i%2)*17,t)})}
  function cell(){const t=targets()[0];const o=new THREE.Mesh(new THREE.SphereGeometry(1.45,48,32),new THREE.MeshStandardMaterial({color:COLORS.cell,roughness:.55,transparent:true,opacity:.82,emissive:0x0b3026,emissiveIntensity:.35}));o.userData.target=t;if(t)clickable.push(o);layerRoot.add(o);const n=new THREE.Mesh(new THREE.SphereGeometry(.55,40,24),new THREE.MeshStandardMaterial({color:0x315e51,roughness:.45,emissive:0x183b31,emissiveIntensity:.45}));n.position.set(-.2,.1,1.05);layerRoot.add(n);const r=new THREE.Mesh(new THREE.TorusGeometry(2,.025,8,96),new THREE.MeshBasicMaterial({color:COLORS.accent,transparent:true,opacity:.55}));layerRoot.add(r);if(t)label(text(t),50,82,t)}
  function render(){const l=level();const deep=!['MACRO','MACRO ANATOMY'].includes(l);layerCanvas.style.display=deep?'block':'none';labels.style.display=deep?'block':'none';if(baseCanvas)baseCanvas.style.visibility=deep?'hidden':'visible';if(controls)controls.style.visibility=deep?'hidden':'visible';if(hint)hint.style.visibility=deep?'hidden':'visible';if(loading)loading.style.visibility=deep?'hidden':'visible';if(!deep)return;clear();camera.position.set(0,0,8);camera.lookAt(0,0,0);if(l.includes('TISSUE'))tissue();else if(l.includes('CELLULAR'))cell();else cell();resize()}
  function resize(){const r=viewport.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
  layerCanvas.addEventListener('pointerdown',e=>{const r=layerCanvas.getBoundingClientRect();pointer.x=(e.clientX-r.left)/r.width*2-1;pointer.y=-(e.clientY-r.top)/r.height*2+1;raycaster.setFromCamera(pointer,camera);const h=raycaster.intersectObjects(clickable,false)[0];if(h?.object?.userData?.target)h.object.userData.target.click()});
  const obs=new MutationObserver(render);obs.observe(badge,{childList:true,characterData:true,subtree:true});obs.observe(node,{childList:true,characterData:true,subtree:true});obs.observe(children,{childList:true,characterData:true,subtree:true});window.addEventListener('resize',resize);render();(function animate(){requestAnimationFrame(animate);if(layerCanvas.style.display!=='none'){layerRoot.rotation.y+=.0025;renderer.render(scene,camera)}})();
}