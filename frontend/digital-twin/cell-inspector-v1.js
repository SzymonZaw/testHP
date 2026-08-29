(() => {
  'use strict';

  const KEY = '__testhpCellInspectorV1';
  if (window[KEY]) return;

  const runtime = () => window.__testhpDigitalTwinRuntime || null;
  const state = { selectedCellId: null };

  function select(cellId) {
    state.selectedCellId = cellId ? String(cellId) : null;
    window.dispatchEvent(new CustomEvent('testhp:cell-selected', {
      detail: { cellId: state.selectedCellId }
    }));
    return state.selectedCellId;
  }

  function snapshot() {
    const twinRuntime = runtime();
    return twinRuntime?.snapshot ? twinRuntime.snapshot() : null;
  }

  const api = Object.freeze({ select, snapshot, state });
  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:cell-inspector-ready'));
})();
