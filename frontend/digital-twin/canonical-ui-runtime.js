import { createDigitalTwinState, reduceAnalysisResult, setDigitalTwinError } from './canonical-state.js';
import { adaptAnalysisResult } from './analysis-result-adapter.js';
import { sanitizeSelection, saveCanonicalSelection, loadCanonicalSelection } from './digital-twin-phase1-8-governor.js';

let state = createDigitalTwinState();
const subscribers = new Set();
function snapshot() { return typeof structuredClone === 'function' ? structuredClone(state) : JSON.parse(JSON.stringify(state)); }
function publish() {
  const next = snapshot();
  subscribers.forEach(listener => listener(next));
  saveCanonicalSelection(next.selection);
  window.dispatchEvent(new CustomEvent('testhp:canonical-state-changed', { detail: next }));
  return next;
}
export function getDigitalTwinState() { return snapshot(); }
export function subscribeDigitalTwinState(listener) {
  if (typeof listener !== 'function') throw new TypeError('listener must be a function');
  subscribers.add(listener); listener(snapshot()); return () => subscribers.delete(listener);
}
export function ingestAnalysisResult(result) {
  state = reduceAnalysisResult(state, adaptAnalysisResult(result));
  state = sanitizeSelection(state, state.selection);
  return publish();
}
export function setAnalysisLoading() { state = createDigitalTwinState(state); state.status = 'analyzing'; state.error = null; return publish(); }
export function setAnalysisError(error) { state = setDigitalTwinError(state, error); return publish(); }
export function setUserInput(input) {
  state = createDigitalTwinState({ ...state, input: { ...state.input, ...input }, modalities: input?.modalities ?? state.modalities });
  state.status = 'validating'; state.error = null; return publish();
}

// A timepoint change invalidates all result data from the previous timepoint.
// The next backend response repopulates the state. This prevents stale T0 data
// from being displayed while T1/T2/T3 is loading or when its endpoint fails.
export function updateSelection(patch = {}) {
  const previous = state.selection.timepoint;
  state = sanitizeSelection(state, patch);
  if (Object.prototype.hasOwnProperty.call(patch, 'timepoint') && state.timepoint !== previous) {
    clearAnalysisDataInPlace();
  }
  return publish();
}

function clearAnalysisDataInPlace() {
  state.status = 'idle';
  state.error = null;
  state.qc = [];
  state.modalities = {};
  state.assets = [];
  state.cells = [];
  state.anatomy = { hand: null, regions: [], tissues: [], cells: [] };
  state.trajectory = null;
  state.diseaseTrajectory = null;
  state.whatIf = null;
  state.molecular = { rna: null, proteomics: null, epigenetics: null, genomics: null, states: [] };
  state.health = null;
  state.biologicalAge = null;
  state.evidence = { coverage: null, confidence: null, missingModalities: [], items: [] };
  state.biologicalState = {
    health: { status: 'Not established', value: null, confidence: null, uncertainty: null, provenance: null },
    diseaseState: { status: 'Not established', value: null, confidence: null, uncertainty: null, provenance: null },
    biologicalAge: { status: 'Not established', value: null, confidence: null, uncertainty: null, provenance: null },
    confidence: null,
    uncertainty: null,
    status: 'Not established',
  };
  state.uncertainty = null;
  state.provenance = null;
  state.validation = null;
  state.interventions = null;
  state.modelMetadata = null;
}

export async function fetchAnalysisResult(endpoint, options = {}, fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== 'function') throw new TypeError('fetch implementation is required');
  if (!endpoint) throw new TypeError('analysis endpoint is required');
  setAnalysisLoading();
  try {
    const response = await fetchImpl(endpoint, { ...options, headers: { Accept: 'application/json', ...(options.headers || {}) } });
    if (!response.ok) throw new Error(`Analysis request failed: HTTP ${response.status}`);
    return ingestAnalysisResult(await response.json());
  } catch (error) { setAnalysisError(error); throw error; }
}
export function resetDigitalTwinState() { state = createDigitalTwinState(); return publish(); }

const restored = loadCanonicalSelection();
if (restored) state = sanitizeSelection(state, restored);

window.TestHPCanonicalState = Object.freeze({
  version: '6', get: getDigitalTwinState, subscribe: subscribeDigitalTwinState, ingestAnalysisResult,
  fetchAnalysisResult, setLoading: setAnalysisLoading, setAnalysisError, setUserInput, updateSelection, reset: resetDigitalTwinState,
});

// A local spatial extract is a bounded, already-materialized source. Registering
// the clicked cell in anatomy lets the normal governor validate the cell ID
// instead of bypassing canonical selection safety for this one event path.
window.addEventListener('testhp:local-cell-selected', event => {
  const detail = event?.detail;
  const cell = detail?.cell;
  const region = String(detail?.region || '').trim().toLowerCase();
  const cellId = cell?.cellId ?? cell?.cell_id ?? null;
  const currentRegion = String(state.selection?.region || '').trim().toLowerCase();
  if (detail?.sourceId !== 'human-skin-spatial-census' || !cellId || !region || region !== currentRegion) return;
  const existing = Array.isArray(state.anatomy?.cells) ? state.anatomy.cells : [];
  const id = String(cellId);
  if (!existing.some(item => String(item?.cellId ?? item?.cell_id ?? item?.id ?? '') === id)) {
    state = createDigitalTwinState({
      ...state,
      anatomy: { ...state.anatomy, cells: [...existing, { ...cell, region }] },
    });
  }
  state = sanitizeSelection(state, { cell: id });
  if (state.selection.cell === id) publish();
});

window.addEventListener('testhp:end-user-analysis-loaded', () => { if (window.__testhpLastAnalysis) ingestAnalysisResult(window.__testhpLastAnalysis); });
window.addEventListener('testhp:analysis-result', event => { if (event.detail) ingestAnalysisResult(event.detail); });
