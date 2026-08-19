(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const panel = document.createElement('section');
  panel.id = 'spatial-viewport-debug';
  Object.assign(panel.style, {position:'absolute',right:'12px',top:'12px',width:'420px',maxWidth:'calc(100% - 24px)',zIndex:'200',display:'none',padding:'10px',borderRadius:'10px',background:'rgba(5,12,13,.94)',border:'1px solid #4b746b',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',boxShadow:'0 12px 35px rgba(0,0,0,.4)',pointerEvents:'auto',boxSizing:'border-box'});
  const head=document.createElement('div');Object.assign(head.style,{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'7px'});
  const title=document.createElement('strong');title.textContent='TWIN-VIEWPORT DEBUG';
  const clear=document.createElement('button');clear.type='button';clear.textContent='CLEAR';Object.assign(clear.style,{background:'#152723',color:'#cfe8df',border:'1px solid #36544e',borderRadius:'6px',padding:'3px 6px',font:'700 9px ui-monospace,monospace',cursor:'pointer'});head.append(title,clear);
  const state=document.createElement('pre');Object.assign(state.style,{margin:'0 0 7px',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#9bd8c4'});
  const log=document.createElement('pre');Object.assign(log.style,{margin:0,maxHeight:'210px',overflow:'auto',whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#b7c9c3'});panel.append(head,state,log);viewport.appendChild(panel);
  const toggle=document.createElement('button');toggle.type='button';toggle.textContent='DEBUG';toggle.title='Toggle twin viewport debug';Object.assign(toggle.style,{position:'absolute',right:'12px',top:'12px',zIndex:'201',padding:'5px 8px',borderRadius:'7px',border:'1px solid #36544e',background:'#101b1a',color:'#9bd8c4',font:'800 9px ui-monospace,monospace',cursor:'pointer',pointerEvents:'auto'});viewport.appendChild(toggle);toggle.onclick=()=>{panel.style.display=panel.style.display==='none'?'block':'none';};

  const lines=[];const MAX=120;
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
    const deepActive=manager?.active && manager.active.constructor?.name==='DeepRenderer';
    return {manager,level,target,crumbs,children,base,deep,baseRect:rect(base),deepRect:rect(deep),basePointer:base?.style.pointerEvents||'default',deepPointer:deep?.style.pointerEvents||'default',renderer:manager?.active?.constructor?.name||'none',key:manager?.activeKey||'none',owner:deepActive?'FOCUS / DeepRenderer':'CONTEXT / BaseRenderer'};
  }
  function snapshot(prefix='STATE'){
    const s=read();
    state.textContent=[`${prefix}`,`level:        ${s.level}`,`target:       ${s.target}`,`path:         ${s.crumbs.join(' > ')||'(root)'}`,`children:     ${s.children.join(' | ')||'(none)'}`,`renderer:     ${s.renderer}`,`input owner:  ${s.owner}`,`base canvas:  ${s.baseRect.w}×${s.baseRect.h} pointer=${s.basePointer}`,`focus canvas: ${s.deepRect.w}×${s.deepRect.h} pointer=${s.deepPointer}`,`key:          ${s.key}`].join('\n');
  }
  function event(message){const now=new Date().toLocaleTimeString();lines.push(`[${now}] ${message}`);while(lines.length>MAX)lines.shift();log.textContent=lines.join('\n');log.scrollTop=log.scrollHeight;snapshot('STATE AFTER EVENT');}
  clear.onclick=()=>{lines.length=0;log.textContent='';event('log cleared');};
  let wrapped=false;
  function attach(){const manager=window.spatialViewportManager;if(!manager||wrapped)return!!manager;const original=manager.render.bind(manager);manager.render=()=>{const before=read();event(`render() called | BEFORE level=${before.level} target=${before.target} renderer=${before.renderer} key=${before.key}`);const result=original();const after=read();event(`render() finished | AFTER level=${after.level} target=${after.target} renderer=${after.renderer} owner=${after.owner} base=${after.baseRect.w}×${after.baseRect.h} deep=${after.deepRect.w}×${after.deepRect.h}`);return result;};wrapped=true;event(`debug attached to SpatialViewportManager (${manager.active?.constructor?.name||'no renderer'})`);snapshot();return true;}
  const observer=new MutationObserver(()=>event('spatial navigation DOM mutation detected'));['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true,characterData:true,attributes:true});});
  const timer=setInterval(()=>{attach();snapshot();},250);window.addEventListener('beforeunload',()=>{clearInterval(timer);observer.disconnect();},{once:true});event('debug panel initialized');
})();
