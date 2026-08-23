(() => {
  'use strict';

  // Read-only diagnostics. Hooks only record calls/assignments; they do not normalize or change values.
  const state = { installedAt: Date.now(), selectedWrites: [], applyCalls: [], managerCalls: [] };
  const MAX = 30;
  const push = (arr, value) => { arr.push(value); if (arr.length > MAX) arr.shift(); };
  const stack = () => { try { return new Error().stack || null; } catch { return null; } };
  const valueOf = v => {
    if (v == null) return null;
    if (typeof v === 'string') return v;
    try { return { id: v.id || v.regionId || null, spatial_id: v.spatial_id || v.spatialId || null, label: v.label || v.name || null, level: v.level || null }; } catch { return String(v); }
  };
  const recordSelected = (value, phase) => push(state.selectedWrites, { t: Date.now() - state.installedAt, phase, value: valueOf(value), stack: stack() });
  const recordApply = (args, phase) => push(state.applyCalls, { t: Date.now() - state.installedAt, phase, args: Array.from(args).map(valueOf), stack: stack() });
  const installSelectedHook = () => {
    try {
      const desc = Object.getOwnPropertyDescriptor(window, 'selectedSpatialNode');
      if (desc && desc.configurable === false) return false;
      let current = desc?.get ? desc.get.call(window) : window.selectedSpatialNode;
      Object.defineProperty(window, 'selectedSpatialNode', { configurable: true, enumerable: desc?.enumerable ?? true,
        get() { return desc?.get ? desc.get.call(window) : current; },
        set(value) { recordSelected(value, 'SET'); if (desc?.set) desc.set.call(window, value); else current = value; }
      });
      recordSelected(current, 'INSTALL'); return true;
    } catch (error) { push(state.selectedWrites, { t: Date.now() - state.installedAt, phase: 'INSTALL_ERROR', error: String(error), stack: stack() }); return false; }
  };
  const installApplyHook = () => {
    try {
      if (typeof window.applySpatialNode !== 'function' || window.applySpatialNode.__testhpTraceWrapped) return false;
      const original = window.applySpatialNode;
      const wrapped = function(...args) { recordApply(args, 'CALL'); return original.apply(this, args); };
      Object.defineProperty(wrapped, '__testhpTraceWrapped', { value: true }); window.applySpatialNode = wrapped; return true;
    } catch (error) { push(state.applyCalls, { t: Date.now() - state.installedAt, phase: 'INSTALL_ERROR', error: String(error), stack: stack() }); return false; }
  };
  const installManagerHook = () => {
    try {
      const manager = window.viewportManager || window.spatialViewportManager || window.testhpViewportManager;
      if (!manager || typeof manager.setSpatialTarget !== 'function' || manager.setSpatialTarget.__testhpTraceWrapped) return false;
      const original = manager.setSpatialTarget;
      const wrapped = function(...args) { push(state.managerCalls, { t: Date.now() - state.installedAt, phase: 'CALL', args: args.map(valueOf), stack: stack() }); return original.apply(this, args); };
      Object.defineProperty(wrapped, '__testhpTraceWrapped', { value: true }); manager.setSpatialTarget = wrapped; return true;
    } catch { return false; }
  };

  // Stage 8 is deliberately read-only: it compares the same target across the
  // contract, viewport manager, selected node, manager state and registry.
  const canonicalId = value => {
    if (!value) return null;
    if (typeof value === 'string') return value;
    return value.spatial_id || value.spatialId || value.spatial_node_id || value.targetSpatialId || value.target?.spatial_id || value.target?.spatialId || null;
  };
  const currentTarget = () => {
    const contract = window.testhpSpatialContract?.getTarget?.() || window.testhpSpatialContract?.current || null;
    const manager = window.spatialViewportManager || window.viewportManager || window.testhpViewportManager || null;
    const selected = window.selectedSpatialNode || null;
    return canonicalId(contract) || canonicalId(manager?.state) || canonicalId(manager?.active) || canonicalId(selected) || null;
  };
  const labelFor = value => value && typeof value === 'object' ? (value.label || value.name || value.title || value.displayName || null) : null;
  const stage8Snapshot = () => {
    const target = currentTarget();
    const contract = window.testhpSpatialContract?.getTarget?.() || window.testhpSpatialContract?.current || null;
    const manager = window.spatialViewportManager || window.viewportManager || window.testhpViewportManager || null;
    const managerState = manager?.state || null;
    const active = manager?.active || null;
    const selected = window.selectedSpatialNode || null;
    const registry = window.__testhpTwinRegistryDiagnostics || null;
    const registryItems = Array.isArray(registry?.targetRecords) ? registry.targetRecords : [];
    const registryIds = registryItems.map(canonicalId).filter(Boolean);
    const stateId = canonicalId(managerState) || canonicalId(manager?.spatialTarget) || null;
    const managerId = canonicalId(active) || stateId || null;
    const selectedId = canonicalId(selected);
    const contractId = canonicalId(contract);
    const label = labelFor(contract) || labelFor(selected) || labelFor(active) || null;
    const expected = target;
    const check = (actual, available = true) => ({ available, actual: actual || null, expected, ok: available && !!expected && actual === expected });
    return {
      expected, label, path: contract?.path || selected?.path || managerState?.path || null,
      contract: check(contractId, !!contract), manager: check(managerId, !!manager), selectedSpatialNode: check(selectedId, !!selected),
      registry: { available: !!registry, ok: !!registry && registryIds.includes(expected), ids: registryIds, status: registry?.status ?? null, targetLinked: registry?.targetLinked ?? 0, error: registry?.error?.message || null },
      state: check(stateId, !!managerState),
      labelCheck: { actual: label, expected: 'Microscopy field A', ok: expected?.endsWith?.('/hypothenar-field-a') ? label === 'Microscopy field A' : null }
    };
  };
  const installStage8Panel = () => {
    const debugHost = document.getElementById('twin-viewport-debug-host'); if (!debugHost) return;
    const tvd = debugHost.querySelector('.tvd-body'); if (!tvd) return;
    let panel = tvd.querySelector('[data-stage8-panel]');
    if (!panel) {
      panel = document.createElement('section'); panel.dataset.stage8Panel = 'true'; panel.className = 'tvd-section';
      panel.innerHTML = '<h4>ETAP 8 · SPATIAL CONSISTENCY</h4><div data-stage8-body></div>';
      const errorSection = [...tvd.querySelectorAll('.tvd-section')].find(x => x.querySelector('h4')?.textContent === 'ERROR / INTERACTION');
      if (errorSection) tvd.insertBefore(panel, errorSection); else tvd.appendChild(panel);
    }
    const s = stage8Snapshot();
    const esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
    const row = (name, item) => `<div class="tvd-kv"><span>${name}</span><b class="${item.ok ? 'tvd-ok' : 'tvd-error'}">${item.available ? (item.ok ? 'OK' : (item.actual || 'MISSING')) : 'NO SOURCE'}</b></div>`;
    const pass = s.contract.ok && s.manager.ok && s.selectedSpatialNode.ok && s.state.ok && s.registry.ok && (s.labelCheck.ok !== false);
    panel.querySelector('[data-stage8-body]').innerHTML = [
      `<div class="tvd-kv"><span>expected spatial_id</span><b>${esc(s.expected)}</b></div>`,
      `<div class="tvd-kv"><span>path</span><b>${esc(Array.isArray(s.path) ? s.path.join(' > ') : s.path)}</b></div>`,
      row('contract', s.contract), row('manager', s.manager), row('selectedSpatialNode', s.selectedSpatialNode), row('state', s.state),
      `<div class="tvd-kv"><span>registry</span><b class="${s.registry.ok ? 'tvd-ok' : 'tvd-error'}">${s.registry.available ? (s.registry.ok ? 'OK' : `NO MATCH (${s.registry.targetLinked})`) : 'NO DIAGNOSTICS'}</b></div>`,
      `<div class="tvd-kv"><span>label</span><b class="${s.labelCheck.ok === false ? 'tvd-error' : 'tvd-ok'}">${esc(s.labelCheck.actual)}</b></div>`,
      `<div class="tvd-kv"><span>Etap 8</span><b class="${pass ? 'tvd-ok' : 'tvd-error'}">${pass ? 'PASS' : 'CHECK'}</b></div>`
    ].join('');
  };

  // Expanded target-drift diagnostics. Read-only and intentionally independent
  // from the evidence/geometry workflow so it can show *why* downstream stages
  // are empty even when navigation itself is healthy.
  const norm = value => String(value ?? '').trim().replace(/^\/+|\/+$/g, '');
  const pathParts = value => norm(value).split('/').filter(Boolean);
  const idOf = value => norm(canonicalId(value) || value?.target || '');
  const relation = (expected, actual) => {
    const e = norm(expected), a = norm(actual);
    if (!e || !a) return 'MISSING';
    if (e === a) return 'EXACT';
    if (e.startsWith(a + '/')) return 'EXPECTED_IS_DESCENDANT';
    if (a.startsWith(e + '/')) return 'ACTUAL_IS_DESCENDANT';
    const ep = pathParts(e), ap = pathParts(a), common = ep.reduce((n, x, i) => n + (x === ap[i] ? 1 : 0), 0);
    return common ? `SHARED_PREFIX_${common}/${Math.max(ep.length, ap.length)}` : 'UNRELATED';
  };
  const hash = value => { let h = 2166136261; const s = String(value ?? ''); for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return ('00000000' + (h >>> 0).toString(16)).slice(-8); };
  const safe = value => { try { return JSON.stringify(value, null, 2); } catch { return String(value); } };
  const readEvidence = () => { try { const x = JSON.parse(localStorage.getItem('digitalTwinEvidenceUX.v2') || '{}'); return Array.isArray(x.evidence) ? x.evidence.filter(x => !x.archived) : []; } catch { return []; } };
  const readSurface = () => { try { return JSON.parse(localStorage.getItem('digitalTwinHandSurface.v1') || '{}'); } catch { return {}; } };
  const targetFromDom = () => {
    const node = document.getElementById('spatial-node');
    const children = [...document.querySelectorAll('#spatial-children > .spatial-target')];
    const manager = window.spatialViewportManager || window.viewportManager || window.testhpViewportManager || null;
    const contract = window.testhpSpatialContract?.getTarget?.() || window.testhpSpatialContract?.current || null;
    const selected = window.selectedSpatialNode || null;
    const evidenceTarget = window.spatialEvidenceTarget || null;
    const managerId = idOf(manager?.spatialTarget) || idOf(manager?.state?.spatialTarget) || idOf(manager?.state?.target) || idOf(manager?.active);
    const contractId = idOf(contract);
    const selectedId = idOf(selected);
    const evidenceId = idOf(evidenceTarget);
    const chosen = managerId || contractId || selectedId || evidenceId || node?.dataset?.spatialId || document.body?.dataset?.spatialTarget || '';
    return { chosen, manager, contract, selected, evidenceTarget, managerId, contractId, selectedId, evidenceId, node, children };
  };
  const nearest = (records, target) => {
    const tp = pathParts(target);
    return (Array.isArray(records) ? records : []).map((record, index) => {
      const candidates = [record?.spatial_node_id, record?.spatial_id, record?.spatialId, record?.target?.spatial_node_id, record?.target?.spatial_id, record?.target].filter(Boolean).map(String);
      let best = null;
      candidates.forEach(actual => {
        const ap = pathParts(actual), diff = [];
        for (let i = 0; i < Math.max(tp.length, ap.length); i++) if (tp[i] !== ap[i]) diff.push({ index:i, expected:tp[i] || 'MISSING', actual:ap[i] || 'MISSING' });
        const common = tp.reduce((n, x, i) => n + (x === ap[i] ? 1 : 0), 0), score = common * 10 - diff.length;
        if (!best || score > best.score) best = { actual, common, diff, score };
      });
      return { index, record, ...(best || { actual:'', common:0, diff:[], score:-999 }) };
    }).sort((a,b) => b.score - a.score).slice(0, 8);
  };
  const expandedSnapshot = () => {
    const t = targetFromDom(), registry = window.__testhpTwinRegistryDiagnostics || {}, allEvidence = readEvidence(), surface = readSurface();
    const target = norm(t.chosen);
    const cacheTarget = allEvidence.filter(x => idOf(x) === target);
    const allRecords = Array.isArray(registry.allRecords) ? registry.allRecords : [];
    const canonicalRecords = Array.isArray(registry.targetRecords) ? registry.targetRecords : [];
    const mappings = Array.isArray(surface.mappings) ? surface.mappings : [];
    const geometryTarget = idOf(surface) === target ? surface : {};
    const targetMappings = mappings.filter(x => norm(x?.spatialTarget || x?.target || x?.spatial_id || x?.spatialId) === target);
    const decisions = Array.isArray(registry.matchDebug?.decisions) ? registry.matchDebug.decisions : [];
    const buttonRows = t.children.map((button, index) => ({ index:index + 1, label:button.querySelector('strong')?.textContent?.trim() || '', spatialId:button.dataset?.spatialId || null, targetId:button.dataset?.targetId || null, disabled:!!button.disabled, pointerEvents:getComputedStyle(button).pointerEvents, connected:button.isConnected, onclick:String(button.onclick || '').slice(0, 220) }));
    const sources = [
      ['manager.spatialTarget', t.managerId], ['manager.state', idOf(t.manager?.state)], ['manager.active', idOf(t.manager?.active)],
      ['contract', t.contractId], ['selectedSpatialNode', t.selectedId], ['spatialEvidenceTarget', t.evidenceId],
      ['DOM node', norm(t.node?.dataset?.spatialId)], ['BODY dataset', norm(document.body?.dataset?.spatialTarget)]
    ];
    const mismatch = sources.filter(([, value]) => value && norm(value) !== target);
    const activeKey = t.manager?.activeKey || null;
    const activeLayer = t.manager?.activeLayer || t.manager?.active?.activeLayer || null;
    const traceEvents = (window.__testhpSpatialTargetTrace?.getManagerCalls?.() || []).slice(-8);
    const applyEvents = (window.__testhpSpatialTargetTrace?.getApplyCalls?.() || []).slice(-8);
    const selectedEvents = (window.__testhpSpatialTargetTrace?.getSelectedWrites?.() || []).slice(-8);
    return {
      target, fingerprint:hash(target), sources, mismatch,
      manager:{present:!!t.manager, activeKey, activeLayer, version:t.manager?.version || null, state:safe(t.manager?.state || null), active:safe(t.manager?.active || null), spatialTarget:safe(t.manager?.spatialTarget || null), keys:t.manager ? Object.keys(t.manager) : []},
      contract:safe(t.contract), selected:safe(t.selected), evidenceTarget:safe(t.evidenceTarget),
      dom:{label:t.node?.querySelector('strong')?.textContent?.trim() || null, level:document.getElementById('spatial-level-badge')?.textContent?.trim() || null, path:[...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()), childCount:t.children.length, bodySpatialTarget:document.body?.dataset?.spatialTarget || null, buttons:buttonRows},
      registry:{requested:registry.requestedTarget || null, endpoint:registry.endpoint || null, status:registry.status ?? null, ok:registry.ok ?? null, rawCount:registry.rawCount ?? registry.raw_count ?? registry.total ?? null, scopedCount:registry.matchDebug?.scoped_count ?? null, exactCount:registry.matchDebug?.exact_count ?? registry.targetLinked ?? null, returnedCount:registry.matchDebug?.returned_count ?? registry.targetLinked ?? null, rejectedCount:registry.matchDebug?.rejected_count ?? null, prepared:registry.prepared ?? null, responseKeys:registry.responseKeys || null, requestParams:registry.requestParams || registry.params || null, decisions, targetRecords:canonicalRecords.length, allRecords:allRecords.length, nearest:nearest(allRecords, target)},
      cache:{total:allEvidence.length, targetLinked:cacheTarget.length, samples:cacheTarget.slice(0,8).map(x => ({id:x.id, spatial_id:x.spatial_id, spatialId:x.spatialId, target:x.target, view:x.view, filename:x.filename, prepared:x.prepared, preparedAssetId:x.preparedAssetId, prepared_asset_id:x.prepared_asset_id}))},
      geometry:{surfaceTarget:idOf(surface) || null, targetMatch:!!Object.keys(geometryTarget).length, mappingCount:mappings.length, targetMappings:targetMappings.length, targetMappingsSample:targetMappings.slice(0,8), hasProjectionPlan:!!geometryTarget.projectionPlan, hasTwinPackage:!!geometryTarget.twinPackage},
      traces:{managerCalls:traceEvents, applyCalls:applyEvents, selectedWrites:selectedEvents}
    };
  };
  const renderExpandedPanel = () => {
    const host = document.getElementById('twin-viewport-debug-host');
    const tvd = host?.querySelector('.tvd-body');
    if (!tvd) return;
    let panel = tvd.querySelector('[data-expanded-target-panel]');
    if (!panel) {
      panel = document.createElement('section'); panel.dataset.expandedTargetPanel = 'true'; panel.className = 'tvd-section';
      panel.innerHTML = '<h4>EXTENDED TARGET / REGISTRY DIAGNOSTICS</h4><div data-expanded-target-body></div>';
      const stage8 = tvd.querySelector('[data-stage8-panel]');
      if (stage8?.nextSibling) tvd.insertBefore(panel, stage8.nextSibling); else tvd.appendChild(panel);
    }
    const s = expandedSnapshot(), esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const status = (ok, text) => `<b class="${ok ? 'tvd-ok' : 'tvd-error'}">${esc(text)}</b>`;
    const lines = [];
    lines.push(`<div class="tvd-kv"><span>resolved target</span><b>${esc(s.target || 'NULL')}</b></div>`);
    lines.push(`<div class="tvd-kv"><span>target fingerprint</span><b>${esc(s.fingerprint)}</b></div>`);
    lines.push(`<div class="tvd-kv"><span>source drift</span>${status(!s.mismatch.length, s.mismatch.length ? `${s.mismatch.length} MISMATCH` : 'NO MISMATCH')}</div>`);
    lines.push(`<div class="tvd-kv"><span>manager</span>${status(s.manager.present, s.manager.present ? `present · ${s.manager.version || 'no-version'}` : 'MISSING')}</div>`);
    lines.push(`<div class="tvd-kv"><span>activeKey / layer</span><b>${esc(`${s.manager.activeKey || 'NULL'} / ${s.manager.activeLayer || 'NULL'}`)}</b></div>`);
    lines.push(`<div class="tvd-kv"><span>registry target match</span>${status(norm(s.registry.requested) === s.target && Number(s.registry.exactCount || 0) > 0, `${s.registry.exactCount ?? 0} exact / ${s.registry.rawCount ?? 0} raw`)}</div>`);
    lines.push(`<div class="tvd-kv"><span>UX cache target-linked</span>${status(Number(s.cache.targetLinked) > 0, `${s.cache.targetLinked} / ${s.cache.total}`)}</div>`);
    lines.push(`<div class="tvd-kv"><span>geometry target-linked</span>${status(s.geometry.targetMatch || s.geometry.targetMappings > 0, `${s.geometry.targetMappings} mappings · plan=${s.geometry.hasProjectionPlan?'YES':'NO'} · package=${s.geometry.hasTwinPackage?'YES':'NO'}`)}</div>`);
    lines.push(`<div class="tvd-kv"><span>buttons rendered</span><b>${s.dom.childCount} · all connected=${s.dom.buttons.every(x=>x.connected)}</b></div>`);
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">TARGET SOURCE MATRIX</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc(s.sources.map(([k,v]) => `${k.padEnd(24)} ${v || 'NULL'}  relation=${relation(s.target,v)}`).join('\n')) + '</pre></details>');
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">BUTTON ROUTING</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc(s.dom.buttons.map(x => `[${x.index}] ${x.label} | spatialId=${x.spatialId || 'NULL'} | targetId=${x.targetId || 'NULL'} | disabled=${x.disabled} | pointerEvents=${x.pointerEvents}\n    onclick=${x.onclick || 'NULL'}`).join('\n')) + '</pre></details>');
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">REGISTRY MATCH / REJECTION DETAILS</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc([`requested=${s.registry.requested || 'NULL'} endpoint=${s.registry.endpoint || 'NULL'} HTTP=${s.registry.status ?? 'NULL'} ok=${s.registry.ok ?? false}`, `raw=${s.registry.rawCount ?? 'NULL'} scoped=${s.registry.scopedCount ?? 'NULL'} exact=${s.registry.exactCount ?? 'NULL'} returned=${s.registry.returnedCount ?? 'NULL'} rejected=${s.registry.rejectedCount ?? 'NULL'} prepared=${s.registry.prepared ?? 'NULL'}`, `responseKeys=${Array.isArray(s.registry.responseKeys) ? s.registry.responseKeys.join(', ') : 'NULL'}`, `requestParams=${safe(s.registry.requestParams)}`, '', ...s.registry.decisions.slice(0,20).map((x,i) => `[${i+1}] ${x.matched?'ACCEPT':'REJECT'} reason=${x.reason || 'NULL'} expected=${x.expected_spatial_node_id || 'NULL'} actual=${x.actual_spatial_node_id || 'NULL'} evidence=${x.evidence_id || 'NULL'} asset=${x.asset_id || 'NULL'} attachment=${x.attachment_status || 'NULL'}`)].join('\n')) + '</pre></details>');
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">NEAREST REGISTRY RECORDS</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc(s.registry.nearest.map(x => `[${x.index}] score=${x.score} common=${x.common} actual=${x.actual || 'NULL'} diff=${safe(x.diff)}`).join('\n') || '(none)') + '</pre></details>');
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">CACHE / GEOMETRY SAMPLES</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc(`CACHE\n${safe(s.cache.samples)}\n\nGEOMETRY\nsurfaceTarget=${s.geometry.surfaceTarget || 'NULL'}\ntargetMappings=${s.geometry.targetMappings}\n${safe(s.geometry.targetMappingsSample)}`) + '</pre></details>');
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">WRITER / APPLY / MANAGER TRACE</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc(`MANAGER CALLS\n${safe(s.traces.managerCalls)}\n\nAPPLY CALLS\n${safe(s.traces.applyCalls)}\n\nSELECTED WRITES\n${safe(s.traces.selectedWrites)}`) + '</pre></details>');
    lines.push('<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">FULL MANAGER STATE</summary><pre style="white-space:pre-wrap;margin:6px 0 0">' + esc(`keys=${s.manager.keys.join(', ')}\nstate=${s.manager.state}\nactive=${s.manager.active}\nspatialTarget=${s.manager.spatialTarget}`) + '</pre></details>');
    panel.querySelector('[data-expanded-target-body]').innerHTML = lines.join('');
  };

  const installExpanded = () => {
    installStage8Panel();
    renderExpandedPanel();
  };

  installSelectedHook(); installApplyHook(); installManagerHook();
  document.addEventListener('DOMContentLoaded', () => { installSelectedHook(); installApplyHook(); installManagerHook(); installExpanded(); }, { once: true });
  window.addEventListener('testhp:spatial-target-changed', () => { installManagerHook(); installExpanded(); });
  window.addEventListener('testhp:spatial-layer-changed', () => { installApplyHook(); installManagerHook(); installExpanded(); });
  window.addEventListener('testhp:spatial-contract-changed', () => { installApplyHook(); installManagerHook(); installExpanded(); });
  window.addEventListener('testhp:evidence-registry-debug', installExpanded);
  window.addEventListener('testhp:viewport-rendered', installExpanded);
  window.addEventListener('testhp:spatial-writer-trace', installExpanded);
  setInterval(installExpanded, 1000);

  window.__testhpSpatialTargetTrace = Object.freeze({ getSelectedWrites: () => state.selectedWrites.slice(), getApplyCalls: () => state.applyCalls.slice(), getManagerCalls: () => state.managerCalls.slice(), getStage8: () => stage8Snapshot(), getExpanded: () => expandedSnapshot(), clear: () => { state.selectedWrites.length = 0; state.applyCalls.length = 0; state.managerCalls.length = 0; } });
})();
