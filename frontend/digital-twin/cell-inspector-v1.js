(() => {
  'use strict';

  const KEY = '__testhpCellInspectorV1';
  if (window[KEY]) return;

  const runtime = () => window.__testhpDigitalTwinRuntime || null;
  const state = { selectedCellId: null, canonicalCells: [] };

  function select(cellId) {
    state.selectedCellId = cellId ? String(cellId) : null;
    const cell = state.canonicalCells.find(item => String(item.id) === state.selectedCellId) || null;
    window.dispatchEvent(new CustomEvent('testhp:cell-selected', {
      detail: { cellId: state.selectedCellId, cell }
    }));
    return state.selectedCellId;
  }

  function snapshot() {
    if (window.TestHPCanonicalState?.get) return window.TestHPCanonicalState.get();
    const twinRuntime = runtime();
    return twinRuntime?.snapshot ? twinRuntime.snapshot() : null;
  }

  function canonicalSnapshot() {
    return window.TestHPCanonicalState?.get ? window.TestHPCanonicalState.get() : null;
  }

  window.addEventListener('testhp:canonical-cells-changed', event => {
    state.canonicalCells = Array.isArray(event.detail) ? event.detail : [];
    window.dispatchEvent(new CustomEvent('testhp:cell-inspector-data-changed', {
      detail: state.canonicalCells
    }));
  });

  const api = Object.freeze({ select, snapshot, canonicalSnapshot, state });
  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:cell-inspector-ready'));
})();
