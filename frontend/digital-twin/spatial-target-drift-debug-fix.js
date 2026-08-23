(() => {
  'use strict';
  const canonical = value => {
    const api = window.testhpSpatialContract;
    if (api?.normalizeId) return api.normalizeId(value);
    return String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
  };
  const authoritativeId = () => {
    const diagnostics = window.__testhpDiagnostics || {};
    const nav = diagnostics.lastNavigation || diagnostics.lastNavigationRoute;
    const navId = nav?.spatial_id || nav?.spatialId;
    if (typeof navId === 'string' && navId.includes('/')) return canonical(navId);
    const clickId = diagnostics.lastClickRoute?.button?.spatialId || diagnostics.lastClickRoute?.button?.spatial_id;
    if (typeof clickId === 'string' && clickId.includes('/')) return canonical(clickId);
    const node = document.getElementById('spatial-node');
    const nodeId = node?.dataset?.spatialId || node?.getAttribute('data-spatial-id');
    if (typeof nodeId === 'string' && nodeId.includes('/')) return canonical(nodeId);
    const manager = window.spatialViewportManager;
    const active = manager?.active || {};
    const activeId = active.spatial_node_id || active.spatial_id || active.spatialId;
    if (typeof activeId === 'string' && activeId.includes('/')) return canonical(activeId);
    const state = manager?.state || {};
    const stateId = state.spatial_node_id || state.spatial_id || state.spatialId;
    if (typeof stateId === 'string' && stateId.includes('/')) return canonical(stateId);
    return '';
  };
  const label = () => document.getElementById('spatial-node')?.querySelector('strong')?.textContent?.trim() || null;
  const relation = (expected, actual) => {
    const e = canonical(expected), a = canonical(actual);
    if (!e || !a) return 'MISSING';
    if (e === a) return 'EXACT';
    if (e.startsWith(a + '/')) return 'EXPECTED_IS_DESCENDANT';
    if (a.startsWith(e + '/')) return 'ACTUAL_IS_DESCENDANT';
    return 'UNRELATED';
  };
  const registryProbe = async target => {
    if (!target) return null;
    try {
      const url = `/api/spatial/registry?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodeURIComponent(target)}&debug=true`;
      const response = await fetch(url, { cache: 'no-store' });
      const payload = await response.json().catch(() => ({}));
      const rows = Array.isArray(payload.items) ? payload.items : Array.isArray(payload.records) ? payload.records : Array.isArray(payload.data) ? payload.data : [];
      const idOf = x => canonical(x?.spatial_node_id || x?.spatial_id || x?.spatialId || x?.target?.spatial_node_id || x?.target?.spatial_id || x?.target?.spatialId);
      const exact = rows.filter(x => idOf(x) === target);
      return { url, status: response.status, ok: response.ok, raw: rows.length, exact: exact.length, matchDebug: payload.matchDebug || payload.match_debug || payload.diagnostics || null };
    } catch (error) {
      return { error: { name: error?.name || 'Error', message: error?.message || String(error) } };
    }
  };
  const render = async () => {
    const target = authoritativeId();
    if (!target) return;
    const manager = window.spatialViewportManager || null;
    const state = manager?.state || {};
    const active = manager?.active || {};
    const sources = {
      navigation: target,
      managerActive: active.spatial_node_id || active.spatial_id || active.spatialId || null,
      managerState: state.spatial_node_id || state.spatial_id || state.spatialId || null,
      managerSpatialTarget: typeof manager?.spatialTarget === 'string' ? manager.spatialTarget : (manager?.spatialTarget?.spatial_id || manager?.spatialTarget?.spatialId || null),
      selected: window.selectedSpatialNode || null,
      evidence: window.spatialEvidenceTarget || null,
      contract: window.testhpSpatialContract?.getTarget?.()?.spatial_id || window.testhpSpatialContract?.getTarget?.()?.spatialId || null
    };
    const drift = Object.entries(sources).filter(([k,v]) => v && canonical(v) !== target && k !== 'managerSpatialTarget');
    const probe = await registryProbe(target);
    window.__testhpAuthoritativeSpatialDiagnostics = { target, label: label(), sources, drift, registry: probe };
    const host = document.getElementById('twin-viewport-debug-host');
    if (!host) return;
    let panel = document.getElementById('testhp-authoritative-target-debug');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'testhp-authoritative-target-debug';
      panel.style.cssText = 'margin-top:10px;padding:12px;border:1px solid #52647a;border-radius:10px;background:#0d1420;color:#dbe7f5;font:11px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace';
      host.appendChild(panel);
    }
    const esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const rows = Object.entries(sources).map(([k,v]) => `${k.padEnd(20)} ${esc(v)}  ${v ? relation(target,v) : 'MISSING'}`).join('\n');
    const registryText = probe ? `HTTP ${probe.status ?? 'ERR'} ok=${!!probe.ok} raw=${probe.raw ?? '—'} exact=${probe.exact ?? '—'}\nendpoint=${probe.url || '—'}${probe.error ? `\nERROR=${probe.error.message}` : ''}` : 'not probed';
    panel.innerHTML = `<details open><summary style="cursor:pointer;font-weight:800">AUTHORITATIVE TARGET · ${esc(target)}</summary><pre style="white-space:pre-wrap;word-break:break-word;margin:8px 0 0">label              ${esc(label())}\nspatial_id         ${esc(target)}\n\nSOURCES\n${rows}\n\nREGISTRY\n${registryText}\n\nDIAGNOSIS\n${drift.length ? `source drift: ${drift.map(([k]) => k).join(', ')}` : 'all ID-bearing sources agree'}\nmanager.spatialTarget label is treated as display text, not as a spatial_id.</pre></details>`;
  };
  let scheduled = false;
  const schedule = () => { if (scheduled) return; scheduled = true; setTimeout(() => { scheduled = false; render(); }, 50); };
  schedule();
  window.addEventListener('testhp:spatial-target-changed', schedule);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:viewport-rendered', schedule);
  const timer = setInterval(render, 1500);
  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
})();
