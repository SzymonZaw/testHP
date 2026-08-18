import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport=document.getElementById('twin-viewport');
const baseCanvas=document.getElementById('twin-canvas');
const controls=document.querySelector('.viewer-controls');
const hint=document.querySelector('.viewer-hint');
const loading=document.getElementById('viewer-loading');
const badge=document.getElementById('spatial-level-badge');
const node=document.getElementById('spatial-node');
const children=document.getElementById('spatial-children');
if(!viewport||!badge||!node||!children)return;

const layerCanvas=document.createElement('canvas');
layerCanvas.id='spatial-layer-canvas';
Object.assign(layerCanvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',zIndex:'20',display:'none',cursor:'grab',background:'#0b1518'});
viewport.appendChild(layerCanvas);
const labels=document.createElement('div');
Object.assign(labels.style,{position:'absolute',inset:'0',zIndex:'21',pointerEvents:'none',display:'none'});
viewport.appendChild(labels);
const title=document.createElement('div');
Object.assign(title.style,{position:'absolute',left:'18px',bottom:'18px',zIndex:'40',display:'none',padding:'8px 11px',borderRadius:'10px',background:'rgba(13,25,24,.92)',border:'1px solid rgba(155,216,196,.35)',color:'#dcece6',font:'800 11px system-ui,sans-serif',letterSpacing:'.1em'});
viewport.appendChild(title);

const renderer=new THREE.WebGLRenderer({canvas:layerCanvas,antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.setClearColor(0x0b1518,1);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(35,1,.1,100);camera.position.set(0,0,8);
scene.add(new THREE.HemisphereLight(0xffffff,0x10201d,2.2));
const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(4,5,7);scene.add(light);
const root=new THREE.Group();scene.add(root);
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
let clickable=[];let renderKey='';
const colors={macro:0xc68b72,tissue:0x5d9d89,cellular:0x5fae98,cell:0x8bc7b0,grid:0x4f9b86};

function level(){const text=String(badge.textContent||'').trim().toUpperCase();if(text.includes('SINGLE'))return'cell';if(text.includes('CELLULAR'))return'cellular';if(text.includes('TISSUE'))return'tissue';return'macro'}
function currentTitle(){return node.querySelector('strong')?.textContent?.trim()||'Spatial target'}
function pathLabels(){return [...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean)}
function targetElements(){return [...children.querySelectorAll('.spatial-target')].filter(x=>x.querySelector('strong'))}
function targetText(el){return el.querySelector('strong')?.textContent?.trim()||'Spatial target'}
function clear(){while(root.children.length){const o=root.children.pop();o.traverse?.(c=>{c.geometry?.dispose?.();if(c.material)c.material.dispose?.()})}clickable=[];labels.replaceChildren()}
function addLabel(text,x,y,target){const b=document.createElement('button');b.type='button';b.textContent=text;Object.assign(b.style,{position:'absolute',left:`${x}%`,top:`${y}%`,transform:'translate(-50%,-50%)',pointerEvents:'auto',padding:'10px 13px',borderRadius:'12px',border:'1px solid #78bca866',background:'#12221fe6',color:'#dcece6',font:'700 12px system-ui,sans-serif',cursor:'pointer',backdropFilter:'blur(6px)'});if(target)b.onclick=()=>target.click();labels.appendChild(b)}
function mesh(geometry,position,color,target){const m=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.62,metalness:.04,emissive:0x071c17,emissiveIntensity:.22}));m.position.set(...position);if(target)m.userData.target=target;root.add(m);if(target)clickable.push(m);return m}
function heading(text){const h=document.createElement('div');h.textContent=text;Object.assign(h.style,{position:'absolute',left:'50%',top:'14%',transform:'translateX(-50%)',font:'800 11px system-ui,sans-serif',letterSpacing:'.16em',color:'#9bd8c4',whiteSpace:'nowrap'});labels.appendChild(h)}
function showHand(){baseCanvas.style.display='block';layerCanvas.style.display='none';labels.style.display='none';title.style.display='none';if(controls)controls.style.visibility='visible';if(hint)hint.style.visibility='visible';if(loading)loading.style.visibility='hidden'}
function renderMacroRegion(){const region=pathLabels().at(-1)||currentTitle();const lower=region.toLowerCase();if(region==='Hand'){showHand();return}const isFinger=['thumb','index finger','middle finger','ring finger','little finger'].includes(lower);if(isFinger){const finger=mesh(new THREE.CapsuleGeometry(.78,3.9,10,24),[0,0,0],colors.macro,null);finger.rotation.z=lower==='little finger'?.08:lower==='thumb'?.55:0}else{mesh(new THREE.BoxGeometry(4.8,2.5,.55),[0,0,0],colors.macro,null)}heading(region.toUpperCase());targetElements().forEach((t,i)=>addLabel(targetText(t),30+i*20,58+(i%2)*15,t));title.textContent=`MACRO ANATOMY · ${region.toUpperCase()}`}
function renderTissue(){mesh(new THREE.BoxGeometry(7,4.2,.18),[0,0,-.55],0x132923,null);heading('TISSUE PLANE');const pos=[[-2.15,.7,.2],[0,-.15,.35],[2.15,.7,.2]];targetElements().slice(0,3).forEach((t,i)=>{const m=mesh(new THREE.BoxGeometry(1.8,1.35,.28),pos[i],colors.tissue,t);m.rotation.z=(i-1)*.05;addLabel(targetText(t),23+i*27,58-(i%2)*18,t)})}
function renderCellular(){mesh(new THREE.BoxGeometry(7,4.2,.18),[0,0,-.5],0x101f20,null);for(let x=-3;x<=3;x++)for(let y=-2;y<=2;y++){const c=new THREE.Mesh(new THREE.CircleGeometry(.12,18),new THREE.MeshBasicMaterial({color:colors.grid,transparent:true,opacity:.5}));c.position.set(x+(y%2)*.35,y*.7,-.1);root.add(c)}heading('CELLULAR FIELD');const pos=[[-2,.75,.2],[0,-.55,.3],[2,.8,.2]];targetElements().slice(0,3).forEach((t,i)=>{const m=mesh(new THREE.SphereGeometry(.62,32,20),pos[i],colors.cellular,t);m.scale.set(1,.72,.35);addLabel(targetText(t),25+i*25,54-(i%2)*17,t)})}
function renderCell(){heading('SINGLE CELL');const outer=mesh(new THREE.SphereGeometry(1.45,48,32),[0,0,.1],colors.cell,null);outer.material.transparent=true;outer.material.opacity=.82;const nucleus=mesh(new THREE.SphereGeometry(.55,40,24),[-.2,.1,1.05],0x315e51,null);nucleus.material.emissive.setHex(0x183b31);nucleus.material.emissiveIntensity=.45;addLabel(currentTitle(),50,82,null)}
function syncBoundary(deep){const inspector=document.querySelector('.inspector');const statePanel=document.querySelector('.state-panel');[inspector,statePanel].forEach(e=>{if(e)e.style.setProperty('display',deep?'none':'','important')});document.body.classList.toggle('spatial-deep',deep)}
function render(){const l=level(),t=currentTitle(),p=pathLabels(),key=`${l}|${p.join('>')}|${t}|${targetElements().map(targetText).join('|')}`;if(key===renderKey){resize();return}renderKey=key;clear();const rootHand=l==='macro'&&p.length<=1&&t==='Hand';const deep=!rootHand;syncBoundary(deep);if(rootHand){showHand();resize();return}baseCanvas.style.display='none';baseCanvas.style.visibility='hidden';layerCanvas.style.display='block';labels.style.display='block';if(controls)controls.style.visibility='hidden';if(hint)hint.style.visibility='hidden';if(loading)loading.style.visibility='hidden';if(l==='macro')renderMacroRegion();else if(l==='tissue')renderTissue();else if(l==='cellular')renderCellular();else renderCell();title.style.display='block';resize()}
function resize(){const r=viewport.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
function animate(){requestAnimationFrame(animate);if(layerCanvas.style.display!=='none'){root.rotation.y+=.0025;renderer.render(scene,camera)}}
layerCanvas.addEventListener('pointerdown',e=>{const r=layerCanvas.getBoundingClientRect();pointer.x=((e.clientX-r.left)/r.width)*2-1;pointer.y=-((e.clientY-r.top)/r.height)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(clickable,false)[0];if(hit?.object?.userData?.target)hit.object.userData.target.click()});
const observerConfig={childList:true,subtree:true,characterData:true};new MutationObserver(render).observe(badge,observerConfig);new MutationObserver(render).observe(node,observerConfig);new MutationObserver(render).observe(children,observerConfig);const breadcrumb=document.getElementById('spatial-breadcrumb');if(breadcrumb)new MutationObserver(render).observe(breadcrumb,observerConfig);window.addEventListener('resize',resize);render();animate();