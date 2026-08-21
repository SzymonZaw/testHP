(() => {
  const boot = () => {
    const canvas = document.getElementById('twin-canvas');
    if (!canvas) return;
    let minimized = true, started = Date.now(), lastError = null;
    let lastNavigation = null, lastInteraction = null, lastStateRequest = null;
    let lastStatePayload = null, lastObservationsPayload = null, stateRequestSeq = 0;

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    if (host.parentElement !== document.body) document.body.appendChild(host);
    Object.assign(host.style,{position:'fixed',right:'16px',bottom:'16px',zIndex:'2147483647',width:'min(720px,calc(100vw - 32px))',pointerEvents:'auto',isolation:'isolate'});

    let toggle=document.getElementById('twin-debug-toggle');
    if(!toggle){toggle=document.createElement('button');toggle.id='twin-debug-toggle';toggle.type='button';host.appendChild(toggle);}
    Object.assign(toggle.style,{display:'block',padding:'8px 12px',borderRadius:'8px',border:'1px solid #4b746b',background:'#0b1514',color:'#9bd8c4',font:'800 11px ui-monospace,SFMono-Regular,Consolas,monospace',cursor:'pointer',pointerEvents:'auto'});

    let panel=document.getElementById('twin-debug-panel');
    if(!panel){panel=document.createElement('div');panel.id='twin-debug-panel';panel.innerHTML='<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><strong>TWIN VIEWPORT · DEBUG</strong><button id="twin-debug-close" type="button">MINIMIZE</button></div><pre id="twin-debug-runtime"></pre><pre id="twin-debug-state"></pre><pre id="twin-debug-evidence"></pre><pre id="twin-debug-errors"></pre>';host.appendChild(panel);}
    Object.assign(panel.style,{display:'none',marginTop:'6px',maxHeight:'760px',overflow:'auto',padding:'12px',boxSizing:'border-box',borderRadius:'10px',background:'rgba(5,12,13,.98)',border:'1px solid #4b746b',boxShadow:'0 12px 35px rgba(0,0,0,.55)',color:'#dcece6',font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',pointerEvents:'auto'});
    const runtime=document.getElementById('twin-debug-runtime'),state=document.getElementById('twin-debug-state'),evidence=document.getElementById('twin-debug-evidence'),errors=document.getElementById('twin-debug-errors');
    if(!runtime||!state||!evidence||!errors)return;

    const readState=()=>{
      const manager=window.spatialViewportManager,node=document.getElementById('spatial-node'),badge=document.getElementById('spatial-level-badge');
      const breadcrumb=[...document.querySelectorAll('#spatial-breadcrumb button')].map(x=>x.textContent.trim()).filter(Boolean);
      const children=[...document.querySelectorAll('#spatial-children .spatial-target')].map(x=>({label:x.querySelector('strong')?.textContent?.trim()||x.textContent.trim(),id:x.dataset?.spatialId||x.getAttribute('data-spatial-id')||null,disabled:!!x.disabled,connected:x.isConnected}));
      return {manager:!!manager,level:badge?.textContent?.trim()||'?',target:node?.querySelector('strong')?.textContent?.trim()||'?',path:breadcrumb.join(' > ')||'(root)',children,renderer:manager?.active?.constructor?.name||'none',activeKey:manager?.activeKey||'none',evidenceTarget:window.spatialEvidenceTarget||null,selectedSpatialNode:window.selectedSpatialNode||null};
    };
    const getSpatialId=detail=>{if(detail?.spatial_id)return String(detail.spatial_id);if(detail?.id)return String(detail.id);const s=readState();return typeof s.evidenceTarget==='string'&&s.evidenceTarget?s.evidenceTarget:'hand/palm';};
    const levelKey=v=>String(v||'?').toLowerCase().replace(/^anatomia\s+/,'').replace('tkanka','tissue').replace('komórkowe','cellular').replace('komórkowa','cellular').replace('molekularne','molecular').replace('makro','macro').replace('tissue field','tissue').replace('cell field','cellular');
    const parseCount=text=>Number(String(text||'').match(/\d+/)?.[0]||0);

    const refreshEvidenceDiagnostics=async detail=>{
      const spatialId=getSpatialId(detail),seq=++stateRequestSeq;
      const params=new URLSearchParams({subject_id:'own_cohort',timepoint:'T0',spatial_id:spatialId,include_descendants:'true'});
      const url=`/api/biological-state?${params.toString()}`,observationsUrl='/api/observations?subject_id=own_cohort&timepoint=T0&include_archived=false';
      const startedAt=performance.now();lastStateRequest={seq,spatialId,url,startedAt:new Date().toISOString()};
      try{
        const [sr,or]=await Promise.all([fetch(url,{cache:'no-store'}),fetch(observationsUrl,{cache:'no-store'})]);
        const st=await sr.text(),ot=await or.text();let sp=null,op=null;try{sp=JSON.parse(st);}catch(_){}try{op=JSON.parse(ot);}catch(_){}
        if(seq!==stateRequestSeq)return;lastStatePayload=sp;lastObservationsPayload=op;
        lastStateRequest={...lastStateRequest,completedAt:new Date().toISOString(),durationMs:Math.round(performance.now()-startedAt),http:sr.status,ok:sr.ok,observationsHttp:or.status,observationsOk:or.ok};
      }catch(error){if(seq!==stateRequestSeq)return;lastStatePayload=null;lastObservationsPayload=null;lastStateRequest={...lastStateRequest,completedAt:new Date().toISOString(),durationMs:Math.round(performance.now()-startedAt),error:error?.message||String(error)};}
      render();
    };

    const render=()=>{
      if(minimized)return;
      const s=readState(),payload=lastStatePayload||{},summary=payload.summary||{},apiState=payload.state||{};
      const observations=Array.isArray(lastObservationsPayload?.observations)?lastObservationsPayload.observations:[];
      const requested=s.evidenceTarget||lastStateRequest?.spatialId||null;
      const normalize=v=>typeof v==='string'?v.replace(/^\/+|\/+$/g,''):'';
      const selected=normalize(requested);
      const rows=observations.map(o=>({id:String(o.id||''),spatial:normalize(o.spatial_id),level:o.biological_level||'?',levelKey:levelKey(o.biological_level),evidence:o.evidence_id?String(o.evidence_id):null,subject:o.subject_id||'?',timepoint:o.timepoint||o.timepoint_id||'?',archived:!!o.archived,value:o.value,modality:o.modality||null,source:o.source||null}));
      const direct=rows.filter(o=>o.spatial===selected),descendants=selected?rows.filter(o=>o.spatial.startsWith(selected+'/')):[];
      const ancestors=selected?selected.split('/').map((_,i)=>selected.split('/').slice(0,i+1).join('/')):[];
      const scoped=direct.concat(descendants),byLocation={},byLevel={};rows.forEach(o=>{byLocation[o.spatial]=(byLocation[o.spatial]||0)+1;byLevel[o.level]=(byLevel[o.level]||0)+1;});
      const scopedByLevel={};scoped.forEach(o=>{scopedByLevel[o.level]=(scopedByLevel[o.level]||0)+1;});
      const apiEvidence=new Set((apiState.evidence_ids||[]).map(String)),apiObs=rows.filter(o=>o.evidence&&apiEvidence.has(o.evidence)),expected=scoped.length;
      const inspector={title:document.getElementById('region-title')?.textContent?.trim()||'?',context:document.getElementById('region-context')?.textContent?.trim()||'?',counts:{macro:document.getElementById('macro-state')?.textContent?.trim()||'',tissue:document.getElementById('tissue-state')?.textContent?.trim()||'',cellular:document.getElementById('cellular-state')?.textContent?.trim()||'',molecular:document.getElementById('molecular-state')?.textContent?.trim()||''},evidenceRows:[...document.querySelectorAll('.evidence-row')].map(r=>({layer:r.querySelector('.layer')?.textContent?.trim()||'?',title:r.querySelector('strong')?.textContent?.trim()||'?',detail:r.querySelector('p')?.textContent?.trim()||''})),interpretationCount:document.getElementById('evidence-count')?.textContent?.trim()||null};
      const spatialChildren=s.children,childIds=spatialChildren.map(c=>c.id).filter(Boolean),childObs=rows.filter(o=>childIds.includes(o.spatial)),childSubtreeObs=rows.filter(o=>childIds.some(id=>o.spatial===id||o.spatial.startsWith(id+'/')));

      const inspectorLayerCounts={macro:parseCount(inspector.counts.macro),tissue:parseCount(inspector.counts.tissue),cellular:parseCount(inspector.counts.cellular),molecular:parseCount(inspector.counts.molecular)};
      const layerDiagnostics=['macro','tissue','cellular','molecular'].map(layer=>{const raw=scoped.filter(o=>o.levelKey===layer),directLayer=direct.filter(o=>o.levelKey===layer),descLayer=descendants.filter(o=>o.levelKey===layer),locations={};raw.forEach(o=>{locations[o.spatial]=(locations[o.spatial]||0)+1;});const distinctLocations=Object.keys(locations).length;return {layer,raw:raw.length,direct:directLayer.length,descendants:descLayer.length,inspector:inspectorLayerCounts[layer],locations,distinctLocations,missingSpatial:raw.filter(o=>!o.spatial).length};});
      const sameLayerCollisions=layerDiagnostics.filter(x=>x.raw>0&&x.distinctLocations>1).map(x=>`${x.layer}: ${x.raw} records across ${x.distinctLocations} spatial nodes`);
      const unscopedSameLayer=layerDiagnostics.filter(x=>x.inspector>0&&x.raw===0).map(x=>`${x.layer}: inspector=${x.inspector}, scoped observations=0`);
      const inspectorMismatch=layerDiagnostics.filter(x=>x.inspector!==x.raw).map(x=>`${x.layer}: inspector=${x.inspector}, scoped observations=${x.raw}`);
      const sameLevelSameLocation=layerDiagnostics.map(x=>{const dup=Object.entries(x.locations).filter(([,n])=>n>1);return dup.length?`${x.layer}: ${dup.map(([id,n])=>`${id}×${n}`).join(', ')}`:null;}).filter(Boolean);
      const consistency=[];
      consistency.push(`selected id == API scope: ${selected&&normalize(summary.scope||lastStateRequest?.spatialId)===selected?'YES':'NO'}`);
      consistency.push(`global observations in selected subtree: ${expected}`);
      consistency.push(`global observations direct: ${direct.length}`);
      consistency.push(`global observations in descendants: ${descendants.length}`);
      consistency.push(`API evidence count: ${apiState.evidence_count??0}`);
      consistency.push(`API evidence-linked observations: ${apiObs.length}`);
      consistency.push(`inspector evidence rows: ${inspector.evidenceRows.length}`);
      consistency.push(`nav child nodes: ${spatialChildren.length}`);
      consistency.push(`observations on immediate child nodes: ${childObs.length}`);
      consistency.push(`observations in child subtrees: ${childSubtreeObs.length}`);
      consistency.push(`INTERPRETATION/UI vs API candidate: ${inspector.interpretationCount!==null&&parseCount(inspector.interpretationCount)!==expected?'YES':'NO'}`);
      consistency.push(`same-layer distribution issue: ${sameLayerCollisions.length||unscopedSameLayer.length||inspectorMismatch.length?'YES':'NO'}`);

      const levelLines=Object.keys(byLevel).sort().map(k=>`  ${k} = ${byLevel[k]}`),locationLines=Object.keys(byLocation).sort().map(id=>`  ${id} = ${byLocation[id]}`),hierarchyLines=spatialChildren.map(c=>`  ${c.label} | id=${c.id||'?'} | disabled=${c.disabled} | connected=${c.connected}`);
      const rawObs=scoped.map(o=>`${o.id} | spatial=${o.spatial||'(none)'} | level=${o.level} | evidence=${o.evidence||'(none)'} | modality=${o.modality||'?'} | source=${o.source||'?'} | time=${o.timepoint}`).join('\n')||'(none)';
      const layerLines=layerDiagnostics.map(x=>`  ${x.layer}: inspector=${x.inspector} | scoped=${x.raw} | direct=${x.direct} | descendants=${x.descendants} | spatial_nodes=${x.distinctLocations} | missing_spatial=${x.missingSpatial}`).join('\n')||'  (none)';
      const distributionLines=layerDiagnostics.map(x=>{const parts=Object.entries(x.locations).map(([id,n])=>`${id}=${n}`);return `  ${x.layer}: ${parts.join(' · ')||'(none)'}`;}).join('\n')||'  (none)';
      const hint=apiState.evidence_count===0&&expected>0?'OBSERVATIONS EXIST IN THE SPATIAL SUBTREE BUT API RETURNS ZERO EVIDENCE. Check evidence_id creation/linking and backend resolver.':inspectorMismatch.length?'INSPECTOR LAYER COUNTS DO NOT MATCH THE SELECTED SPATIAL SCOPE. Inspector may be counting region-level records instead of records for this node/subtree.':sameLayerCollisions.length?'MULTIPLE RECORDS OF THE SAME BIOLOGICAL LEVEL EXIST IN DIFFERENT SPATIAL NODES. Verify that Inspector preserves spatial_id and does not collapse same-level records.':unscopedSameLayer.length?'INSPECTOR SHOWS A LAYER COUNT WITHOUT OBSERVATIONS IN THE SELECTED SCOPE. Check whether the layer count is sourced from a broader region.':sameLevelSameLocation.length?'MULTIPLE SAME-LAYER RECORDS SHARE THE SAME spatial_id. This may be valid, but records must remain distinct by observation/evidence id.':'No immediate same-layer mismatch detected.';

      runtime.textContent=['RUNTIME',`status:       ${window.__testhpTwinReady?'READY':'INITIALIZING'}`,`init age:     ${Date.now()-started} ms`,`manager:      ${s.manager?'present':'missing'}`,`canvas:       ${canvas.width}×${canvas.height}`,`last API:     ${lastStateRequest?`${lastStateRequest.http??'—'} · ${lastStateRequest.durationMs??'—'} ms`:'(none)'}`].join('\n');
      state.textContent=['','SPATIAL STATE',`level:        ${s.level}`,`target:       ${s.target}`,`path:         ${s.path}`,`evidence id:  ${requested?JSON.stringify(requested):'(none)'}`,`selected node: ${s.selectedSpatialNode?JSON.stringify(s.selectedSpatialNode):'(none)'}`,`children:     ${s.children.map(c=>`${c.label}[${c.id||'?'}${c.disabled?',disabled':''}]`).join(' | ')||'(none)'}`,`renderer:     ${s.renderer}`,`active key:   ${s.activeKey}`,'','LAST NAVIGATION',lastNavigation?JSON.stringify(lastNavigation,null,2):'(none)','','HIERARCHY / SCOPE CHECK',`normalized scope: ${selected||'(none)'}`,`ancestor chain: ${ancestors.join(' > ')||'(none)'}`,'navigation children:',hierarchyLines.join('\n')||'  (none)','raw observation locations:',locationLines.join('\n')||'  (none)','observations by biological level:',levelLines.join('\n')||'  (none)'].join('\n');
      evidence.textContent=['','BIOLOGICAL STATE · EVIDENCE SCOPE',`request:      ${lastStateRequest?.url||'(none)'}`,`include desc: ${summary.include_descendants===true?'YES':'NO'}`,`scope:        ${summary.scope||requested||'(none)'}`,`API status:   ${lastStateRequest?.ok?'OK':lastStateRequest?'FAILED':'NOT RUN'}`,`state count:  ${apiState.evidence_count??'—'}`,`observation_count: ${summary.observations??apiState.observation_count??'—'}`,`direct:       ${summary.direct_evidence??'—'}`,`descendants:  ${summary.descendant_evidence??'—'}`,`availability: ${apiState.availability??'—'}`,`confidence:   ${apiState.confidence?.value??'—'}`,`evidence ids: ${(apiState.evidence_ids||[]).join(' | ')||'(none)'}`,`by location:  ${Array.isArray(summary.by_location)&&summary.by_location.length?summary.by_location.map(x=>`${x.name||x.spatial_id}=${x.count}`).join(' · '):'(none)'}`,'','RESOLUTION CONSISTENCY',...consistency,'','SAME-LAYER RESOLUTION','Inspector layer count vs selected scope:',layerLines,'','Records by same-layer spatial node:',distributionLines,'','Same-layer duplicates on one spatial node:',sameLevelSameLocation.join('\n')||'(none)','',sameLayerCollisions.length?'Same biological level across multiple nodes:\n'+sameLayerCollisions.map(x=>'  '+x).join('\n'):'Same biological level across multiple nodes: (none)','',inspectorMismatch.length?'Inspector/scoped mismatches:\n'+inspectorMismatch.map(x=>'  '+x).join('\n'):'Inspector/scoped mismatches: (none)','',unscopedSameLayer.length?'Inspector-only layer counts:\n'+unscopedSameLayer.map(x=>'  '+x).join('\n'):'Inspector-only layer counts: (none)','', 'RAW OBSERVATION MATCHING',`direct:       ${direct.length}`,`descendants:  ${descendants.length}`,`total subtree: ${expected}`,rawObs,'','API-LINKED OBSERVATIONS',apiObs.map(o=>`${o.id} | spatial=${o.spatial} | level=${o.level} | evidence=${o.evidence}`).join('\n')||'(none)','','INSPECTOR DOM SNAPSHOT',`region title: ${inspector.title}`,`context:      ${inspector.context}`,`interpretation count UI: ${inspector.interpretationCount??'(not found)'}`,`layer states: ${JSON.stringify(inspector.counts)}`,inspector.evidenceRows.map(r=>`  ${r.layer} | ${r.title} | ${r.detail}`).join('\n')||'  (none)','','DIAGNOSTIC HINT',hint].join('\n');
      errors.textContent=['','ERROR / INTERACTION',`last error:   ${lastError||'(none)'}`,`last input:   ${lastInteraction?JSON.stringify(lastInteraction):'(none)'}`,`last request: ${lastStateRequest?JSON.stringify(lastStateRequest,null,2):'(none)'}`].join('\n');
    };

    window.addEventListener('error',e=>{lastError=`${e.message||'unknown'} | ${e.filename||''}:${e.lineno||''}`;render();});
    window.addEventListener('unhandledrejection',e=>{lastError=String(e.reason?.stack||e.reason||'Unhandled promise rejection');render();});
    window.addEventListener('testhp:twin-error',e=>{lastError=JSON.stringify(e.detail||{});render();});
    ['testhp:spatial-layer-changed','testhp:spatial-change','testhp:viewport-rendered'].forEach(name=>window.addEventListener(name,e=>{lastNavigation=e.detail||{};refreshEvidenceDiagnostics(e.detail||{});}));
    canvas.addEventListener('click',e=>{lastInteraction={type:'canvas click',x:Math.round(e.clientX),y:Math.round(e.clientY)};render();},{passive:true});
    document.addEventListener('click',e=>{const target=e.target?.closest?.('.spatial-target,#spatial-breadcrumb button');if(!target)return;lastInteraction={type:'spatial navigation click',label:target.textContent?.trim()||'',spatialId:target.dataset?.spatialId||target.getAttribute('data-spatial-id')||null,disabled:!!target.disabled,time:new Date().toISOString()};setTimeout(()=>refreshEvidenceDiagnostics(readState()),0);},true);
    const setMinimized=value=>{minimized=value;panel.style.display=minimized?'none':'block';toggle.textContent=minimized?'TWIN VIEWPORT DEBUG · ROZWIŃ':'TWIN VIEWPORT DEBUG · ZWIŃ';if(!minimized){render();refreshEvidenceDiagnostics(readState());}};
    toggle.onclick=()=>setMinimized(!minimized);document.getElementById('twin-debug-close')?.addEventListener('click',()=>setMinimized(true));setMinimized(true);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
