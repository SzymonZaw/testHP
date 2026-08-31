import { createDigitalTwinState, setSelection } from './canonical-state.js';

export const NOT_ESTABLISHED = 'Not established';
export const SPATIAL_REGIONS = Object.freeze([
  ['palm', 'Palm'], ['thumb', 'Thumb'], ['index', 'Index'], ['middle', 'Middle'],
  ['ring', 'Ring'], ['little', 'Little'], ['wrist', 'Wrist'],
]);
export const MOLECULAR_LAYERS = Object.freeze([
  ['rna', 'RNA'], ['gene_expression', 'Gene expression'],
  ['spatial_transcriptomics', 'Spatial transcriptomics'], ['proteomics', 'Proteomics'],
  ['epigenetics', 'Epigenetics'], ['genomics', 'Genomics'], ['multi_omics', 'Multi-omics'],
]);

const STORAGE_KEY = 'testhp.digitalTwin.canonicalSelection.v1';
const VALID_TIMEPOINTS = new Set(['T0', 'T1', 'T2', 'T3']);

export function displayNotEstablished(value) {
  return value === undefined || value === null || value === '' ? NOT_ESTABLISHED : value;
}

export function suppliedCellId(cell) {
  const id = cell?.cell_id ?? cell?.cellId ?? cell?.id ?? null;
  return id === undefined || id === null || id === '' ? null : String(id);
}

export function suppliedTissueId(tissue) {
  const id = tissue?.tissue_id ?? tissue?.tissueId ?? tissue?.id ?? tissue?.name ?? null;
  return id === undefined || id === null || id === '' ? null : String(id);
}

export function anatomyForState(state) {
  const anatomy = state?.anatomy && typeof state.anatomy === 'object' ? state.anatomy : {};
  return {
    hand: anatomy.hand ?? null,
    regions: Array.isArray(anatomy.regions) ? anatomy.regions : [],
    tissues: Array.isArray(anatomy.tissues) ? anatomy.tissues : [],
    cells: Array.isArray(anatomy.cells) ? anatomy.cells : [],
  };
}

export function suppliedTissues(state, region) {
  return anatomyForState(state).tissues.filter((tissue) => {
    const tissueRegion = tissue?.region_id ?? tissue?.regionId ?? tissue?.region ?? null;
    return (tissueRegion === null || String(tissueRegion) === String(region)) && suppliedTissueId(tissue);
  });
}

export function suppliedCells(state, region, tissue = null) {
  return anatomyForState(state).cells.filter((cell) => {
    if (!suppliedCellId(cell)) return false;
    const cellRegion = cell?.region_id ?? cell?.regionId ?? cell?.region ?? null;
    const cellTissue = cell?.tissue_id ?? cell?.tissueId ?? cell?.tissue ?? null;
    if (cellRegion !== null && String(cellRegion) !== String(region)) return false;
    if (tissue !== null && cellTissue !== null && String(cellTissue) !== String(tissue)) return false;
    return true;
  });
}

export function suppliedMolecularLayers(state, cellId) {
  if (!cellId) return [];
  const states = Array.isArray(state?.molecular?.states) ? state.molecular.states : [];
  const layers = new Set();
  for (const item of states) {
    const itemCell = item?.cell_id ?? item?.cellId ?? item?.cell ?? null;
    if (itemCell !== null && String(itemCell) !== String(cellId)) continue;
    const layer = item?.layer ?? item?.molecular_layer ?? item?.modality ?? null;
    if (layer) layers.add(String(layer));
  }
  return MOLECULAR_LAYERS.filter(([id]) => layers.has(id)).map(([id, label]) => ({ id, label }));
}

export function canonicalSpatialTree(state) {
  const region = state?.selection?.region ?? 'palm';
  const tissue = state?.selection?.tissue ?? null;
  const cell = state?.selection?.cell ?? null;
  return {
    hand: { id: 'hand', label: 'Hand' },
    regions: SPATIAL_REGIONS.map(([id, label]) => ({
      id, label, selected: id === region, supplied: true,
      tissues: id === region ? suppliedTissues(state, id).map((item) => ({
        id: suppliedTissueId(item), label: item?.name ?? item?.label ?? suppliedTissueId(item),
        selected: suppliedTissueId(item) === tissue,
        cells: suppliedCells(state, id, suppliedTissueId(item)).map((itemCell) => ({
          id: suppliedCellId(itemCell), label: itemCell?.label ?? suppliedCellId(itemCell),
          selected: suppliedCellId(itemCell) === cell,
        })),
      })) : [],
    })),
  };
}

export function sanitizeSelection(state, patch = {}) {
  let next = setSelection(state, patch);
  const region = next.selection.region;
  if (next.selection.tissue && !suppliedTissues(next, region).some((item) => suppliedTissueId(item) === String(next.selection.tissue))) {
    next = setSelection(next, { tissue: null, cell: null, molecularLayer: null });
  }
  if (
    next.selection.cell &&
    !Object.prototype.hasOwnProperty.call(patch, 'cell') &&
    !suppliedCells(next, region, next.selection.tissue).some(
      (item) => suppliedCellId(item) === String(next.selection.cell)
    )
  ) {
    next = setSelection(next, { cell: null, molecularLayer: null });
  }
  if (next.selection.molecularLayer && !suppliedMolecularLayers(next, next.selection.cell).some((item) => item.id === next.selection.molecularLayer)) {
    next = setSelection(next, { molecularLayer: null });
  }
  return next;
}

export function saveCanonicalSelection(selection, storage = globalThis.localStorage) {
  if (!storage) return;
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify({
      subject: selection?.subject ?? 'own_cohort',
      timepoint: VALID_TIMEPOINTS.has(selection?.timepoint) ? selection.timepoint : 'T0',
      region: selection?.region ?? 'palm', tissue: selection?.tissue ?? null,
      cell: selection?.cell ?? null, molecularLayer: selection?.molecularLayer ?? null,
    }));
  } catch { /* best effort */ }
}

export function loadCanonicalSelection(storage = globalThis.localStorage) {
  if (!storage) return null;
  try {
    const value = JSON.parse(storage.getItem(STORAGE_KEY) || 'null');
    if (!value || typeof value !== 'object') return null;
    return {
      subject: value.subject ?? 'own_cohort',
      timepoint: VALID_TIMEPOINTS.has(value.timepoint) ? value.timepoint : 'T0',
      region: value.region ?? 'palm', tissue: value.tissue ?? null,
      cell: value.cell ?? null, molecularLayer: value.molecularLayer ?? null,
    };
  } catch { return null; }
}

function removeUnsupportedCellsFromLegacyTree() {
  document.querySelectorAll('[data-cell]').forEach((button) => {
    if (!button.getAttribute('data-cell')) button.remove();
  });
}

function installRuntimeGuards() {
  if (window.__testhpPhase1to8Governor) return;
  window.__testhpPhase1to8Governor = true;
  const restored = loadCanonicalSelection();
  if (restored && typeof window.TestHPCanonicalState?.updateSelection === 'function') {
    const current = window.TestHPCanonicalState.get?.() ?? createDigitalTwinState();
    const safe = sanitizeSelection(current, restored);
    window.TestHPCanonicalState.updateSelection(safe.selection);
  }
  window.addEventListener('testhp:canonical-state-changed', (event) => {
    const state = event.detail;
    if (state?.selection) saveCanonicalSelection(state.selection);
    removeUnsupportedCellsFromLegacyTree();
  });
  const observer = new MutationObserver(removeUnsupportedCellsFromLegacyTree);
  observer.observe(document.body, { childList: true, subtree: true });
}

export function installPhase1to8Governor() {
  installRuntimeGuards();
  return { notEstablished: NOT_ESTABLISHED, spatialTree: canonicalSpatialTree(window.TestHPCanonicalState?.get?.() ?? createDigitalTwinState()) };
}

if (typeof window !== 'undefined') {
  window.TestHPPhase1to8 = Object.freeze({
    NOT_ESTABLISHED, SPATIAL_REGIONS, MOLECULAR_LAYERS, suppliedCellId, suppliedTissueId,
    suppliedTissues, suppliedCells, suppliedMolecularLayers, canonicalSpatialTree,
    sanitizeSelection, saveCanonicalSelection, loadCanonicalSelection,
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installPhase1to8Governor, { once: true });
  else installPhase1to8Governor();
}
