import { createDigitalTwinState, reduceAnalysisResult, setDigitalTwinError, setSelection } from './canonical-state.js';
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
export function ingestAnalysisResult(result) { state = reduceAnalysisResult(state, adaptAnalysisResult(result)); return publish(); }
export function setAnalysisLoading() { state = createDigitalTwinState(state); state.status = 'analyzing'; state.error = null; return publish(); }
export function setAnalysisError(error) { state = setDigitalTwinError(state, error); return publish(); }
export function setUserInput(input) {
  state = createDigitalTwinState({ ...state, input: { ...state.input, ...input }, modalities: input?.modalities ?? state.modalities });
  state.status = 'validating'; state.error = null; return publish();
}
export function updateSelection(patch = {}) {
  state = sanitizeSelection(state, patch);
  return publish();
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
  version: '4', get: getDigitalTwinState, subscribe: subscribeDigitalTwinState, ingestAnalysisResult,
  fetchAnalysisResult, setLoading: setAnalysisLoading, setAnalysisError, setUserInput, updateSelection, reset: resetDigitalTwinState,
});
window.addEventListener('testhp:end-user-analysis-loaded', () => { if (window.__testhpLastAnalysis) ingestAnalysisResult(window.__testhpLastAnalysis); });
window.addEventListener('testhp:analysis-result', event => { if (event.detail) ingestAnalysisResult(event.detail); });
