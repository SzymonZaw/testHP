import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const viewport=document.getElementById('twin-viewport');
const baseCanvas=document.getElementById('twin-canvas');
const controls=document.querySelector('.viewer-controls');
const hint=document.querySelector('.viewer-hint');
const loading=document.getElementById('viewer-loading');
const badge=document.getElementById('spatial-level-badge');
const node=document.getElementById('spatial-node');
const children=document.getElementById('spatial-children');

if(viewport&&badge&&node&&children){
  const canvas=document.createElement('canvas');
  canvas.id='spatial-layer-canvas';
  Object.assign(canvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',zIndex:'20',display:'none',cursor:'grab',background:'#0b1518'});
  viewport.appendChild(canvas);

  const overlay=document.createElement('div');
  Object.assign(overlay.style,{position:'absolute',inset:'0',zIndex:'21',pointerEvents:'none',display:'none'});
  viewport.appendChild(overlay);

  const switcher=document.createElement('div');
  switcher.id='spatial-layer-switcher';
  Object.assign(switcher.style,{position:'absolute',left:'14px',top:'14px',zIndex:'50',display:'flex',flexWrap:'wrap',gap:'6px',alignItems:'center',padding:'8px 10px',borderRadius:'12px',background:'rgba(8,16,22,.94)',border:'1px solid rgba(155,216,196,.4)',boxShadow:'0 8px 28px rgba(0,0,0,.38)',backdropFilter:'blur(8px)',pointerEvents:'auto'});
  viewport.appendChild(switcher);

  const title=document.createElement('div');
  Object.assign(title.style,{position:'absolute',left:'18px',bottom:'18px',zIndex:'40',display:'none',padding:'8px 11px',borderRadius:'10px',background:'rgba(13,25,24,.9)',border:'1px solid rgba(155,216,196,.35)',color:'#dcece6',font:'800 11px system-ui,sans-serif',letterSpacing:'.1em'});
  viewport.appendChild(title);

  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.setClearColor(0x0b1518,1);
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(35,1,.1,100);camera.position.set(0,0,8);
  scene.add(new THREE.HemisphereLight(0xffffff,0x10201d,2.2));
  const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(4,5,7);scene.add(light);
  const root=new THREE.Group();scene.add(root);
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
  let clickable=[];
  let selected='macro';
  let renderKey='';

  const names={macro:'Hand',tissue:'Tissue planes',cellular:'Cellular fields',cell:'Single cell'};
  const colors={tissue:0x5d9d89,cellular:0x5fae98,cell:0x8bc7b0,accent:0x9bd8c4,grid:0x4f9b86};

  function currentNavigationLevel(){
    const text=String(badge.textContent||'').toUpperCase();
    if(text.includes('SINGLE'))return'cell';
    if(text.includes('CELLULAR'))return'cellular';
    if(text.includes('TISSUE'))return'tissue';
    return'macro';
  }
  function targetElements(){return [...children.querySelectorAll('.spatial-target')].filter(x=>x.querySelector('strong'));}
  function targetText(x){return x.querySelector('strong')?.textContent?.trim()||'Spatial target';}
  function clear(){while(root.children.length){const o=root.children.pop();o.traverse?.(c=>{c.geometry?.dispose?.();c.material?.dispose?.()})}clickable=[];overlay.replaceChildren();}
  function addLabel(text,x,y,target){
    const b=document.createElement('button');b.type='button';b.textContent=text;
    Object.assign(b.style,{position:'absolute',left:`${x}%`,top:`${y}%`,transform:'translate(-50%,-50%)',pointerEvents:'auto',padding:'10px 13px',borderRadius:'11px',border:'1px solid #78bca866',background:'#12221fe8',color:'#dcece6',font:'700 12px system-ui,sans-serif',cursor:'pointer'});
    if(target)b.onclick=()=>target.click();
    overlay.appendChild(b);
  }
  function makeMesh(geometry,position,color,target){
    const m=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.62,metalness:.04,emissive:0x071c17,emissiveIntensity:.22}));
    m.position.set(...position);if(target)m.userData.target=target;root.add(m);if(target)clickable.push(m);return m;
  }
  function renderTissue(){
    const plate=makeMesh(new THREE.BoxGeometry(7,4.2,.18),[0,0,-.55],0x132923,null);
    plate.material.roughness=.9;
    const targets=targetElements();
    const fallback=['Thenar eminence','Hypothenar eminence','Central palm'];
    const list=targets.length?targets.slice(0,3):fallback.map(()=>null);
    list.forEach((t,i)=>{
      const m=makeMesh(new THREE.BoxGeometry(1.8,1.35,.28),[[-2.15,.55,.2],[0,-.25,.35],[2.15,.55,.2]][i],colors.tissue,t);
      m.rotation.z=(i-1)*.05;
      addLabel(t?targetText(t):fallback[i],23+i*27,58-(i%2)*18,t);
    });
    title.textContent='TISSUE PLANES';
  }
  function renderCellular(){
    makeMesh(new THREE.BoxGeometry(7,4.2,.18),[0,0,-.5],0x101f20,null);
    for(let x=-3;x<=3;x++)for(let y=-2;y<=2;y++){
      const c=new THREE.Mesh(new THREE.CircleGeometry(.12,18),new THREE.MeshBasicMaterial({color:colors.grid,transparent:true,opacity:.5}));
      c.position.set(x+(y%2)*.35,y*.7,-.1);root.add(c);
    }
    const targets=targetElements();
    const positions=[[-2,.75,.2],[0,-.55,.3],[2,.8,.2]];
    targets.slice(0,3).forEach((t,i)=>{const m=makeMesh(new THREE.SphereGeometry(.62,32,20),positions[i],colors.cellular,t);m.scale.set(1,.72,.35);addLabel(targetText(t),25+i*25,54-(i%2)*17,t)});
    title.textContent='CELLULAR FIELDS';
  }
  function renderCell(){
    const t=targetElements()[0];
    const outer=makeMesh(new THREE.SphereGeometry(1.45,48,32),[0,0,.1],colors.cell,t);outer.material.transparent=true;outer.material.opacity=.82;outer.material.emissive.setHex(0x0b3026);outer.material.emissiveIntensity=.35;
    const nucleus=makeMesh(new THREE.SphereGeometry(.55,40,24),[-.2,.1,1.05],0x315e51,null);nucleus.material.emissive.setHex(0x183b31);nucleus.material.emissiveIntensity=.45;
    if(t)addLabel(targetText(t),50,82,t);
    title.textContent='SINGLE CELL';
  }
  function renderIndependent(){
    clear();camera.position.set(0,0,8);camera.lookAt(0,0,0);
    if(selected==='tissue')renderTissue();else if(selected==='cellular')renderCellular();else if(selected==='cell')renderCell();
    title.style.display=selected==='macro'?'none':'block';
    canvas.style.display=selected==='macro'?'none':'block';overlay.style.display=selected==='macro'?'none':'block';
    if(baseCanvas)baseCanvas.style.display=selected==='macro'?'block':'none';
    if(controls)controls.style.visibility=selected==='macro'?'visible':'hidden';
    if(hint)hint.style.visibility=selected==='macro'?'visible':'hidden';
    if(loading)loading.style.visibility=selected==='macro'?'visible':'hidden';
    syncBoundary(selected!=='macro');resize();
  }
  function syncBoundary(deep){
    const inspector=document.querySelector('.inspector'),statePanel=document.querySelector('.state-panel');
    [inspector,statePanel].forEach(e=>{if(e)e.style.setProperty('display',deep?'none':'','important')});
    document.body.classList.toggle('spatial-deep',deep);
  }
  function buildSwitcher(){
    switcher.replaceChildren();
    const label=document.createElement('span');label.textContent='VISUALIZATION';Object.assign(label.style,{font:'800 9px system-ui,sans-serif',letterSpacing:'.12em',color:'#9aaeb6',marginRight:'3px'});switcher.appendChild(label);
    Object.entries(names).forEach(([key,labelText])=>{
      const b=document.createElement('button');b.type='button';b.textContent=labelText;
      Object.assign(b.style,{padding:'7px 10px',borderRadius:'8px',border:`1px solid ${key===selected?'#9bd8c4':'#36544e'}`,background:key===selected?'#23463e':'#101b1a',color:key===selected?'#fff':'#cbdad5',font:'700 10px system-ui,sans-serif',cursor:'pointer'});
      b.onclick=()=>{selected=key;renderIndependent();buildSwitcher();};
      switcher.appendChild(b);
    });
  }
  function resize(){const r=viewport.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
  function animate(){requestAnimationFrame(animate);if(selected!=='macro'){root.rotation.y+=.0025;renderer.render(scene,camera)}}
  canvas.addEventListener('pointerdown',e=>{const r=canvas.getBoundingClientRect();pointer.x=((e.clientX-r.left)/r.width)*2-1;pointer.y=-((e.clientY-r.top)/r.height)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(clickable,false)[0];if(hit?.object?.userData?.target)hit.object.userData.target.click()});

  buildSwitcher();
  new MutationObserver(()=>{if(selected==='macro')buildSwitcher();}).observe(badge,{childList:true,characterData:true,subtree:true});
  new MutationObserver(()=>{if(selected!=='macro'){const k=`${selected}:${targetElements().map(targetText).join('|')}`;if(k!==renderKey){renderKey=k;renderIndependent();}}}).observe(children,{childList:true,subtree:true,characterData:true});
  window.addEventListener('resize',resize);
  renderIndependent();
  animate();
}
