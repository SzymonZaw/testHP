(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const panel = document.createElement('section');
  panel.id = 'spatial-viewport-debug';
  Object.assign(panel.style, {position:'absolute',right:'12px',top:'12px',width:'560px',maxWidth:'calc(100% - 24px)',zIndex:'200',display:'none',padding:'10px',borderRadius:'10px',background:'rgba(5,12,13,.96)',border:'1px solid #4b746b',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',boxShadow:'0 12px 35px rgba(0,0,0,.4)',pointerEvents:'auto',boxSizing:'border-box'});
  const head=document.createElement('div');Object.assign(head.style,{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'7px'});
  const title=document.createElement('strong');title.textContent='TWIN VIEWPORT · DEBUG';
  const clear=document.createElement('button');clear.type='button';clear.textContent='CLEAR';Object.assign(clear.style,{background:'#152723',color:'#cfe8df',border:'1px solid #36544e',borderRadius:'6px',padding:'3px 6px',font:'700 9px ui-monospace,monospace',cursor:'pointer'});head.append(title,clear);
  const state=document.createElement('pre');Object.assign(state.style,{margin:'0 0 7px',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#9bd8c4'});
  const log=document.createElement('pre');Object.assign(log.style,{margin:0,maxHeight:'330px',overflow:'auto',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#b7c9c3'});panel.append(head,state,log);viewport.appendChild(panel);
  const toggle=document.createElement('button');toggle.type='button';toggle.textContent='DEBUG';toggle.title='Toggle twin viewport debug';Object.assign(toggle.style,{position:'absolute',right:'12px',top:'12px',zIndex:'201',padding:'5px 8px',borderRadius:'7px',border:'1px solid #36544e',background:'#101b1a',color:'#9bd8c4',font:'800 9px ui-monospace,monospace',cursor:'pointer',pointerEvents:'auto'});viewport.appendChild(toggle);toggle.onclick=()=>{panel.style.display=panel.style.display==='none'?'block':'none';};

  const lines=[];const MAX=240;
  let lastRaycast=null,lastDeepClick=null,lastOwner=null,lastRendered=null,lastSync=null,lastManager=null,lastVisualSignature='';
  let renderCalls=0;

  const text=id=>document.getElementById(id)?.textContent?.trim()||'';
  const rect=el=>{if(!el)return{w:0,h:0,x:0,y:0};const r=el.getBoundingClientRect();return{w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.left),y:Math.round(r.top)};};
  const scripts=()=>[...document.scripts].map(s=>s.src||'inline').filter(s=>/digital-twin|spatial-layer-viewport|deep-viewport-sync|app\.js/.test(s));
  const meshInfo=object=>{const out=[];object?.traverse?.(x=>{if(x.isMesh)out.push(`${x.name||'?'}${x.visible?'':'(hidden)'}`);});return out;};
  const groupByName=(scene,names)=>{for(const name of names){const found=[];scene?.traverse?.(x=>{if(x.name===name)found.push(x);});if(found.length)return found;}return[];};
  const managerSignature=m=>m?`${m.constructor?.name||'?'}|renderLen=${String(m.render||'').length}|renderHead=${String(m.render||'').replace(/\s+/g,' ').slice(0,90)}`:'none';

  function read(){
    const manager=window.spatialViewportManager;
    const badge=document.getElementById('spatial-level-badge');
    const node=document.getElementById('spatial-node');
    const crumbs=[...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean);
    const children=[...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x=>x.textContent.trim()).filter(Boolean);
    const base=document.getElementById('twin-canvas');
    const deep=document.getElementById('spatial-active-canvas');
    const active=manager?.active;
    const scene=active?.scene;
    const deepGroups=groupByName(scene,['canonical-deep-navigation-layer','digital-twin-navigation-layer']);
    const rendererCanvas=active?.renderer?.domElement;
    const deepRendererCanvas=manager?.deepRenderer?.domElement;
    const level=badge?.textContent?.trim()||'?';
    const target=node?.querySelector('strong')?.textContent?.trim()||'?';
    const currentLayer=active?.activeLayer||'unknown';
    const visualSignature=`${level}|${target}|${crumbs.join('>')}|${currentLayer}|${active?.root?.visible}|${active?.root?.children?.length}|${deepGroups.map(g=>`${g.name}:${g.visible}:${g.children.length}`).join(',')}`;
    const contract=level.toLowerCase().includes('pojedync')||level.toLowerCase().includes('single')||level.toLowerCase().includes('komórk')||level.toLowerCase().includes('cell') ? 'deep' : 'macro';
    const violations=[];
    if(contract==='deep' && currentLayer!=='deep')violations.push('DOM=DEEP but activeLayer!=deep');
    if(contract==='deep' && active?.root?.visible!==false)violations.push('DEEP target but macro root is VISIBLE');
    if(contract==='deep' && !deepGroups.length)violations.push('DEEP target but no deep group exists in active scene');
    if(contract==='deep' && deepGroups.length && !deepGroups.some(g=>g.visible))violations.push('DEEP group exists but is HIDDEN');
    if(contract==='deep' && deepGroups.length && !deepGroups.some(g=>g.children.length))violations.push('DEEP group exists but has NO CHILD OBJECTS');
    if(rendererCanvas && base && rendererCanvas!==base)violations.push('active renderer does not own twin-canvas');
    if(deepRendererCanvas && deep && deepRendererCanvas!==deep)violations.push('deepRenderer does not own spatial-active-canvas');
    return {manager,badge,level,target,crumbs,children,base,deep,active,scene,deepGroups,rendererCanvas,deepRendererCanvas,contract,violations,visualSignature,
      baseRect:rect(base),deepRect:rect(deep),baseDisplay:base?.style.display||'default',baseVisibility:base?.style.visibility||'default',basePointer:base?.style.pointerEvents||'default',deepDisplay:deep?.style.display||'none',deepVisibility:deep?.style.visibility||'hidden',deepPointer:deep?.style.pointerEvents||'none',
      renderer:active?.constructor?.name||'none',version:manager?.version||'none',key:manager?.activeKey||'none',activeLayer:currentLayer,sceneObjects:scene?.children?.length||0,rootObjects:active?.root?.children?.length||0,rootVisible:active?.root?.visible,clickable:active?.clickable?.length||0,deepClickable:active?.deepClickable?.length||0,
      deepSummary:deepGroups.map(g=>`${g.name} visible=${g.visible} children=${g.children.length} meshes=${meshInfo(g).join('|')||'(none)'}`),scriptList:scripts(),managerSig:managerSignature(manager)};
  }

  function snapshot(prefix='STATE'){
    const s=read(),ray=lastRaycast,click=lastDeepClick,owner=lastOwner;
    state.textContent=[`${prefix}`,`level:          ${s.level}`,`target:         ${s.target}`,`path:           ${s.crumbs.join(' > ')||'(root)'}`,`children:       ${s.children.join(' | ')||'(none)'}`,`contract:       ${s.contract} · activeLayer=${s.activeLayer}`,`manager:        ${s.version} · key=${s.key}`,`scene/root:     ${s.sceneObjects}/${s.rootObjects} · rootVisible=${s.rootVisible}`,`deep groups:    ${s.deepSummary.join(' || ')||'(none)'}`,`clickable:      ${s.clickable} · deepClickable=${s.deepClickable}`,`base canvas:    ${s.baseRect.w}×${s.baseRect.h} ${s.baseDisplay}/${s.baseVisibility} pointer=${s.basePointer}`,`deep overlay:   ${s.deepRect.w}×${s.deepRect.h} ${s.deepDisplay}/${s.deepVisibility} pointer=${s.deepPointer}`,`renderer owner: ${s.rendererCanvas===s.base?'twin-canvas':'DIFFERENT/UNKNOWN'} · deepRenderer=${s.deepRendererCanvas===s.deep?'active-canvas':'DIFFERENT/UNKNOWN'}`,`render calls:   ${renderCalls}`,`scripts:        ${s.scriptList.length} digital-twin script(s)`,s.violations.length?`CONTRACT:       VIOLATION · ${s.violations.join(' | ')}`:'CONTRACT:       OK',`last sync:      ${lastSync?detailString(lastSync):'(none)'}`,`last raycast:   ${ray?`${ray.hit?'HIT':'MISS'} intersections=${ray.intersections??'?'} deepChildren=${ray.deepChildren??'?'} ndc=${ray.ndcX??'?'},${ray.ndcY??'?'}`:'(none)'}`,`last deep click:${click?`${click.navigated?'NAVIGATED':'NO NAV'} reason=${click.reason||'?'} index=${click.index??'?'}/${click.buttonCount??'?'}`:'(none)'}`,`event owner:    ${owner?`${owner.event} → ${owner.owner} moved=${owner.moved??'-'} stopped=${owner.propagationStopped??'-'}`:'(none)'}`].join('\n');
  }
  function detailString(d){try{return JSON.stringify(d);}catch{return '[unserializable detail]';}}
  function event(message){const now=new Date().toLocaleTimeString();lines.push(`[${now}] ${message}`);while(lines.length>MAX)lines.shift();log.textContent=lines.join('\n');log.scrollTop=log.scrollHeight;snapshot('STATE AFTER EVENT');}
  clear.onclick=()=>{lines.length=0;log.textContent='';lastRaycast=lastDeepClick=lastOwner=lastRendered=lastSync=null;renderCalls=0;event('log cleared');};

  let wrappedManager=null;
  function attach(){
    const manager=window.spatialViewportManager;
    if(!manager)return false;
    if(wrappedManager===manager)return true;
    if(wrappedManager)event(`MANAGER REPLACED | old=${managerSignature(wrappedManager)} new=${managerSignature(manager)}`);
    const original=manager.render?.bind(manager);
    if(original){manager.render=(...args)=>{renderCalls++;const before=read();event(`RENDER CALL #${renderCalls} BEFORE | level=${before.level} layer=${before.activeLayer} rootVisible=${before.rootVisible} deep=${before.deepSummary.join(' || ')||'none'}`);const result=original(...args);const after=read();event(`RENDER CALL #${renderCalls} AFTER | level=${after.level} layer=${after.activeLayer} rootVisible=${after.rootVisible} deep=${after.deepSummary.join(' || ')||'none'}`);return result;};}
    wrappedManager=manager;event(`MANAGER ATTACHED | ${managerSignature(manager)}`);return true;
  }

  window.addEventListener('testhp:viewport-rendered',e=>{lastRendered=e.detail||null;event(`VIEW RENDERED | ${detailString(e.detail)}`);},true);
  window.addEventListener('testhp:spatial-layer-changed',e=>event(`SPATIAL LAYER CHANGED | ${detailString(e.detail)}`),true);
  window.addEventListener('testhp:deep-viewport-sync',e=>{lastSync=e.detail||{};event(`DEEP SYNC | ${detailString(e.detail)}`);},true);
  window.addEventListener('testhp:canonical-macro-click-skipped',e=>event(`MACRO CLICK BLOCKED | ${detailString(e.detail)}`),true);
  window.addEventListener('testhp:viewport-deep-raycast',e=>{lastRaycast=e.detail||{};const d=lastRaycast;event(`DEEP RAYCAST | phase=${d.phase||'?'} reason=${d.reason||'-'} hit=${d.hit??'-'} intersections=${d.intersections??'-'} deepChildren=${d.deepChildren??'-'} clickable=${d.clickable??'-'} ndc=${d.ndcX??'-'},${d.ndcY??'-'} camera=${d.camera?`${d.camera.x},${d.camera.y},${d.camera.z}`:'-'}`);if(d.candidates?.length)event(`RAYCAST CANDIDATES | ${d.candidates.map(x=>`${x.object}[${x.index??'-'}]${x.label?`=${x.label}`:''}@${x.distance??'-'}`).join(' | ')}`);},true);
  window.addEventListener('testhp:viewport-deep-click',e=>{lastDeepClick=e.detail||{};const d=lastDeepClick;event(`DEEP CLICK | ${d.navigated?'NAVIGATED':'NOT NAVIGATED'} child=${d.child||'-'} index=${d.index??'-'} buttons=${d.buttonCount??'-'} inRange=${d.indexInRange??'-'} leaf=${d.leaf??'-'} reason=${d.reason||'-'}`);},true);
  window.addEventListener('testhp:viewport-deep-event-owner',e=>{lastOwner=e.detail||{};const d=lastOwner;event(`EVENT OWNER | ${d.event||'?'} owner=${d.owner||'?'} moved=${d.moved??'-'} navigated=${d.navigated??'-'} stopped=${d.propagationStopped??'-'}`);},true);

  const observer=new MutationObserver(()=>{event('DOM SPATIAL MUTATION');});
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true,characterData:true,attributes:true});});
  const timer=setInterval(()=>{attach();const s=read();if(s.visualSignature!==lastVisualSignature){lastVisualSignature=s.visualSignature;event(`VISUAL STATE CHANGED | ${s.visualSignature}`);}snapshot();},250);
  window.addEventListener('beforeunload',()=>{clearInterval(timer);observer.disconnect();},{once:true});
  event('debug initialized · renderer ownership + deep-scene contract diagnostics enabled');
})();
