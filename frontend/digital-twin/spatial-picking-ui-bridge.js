import { updateSelection } from './canonical-ui-runtime.js';

(() => {
  'use strict';
  if (window.__testhpSpatialPickingUIBridge) return;
  window.__testhpSpatialPickingUIBridge = true;

  window.addEventListener('testhp:spatial-picked', (event) => {
    const detail = event?.detail || {};
    const selection = {};
    if (detail.regionId) selection.region = detail.regionId;
    if (detail.tissueId) selection.tissue = detail.tissueId;
    if (detail.cellId) selection.cell = detail.cellId;
    if (!Object.keys(selection).length) return;

    updateSelection({ ...selection, molecularLayer: null });
    window.dispatchEvent(new CustomEvent('testhp:spatial-selection-committed', {
      detail: { ...detail, selection }
    }));
  });
})();
