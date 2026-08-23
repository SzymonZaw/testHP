(() => {
  const start = () => {
    const panel = document.getElementById('twin-debug-panel');
    if (!panel || document.getElementById('hand-surface-debug-flow')) return false;

    const box = document.createElement('section');
    box.id = 'hand-surface-debug-flow';
    box.style.cssText = 'margin:12px 0;padding:12px;border:1px solid #52647a;border-radius:10px;background:#0d1420;color:#dbe7f5;font:12px/1.45 system-ui,sans-serif;';
    box.innerHTML = '<div style="font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">HAND SURFACE · DEBUG FLOW</div><div id="hsd-target" style="margin-bottom:10px"></div><div id="hsd-flow" style="display:grid;gap:6px"></div><pre id="hsd-details" style="white-space:pre-wrap;margin:10px 0 0;color:#aebed0;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace"></pre><details id="hsd-chain" style="margin-top:10px"><summary style="cursor:pointer;color:#9fc4e8;font-weight:700">TARGET CHAIN / PROVENANCE</summary><pre id="hsd-chain-body" style="white-space:pre-wrap;margin:8px 0 0;color:#aebed0;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace"></pre></details><details id="hsd-registry" style="margin-top:10px"><summary style="cursor:pointer;color:#9fc4e8;font-weight:700">REGISTRY / CACHE MISMATCH DIAGNOSTICS</summary><pre id="hsd-registry-body" style="white-space:pre-wrap;margin:8px 0 0;color:#aebed0;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace"></pre></details>';
    panel.appendChild(box);

    const esc = v => String(v ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
    const normalize = v => String(v ?? '').trim().replace(/^\/+|\/+$/g, '');
    const safe = v => { try { return JSON.stringify(v, null, 2); } catch { return String(v); } };
    const hash = value => {
      const s = String(value ?? ''); let h = 2166136261;
      for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
      return ('00000000' + (h >>> 0).toString(16)).slice(-8);
    };
    const first = (obj, keys) => { for (const k of keys) if (obj && obj[k] != null && obj[k] !== '') return obj[k]; return null; };
    const splitPath = value => normalize(value).split('/').filter(Boolean);
    const pathDiff = (expected, actual) => {
      const a = splitPath(expected), b = splitPath(actual), max = Math.max(a.length, b.length), out = [];
      for (let i = 0; i < max; i++) if (a[i] !== b[i]) out.push({ index:i, expected:a[i] ?? 'MISSING', actual:b[i] ?? 'MISSING' });
      return out;
    };
    const relation = (expected, actual) => {
      const e = normalize(expected), a = normalize(actual);
      if (!e || !a) return 'MISSING';
      if (e === a) return 'EXACT';
      if (e.startsWith(a + '/')) return 'EXPECTED_IS_DESCENDANT';
      if (a.startsWith(e + '/')) return 'ACTUAL_IS_DESCENDANT';
      const ep = splitPath(e), ap = splitPath(a), common = ep.reduce((n, x, i) => n + (x === ap[i] ? 1 : 0), 0);
      return common ? `SHARED_PREFIX_${common}/${Math.max(ep.length, ap.length)}` : 'UNRELATED';
    };

    const managerSnapshot = () => {
      const m = window.spatialViewportManager, s = m?.state || {}, active = m?.active || {};
      return {
        activeKey:m?.activeKey||null, activeLayer:m?.activeLayer||null,
        stateSpatialId:first(s,['spatial_id','spatialId','spatialTarget']),
        stateTarget:typeof s?.target==='object' ? first(s.target,['spatial_node_id','spatial_id','spatialId','id','target']) : (s?.target||null),
        activeSpatialId:first(active,['spatial_node_id','spatial_id','spatialId']), activeId:active?.id||null,
        activeLabel:first(active,['label','name']), managerSpatialTarget:m?.spatialTarget||null,
        renderer:m?.active?.constructor?.name||null
      };
    };
    const managerTarget = () => {
      const m=window.spatialViewportManager, s=m?.state||{}, c=s.spatialTarget||s.target||m?.spatialTarget||m?.target||null;
      return c && typeof c==='object' ? first(c,['spatial_node_id','spatial_id','spatialId','id','target'])||'' : c||'';
    };
    const target = () => {
      const managerId=normalize(managerTarget()), contract=window.testhpSpatialContract?.getTarget?.();
      const contractId=normalize(typeof contract==='object'?first(contract,['spatial_node_id','spatial_id','spatialId','id']):contract);
      const selectedId=normalize(window.selectedSpatialNode), evidenceId=normalize(window.spatialEvidenceTarget);
      const id=managerId||contractId||selectedId||evidenceId||'hand';
      const source=managerId?'viewport-manager':contractId?'spatial-contract':selectedId?'selectedSpatialNode':evidenceId?'spatialEvidenceTarget':'fallback';
      const navNode=document.getElementById('spatial-node');
      const label=navNode?.querySelector('strong')?.textContent?.trim()||(typeof contract==='object'?contract.label:'')||id;
      return {label,id,source,managerId,contractId,selectedId,evidenceId,manager:managerSnapshot(),contract:typeof contract==='object'?contract:null};
    };

    const evidence = () => { try { const x=JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2')||'{}'); return Array.isArray(x.evidence)?x.evidence.filter(x=>!x.archived):[]; } catch { return []; } };
    const geometry = () => { try { return JSON.parse(localStorage.getItem('digitalTwinHandSurface.v1')||'{}'); } catch { return {}; } };
    const targetId = x => String(first(x,['spatial_node_id','spatial_id','spatialId'])||first(x?.target||{},['spatial_node_id','spatial_id','spatialId'])||x?.target||'');
    const targetItems = (items,id) => items.filter(x=>normalize(targetId(x))===normalize(id));
    const targetGeometry = (g,id) => targetId(g)===id?g:{};
    const stage = (name,status,detail) => `<div style="display:grid;grid-template-columns:150px 90px 1fr;gap:8px;align-items:center;padding:7px 9px;border:1px solid #26364b;border-radius:7px;background:#111b29"><strong>${esc(name)}</strong><span style="font-weight:800">${esc(status)}</span><span>${esc(detail)}</span></div>`;

    // Observe future registry fetches without consuming response bodies.
    if (!window.__testhpDebugFetchInstalled && window.fetch) {
      const originalFetch=window.fetch.bind(window);
      window.__testhpDebugFetchInstalled=true;
      window.__testhpDebugFetchLog=[];
      window.fetch=async (...args) => {
        const started=performance.now(), input=args[0], init=args[1]||{};
        const url=typeof input==='string'?input:(input?.url||'');
        const method=(init.method||(typeof input!=='string'&&input?.method)||'GET').toUpperCase();
        let response;
        try { response=await originalFetch(...args); }
        catch(error) { window.__testhpDebugFetchLog.push({url,method,started,elapsed:performance.now()-started,error:{name:error?.name,message:error?.message}}); throw error; }
        if (/\/api\/(spatial|observations|biological-state)/.test(url)) {
          window.__testhpDebugFetchLog.push({url,method,status:response.status,ok:response.ok,started,elapsed:performance.now()-started,type:response.type||null});
          window.__testhpDebugFetchLog=window.__testhpDebugFetchLog.slice(-30);
        }
        return response;
      };
    }

    const registrySnapshot = () => window.__testhpTwinRegistryDiagnostics || {};
    const nearestRecords = (records,id) => {
      const targetParts=splitPath(id);
      return (Array.isArray(records)?records:[]).map((r,index)=>{
        const candidates=[r.spatial_node_id,r.spatial_id,r.target].filter(Boolean).map(String);
        let best=null;
        candidates.forEach(actual=>{ const dif=pathDiff(id,actual); const common=targetParts.reduce((n,x,i)=>n+(x===splitPath(actual)[i]?1:0),0); const score=(common*10)-dif.length; if(!best||score>best.score) best={actual,dif,common,score}; });
        return {r,index,...(best||{actual:'',dif:[],common:0,score:-999})};
      }).sort((a,b)=>b.score-a.score).slice(0,12);
    };

    const renderChain = t => {
      const body=document.getElementById('hsd-chain-body'); if(!body)return;
      const d=registrySnapshot(), nav=window.__testhpDiagnostics||{}, spatialState=window.__testhpSpatialState||{}, rows=[];
      const push=(name,value,expected='')=>{const v=value==null||value===''?'NULL':String(value),e=expected?String(expected):'';const verdict=e?(normalize(v)===normalize(e)?'OK':'MISMATCH'):'';rows.push(`${name.padEnd(30)} ${v}${verdict?`  => ${verdict} (expected ${e})`:''}`);};
      rows.push('--- VIEWPORT / NAVIGATION ---');
      push('DOM selectedSpatialNode',t.selectedId,t.id); push('spatialEvidenceTarget',t.evidenceId,t.id); push('spatial contract target',t.contractId,t.id);
      push('manager state target',t.manager.stateSpatialId,t.id); push('manager active target',t.manager.activeSpatialId,t.id); push('manager active id',t.manager.activeId);
      push('manager activeKey',t.manager.activeKey); push('manager activeLayer',t.manager.activeLayer); push('manager spatialTarget',t.manager.managerSpatialTarget,t.id);
      rows.push(`manager renderer                 ${t.manager.renderer||'NULL'}`); rows.push(`resolved debug target            ${t.id} [${t.source}]`); rows.push(`target fingerprint               ${hash(t.id)}`);
      rows.push(''); rows.push('--- CONTRACT / STATE OBJECTS ---'); rows.push(`contract object                  ${safe(t.contract)}`); rows.push(`__testhpSpatialState             ${safe(spatialState)}`); rows.push(`__testhpDiagnostics              ${safe(nav)}`);
      rows.push(''); rows.push('--- REGISTRY REQUEST / RESPONSE ---');
      push('registry requestedTarget',d.requestedTarget,t.id); rows.push(`registry endpoint                ${d.endpoint||'NULL'}`); rows.push(`registry HTTP                    ${d.status==null?'NULL':d.status} ok=${!!d.ok}`);
      rows.push(`registry raw_count               ${d.rawCount??d.raw_count??d.total??'NULL'}`); rows.push(`registry scoped_count            ${d.matchDebug?.scoped_count??'NULL'}`);
      rows.push(`registry exact_count             ${d.matchDebug?.exact_count??d.targetLinked??'NULL'}`); rows.push(`registry returned_count          ${d.matchDebug?.returned_count??d.targetLinked??'NULL'}`);
      rows.push(`registry rejected_count          ${d.matchDebug?.rejected_count??d.matchDebug?.rejectedCount??'NULL'}`); rows.push(`registry prepared                ${d.prepared??'NULL'}`);
      rows.push(`registry aliasUsed               ${d.matchDebug?.aliasUsed||'NULL'}`); rows.push(`registry response keys           ${Array.isArray(d.responseKeys)?d.responseKeys.join(', '):'NULL'}`);
      const decisions=Array.isArray(d.matchDebug?.decisions)?d.matchDebug.decisions:[];
      decisions.slice(0,20).forEach((x,i)=>rows.push(`decision[${i+1}]                    ${x.matched?'ACCEPT':'REJECT'} reason=${x.reason||'NULL'} expected=${x.expected_spatial_node_id||'NULL'} actual=${x.actual_spatial_node_id||'NULL'} evidence=${x.evidence_id||'NULL'} asset=${x.asset_id||'NULL'} attachment=${x.attachment_status||'NULL'}`));
      rows.push(''); rows.push('--- NETWORK OBSERVATION ---');
      const fetchLog=window.__testhpDebugFetchLog||[];
      if(fetchLog.length) fetchLog.slice(-20).forEach((r,i)=>rows.push(`[fetch ${i+1}] ${r.method} ${r.status??'ERR'} ok=${r.ok??false} ${Math.round(r.elapsed||0)}ms ${r.url}`));
      else rows.push('no intercepted spatial fetches');
      const resources=performance.getEntriesByType('resource').filter(r=>/\/api\/(spatial|observations|biological-state)/.test(r.name)).slice(-20);
      if(resources.length) resources.forEach((r,i)=>rows.push(`[timing ${i+1}] ${r.initiatorType||'unknown'} ${Math.round(r.duration||0)}ms ${r.name}`));
      body.textContent=rows.join('\n');
    };

    const renderRegistryDiagnostics = (t,cacheItems) => {
      const body=document.getElementById('hsd-registry-body'); if(!body)return;
      const d=registrySnapshot(), lines=[];
      const canonical=Array.isArray(d.targetRecords)?d.targetRecords:[], allCanonical=Array.isArray(d.allRecords)?d.allRecords:[], cache=targetItems(cacheItems,t.id);
      lines.push(`requested target: ${t.id}`); lines.push(`target fingerprint: ${hash(t.id)}`); lines.push(`target source: ${t.source}`);
      lines.push(`manager target: ${t.managerId||'NULL'}`); lines.push(`contract target: ${t.contractId||'NULL'}`); lines.push(`selectedSpatialNode: ${t.selectedId||'NULL'}`); lines.push(`spatialEvidenceTarget: ${t.evidenceId||'NULL'}`);
      const sources=[['manager',t.managerId],['contract',t.contractId],['selected',t.selectedId],['evidence',t.evidenceId]].filter(([,v])=>v).map(([k,v])=>`${k}=${relation(t.id,v)}`);
      lines.push(`target relation: ${sources.join(' | ')||'none'}`);
      const drift=[t.managerId,t.contractId,t.selectedId,t.evidenceId].filter(Boolean).some(x=>normalize(x)!==normalize(t.id)); if(drift)lines.push('TARGET DRIFT: renderer/manager target differs from one or more legacy target globals.');
      lines.push(`endpoint: ${d.endpoint||'/api/spatial/registry?subject_id=own_cohort&timepoint=T0&debug=true'}`); lines.push(`HTTP: ${d.status??'not fetched'} | ok=${d.ok??false}`);
      lines.push(`request started: ${d.requestStartedAt||'NULL'} | duration: ${d.requestDurationMs??'NULL'}ms`); lines.push(`request params: ${safe(d.requestParams||d.params||null)}`);
      lines.push(`canonical counts: raw=${d.rawCount??d.raw_count??d.total??'—'} scoped=${d.matchDebug?.scoped_count??'—'} exact=${d.matchDebug?.exact_count??'—'} returned=${d.matchDebug?.returned_count??d.targetLinked??'—'} rejected=${d.matchDebug?.rejected_count??'—'} prepared=${d.prepared??'—'}`);
      lines.push(`response keys: ${Array.isArray(d.responseKeys)?d.responseKeys.join(', '):'—'}`); lines.push(`localStorage UX cache: total=${cacheItems.length} target-linked=${cache.length}`);
      if(d.error)lines.push(`ERROR: ${d.error.name}: ${d.error.message}`);
      const decisions=Array.isArray(d.matchDebug?.decisions)?d.matchDebug.decisions:[];
      if(decisions.length){lines.push('BACKEND TARGET-MATCH DECISIONS (exact rejection point):');decisions.forEach((x,i)=>lines.push(`  [${i+1}] ${x.matched?'ACCEPT':'REJECT'} reason=${x.reason||'NULL'} expected=${x.expected_spatial_node_id||'NULL'} actual=${x.actual_spatial_node_id||'NULL'} relation=${relation(t.id,x.actual_spatial_node_id)} attachment=${x.attachment_status||'NULL'} localized=${x.spatially_localized??'NULL'} evidence=${x.evidence_id||'NULL'} asset=${x.asset_id||'NULL'} file=${x.filename||'NULL'}`));}
      if(canonical.length){lines.push('canonical target records:');canonical.forEach((x,i)=>lines.push(`  [${i+1}] spatial_node_id=${x.spatial_node_id||'NULL'} spatial_id=${x.spatial_id||'NULL'} target=${x.target||'NULL'} level=${x.spatial_level||'NULL'} attachment=${x.attachment_status||'NULL'} localized=${x.spatially_localized??'NULL'} prepared=${x.prepared??'NULL'} prepared_asset_id=${x.prepared_asset_id||'NULL'} asset=${x.asset_id||'NULL'} file=${x.filename||'NULL'}`));}
      if(cache.length){lines.push('cache target records:');cache.slice(0,20).forEach((x,i)=>lines.push(`  [${i+1}] spatial_id=${targetId(x)||'NULL'} prepared=${!!(x.prepared||x.preparedAssetId)} view=${x.view||'NULL'} file=${x.filename||x.name||'NULL'} evidence=${x.evidence_id||'NULL'} asset=${x.asset_id||'NULL'}`));}
      const near=nearestRecords(allCanonical,t.id);
      if(near.length){lines.push(`NEAREST CANONICAL CANDIDATES (${near.length}):`);near.forEach((x,i)=>lines.push(`  [${i+1}] relation=${relation(t.id,x.actual)} common=${x.common} diff=${safe(x.dif)} spatial_node_id=${x.r.spatial_node_id||'NULL'} spatial_id=${x.r.spatial_id||'NULL'} target=${x.r.target||'NULL'} level=${x.r.spatial_level||'NULL'} attachment=${x.r.attachment_status||'NULL'} localized=${x.r.spatially_localized??'NULL'} prepared=${x.r.prepared??'NULL'} evidence=${x.r.evidence_id||'NULL'} asset=${x.r.asset_id||'NULL'}`));}
      if(d.matchDebug?.decisions?.some(x=>x.reason==='ROOT_ONLY_REGISTERED_ASSET_NOT_DEEP_ATTACHED'))lines.push('VERDICT: DATA ATTACHMENT — evidence exists, but ingestion registered it only at root and rejected the deeper target.');
      else if(!canonical.length&&near.length)lines.push('VERDICT: TARGET MATCH / SPATIAL ATTACHMENT — registry has related records but no exact target match. Inspect NEAREST CANDIDATES and path diff.');
      else if(!canonical.length&&!near.length&&d.ok)lines.push('VERDICT: DATA / INGESTION GAP — canonical registry returned no exact or nearby target record; renderer click path is not the failure.');
      else if(canonical.length&&!cache.length)lines.push('VERDICT: CACHE SYNC — canonical registry has target evidence but UX cache has none.');
      else if(!canonical.length&&cache.length)lines.push('VERDICT: CACHE / CANONICAL MISMATCH — UX cache has target evidence but canonical registry does not.');
      else if(canonical.length)lines.push('VERDICT: TARGET DATA PRESENT — inspect preparation/geometry/projection stages for the next failing stage.');
      else lines.push('VERDICT: INCONCLUSIVE — registry diagnostics did not expose enough information yet.');
      body.textContent=lines.join('\n');
    };

    const render=()=>{
      const t=target(),all=evidence(),items=targetItems(all,t.id),g=targetGeometry(geometry(),t.id),d=registrySnapshot();
      const views=['front','back','side_left','side_right','thumb'];
      const present=views.filter(v=>items.some(x=>{const name=String(x.filename||x.name||'').toLowerCase();return name.includes(v)||String(x.view||'').toLowerCase()===v;}));
      const preparedCount=items.filter(x=>x.prepared===true||x.preparedAssetId).length,regReady=present.length===5&&preparedCount>0,projectionReady=!!g.projectionPlan,packageReady=!!g.twinPackage;
      const driftSources=[t.contractId,t.selectedId,t.evidenceId].filter(Boolean).filter(x=>normalize(x)!==normalize(t.id));
      const targetNode=document.getElementById('hsd-target');
      if(targetNode)targetNode.innerHTML=`<strong>Aktualny cel:</strong> ${esc(t.label)} <code style="color:#9fc4e8">${esc(t.id)}</code> <span style="color:#71849b">source=${esc(t.source)}</span> <span style="color:#71849b">fp=${hash(t.id)}</span>${driftSources.length?` <span style="color:#f0b36a;font-weight:800">TARGET DRIFT</span>`:''}`;
      const flowNode=document.getElementById('hsd-flow');
      if(flowNode)flowNode.innerHTML=[stage('ŹRÓDŁA · 11',items.length?'READY':'EMPTY',`${items.length} rekordów dla celu`),stage('PRZYGOTOWANIE · 12',preparedCount?'READY':'BLOCKED',preparedCount?`${preparedCount} prepared asset dla celu`:'brak prepared asset dla celu'),stage('GEOMETRIA · 13',Object.keys(g).length?'READY':'EMPTY',Object.keys(g).length?'geometria dla celu':'brak geometrii dla celu'),stage('REJESTRACJA · 14',regReady?'READY':present.length?'PARTIAL':'BLOCKED',`${present.length}/5 widoków dla celu`),stage('WORKFLOW · 15',regReady?'READY':'WAITING',regReady?'można kontynuować':'oczekuje na dane celu'),stage('PROJEKCJA · 21',projectionReady?'READY':'WAITING',projectionReady?'plan dla celu':'plan nieutworzony dla celu'),stage('PAKIET · 22',packageReady?'READY':'WAITING',packageReady?'pakiet dla celu':'pakiet nieutworzony dla celu')].join('<div style="text-align:center;color:#71849b">↓</div>');
      const detailsNode=document.getElementById('hsd-details');
      if(detailsNode)detailsNode.textContent=`TARGET: ${t.id}\nTARGET FP: ${hash(t.id)}\nSOURCE: ${t.source}\nMANAGER: ${t.managerId||'NULL'} | CONTRACT: ${t.contractId||'NULL'} | SELECTED: ${t.selectedId||'NULL'} | EVIDENCE: ${t.evidenceId||'NULL'}\nEVIDENCE CACHE: ${all.length} total | ${items.length} target-linked | prepared=${preparedCount}\nCANONICAL: raw=${d.rawCount??d.raw_count??d.total??'NULL'} | exact=${d.matchDebug?.exact_count??d.targetLinked??'NULL'} | rejected=${d.matchDebug?.rejected_count??'NULL'}\nVIEWS: ${present.length}/5 target-scoped\nRENDERER: ${window.spatialViewportManager?.active?.constructor?.name||'unknown'} | manager=${window.spatialViewportManager?'present':'missing'}`;
      renderChain(t); renderRegistryDiagnostics(t,all);
    };

    render();
    let scheduled=false; const schedule=()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;render();});};
    ['testhp:spatial-layer-changed','testhp:spatial-contract-changed','testhp:spatial-target-changed','testhp:evidence-attached','testhp:hand-surface-ready','testhp:surface-projection-plan-changed','testhp:evidence-registry-debug','testhp:evidence-registry-synced'].forEach(e=>window.addEventListener(e,schedule));
    const refreshCanonical=()=>{const t=target();if(typeof window.__testhpCollectRegistryDiagnostics==='function')window.__testhpCollectRegistryDiagnostics(t.id).then(schedule).catch(error=>{window.__testhpDebugLastCollectError={name:error?.name,message:error?.message};schedule();});};
    window.addEventListener('testhp:spatial-layer-changed',refreshCanonical); window.addEventListener('testhp:spatial-target-changed',refreshCanonical); refreshCanonical();
    return true;
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
