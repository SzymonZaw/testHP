(() => {
  const start = () => {
    const panel = document.getElementById('twin-debug-panel');
    if (!panel || document.getElementById('hand-surface-debug-flow')) return false;
    const box = document.createElement('section');
    box.id = 'hand-surface-debug-flow';
    box.style.cssText = 'margin:12px 0;padding:12px;border:1px solid #52647a;border-radius:10px;background:#0d1420;color:#dbe7f5;font:12px/1.45 system-ui,sans-serif;';
    box.innerHTML = '<div style="font-weight:800;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px">HAND SURFACE · DEBUG FLOW</div><div id="hsd-target" style="margin-bottom:10px"></div><div id="hsd-flow" style="display:grid;gap:6px"></div><div id="hsd-details" style="margin-top:10px;color:#aebed0;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace"></div><details id="hsd-registry" style="margin-top:10px"><summary style="cursor:pointer;color:#9fc4e8;font-weight:700">REGISTRY / CACHE MISMATCH DIAGNOSTICS</summary><pre id="hsd-registry-body" style="white-space:pre-wrap;margin:8px 0 0;color:#aebed0;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace"></pre></details>';
    panel.appendChild(box);

    const esc = v => String(v ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
    const target = () => {
      const t = window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || window.spatialEvidenceTarget || 'hand';
      return typeof t === 'object'
        ? {label:t.label||t.path?.join(' > ')||t.spatial_id||t.id||'Bieżący cel',id:t.spatial_id||t.spatialId||t.id||'hand'}
        : {label:String(t),id:String(t)};
    };
    const evidence = () => { try { const x=JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2')||'{}'); return Array.isArray(x.evidence)?x.evidence.filter(x=>!x.archived):[]; } catch { return []; } };
    const geometry = () => { try { return JSON.parse(localStorage.getItem('digitalTwinHandSurface.v1')||'{}'); } catch { return {}; } };
    const targetId = x => String(x?.spatial_id||x?.spatialId||x?.target?.spatial_id||x?.target?.spatialId||x?.target||'');
    const targetItems = (items,id) => items.filter(x => targetId(x) === id);
    const targetGeometry = (g,id) => targetId(g)===id ? g : {};
    const stage = (name,status,detail) => `<div style="display:grid;grid-template-columns:150px 90px 1fr;gap:8px;align-items:center;padding:7px 9px;border:1px solid #26364b;border-radius:7px;background:#111b29"><strong>${esc(name)}</strong><span style="font-weight:800">${esc(status)}</span><span>${esc(detail)}</span></div>`;

    const renderRegistryDiagnostics = (t, cacheItems) => {
      const body = document.getElementById('hsd-registry-body');
      if (!body) return;
      const d = window.__testhpTwinRegistryDiagnostics;
      const lines = [];
      lines.push(`requested target: ${t.id}`);
      lines.push(`endpoint: ${d?.endpoint || '/api/spatial/registry?subject_id=own_cohort&timepoint=T0&debug=true'}`);
      lines.push(`HTTP: ${d?.status ?? 'not fetched'} | ok=${d?.ok ?? false}`);
      lines.push(`canonical registry: scoped=${d?.matchDebug?.scoped_count ?? d?.total ?? '—'} returned=${d?.matchDebug?.returned_count ?? d?.targetLinked ?? '—'} rejected=${d?.matchDebug?.rejected_count ?? '—'} prepared=${d?.prepared ?? '—'}`);
      lines.push(`localStorage UX cache: total=${cacheItems.length} target-linked=${targetItems(cacheItems,t.id).length}`);
      if (d?.error) lines.push(`ERROR: ${d.error.name}: ${d.error.message}`);

      const decisions = Array.isArray(d?.matchDebug?.decisions) ? d.matchDebug.decisions : [];
      if (decisions.length) {
        lines.push('BACKEND TARGET-MATCH DECISIONS (exact rejection point):');
        decisions.forEach((x,i)=>lines.push(`  [${i+1}] ${x.matched?'ACCEPT':'REJECT'} reason=${x.reason} expected=${x.expected_spatial_node_id||'NULL'} actual=${x.actual_spatial_node_id||'NULL'} attachment=${x.attachment_status||'NULL'} localized=${x.spatially_localized} evidence=${x.evidence_id||'NULL'} asset=${x.asset_id||'NULL'} file=${x.filename||'NULL'}`));
      }

      const canonical = Array.isArray(d?.targetRecords) ? d.targetRecords : [];
      const cache = targetItems(cacheItems,t.id);
      if (canonical.length) {
        lines.push('canonical target records:');
        canonical.forEach((x,i)=>lines.push(`  [${i+1}] spatial_node_id=${x.spatial_node_id||'NULL'} spatial_id=${x.spatial_id||'NULL'} target=${x.target||'NULL'} attachment=${x.attachment_status||'NULL'} localized=${x.spatially_localized} prepared=${x.prepared} prepared_asset_id=${x.prepared_asset_id||'NULL'} asset=${x.asset_id||'NULL'} file=${x.filename||'NULL'}`));
      }
      if (cache.length) {
        lines.push('cache target records:');
        cache.forEach((x,i)=>lines.push(`  [${i+1}] spatial_id=${targetId(x)||'NULL'} prepared=${!!(x.prepared||x.preparedAssetId)} file=${x.filename||x.name||'NULL'}`));
      }
      const allCanonical = Array.isArray(d?.allRecords) ? d.allRecords : [];
      const near = allCanonical.filter(x => [x.spatial_node_id,x.spatial_id,x.target].some(v => String(v||'').includes(t.id) || t.id.includes(String(v||''))));
      if (near.length) lines.push(`near-match records (${near.length}) — useful for path/id mismatch:`);
      near.slice(0,12).forEach((x,i)=>lines.push(`  [${i+1}] spatial_node_id=${x.spatial_node_id||'NULL'} spatial_id=${x.spatial_id||'NULL'} target=${x.target||'NULL'} level=${x.spatial_level||'NULL'} attachment=${x.attachment_status||'NULL'} localized=${x.spatially_localized} prepared=${x.prepared}`));
      if (decisions.some(x=>x.reason==='ROOT_ONLY_REGISTERED_ASSET_NOT_DEEP_ATTACHED')) lines.push('DIAGNOSIS: evidence exists in canonical registry, but ingestion registered it only at root `hand`; it is intentionally rejected for this deeper target until explicitly attached.');
      else if (!canonical.length && near.length) lines.push('DIAGNOSIS HINT: registry has nearby IDs but none exact-match the active target; likely spatial-id/attachment mismatch.');
      else if (!canonical.length && !near.length && d?.ok) lines.push('DIAGNOSIS HINT: canonical registry returned no exact or nearby target record; this is a data/ingestion gap, not a renderer click failure.');
      if (canonical.length && !cache.length) lines.push('DIAGNOSIS HINT: canonical registry has target evidence but UX cache does not; cache synchronization/rendering is stale.');
      if (!canonical.length && cache.length) lines.push('DIAGNOSIS HINT: UX cache has target evidence but canonical registry does not; cached/manual evidence is not backed by the canonical registry.');
      body.textContent = lines.join('\n');
    };

    const render = () => {
      const t=target(),all=evidence(),items=targetItems(all,t.id),g=targetGeometry(geometry(),t.id);
      const views=['front','back','side_left','side_right','thumb'];
      const present=views.filter(v=>items.some(x=>{const name=String(x.filename||x.name||'').toLowerCase(); return name.includes(v)||String(x.view||'').toLowerCase()===v;}));
      const preparedCount=items.filter(x=>x.prepared===true||x.preparedAssetId).length;
      const regReady=present.length===5&&preparedCount>0;
      const projectionReady=!!g.projectionPlan;
      const packageReady=!!g.twinPackage;
      document.getElementById('hsd-target').innerHTML=`<strong>Aktualny cel:</strong> ${esc(t.label)} <code style="color:#9fc4e8">${esc(t.id)}</code>`;
      document.getElementById('hsd-flow').innerHTML=[
        stage('ŹRÓDŁA · 11',items.length?'READY':'EMPTY',`${items.length} rekordów dla celu`),
        stage('PRZYGOTOWANIE · 12',preparedCount?'READY':'BLOCKED',preparedCount?`${preparedCount} prepared asset dla celu`:'brak prepared asset dla celu'),
        stage('GEOMETRIA · 13',Object.keys(g).length?'READY':'EMPTY',Object.keys(g).length?'geometria dla celu':'brak geometrii dla celu'),
        stage('REJESTRACJA · 14',regReady?'READY':present.length?'PARTIAL':'BLOCKED',`${present.length}/5 widoków dla celu`),
        stage('WORKFLOW · 15',regReady?'READY':'WAITING',regReady?'można kontynuować':'oczekuje na dane celu'),
        stage('PROJEKCJA · 21',projectionReady?'READY':'WAITING',projectionReady?'plan dla celu':'plan nieutworzony dla celu'),
        stage('PAKIET · 22',packageReady?'READY':'WAITING',packageReady?'pakiet dla celu':'pakiet nieutworzony dla celu')
      ].join('<div style="text-align:center;color:#71849b">↓</div>');
      document.getElementById('hsd-details').textContent=`TARGET: ${t.id}\nEVIDENCE: ${all.length} total | ${items.length} target-linked | prepared=${preparedCount}\nVIEWS: ${present.length}/5 target-scoped\nRENDERER: ${window.spatialViewportManager?.active?.constructor?.name||'unknown'} | manager=${window.spatialViewportManager?'present':'missing'}`;
      renderRegistryDiagnostics(t,all);
    };

    render();
    let scheduled=false;
    const schedule=()=>{ if(scheduled)return; scheduled=true; requestAnimationFrame(()=>{scheduled=false;render();}); };
    ['testhp:spatial-layer-changed','testhp:spatial-contract-changed','testhp:evidence-attached','testhp:hand-surface-ready','testhp:surface-projection-plan-changed','testhp:evidence-registry-debug','testhp:evidence-registry-synced'].forEach(e=>window.addEventListener(e,schedule));

    const refreshCanonical = () => {
      const t=target();
      if (typeof window.__testhpCollectRegistryDiagnostics === 'function') {
        window.__testhpCollectRegistryDiagnostics(t.id).then(schedule).catch(()=>{});
      }
    };
    window.addEventListener('testhp:spatial-layer-changed', refreshCanonical);
    refreshCanonical();
    return true;
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start,{once:true}); else start();
})();
