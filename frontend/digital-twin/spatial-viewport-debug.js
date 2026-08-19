(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const panel = document.createElement('section');
  panel.id = 'spatial-viewport-debug';
  Object.assign(panel.style, {
    position: 'absolute', right: '12px', top: '12px', width: '390px', maxWidth: 'calc(100% - 24px)',
    maxHeight: 'calc(100% - 24px)', overflow: 'auto', zIndex: '200', display: 'block', padding: '10px', borderRadius: '10px',
    background: 'rgba(5,12,13,.94)', border: '1px solid #4b746b', color: '#dcece6',
    font: '11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace', boxShadow: '0 12px 35px rgba(0,0,0,.4)',
    pointerEvents: 'auto', boxSizing: 'border-box'
  });
  const head = document.createElement('div');
  Object.assign(head.style, {display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'7px'});
  const title = document.createElement('strong'); title.textContent = 'TWIN-VIEWPORT DEBUG';
  const clear = document.createElement('button'); clear.type='button'; clear.textContent='CLEAR';
  Object.assign(clear.style,{background:'#152723',color:'#cfe8df',border:'1px solid #36544e',borderRadius:'6px',padding:'3px 6px',font:'700 9px ui-monospace,monospace',cursor:'pointer'});
  head.append(title,clear);
  const state = document.createElement('pre'); Object.assign(state.style,{margin:'0 0 7px',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#9bd8c4'});
  const log = document.createElement('pre'); Object.assign(log.style,{margin:0,maxHeight:'210px',overflow:'auto',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#b7c9c3'});
  panel.append(head,state,log); viewport.appendChild(panel);

  const toggle = document.createElement('button'); toggle.type='button'; toggle.textContent='DEBUG'; toggle.title='Toggle twin viewport debug';
  Object.assign(toggle.style,{position:'absolute',right:'12px',top:'12px',zIndex:'201',padding:'5px 8px',borderRadius:'7px',border:'1px solid #36544e',background:'#101b1a',color:'#9bd8c4',font:'800 9px ui-monospace,monospace',cursor:'pointer',pointerEvents:'auto'});
  viewport.appendChild(toggle); toggle.onclick=()=>{panel.style.display=panel.style.display==='none'?'block':'none';};

  const lines=[]; const MAX=160;
  const el = id => document.getElementById(id);
  function read(){
    const manager=window.spatialViewportManager;
    const badge=el('spatial-level-badge'), node=el('spatial-node');
    const base=el('twin-canvas'), deep=el('spatial-active-canvas');
    const crumbs=[...(document.querySelectorAll('#spatial-breadcrumb button'))].map(x=>x.textContent.trim()).filter(Boolean);
    const children=[...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x=>x.textContent.trim()).filter(Boolean);
    const level=badge?.textContent?.trim()||'?';
    const target=node?.querySelector('strong')?.textContent?.trim()||'?';
    const deepRect=deep?.getBoundingClientRect(); base?.getBoundingClientRect();
    return {manager,level,target,crumbs,children,base,deep,deepRect,
      renderer:manager?.active?.constructor?.name||'none', key:manager?.activeKey||'none'};
  }
  function enforceLayerIsolation(logChanges=true){
    const s=read(); if(!s.manager || !s.base || !s.deep) return;
    const isMacro=s.renderer==='Hand3DRenderer' || (s.level.toUpperCase()==='MACRO' && s.crumbs.length<=1 && s.target==='Hand');
    const before=`${s.base.style.display}|${s.base.style.visibility}|${s.base.style.pointerEvents}|${s.deep.style.display}|${s.deep.style.visibility}|${s.deep.style.pointerEvents}`;
    if(isMacro){
      s.base.style.display='block'; s.base.style.visibility='visible'; s.base.style.pointerEvents='auto'; s.base.style.opacity='1';
      s.deep.style.display='none'; s.deep.style.visibility='hidden'; s.deep.style.pointerEvents='none';
    } else {
      s.base.style.display='none'; s.base.style.visibility='hidden'; s.base.style.pointerEvents='none'; s.base.style.opacity='0';
      s.deep.style.display='block'; s.deep.style.visibility='visible'; s.deep.style.pointerEvents='auto'; s.deep.style.opacity='1';
      s.deep.style.position='absolute'; s.deep.style.inset='0'; s.deep.style.zIndex='20';
    }
    const after=`${s.base.style.display}|${s.base.style.visibility}|${s.base.style.pointerEvents}|${s.deep.style.display}|${s.deep.style.visibility}|${s.deep.style.pointerEvents}`;
    if(logChanges && before!==after) event(`LAYER ISOLATION | ${isMacro?'MACRO ACTIVE':'DEEP ACTIVE'} | base=${s.base.style.display}/${s.base.style.pointerEvents} | deep=${s.deep.style.display}/${s.deep.style.pointerEvents}`);
  }
  function snapshot(prefix='STATE'){
    const s=read();
    const base=s.base, deep=s.deep;
    const br=base?.getBoundingClientRect(), dr=deep?.getBoundingClientRect();
    state.textContent=[
      prefix,
      `level:        ${s.level}`,
      `target:       ${s.target}`,
      `path:         ${s.crumbs.join(' > ')||'(root)'}`,
      `children:     ${s.children.join(' | ')||'(none)'}`,
      `renderer:     ${s.renderer}`,
      `active_key:   ${s.key}`,
      `BASE VIEW`,
      `display:      ${base?.style.display||'missing'}  visibility: ${base?.style.visibility||'default'}  pointer: ${base?.style.pointerEvents||'auto'}`,
      `rect:         ${br ? `${Math.round(br.width)}×${Math.round(br.height)}` : '—'}`,
      `DEEP VIEW`,
      `display:      ${deep?.style.display||'missing'}  visibility: ${deep?.style.visibility||'default'}  pointer: ${deep?.style.pointerEvents||'auto'}`,
      `rect:         ${dr ? `${Math.round(dr.width)}×${Math.round(dr.height)}` : '—'}`,
      `interaction:  ${s.renderer==='Hand3DRenderer'?'BASE ONLY':'DEEP ONLY'}`
    ].join('\n');
  }
  function event(message){
    const now=new Date().toLocaleTimeString(); lines.push(`[${now}] ${message}`); while(lines.length>MAX)lines.shift();
    log.textContent=lines.join('\n'); log.scrollTop=log.scrollHeight; snapshot('STATE AFTER EVENT');
  }
  clear.onclick=()=>{lines.length=0;log.textContent='';event('log cleared');};

  let wrapped=false;
  function attach(){
    const manager=window.spatialViewportManager; if(!manager || wrapped) return !!manager;
    const original=manager.render.bind(manager);
    manager.render=()=>{
      const before=read(); event(`render() called | BEFORE ${before.level} / ${before.target} / ${before.renderer}`);
      const result=original(); enforceLayerIsolation(false);
      const after=read(); event(`render() finished | AFTER ${after.level} / ${after.target} / ${after.renderer} | base=${after.base?.style.display} | deep=${after.deep?.style.display}`);
      return result;
    };
    wrapped=true; event(`debug attached | renderer=${manager.active?.constructor?.name||'none'}`); snapshot();
    return true;
  }

  const observer=new MutationObserver(() => {
    enforceLayerIsolation();
    event('spatial navigation DOM mutation detected');
  });
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const node=el(id);if(node)observer.observe(node,{childList:true,subtree:true,characterData:true,attributes:true});});

  const timer=setInterval(()=>{ attach(); enforceLayerIsolation(); snapshot(); },250);
  window.addEventListener('beforeunload',()=>{clearInterval(timer);observer.disconnect();},{once:true});
  event('debug panel initialized');
})();
