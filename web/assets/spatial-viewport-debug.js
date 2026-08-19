(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const panel = document.createElement('section');
  panel.id = 'spatial-viewport-debug';
  Object.assign(panel.style, {position:'absolute',right:'12px',top:'12px',width:'500px',maxWidth:'calc(100% - 24px)',zIndex:'200',display:'none',padding:'10px',borderRadius:'10px',background:'rgba(5,12,13,.95)',border:'1px solid #4b746b',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',boxShadow:'0 12px 35px rgba(0,0,0,.4)',pointerEvents:'auto',boxSizing:'border-box'});
  const head=document.createElement('div');Object.assign(head.style,{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'7px'});
  const title=document.createElement('strong');title.textContent='TWIN-VIEWPORT DEBUG';
  const clear=document.createElement('button');clear.type='button';clear.textContent='CLEAR';Object.assign(clear.style,{background:'#152723',color:'#cfe8df',border:'1px solid #36544e',borderRadius:'6px',padding:'3px 6px',font:'700 9px ui-monospace,monospace',cursor:'pointer'});head.append(title,clear);
  const state=document.createElement('pre');Object.assign(state.style,{margin:'0 0 7px',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#9bd8c4'});
  const log=document.createElement('pre');Object.assign(log.style,{margin:0,maxHeight:'300px',overflow:'auto',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#b7c9c3'});panel.append(head,state,log);viewport.appendChild(panel);
  const toggle=document.createElement('button');toggle.type='button';toggle.textContent='DEBUG';toggle.title='Toggle twin viewport debug';Object.assign(toggle.style,{position:'absolute',right:'12px',top:'12px',zIndex:'201',padding:'5px 8px',borderRadius:'7px',border:'1px solid #36544e',background:'#101b1a',color:'#9bd8c4',font:'800 9px ui-monospace,monospace',cursor:'pointer',pointerEvents:'auto'});viewport.appendChild(toggle);toggle.onclick=()=>{panel.style.display=panel.style.display==='none'?'block':'none';};

  const lines=[];const MAX=180;
  let lastRaycast=null;let lastDeepClick=null;let lastOwner=null;let lastRendered=null;
  function read(){
    const manager=window.spatialViewportManager;
    const badge=document.getElementById('spatial-level-badge');
    const node=document.getElementById('spatial-node');
    const crumbs=[...(document.querySelectorAll('#spatial-breadcrumb button'))].map(x=>x.textContent.trim()).filter(Boolean);
    const children=[...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x=>x.textContent.trim()).filter(Boolean);
    const base=document.getElementById('twin-canvas');
    const deep=document.getElementById('spatial-active-canvas');
    const rect=(el)=>{if(!el)return{w:0,h:0};const r=el.getBoundingClientRect();return{w:Math.round(r.width),h:Math.round(r.height)};};
    const level=badge?.textContent?.trim()||'?';
    const target=node?.querySelector('strong')?.textContent?.trim()||'?';
    const active=manager?.active;
    return {
      manager,level,target,crumbs,children,base,deep,baseRect:rect(base),deepRect:rect(deep),
      basePointer:base?.style.pointerEvents||'default',deepPointer:deep?.style.pointerEvents||'default',
      renderer:active?.constructor?.name||'none',key:manager?.activeKey||'none',
      activeLayer:active?.activeLayer||'unknown',version:manager?.version||'none',
      sceneObjects:active?.scene?.children?.length||0,rootObjects:active?.root?.children?.length||0,
      clickable:active?.clickable?.length||0,deepClickable:active?.deepClickable?.length||0,
      rootVisible:active?.root?.visible,owner:active?.activeLayer==='deep'?'DEEP':'MACRO/BASE'
    };
  }
  function snapshot(prefix='STATE'){
    const s=read();
    const ray=lastRaycast;const click=lastDeepClick;const owner=lastOwner;
    state.textContent=[
      `${prefix}`,
      `level:          ${s.level}`,
      `target:         ${s.target}`,
      `path:           ${s.crumbs.join(' > ')||'(root)'}`,
      `children:       ${s.children.join(' | ')||'(none)'}`,
      `renderer:       ${s.renderer} · activeLayer=${s.activeLayer}`,
      `manager:        ${s.version} · key=${s.key}`,
      `scene/root:     ${s.sceneObjects}/${s.rootObjects} · rootVisible=${s.rootVisible}`,
      `clickable:      ${s.clickable} · deepClickable=${s.deepClickable}`,
      `base canvas:    ${s.baseRect.w}×${s.baseRect.h} pointer=${s.basePointer}`,
      `focus canvas:   ${s.deepRect.w}×${s.deepRect.h} pointer=${s.deepPointer}`,
      `last raycast:   ${ray ? `${ray.hit?'HIT':'MISS'} intersections=${ray.intersections??'?'} deepChildren=${ray.deepChildren??'?'} ndc=${ray.ndcX??'?'} ,${ray.ndcY??'?'}` : '(none)'}`,
      `last deep click:${click ? `${click.navigated?'NAVIGATED':'NO NAV'} reason=${click.reason||'?'} index=${click.index??'?'}/${click.buttonCount??'?'}` : ' (none)'}`,
      `event owner:    ${owner ? `${owner.event} → ${owner.owner} stopped=${owner.propagationStopped??'?'}` : '(none)'}`
    ].join('\n');
  }
  function event(message){const now=new Date().toLocaleTimeString();lines.push(`[${now}] ${message}`);while(lines.length>MAX)lines.shift();log.textContent=lines.join('\n');log.scrollTop=log.scrollHeight;snapshot('STATE AFTER EVENT');}
  function detailString(d){try{return JSON.stringify(d);}catch{return '[unserializable detail]';}}
  clear.onclick=()=>{lines.length=0;log.textContent='';lastRaycast=lastDeepClick=lastOwner=lastRendered=null;event('log cleared');};

  let wrapped=false;
  function attach(){
    const manager=window.spatialViewportManager;if(!manager||wrapped)return!!manager;
    const original=manager.render.bind(manager);
    manager.render=()=>{
      const before=read();
      event(`render() called | BEFORE level=${before.level} target=${before.target} layer=${before.activeLayer} renderer=${before.renderer}`);
      const result=original();
      const after=read();
      event(`render() finished | AFTER level=${after.level} target=${after.target} layer=${after.activeLayer} renderer=${after.renderer} deepClickable=${after.deepClickable}`);
      return result;
    };
    wrapped=true;event(`debug attached to SpatialViewportManager (${manager.active?.constructor?.name||'no renderer'})`);snapshot();return true;
  }

  window.addEventListener('testhp:viewport-rendered',e=>{lastRendered=e.detail||null;event(`VIEW RENDERED | ${detailString(e.detail)}`);},true);
  window.addEventListener('testhp:spatial-layer-changed',e=>event(`SPATIAL LAYER CHANGED | ${detailString(e.detail)}`),true);
  window.addEventListener('testhp:viewport-deep-raycast',e=>{
    lastRaycast=e.detail||{};
    const d=lastRaycast;
    event(`DEEP RAYCAST | phase=${d.phase||'?'} reason=${d.reason||'-'} hit=${d.hit??'-'} intersections=${d.intersections??'-'} deepChildren=${d.deepChildren??'-'} clickable=${d.clickable??'-'} ndc=${d.ndcX??'-'},${d.ndcY??'-'} camera=${d.camera?`${d.camera.x},${d.camera.y},${d.camera.z}`:'-'}`);
    if(d.candidates?.length) event(`RAYCAST CANDIDATES | ${d.candidates.map(x=>`${x.object}[${x.index??'-'}]${x.label?`=${x.label}`:''}@${x.distance??'-'}`).join(' | ')}`);
  },true);
  window.addEventListener('testhp:viewport-deep-click',e=>{
    lastDeepClick=e.detail||{};
    const d=lastDeepClick;
    event(`DEEP CLICK | ${d.navigated?'NAVIGATED':'NOT NAVIGATED'} child=${d.child||'-'} index=${d.index??'-'} buttons=${d.buttonCount??'-'} inRange=${d.indexInRange??'-'} leaf=${d.leaf??'-'} reason=${d.reason||'-'}`);
  },true);
  window.addEventListener('testhp:viewport-deep-event-owner',e=>{
    lastOwner=e.detail||{};
    const d=lastOwner;
    event(`EVENT OWNER | ${d.event||'?'} owner=${d.owner||'?'} moved=${d.moved??'-'} navigated=${d.navigated??'-'} stopped=${d.propagationStopped??'-'}`);
  },true);

  const observer=new MutationObserver(()=>event('spatial navigation DOM mutation detected'));
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true,characterData:true,attributes:true});});
  const timer=setInterval(()=>{attach();snapshot();},250);
  window.addEventListener('beforeunload',()=>{clearInterval(timer);observer.disconnect();},{once:true});
  event('debug panel initialized · deep raycast diagnostics enabled');
})();
