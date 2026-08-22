(() => {
  'use strict';

  // Read-only diagnostics. Hooks only record calls/assignments; they do not normalize or change values.
  const state = {
    installedAt: Date.now(),
    selectedWrites: [],
    applyCalls: [],
    managerCalls: []
  };
  const MAX = 30;
  const push = (arr, value) => { arr.push(value); if (arr.length > MAX) arr.shift(); };
  const stack = () => { try { return new Error().stack || null; } catch { return null; } };
  const valueOf = v => {
    if (v == null) return null;
    if (typeof v === 'string') return v;
    try { return { id: v.id || v.regionId || null, spatial_id: v.spatial_id || v.spatialId || null, label: v.label || v.name || null, level: v.level || null }; }
    catch { return String(v); }
  };
  const recordSelected = (value, phase) => push(state.selectedWrites, {
    t: Date.now() - state.installedAt,
    phase,
    value: valueOf(value),
    stack: stack()
  });
  const recordApply = (args, phase) => push(state.applyCalls, {
    t: Date.now() - state.installedAt,
    phase,
    args: Array.from(args).map(valueOf),
    stack: stack()
  });
  const installSelectedHook = () => {
    try {
      const desc = Object.getOwnPropertyDescriptor(window, 'selectedSpatialNode');
      if (desc && desc.configurable === false) return false;
      let current = desc?.get ? desc.get.call(window) : window.selectedSpatialNode;
      Object.defineProperty(window, 'selectedSpatialNode', {
        configurable: true,
        enumerable: desc?.enumerable ?? true,
        get() { return desc?.get ? desc.get.call(window) : current; },
        set(value) {
          recordSelected(value, 'SET');
          if (desc?.set) desc.set.call(window, value); else current = value;
        }
      });
      recordSelected(current, 'INSTALL');
      return true;
    } catch (error) {
      push(state.selectedWrites, { t: Date.now() - state.installedAt, phase: 'INSTALL_ERROR', error: String(error), stack: stack() });
      return false;
    }
  };
  const installApplyHook = () => {
    try {
      if (typeof window.applySpatialNode !== 'function' || window.applySpatialNode.__testhpTraceWrapped) return false;
      const original = window.applySpatialNode;
      const wrapped = function(...args) {
        recordApply(args, 'CALL');
        return original.apply(this, args);
      };
      Object.defineProperty(wrapped, '__testhpTraceWrapped', { value: true });
      window.applySpatialNode = wrapped;
      return true;
    } catch (error) {
      push(state.applyCalls, { t: Date.now() - state.installedAt, phase: 'INSTALL_ERROR', error: String(error), stack: stack() });
      return false;
    }
  };
  const installManagerHook = () => {
    try {
      const manager = window.viewportManager || window.testhpViewportManager;
      if (!manager || typeof manager.setSpatialTarget !== 'function' || manager.setSpatialTarget.__testhpTraceWrapped) return false;
      const original = manager.setSpatialTarget;
      const wrapped = function(...args) {
        push(state.managerCalls, { t: Date.now() - state.installedAt, phase: 'CALL', args: args.map(valueOf), stack: stack() });
        return original.apply(this, args);
      };
      Object.defineProperty(wrapped, '__testhpTraceWrapped', { value: true });
      manager.setSpatialTarget = wrapped;
      return true;
    } catch { return false; }
  };

  installSelectedHook();
  installApplyHook();
  installManagerHook();
  document.addEventListener('DOMContentLoaded', () => { installSelectedHook(); installApplyHook(); installManagerHook(); }, { once: true });

  window.addEventListener('testhp:spatial-target-changed', () => installManagerHook());
  window.addEventListener('testhp:spatial-layer-changed', () => { installApplyHook(); installManagerHook(); });
  window.addEventListener('testhp:spatial-contract-changed', () => { installApplyHook(); installManagerHook(); });

  window.__testhpSpatialTargetTrace = Object.freeze({
    getSelectedWrites: () => state.selectedWrites.slice(),
    getApplyCalls: () => state.applyCalls.slice(),
    getManagerCalls: () => state.managerCalls.slice(),
    clear: () => { state.selectedWrites.length = 0; state.applyCalls.length = 0; state.managerCalls.length = 0; }
  });
})();
