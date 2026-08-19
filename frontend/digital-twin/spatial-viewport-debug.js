(() => {
  const viewport = document.getElementById('twin-viewport');
  if (!viewport) return;

  const panel = document.createElement('section');
  panel.id = 'spatial-viewport-debug';
  Object.assign(panel.style, {
    position:'absolute',right:'12px',top:'12px',width:'390px',maxWidth:'calc(100% - 24px)',
    maxHeight:'calc(100% - 24px)',overflow:'hidden',zIndex:'200',display:'none',padding:'10px',borderRadius:'10px',
    background:'rgba(5,12,13,.96)',border:'1px solid #4b746b',color:'#dcece6',
    font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',boxShadow:'0 12px 35px rgba(0,0,0,.45)',
    pointerEvents:'auto',boxSizing:'border-box'
  });
  const head=document.createElement('div'); Object.assign(head.style,{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'7px'});
  const title=document.createElement('strong'); title.textContent='HAND DIGITAL TWIN · DEBUG';
  const actions=document.createElement('div'); Object.assign(actions.style,{display:'flex',gap:'5px'});
  const clear=document.createElement('button'); clear.type='button'; clear.textContent='CLEAR';
  const close=document.createElement('button'); close.type='button'; close.textContent='CLOSE';
  [clear,close].forEach(b=>Object.assign(b.style,{background:'#152723',color:'#cfe8df',border:'1px solid #36544e',borderRadius:'6px',padding:'3px 6px',font:'700 9px ui-monospace,monospace',cursor:'pointer'}));
  actions.append(clear,close); head.append(title,actions);
  const body=document.createElement('div'); Object.assign(body.style,{maxHeight:'calc(100vh - 170px)',overflow:'auto',paddingRight:'2px'});
  const state=document.createElement('pre'), registry=document.createElement('pre'), evidence=document.createElement('pre'), log=document.createElement('pre');
  [state,registry,evidence,log].forEach(el=>Object.assign(el.style,{margin:'0 0 8px',whiteSpace:'pre-wrap',wordBreak:'break-word'}));
  state.style.color='#9bd8c4'; registry.style.color='#b9e1d2'; evidence.style.color='#d3dfdb'; log.style.color='#9aaea8';
  body.append(state,registry,evidence,log); panel.append(head,body); viewport.appendChild(panel);

  const toggle=document.createElement('button'); toggle.type='button'; toggle.textContent='DEBUG'; toggle.title='Toggle Hand Digital Twin debug view';
  Object.assign(toggle.style,{position:'absolute',right:'12px',top:'12px',zIndex:'201',padding:'5px 8px',borderRadius:'7px',border:'1px solid #36544e',background:'#101b1a',color:'#9bd8c4',font:'800 9px ui-monospace,monospace',cursor:'pointer',pointerEvents:'auto'});
  viewport.appendChild(toggle);

  const STORAGE='digitalTwinEvidenceUX.v2'; const lines=[]; const MAX=100; let canonicalItems=[]; let wrapped=false;
  function readSpatial(){
    const manager=window.spatialViewportManager,badge=document.getElementById('spatial-level-badge'),node=document.getElementById('spatial-node');
    const crumbs=[...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean);
    const children=[...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x=>x.textContent.trim()).filter(Boolean);
    return {manager,level:badge?.textContent?.trim()||'?',target:node?.querySelector('strong')?.textContent?.trim()||'?',targetId:window.spatialEvidenceTarget||manager?.activeKey||'?',crumbs,children,renderer:manager?.active?.constructor?.name||'none',key:manager?.activeKey||'none'};
  }
  function readEvidence(){try{const x=JSON.parse(localStorage.getItem(STORAGE)||'{}').evidence||[];return Array.isArray(x)?x:[]}catch{return[]}}
  function normalizeTarget(v){return String(v||'').replace(/^\/+|\/+$/g,'').toLowerCase()}
  function renderDebug(){
    const s=readSpatial(),items=canonicalItems.length?canonicalItems:readEvidence(),target=normalizeTarget(s.targetId==='?'?s.crumbs.join('/'):s.targetId)||'hand';
    const local=items.filter(i=>normalizeTarget(i.spatial_node_id||i.target)===target);
    const ancestors=target==='hand'?[]:items.filter(i=>{const t=normalizeTarget(i.spatial_node_id||i.target);return t&&target.startsWith(t+'/')});
    const root=items.filter(i=>normalizeTarget(i.spatial_node_id||i.target)==='hand');
    state.textContent=['CURRENT TARGET',`level:       ${s.level}`,`target:      ${s.target}`,`spatial_id:  ${target}`,`path:        ${s.crumbs.join(' > ')||'(root)'}`,`children:    ${s.children.join(' | ')||'(none)'}`,`renderer:    ${s.renderer}`,`active_key:  ${s.key}`,'',`LOCAL EVIDENCE:  ${local.length}`,`ROOT/HAND:       ${root.length}`,`PARENT/ANCESTOR: ${ancestors.length}`].join('\n');
    const cache=readEvidence().length;
    registry.textContent=['REGISTRY',`backend canonical: ${canonicalItems.length?'✓ '+canonicalItems.length+' item(s)':'… loading / unavailable'}`,`browser cache:     ${cache?'✓ '+cache+' item(s)':'— empty'}`,'source of truth:   /api/spatial/registry',`localization:      ${local.length?'✓ explicit on selected target':'— none on selected target'}`,`hand root:         ${root.length?'✓ '+root.length+' registered':'— none'}`].join('\n');
    const shown=(local.length?local:(target!=='hand'?root:items)).slice(0,20);
    evidence.textContent='EVIDENCE\n'+(shown.length?shown.map(i=>{const t=normalizeTarget(i.spatial_node_id||i.target)||'hand',localized=i.spatially_localized===false?'NO':'YES';return [`${i.filename||i.asset_id||i.id||'unnamed'}`,`  modality: ${i.modality||i.type||'—'}`,`  target:   ${t}`,`  localized:${localized}`,`  status:   ${i.attachment_status||(localized==='YES'?'attached':'registered')}`].join('\n')}).join('\n\n'):'  (no evidence)');
  }
  function event(message){const now=new Date().toLocaleTimeString();lines.push(`[${now}] ${message}`);while(lines.length>MAX)lines.shift();log.textContent=lines.join('\n');log.scrollTop=log.scrollHeight;renderDebug()}
  async function loadCanonical(){try{const r=await fetch('/api/spatial/registry?subject_id=own_cohort&timepoint=T0',{cache:'no-store'});if(!r.ok)throw new Error(`HTTP ${r.status}`);const p=await r.json();canonicalItems=Array.isArray(p.items)?p.items:[];event(`canonical registry loaded | ${canonicalItems.length} item(s)`)}catch(e){event(`canonical registry unavailable | ${e.message}`)}}
  function attach(){const m=window.spatialViewportManager;if(!m||wrapped)return!!m;const original=m.render.bind(m);m.render=()=>{const before=readSpatial();event(`render() BEFORE | ${before.level} ${before.target} ${before.key}`);const result=original();const after=readSpatial();event(`render() AFTER  | ${after.level} ${after.target} ${after.key}`);return result};wrapped=true;event(`debug attached to SpatialViewportManager (${m.active?.constructor?.name||'no renderer'})`);return true}
  function setOpen(open){panel.style.display=open?'block':'none';toggle.style.display=open?'none':'block';if(open){renderDebug();loadCanonical()}}
  toggle.onclick=()=>setOpen(true);close.onclick=()=>setOpen(false);clear.onclick=()=>{lines.length=0;log.textContent='';event('log cleared')};
  const observer=new MutationObserver(()=>event('spatial navigation DOM mutation detected'));
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true,characterData:true,attributes:true})});
  window.addEventListener('testhp:evidence-registry-synced',()=>{event('evidence registry sync event received');loadCanonical()},{passive:true});
  const timer=setInterval(()=>{attach();if(panel.style.display!=='none')renderDebug()},500);
  window.addEventListener('beforeunload',()=>{clearInterval(timer);observer.disconnect()},{once:true});
  event('debug panel initialized');
})();
