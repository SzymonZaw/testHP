(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const panel = document.createElement('section');
  panel.id = 'spatial-viewport-debug';
  Object.assign(panel.style, {
    position:'absolute',right:'12px',top:'12px',width:'430px',maxWidth:'calc(100% - 24px)',zIndex:'200',display:'none',
    padding:'10px',borderRadius:'10px',background:'rgba(5,12,13,.95)',border:'1px solid #4b746b',color:'#dcece6',
    font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',boxShadow:'0 12px 35px rgba(0,0,0,.4)',
    pointerEvents:'auto',boxSizing:'border-box',maxHeight:'calc(100% - 24px)',overflow:'auto'
  });
  const head=document.createElement('div');
  Object.assign(head.style,{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'7px',position:'sticky',top:'0',background:'rgba(5,12,13,.98)',paddingBottom:'5px',zIndex:'2'});
  const title=document.createElement('strong'); title.textContent='TWIN VIEWPORT · DEBUG';
  const actions=document.createElement('div');
  const refresh=document.createElement('button'); refresh.type='button'; refresh.textContent='REFRESH';
  const clear=document.createElement('button'); clear.type='button'; clear.textContent='CLEAR';
  [refresh,clear].forEach(b=>Object.assign(b.style,{background:'#152723',color:'#cfe8df',border:'1px solid #36544e',borderRadius:'6px',padding:'3px 6px',font:'700 9px ui-monospace,monospace',cursor:'pointer',marginLeft:'4px'}));
  actions.append(refresh,clear); head.append(title,actions);
  const state=document.createElement('pre'); Object.assign(state.style,{margin:'0 0 7px',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#9bd8c4'});
  const log=document.createElement('pre'); Object.assign(log.style,{margin:0,maxHeight:'230px',overflow:'auto',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#b7c9c3'});
  panel.append(head,state,log); viewport.appendChild(panel);

  const toggle=document.createElement('button'); toggle.type='button'; toggle.textContent='DEBUG'; toggle.title='Toggle twin viewport debug';
  Object.assign(toggle.style,{position:'absolute',right:'12px',top:'12px',zIndex:'201',padding:'5px 8px',borderRadius:'7px',border:'1px solid #36544e',background:'#101b1a',color:'#9bd8c4',font:'800 9px ui-monospace,monospace',cursor:'pointer',pointerEvents:'auto'});
  viewport.appendChild(toggle); toggle.onclick=()=>{panel.style.display=panel.style.display==='none'?'block':'none';snapshot('MANUAL SNAPSHOT');};

  const lines=[]; const MAX=160;
  const text=id=>document.getElementById(id)?.textContent?.trim()||'';
  const path=()=>[...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean);
  const children=()=>[...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x=>x.textContent.trim()).filter(Boolean);
  const rect=el=>{if(!el)return {width:0,height:0};const r=el.getBoundingClientRect();return {width:Math.round(r.width),height:Math.round(r.height)};};
  const css=el=>el?{display:getComputedStyle(el).display,visibility:getComputedStyle(el).visibility,opacity:getComputedStyle(el).opacity,pointerEvents:getComputedStyle(el).pointerEvents,zIndex:getComputedStyle(el).zIndex,rect:rect(el)}:null;

  function read(){
    const manager=window.spatialViewportManager;
    const base=document.getElementById('twin-canvas');
    const deep=document.getElementById('spatial-active-canvas');
    const active=manager?.active;
    const level=text('spatial-level-badge')||'?';
    const target=document.querySelector('#spatial-node strong')?.textContent?.trim()||'?';
    const p=path();
    const state=manager?.getViewportState?.();
    return {manager,active,base,deep,level,target,path:p,children:children(),activeKey:manager?.activeKey||'none',state};
  }

  function snapshot(prefix='STATE'){
    const s=read();
    const active=s.active;
    const state=s.state;
    const layer=state?.activeLayer||((s.level.toUpperCase().includes('MACRO'))?'macro':'deep');
    const input=state?.inputOwner||'unknown';
    const linesOut=[
      prefix,
      '',
      'RUNTIME',
      `status:       ${s.manager?'READY':'WAITING FOR MANAGER'}`,
      `viewport:     ${rect(viewport).width}×${rect(viewport).height}`,
      `base canvas:  ${JSON.stringify(css(s.base))}`,
      `deep canvas:  ${JSON.stringify(css(s.deep))}`,
      '',
      'SPATIAL STATE',
      `level:        ${s.level}`,
      `target:       ${s.target}`,
      `spatial_id:   ${s.target==='?'?'?':(document.querySelector('#spatial-node [data-spatial-id]')?.getAttribute('data-spatial-id')||'DOM-managed')}`,
      `path:         ${s.path.join(' > ')||'(root)'}`,
      `children:     ${s.children.join(' | ')||'(none)'}`,
      `active_key:   ${s.activeKey}`,
      `renderer:     ${active?.constructor?.name||'none'}`,
      `active layer: ${layer}`,
      `input owner:  ${input}`,
      '',
      'DISPLAY / INPUT CONTRACT',
      `base:         ${state?`${state.base.display} / ${state.base.visibility} / pointer=${state.base.pointerEvents} / ${state.base.rect.width}×${state.base.rect.height}`:'unknown'}`,
      `deep:         ${state?`${state.deep.display} / ${state.deep.visibility} / pointer=${state.deep.pointerEvents} / ${state.deep.rect.width}×${state.deep.rect.height}`:'unknown'}`,
      `manager deep: ${s.manager?.deepCanvas?'present':'missing'}`,
      `clickable:    ${active?.clickable?.length??'—'}`,
      `scene:        ${active?.scene?.children?.length??'—'}`,
      `root:         ${active?.root?.children?.length??'—'}`
    ];
    stateEl.textContent=linesOut.join('\n');
  }

  function event(message){const now=new Date().toLocaleTimeString();lines.push(`[${now}] ${message}`);while(lines.length>MAX)lines.shift();log.textContent=lines.join('\n');log.scrollTop=log.scrollHeight;snapshot('STATE AFTER EVENT');}
  const stateEl=state;
  clear.onclick=()=>{lines.length=0;log.textContent='';event('log cleared');};
  refresh.onclick=()=>snapshot('MANUAL REFRESH');

  let lastKey='';
  const observer=new MutationObserver(()=>{
    const s=read();
    const key=`${s.level}|${s.target}|${s.path.join('>')}|${s.activeKey}`;
    if(key!==lastKey){lastKey=key;event(`SPATIAL CHANGE | level=${s.level} | target=${s.target} | path=${s.path.join(' > ')||'(root)'} | children=${s.children.join(' | ')||'(none)'} | renderer=${s.active?.constructor?.name||'none'}`);}
  });
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true,characterData:true,attributes:true});});

  function bindCanvas(el,name){
    if(!el || el.dataset.debugBound==='1')return;
    el.dataset.debugBound='1';
    ['pointerdown','pointerup','click','wheel'].forEach(type=>el.addEventListener(type,e=>{
      const r=el.getBoundingClientRect();
      const localX=Math.round(e.clientX-r.left),localY=Math.round(e.clientY-r.top);
      const ndcX=r.width?((localX/r.width)*2-1).toFixed(3):'n/a';
      const ndcY=r.height?(-(localY/r.height)*2+1).toFixed(3):'n/a';
      event(`${name} ${type} | layer=${read().level} | target=${read().target} | local=${localX},${localY} | ndc=${ndcX},${ndcY}${type==='wheel'?` | deltaY=${e.deltaY}`:''}`);
    },{passive:type==='wheel'}));
  }

  const timer=setInterval(()=>{const s=read();bindCanvas(s.base,'BASE CANVAS');bindCanvas(s.deep,'DEEP CANVAS');snapshot();},300);
  window.addEventListener('beforeunload',()=>{clearInterval(timer);observer.disconnect();},{once:true});
  event('debug initialized · observer only · no render/style mutation');
})();
