(() => {
  'use strict';

  const LEVELS = ['macro', 'tissue', 'cellular', 'molecular'];
  let startedAt = Date.now();
  let minimized = true;
  let booted = false;
  let rendering = false;
  let lastError = null;
  let lastNavigation = null;
  let lastInteraction = null;
  let lastRequest = null;
  let lastStatePayload = null;
  let lastObservationsPayload = null;
  let requestSeq = 0;

  const normalize = value => typeof value === 'string' ? value.replace(/^\/+|\/+$/g, '') : '';
  const parseCount = value => Number(String(value || '').match(/\d+/)?.[0] || 0);
  const levelKey = value => {
    const v = String(value || '').toLowerCase();
    if (v.includes('molecular') || v.includes('molekular')) return 'molecular';
    if (v.includes('cellular') || v.includes('komór')) return 'cellular';
    if (v.includes('tissue') || v.includes('tkank')) return 'tissue';
    if (v.includes('macro') || v.includes('makro')) return 'macro';
    return v || '?';
  };

  function getState() {
    const node = document.getElementById('spatial-node');
    const badge = document.getElementById('spatial-level-badge');
    const breadcrumb = [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
    const children = [...document.querySelectorAll('#spatial-children .spatial-target')].map(x => ({
      id: normalize(x.dataset?.spatialId || x.getAttribute('data-spatial-id') || ''),
      label: x.querySelector('strong')?.textContent?.trim() || x.textContent.trim(),
      level: x.dataset?.spatialLevel || x.getAttribute('data-spatial-level') || '?',
      disabled: !!x.disabled,
      connected: x.isConnected
    }));
    const selected = window.selectedSpatialNode;
    return {
      manager: !!window.spatialViewportManager,
      level: badge?.textContent?.trim() || '?',
      target: node?.querySelector('strong')?.textContent?.trim() || '?',
      path: breadcrumb.join(' > ') || '(root)',
      children,
      selectedId: normalize(selected?.spatial_id || selected?.id || window.spatialEvidenceTarget || ''),
      renderer: window.spatialViewportManager?.active?.constructor?.name || 'none',
      activeKey: window.spatialViewportManager?.activeKey || 'none'
    };
  }

  function ensureHost() {
    if (!document.body) return null;
    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) { host = document.createElement('section'); host.id = 'twin-viewport-debug-host'; document.body.appendChild(host); }
    Object.assign(host.style, { position:'fixed', right:'16px', bottom:'16px', zIndex:'2147483647', width:'min(820px, calc(100vw - 32px))', maxWidth:'820px', display:'block', visibility:'visible', opacity:'1', pointerEvents:'auto', isolation:'isolate' });

    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) { toggle=document.createElement('button'); toggle.id='twin-debug-toggle'; toggle.type='button'; host.appendChild(toggle); }
    toggle.textContent=minimized?'TWIN VIEWPORT · DEBUG':'TWIN VIEWPORT · DEBUG · MINIMIZE';
    Object.assign(toggle.style,{display:'block',visibility:'visible',opacity:'1',position:'relative',zIndex:'2147483647',padding:'9px 13px',borderRadius:'8px',border:'1px solid #4b746b',background:'#0b1514',color:'#9bd8c4',font:'800 11px ui-monospace,SFMono-Regular,Consolas,monospace',cursor:'pointer',pointerEvents:'auto',boxSizing:'border-box'});
    if (!toggle.dataset.bound) { toggle.addEventListener('click',()=>{ minimized=!minimized; ensureHost(); render(); }); toggle.dataset.bound='1'; }

    let panel=document.getElementById('twin-debug-panel');
    if (!panel) {
      panel=document.createElement('div'); panel.id='twin-debug-panel';
      panel.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;position:sticky;top:0;background:#050c0d;padding-bottom:8px"><strong>TWIN VIEWPORT · DEBUG</strong><button id="twin-debug-close" type="button">MINIMIZE</button></div><pre id="twin-debug-runtime"></pre><pre id="twin-debug-spatial"></pre><pre id="twin-debug-resolution"></pre><pre id="twin-debug-evidence"></pre><pre id="twin-debug-modules"></pre><pre id="twin-debug-errors"></pre>';
      host.appendChild(panel);
    }
    Object.assign(panel.style,{display:minimized?'none':'block',visibility:'visible',opacity:'1',marginTop:'6px',maxHeight:'calc(100vh - 70px)',overflow:'auto',padding:'12px',boxSizing:'border-box',borderRadius:'10px',background:'rgba(5,12,13,.98)',border:'1px solid #4b746b',boxShadow:'0 12px 35px rgba(0,0,0,.55)',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',pointerEvents:'auto'});
    const close=document.getElementById('twin-debug-close');
    if (close && !close.dataset.bound) { close.addEventListener('click',()=>{ minimized=true; ensureHost(); render(); }); close.dataset.bound='1'; }
    return host;
  }

  async function refresh(detail) {
    const ui=getState();
    const spatialId=normalize(detail?.spatial_id||detail?.id||ui.selectedId||'hand');
    const seq=++requestSeq;
    const params=new URLSearchParams({subject_id:'own_cohort',timepoint:'T0',spatial_id:spatialId,include_descendants:'true'});
    const stateUrl=`/api/biological-state?${params.toString()}`;
    const observationsUrl='/api/observations?subject_id=own_cohort&timepoint=T0&include_archived=false';
    const started=performance.now();
    lastRequest={seq,spatialId,url:stateUrl,startedAt:new Date().toISOString()};
    try {
      const [sr,or]=await Promise.all([fetch(stateUrl,{cache:'no-store'}),fetch(observationsUrl,{cache:'no-store'})]);
      const [st,ot]=await Promise.all([sr.text(),or.text()]);
      if(seq!==requestSeq)return;
      try{lastStatePayload=JSON.parse(st);}catch(_){lastStatePayload=null;}
      try{lastObservationsPayload=JSON.parse(ot);}catch(_){lastObservationsPayload=null;}
      lastRequest={...lastRequest,completedAt:new Date().toISOString(),durationMs:Math.round(performance.now()-started),http:sr.status,ok:sr.ok,observationsHttp:or.status,observationsOk:or.ok};
    }catch(error){
      if(seq!==requestSeq)return;
      lastError=error?.message||String(error);
      lastRequest={...lastRequest,completedAt:new Date().toISOString(),durationMs:Math.round(performance.now()-started),error:lastError};
    }
    if(!minimized)render();
  }

  function render() {
    if(rendering)return;
    rendering=true;
    try {
      const host=ensureHost();
      if(!host||minimized)return;
      const ui=getState();
      const payload=lastStatePayload||{};
      const summary=payload.summary||{};
      const apiState=payload.state||{};
      const raw=Array.isArray(lastObservationsPayload?.observations)?lastObservationsPayload.observations:[];
      const selected=normalize(lastRequest?.spatialId||ui.selectedId||'');
      const observations=raw.map(item=>({id:String(item.id||''),spatial:normalize(item.spatial_id),level:item.biological_level||'?',levelKey:levelKey(item.biological_level),evidence:item.evidence_id?String(item.evidence_id):null,subject:item.subject_id||'?',timepoint:item.timepoint||item.timepoint_id||'?',archived:!!item.archived}));
      const direct=observations.filter(o=>o.spatial===selected);
      const descendants=selected?observations.filter(o=>o.spatial.startsWith(`${selected}/`)):[];
      const scoped=direct.concat(descendants);
      const ancestors=selected?selected.split('/').map((_,i)=>selected.split('/').slice(0,i+1).join('/')):[];
      const siblings=observations.filter(o=>{if(!selected||!o.spatial||o.spatial===selected)return false;const a=o.spatial.split('/'),b=selected.split('/');return a.length===b.length&&a.slice(0,-1).join('/')===b.slice(0,-1).join('/');});
      const byLocation={},byLevel={},scopedByLevel={};
      observations.forEach(o=>{const l=o.spatial||'(missing spatial_id)';byLocation[l]=(byLocation[l]||0)+1;byLevel[o.levelKey]=(byLevel[o.levelKey]||0)+1;});
      scoped.forEach(o=>{scopedByLevel[o.levelKey]=(scopedByLevel[o.levelKey]||0)+1;});
      const apiEvidenceIds=new Set((apiState.evidence_ids||[]).map(String));
      const linked=scoped.filter(o=>o.evidence&&apiEvidenceIds.has(o.evidence));
      const inspectorCounts=Object.fromEntries(LEVELS.map(level=>[level,parseCount(document.getElementById(`${level}-state`)?.textContent)]));
      const interpretationText=document.getElementById('evidence-count')?.textContent?.trim()||null;
      const interpretationCount=interpretationText===null?null:parseCount(interpretationText);
      const layerDiagnostics=LEVELS.map(level=>{const list=scoped.filter(o=>o.levelKey===level),locations={};list.forEach(o=>{const l=o.spatial||'(missing spatial_id)';locations[l]=(locations[l]||0)+1;});return{level,inspector:inspectorCounts[level],scoped:list.length,direct:direct.filter(o=>o.levelKey===level).length,descendants:descendants.filter(o=>o.levelKey===level).length,locations,spatialNodes:Object.keys(locations).length,missingSpatial:list.filter(o=>!o.spatial).length};});
      const resolution=observations.map(o=>{let relation='OUTSIDE';if(o.spatial===selected)relation='DIRECT';else if(selected&&o.spatial.startsWith(`${selected}/`))relation='DESCENDANT';else if(siblings.some(s=>s.id===o.id))relation='SIBLING';else if(ancestors.includes(o.spatial))relation='ANCESTOR';const subjectMatch=o.subject==='own_cohort',timeMatch=o.timepoint==='T0',included=(relation==='DIRECT'||relation==='DESCENDANT')&&subjectMatch&&timeMatch&&!o.archived;return{...o,relation,subjectMatch,timeMatch,included};});
      const scopes={model:ui.selectedId,navigation:ui.selectedId,inspector:selected,observations:selected,interpretation:selected,api:normalize(summary.scope||lastRequest?.spatialId)};
      const values=Object.values(scopes).filter(Boolean);const scopeAgree=values.length>0&&values.every(x=>x===selected);
      const observationCount=Number(summary.observation_count??summary.observations??apiState.observation_count??scoped.length);
      const evidenceCount=Number(apiState.evidence_count??summary.explicit_evidence??0);
      const stateCount=Number(apiState.state_count??apiState.evidence_count??0);
      const issues=[];
      if(!scopeAgree)issues.push('MODULE_SCOPE_MISMATCH');
      if(observationCount!==scoped.length)issues.push('API_OBSERVATION_COUNT_MISMATCH');
      if(evidenceCount!==linked.length)issues.push('API_EVIDENCE_LINK_MISMATCH');
      if(interpretationCount!==null&&interpretationCount!==observationCount)issues.push('INTERPRETATION_COUNT_MISMATCH');
      if(ui.children.some(c=>!c.id))issues.push('NAVIGATION_CHILD_WITHOUT_SPATIAL_ID');
      if(layerDiagnostics.some(x=>x.inspector!==x.scoped))issues.push('INSPECTOR_SCOPE_MISMATCH');

      const spatialText=['SPATIAL CONTRACT','────────────────────────────────────────',`selected id:       ${selected||'(none)'}`,`label:              ${ui.target}`,`level:              ${ui.level}`,`path:               ${ui.path}`,`parent:             ${selected.includes('/')?selected.split('/').slice(0,-1).join('/')||'(root)':'(root)'}`,'','CHILDREN',...(ui.children.length?ui.children.map(c=>`  ${c.label} | id=${c.id||'?'} | level=${c.level} | disabled=${c.disabled} | connected=${c.connected}`):['  (none)']),'','HIERARCHY INTEGRITY',`  children without id: ${ui.children.filter(c=>!c.id).length}`,'  cycles: runtime check unavailable','  orphan nodes: runtime check unavailable','','NAVIGATION CONTRACT',`  invalid fallback candidate: ${ui.children.some(c=>/regional field/i.test(c.label))?'Regional field':'(none)'}`].join('\n');
      const resolutionText=['OBSERVATION RESOLUTION','────────────────────────────────────────',`selected spatial: ${selected||'(none)'}`,`direct:          ${direct.length}`,`descendants:     ${descendants.length}`,`subtree total:   ${scoped.length}`,`siblings:        ${siblings.length}`,`ancestors:       ${observations.filter(o=>ancestors.slice(0,-1).includes(o.spatial)).length}`,'','RAW OBSERVATION DECISIONS',...(resolution.length?resolution.map(o=>`  ${o.id} | spatial=${o.spatial||'(none)'} | level=${o.level} | ${o.relation} | subject=${o.subjectMatch?'MATCH':'MISS'} | time=${o.timeMatch?'MATCH':'MISS'} | included=${o.included?'YES':'NO'} | evidence=${o.evidence||'(none)'}`):['  (none)']),'','SAME-LAYER RESOLUTION','Inspector vs selected scope:',...layerDiagnostics.map(x=>`  ${x.level}: inspector=${x.inspector} | scoped=${x.scoped} | direct=${x.direct} | descendants=${x.descendants} | spatial_nodes=${x.spatialNodes} | missing_spatial=${x.missingSpatial}`),'','Records by same-layer spatial node:',...layerDiagnostics.map(x=>`  ${x.level}: ${Object.entries(x.locations).map(([id,n])=>`${id}=${n}`).join(' · ')||'(none)'}`)].join('\n');
      const evidenceText=['BIOLOGICAL STATE · EVIDENCE SCOPE','────────────────────────────────────────',`request:          ${lastRequest?.url||'(none)'}`,`API status:       ${lastRequest?.ok?'OK':lastRequest?'FAILED':'NOT RUN'}`,`scope:            ${summary.scope||selected||'(none)'}`,`include desc:     ${summary.include_descendants===true?'YES':'NO'}`,`state count:      ${stateCount}`,`observation_count: ${observationCount}`,`evidence count:   ${evidenceCount}`,`linked scoped:    ${linked.length}`,`unlinked scoped:  ${scoped.length-linked.length}`,`availability:     ${apiState.availability||'—'}`,`confidence:       ${apiState.confidence?.value||'—'}`,'','OBSERVATION / EVIDENCE SEPARATION',`  observations in scope: ${scoped.length}`,`  with evidence:         ${linked.length}`,`  without evidence:      ${scoped.length-linked.length}`,`  biological data:        ${scoped.length?'PRESENT':'ABSENT'}`,`  evidence:               ${linked.length?'PRESENT':'ABSENT'}`,`  validated state:        ${stateCount?'PRESENT':'NOT ESTABLISHED'}`,'','INTERPRETATION SEMANTICS',`  UI "Dane":             ${interpretationCount??'(not found)'}`,`  expected observation:  ${observationCount}`,`  evidence:               ${evidenceCount}`,`  result:                 ${interpretationCount===null?'UI FIELD NOT FOUND':interpretationCount===observationCount?'PASS':'FAIL'}`,'','RAW OBSERVATION LOCATIONS',...Object.entries(byLocation).sort().map(([id,n])=>`  ${id} = ${n}`),'','GLOBAL BIOLOGICAL LEVELS',...Object.entries(byLevel).sort().map(([id,n])=>`  ${id} = ${n}`),'','SCOPED BIOLOGICAL LEVELS',...LEVELS.map(level=>`  ${level} = ${scopedByLevel[level]||0}`)].join('\n');
      const modulesText=['MODULE AGREEMENT','────────────────────────────────────────',...Object.entries(scopes).map(([name,value])=>`  ${name.padEnd(16)} ${value||'(none)'}`),'',`SPATIAL SCOPE:       ${scopeAgree?'PASS':'FAIL'}`,`OBSERVATION SCOPE:   ${observationCount===scoped.length?'PASS':'FAIL'}`,`EVIDENCE SEPARATION: ${evidenceCount===linked.length?'PASS':'FAIL'}`,`INTERPRETATION COUNT: ${interpretationCount===null?'UNKNOWN':interpretationCount===observationCount?'PASS':'FAIL'}`,`NAVIGATION IDS:      ${ui.children.every(c=>!!c.id)?'PASS':'FAIL'}`,`SAME-LAYER SCOPE:    ${layerDiagnostics.every(x=>x.inspector===x.scoped)?'PASS':'FAIL'}`,'','DIAGNOSTIC HINT',issues.includes('INTERPRETATION_COUNT_MISMATCH')?'INTERPRETATION UI is not using observation_count.':issues.includes('INSPECTOR_SCOPE_MISMATCH')?'INSPECTOR layer count differs from selected spatial scope.':issues.includes('MODULE_SCOPE_MISMATCH')?'Modules disagree about selected spatial_id.':issues.includes('NAVIGATION_CHILD_WITHOUT_SPATIAL_ID')?'Navigation exposes a child without a canonical spatial_id.':evidenceCount===0&&scoped.length>0?'Observations exist but no evidence is linked. This is not the same as no data.':'No immediate semantic mismatch detected.','',`OVERALL: ${issues.length?issues.join(' | '):'NO DETECTED ISSUES'}`].join('\n');

      document.getElementById('twin-debug-runtime').textContent=['RUNTIME',`status:       ${window.__testhpTwinReady?'READY':'INITIALIZING'}`,`init age:     ${Date.now()-startedAt} ms`,`manager:      ${ui.manager?'present':'missing'}`,`canvas:       ${document.getElementById('twin-canvas')?.width||0}×${document.getElementById('twin-canvas')?.height||0}`,`last API:     ${lastRequest?`${lastRequest.http??'—'} · ${lastRequest.durationMs??'—'} ms`:'(none)'}`,`last input:   ${lastInteraction?JSON.stringify(lastInteraction):'(none)'}`].join('\n');
      document.getElementById('twin-debug-spatial').textContent=spatialText;
      document.getElementById('twin-debug-resolution').textContent=resolutionText;
      document.getElementById('twin-debug-evidence').textContent=evidenceText;
      document.getElementById('twin-debug-modules').textContent=modulesText;
      document.getElementById('twin-debug-errors').textContent=['ERROR / INTERACTION',`last error: ${lastError||'(none)'}`,`last navigation: ${lastNavigation?JSON.stringify(lastNavigation,null,2):'(none)'}`].join('\n');
    } finally { rendering=false; }
  }

  function boot() {
    if(booted||!document.getElementById('twin-canvas'))return;
    booted=true;startedAt=Date.now();ensureHost();render();refresh();
    ['testhp:spatial-navigation','testhp:spatial-scope-consistency-updated','testhp:observation-created','testhp:observation-updated'].forEach(eventName=>window.addEventListener(eventName,event=>{lastNavigation=event?.detail||{type:eventName};lastInteraction={type:eventName,detail:event?.detail||null};refresh(event?.detail);}));
    window.addEventListener('error',event=>{lastError=event?.error?.message||event?.message||'window error';if(!minimized)render();});
    window.addEventListener('unhandledrejection',event=>{lastError=event?.reason?.message||String(event?.reason||'unhandled rejection');if(!minimized)render();});
    document.addEventListener('click',event=>{const target=event.target?.closest?.('#spatial-children .spatial-target, #spatial-breadcrumb button');if(!target)return;lastInteraction={type:'navigation click',label:target.textContent?.trim()||'',spatialId:normalize(target.dataset?.spatialId||target.getAttribute('data-spatial-id')||'')};setTimeout(()=>refresh({spatial_id:lastInteraction.spatialId}),80);},true);
    setInterval(()=>{ensureHost();},2000);
  }

  const wait=()=>{if(document.body)boot();if(!booted)setTimeout(wait,250);};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wait,{once:true});else wait();
})();