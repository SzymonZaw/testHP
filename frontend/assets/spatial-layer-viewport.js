import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport=document.getElementById('twin-viewport');
const baseCanvas=document.getElementById('twin-canvas');
const controls=document.querySelector('.viewer-controls');
const hint=document.querySelector('.viewer-hint');
const loading=document.getElementById('viewer-loading');
const badge=document.getElementById('spatial-level-badge');
const node=document.getElementById('spatial-node');
const children=document.getElementById('spatial-children');
const breadcrumb=document.getElementById('spatial-breadcrumb');

if(viewport&&badge&&node&&children){
  const canvas=document.createElement('canvas');
  canvas.id='spatial-layer-canvas';
  Object.assign(canvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',zIndex:'20',display:'none',cursor:'grab',background:'#0b1518'});
  viewport.appendChild(canvas);

  const overlay=document.createElement('div');
  Object.assign(overlay.style,{position:'absolute',inset:'0',zIndex:'21',pointerEvents:'none',display:'none'});
  viewport.appendChild(overlay);

  const title=document.createElement('div');
  Object.assign(title.style,{position:'absolute',left:'18px',bottom:'18px',zIndex:'40',display:'none',padding:'8px 11px',borderRadius:'10px',background:'rgba(13,25,24,.92)',border:'1px solid rgba(155,216,196,.35)',color:'#dcece6',font:'800 11px system-ui,sans-serif',letterSpacing:'.1em'});
  viewport.appendChild(title);

  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.setClearColor(0x0b1518,1);
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(35,1,.1,100);
  camera.position.set(0,0,8);
  scene.add(new THREE.HemisphereLight(0xffffff,0x10201d,2.2));
  const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(4,5,7);scene.add(light);
  const root=new THREE.Group();scene.add(root);
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
  let clickable=[];
  let renderKey='';

  const colors={macro:0xc68b72,tissue:0x5d9d89,cellular:0x5fae98,cell:0x8bc7b0,accent:0x9bd8c4,grid:0x4f9b86};

  function level(){
    const text=String(badge.textContent||'').toUpperCase();
    if(text.includes('SINGLE'))return'cell';
    if(text.includes('CELLULAR'))return'cellular';
    if(text.includes('TISSUE'))return'tissue';
    return'macro';
  }
  function currentTitle(){return node.querySelector('strong')?.textContent?.trim()||'Spatial target';}
  function pathLabels(){return [...(breadcrumb?.querySelectorAll('button')||[])].map(b=>b.textContent.trim()).filter(Boolean);}
  function targetElements(){return [...children.querySelectorAll('.spatial-target')].filter(x=>x.querySelector('strong'));}
  function targetText(x){return x.querySelector('strong')?.textContent?.trim()||'Spatial target';}
  function clear(){while(root.children.length){const o=root.children.pop();o.traverse?.(c=>{c.geometry?.dispose?.();if(c.material){if(Array.isArray(c.material))c.material.forEach(m=>m.dispose?.());else c.material.dispose?.()}})}clickable=[];overlay.replaceChildren();}
  function addLabel(text,x,y,target){
    const b=document.createElement('button');b.type='button';b.textContent=text;
    Object.assign(b.style,{position:'absolute',left:`${x}%`,top:`${y}%`,transform:'translate(-50%,-50%)',pointerEvents:'auto',padding:'10px 13px',borderRadius:'11px',border:'1px solid #78bca866',background:'#12221fe8',color:'#dcece6',font:'700 12px system-ui,sans-serif',cursor:'pointer',backdropFilter:'blur(6px)'});
    if(target)b.onclick=()=>target.click();
    overlay.appendChild(b);
  }
  function makeMesh(geometry,position,color,target){
    const m=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.62,metalness:.04,emissive:0x071c17,emissiveIntensity:.22}));
    m.position.set(...position);if(target)m.userData.target=target;root.add(m);if(target)clickable.push(m);return m;
  }
  function heading(text){
    const h=document.createElement('div');h.textContent=text;
    Object.assign(h.style,{position:'absolute',left:'50%',top:'14%',transform:'translateX(-50%)',font:'800 11px system-ui,sans-serif',letterSpacing:'.16em',color:'#9bd8c4',whiteSpace:'nowrap'});
    overlay.appendChild(h);
  }

  function renderMacroHand(){
    title.textContent='MACRO ANATOMY · HAND';
    title.style.display='block';
    baseCanvas.style.display='block';
    canvas.style.display='none';
    overlay.style.display='none';
    if(controls)controls.style.visibility='visible';
    if(hint)hint.style.visibility='visible';
    if(loading)loading.style.visibility='visible';
    document.body.classList.remove('spatial-deep');
  }

  function renderMacroRegion(){
    const labels=pathLabels();
    const region=(labels[labels.length-1]||currentTitle()).toLowerCase();
    const isFinger=['thumb','index finger','middle finger','ring finger','little finger'].includes(region);
    if(!isFinger){renderMacroHand();return;}
    const geom=new THREE.CapsuleGeometry(.78,3.9,10,24);
    const finger=makeMesh(geom,[0,0,0],colors.macro,null);
    finger.rotation.z=region==='little finger'?.08:region==='thumb'?.55:0;
    finger.material.roughness=.72;
    heading(currentTitle().toUpperCase());
    const targets=targetElements();
    targets.forEach((t,i)=>addLabel(targetText(t),30+i*20,58+(i%2)*15,t));
    title.textContent=`MACRO ANATOMY · ${currentTitle().toUpperCase()}`;
  }

  function renderTissue(){
    makeMesh(new THREE.BoxGeometry(7,4.2,.18),[0,0,-.55],0x132923,null).material.roughness=.9;
    heading('TISSUE PLANE');
    const targets=targetElements();
    const positions=[[-2.15,.7,.2],[0,-.15,.35],[2.15,.7,.2]];
    targets.slice(0,3).forEach((t,i)=>{
      const m=makeMesh(new THREE.BoxGeometry(1.8,1.35,.28),positions[i],colors.tissue,t);
      m.rotation.z=(i-1)*.05;
      addLabel(targetText(t),23+i*27,58-(i%2)*18,t);
    });
    title.textContent=`TISSUE · ${currentTitle().toUpperCase()}`;
  }

  function renderCellular(){
    makeMesh(new THREE.BoxGeometry(7,4.2,.18),[0,0,-.5],0x101f20,null);
    for(let x=-3;x<=3;x++)for(let y=-2;y<=2;y++){
      const c=new THREE.Mesh(new THREE.CircleGeometry(.12,18),new THREE.MeshBasicMaterial({color:colors.grid,transparent:true,opacity:.5}));
      c.position.set(x+(y%2)*.35,y*.7,-.1);root.add(c);
    }
    heading('CELLULAR FIELD');
    const targets=targetElements();
    const positions=[[-2,.75,.2],[0,-.55,.3],[2,.8,.2]];
    targets.slice(0,3).forEach((t,i)=>{
      const m=makeMesh(new THREE.SphereGeometry(.62,32,20),positions[i],colors.cellular,t);
      m.scale.set(1,.72,.35);
      addLabel(targetText(t),25+i*25,54-(i%2)*17,t);
    });
    title.textContent=`CELLULAR FIELD · ${currentTitle().toUpperCase()}`;
  }

  function renderCell(){
    heading('SINGLE CELL');
    const t=currentTitle();
    const outer=makeMesh(new THREE.SphereGeometry(1.45,48,32),[0,0,.1],colors.cell,null);
    outer.material.transparent=true;outer.material.opacity=.82;outer.material.emissive.setHex(0x0b3026);outer.material.emissiveIntensity=.35;
    const nucleus=makeMesh(new THREE.SphereGeometry(.55,40,24),[-.2,.1,1.05],0x315e51,null);
    nucleus.material.emissive.setHex(0x183b31);nucleus.material.emissiveIntensity=.45;
    addLabel(t,50,82,null);
    title.textContent=`SINGLE CELL · ${t.toUpperCase()}`;
  }

  function syncBoundary(deep){
    const inspector=document.querySelector('.inspector'),statePanel=document.querySelector('.state-panel');
    [inspector,statePanel].forEach(e=>{if(e)e.style.setProperty('display',deep?'none':'','important')});
    document.body.classList.toggle('spatial-deep',deep);
  }

  function render(){
    const l=level();
    const t=currentTitle();
    const labels=pathLabels();
    const key=`${l}|${labels.join('>')}|${[...targetElements()].map(targetText).join('|')}`;
    if(key===renderKey){resize();return;}
    renderKey=key;
    clear();
    camera.position.set(0,0,8);camera.lookAt(0,0,0);
    const handRoot=labels.length<=1||t==='Hand';
    const deep=l!=='macro'||!handRoot;
    syncBoundary(deep);
    if(!deep){renderMacroHand();resize();return;}
    baseCanvas.style.display='none';
    canvas.style.display='block';overlay.style.display='block';
    if(controls)controls.style.visibility='hidden';
    if(hint)hint.style.visibility='hidden';
    if(loading)loading.style.visibility='hidden';
    if(l==='macro')renderMacroRegion();
    else if(l==='tissue')renderTissue();
    else if(l==='cellular')renderCellular();
    else renderCell();
    resize();
  }

  function resize(){const r=viewport.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
  function animate(){requestAnimationFrame(animate);if(canvas.style.display!=='none'){root.rotation.y+=.0025;renderer.render(scene,camera)}}
  canvas.addEventListener('pointerdown',e=>{
    const r=canvas.getBoundingClientRect();pointer.x=((e.clientX-r.left)/r.width)*2-1;pointer.y=-((e.clientY-r.top)/r.height)*2+1;
    raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(clickable,false)[0];if(hit?.object?.userData?.target)hit.object.userData.target.click();
  });

  const observerConfig={childList:true,subtree:true,characterData:true};
  new MutationObserver(render).observe(badge,observerConfig);
  new MutationObserver(render).observe(node,observerConfig);
  new MutationObserver(render).observe(children,observerConfig);
  if(breadcrumb)new MutationObserver(render).observe(breadcrumb,observerConfig);
  window.addEventListener('resize',resize);
  render();
  animate();
}
