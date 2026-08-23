(() => {
  const state = { last: null, timer: null };
  const safeJson = value => { try { return JSON.stringify(value, null, 2); } catch { return String(value); } };

  const read = () => {
    const node = document.getElementById('spatial-node');
    const breadcrumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(el => el.textContent.trim()).filter(Boolean);
    const selected = window.selectedSpatialNode || null;
    const evidence = window.spatialEvidenceTarget || null;
    const manager = window.spatialViewportManager;
    const managerTarget = manager?.state?.spatial_id || manager?.state?.spatialId || manager?.state?.spatialTarget || manager?.spatialTarget || null;
    const contract = window.testhpSpatialContract?.getTarget?.()?.spatial_id || window.testhpSpatialContract?.getTarget?.()?.spatialId || window.testhpSpatialContract?.getTarget?.()?.spatial_node_id || null;
    const bodyTarget = document.body?.dataset?.spatialTarget || null;
    const navId = node?.dataset?.spatialId || node?.getAttribute('data-spatial-id') || null;
    const chosen = managerTarget || contract || selected || evidence || navId || bodyTarget || null;
    const candidates = { contract, manager: managerTarget, selectedNode: selected, evidence, navigationNode: navId, body: bodyTarget };
    const distinctIds = [...new Set(Object.values(candidates).filter(Boolean))];
    return {
      selected: chosen,
      navigation: {
        level: document.getElementById('spatial-level-badge')?.textContent?.trim() || null,
        label: node?.querySelector('strong')?.textContent?.trim() || null,
        path: breadcrumbs.join(' > '),
        childCount: document.querySelectorAll('#spatial-children .spatial-target').length
      },
      candidates,
      canonical: { contract, manager: managerTarget, selectedSpatialNode: selected, evidence, chosen },
      distinctSpatialIds: distinctIds,
      mismatch: distinctIds.length > 1,
      warning: distinctIds.length > 1 ? 'TARGET CHAIN DRIFT: źródła wskazują różne spatial_id.' : null
    };
  };

  const fetchJson = async url => {
    try {
      const started = performance.now();
      const response = await fetch(url, { cache: 'no-store' });
      let payload = null;
      try { payload = await response.json(); } catch { payload = null; }
      return { url, status: response.status, ok: response.ok, ms: Math.round(performance.now() - started), payload };
    } catch (error) {
      return { url, status: 0, ok: false, ms: 0, error: { name: error?.name || 'Error', message: error?.message || String(error) } };
    }
  };

  const rowsFrom = payload => {
    if (Array.isArray(payload?.items)) return payload.items;
    if (Array.isArray(payload?.records)) return payload.records;
    if (Array.isArray(payload?.data)) return payload.data;
    if (Array.isArray(payload?.evidence)) return payload.evidence;
    if (Array.isArray(payload?.targetRecords)) return payload.targetRecords;
    return [];
  };

  const buildRegistryDiagnostics = (target, registry) => {
    const payload = registry.payload || {};
    const rows = rowsFrom(payload);
    const targetId = String(target || '').replace(/^\/+|\/+$/g, '');
    const idOf = x => String(x?.spatial_node_id || x?.spatial_id || x?.spatialId || x?.target?.spatial_node_id || x?.target?.spatial_id || x?.target?.spatialId || '').replace(/^\/+|\/+$/g, '');
    const targetRecords = rows.filter(x => idOf(x) === targetId);
    const allRecords = rows;
    const matchDebug = payload.matchDebug || payload.match_debug || payload.diagnostics || null;
    const prepared = targetRecords.filter(x => x?.prepared === true || x?.preparedAssetId || x?.prepared_asset_id).length;
    return {
      requestedTarget: targetId,
      endpoint: registry.url,
      status: registry.status,
      ok: registry.ok,
      ms: registry.ms,
      error: registry.error || null,
      total: rows.length,
      targetLinked: targetRecords.length,
      targetRecords,
      allRecords,
      prepared,
      matchDebug,
      response: payload
    };
  };

  const collectRegistryDiagnostics = async target => {
    const targetId = String(target || '').trim().replace(/^\/+|\/+$/g, '');
    if (!targetId) return null;
    const encoded = encodeURIComponent(targetId);
    const registry = await fetchJson(`/api/spatial/registry?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encoded}&debug=true`);
    const diagnostics = buildRegistryDiagnostics(targetId, registry);
    state.last = state.last || {};
    state.last.registry = diagnostics;
    window.__testhpTwinRegistryDiagnostics = diagnostics;
    window.dispatchEvent(new CustomEvent('testhp:evidence-registry-debug', { detail: diagnostics }));
    return diagnostics;
  };

  window.__testhpCollectRegistryDiagnostics = collectRegistryDiagnostics;

  const probeRegistry = async target => {
    if (!target) return { registry: null, state: null };
    const encoded = encodeURIComponent(target);
    const [registry, stateResponse] = await Promise.all([
      fetchJson(`/api/spatial/registry?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encoded}`),
      fetchJson(`/api/spatial/state?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encoded}`)
    ]);
    const registryRows = rowsFrom(registry.payload);
    const registryIds = registryRows.map(item => item.spatial_node_id || item.spatial_id).filter(Boolean);
    const stateSpatialId = stateResponse.payload?.spatial_id || stateResponse.payload?.item?.spatial_id || null;
    return {
      registry: { target, http: { status: registry.status, ok: registry.ok, ms: registry.ms }, recordCount: registryRows.length, targetLinked: registryRows.filter(item => (item.spatial_node_id || item.spatial_id) === target).length, spatialIds: registryIds, response: registry.payload },
      state: { url: stateResponse.url, spatial_id: stateSpatialId, response: stateResponse.status, payload: stateResponse.payload }
    };
  };

  const render = (chain, probe) => {
    const host = document.getElementById('twin-viewport-debug-host');
    if (!host) return;
    let panel = document.getElementById('testhp-target-chain-debug');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'testhp-target-chain-debug';
      panel.style.cssText = 'margin-top:10px;padding:12px;border:1px solid rgba(130,145,165,.35);border-radius:10px;background:rgba(13,17,23,.96);color:#e6edf3;font:11px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;max-height:55vh;overflow:auto;box-shadow:0 8px 28px rgba(0,0,0,.2)';
      host.appendChild(panel);
    }
    const badge = chain.mismatch ? 'TARGET DRIFT' : 'TARGET CHAIN OK';
    panel.innerHTML = `<details open><summary style="cursor:pointer;font-weight:800">TARGET CHAIN / PROVENANCE · ${badge}</summary><pre style="white-space:pre-wrap;word-break:break-word">${safeJson(chain)}\n\nREGISTRY / CACHE PROBE\n${safeJson(probe)}</pre></details>`;
  };

  const run = async () => {
    const chain = read();
    const probe = await probeRegistry(chain.selected);
    state.last = { at: new Date().toISOString(), chain, probe };
    window.__testhpTargetChainDiagnostics = state.last;
    window.dispatchEvent(new CustomEvent('testhp:target-chain-diagnostics', { detail: state.last }));
    render(chain, probe);
    await collectRegistryDiagnostics(chain.selected);
    return state.last;
  };

  const install = () => {
    if (state.timer) return;
    run();
    state.timer = setInterval(run, 1500);
    window.addEventListener('testhp:spatial-target-changed', run);
    window.addEventListener('testhp:spatial-layer-changed', run);
    window.addEventListener('beforeunload', () => clearInterval(state.timer), { once: true });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
