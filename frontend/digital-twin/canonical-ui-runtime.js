import { createDigitalTwinState, reduceAnalysisResult, setDigitalTwinError } from './canonical-state.js';
import { adaptAnalysisResult } from './analysis-result-adapter.js';

let state = createDigitalTwinState();
const subscribers = new Set();

function snapshot() {
  return typeof structuredClone === 'function'
    ? structuredClone(state)
    : JSON.parse(JSON.stringify(state));
}

function publish() {
  const next = snapshot();
  subscribers.forEach(listener => listener(next));
  window.dispatchEvent(new CustomEvent('testhp:canonical-state-changed', { detail: next }));
  return next;
}

export function getDigitalTwinState() { return snapshot(); }
export function subscribeDigitalTwinState(listener) {
  if (typeof listener !== 'function') throw new TypeError('listener must be a function');
  subscribers.add(listener);
  listener(snapshot());
  return () => subscribers.delete(listener);
}
export function ingestAnalysisResult(result) {
  const adapted = adaptAnalysisResult(result);
  state = reduceAnalysisResult(state, adapted);
  return publish();
}
export function setAnalysisError(error) {
  state = setDigitalTwinError(state, error);
  return publish();
}
export function setUserInput(input) {
  state = createDigitalTwinState({
    ...state,
    input: { ...state.input, ...input },
    modalities: input?.modalities ?? state.modalities,
  });
  state.status = 'validating';
  return publish();
}
export function resetDigitalTwinState() {
  state = createDigitalTwinState();
  return publish();
}

window.TestHPCanonicalState = Object.freeze({
  version: '1',
  get: getDigitalTwinState,
  subscribe: subscribeDigitalTwinState,
  ingestAnalysisResult,
  setAnalysisError,
  setUserInput,
  reset: resetDigitalTwinState,
});

window.addEventListener('testhp:end-user-analysis-loaded', () => {
  if (window.__testhpLastAnalysis) ingestAnalysisResult(window.__testhpLastAnalysis);
});
window.addEventListener('testhp:analysis-result', event => {
  if (event.detail) ingestAnalysisResult(event.detail);
});
