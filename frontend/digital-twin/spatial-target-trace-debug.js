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

  installSelectedHook(); installApplyHook(); installManagerHook();
  document.addEventListener('DOMContentLoaded', () => { installSelectedHook(); installApplyHook(); installManagerHook(); installStage8Panel(); }, { once: true });
  window.addEventListener('testhp:spatial-target-changed', () => { installManagerHook(); installStage8Panel(); });
  window.addEventListener('testhp:spatial-layer-changed', () => { installApplyHook(); installManagerHook(); installStage8Panel(); });
  window.addEventListener('testhp:spatial-contract-changed', () => { installApplyHook(); installManagerHook(); installStage8Panel(); });
  window.addEventListener('testhp:evidence-registry-debug', () => installStage8Panel());

  window.__testhpSpatialTargetTrace = Object.freeze({ getSelectedWrites: () => state.selectedWrites.slice(), getApplyCalls: () => state.applyCalls.slice(), getManagerCalls: () => state.managerCalls.slice(), getStage8: () => stage8Snapshot(), clear: () => { state.selectedWrites.length = 0; state.applyCalls.length = 0; state.managerCalls.length = 0; } });
})();
