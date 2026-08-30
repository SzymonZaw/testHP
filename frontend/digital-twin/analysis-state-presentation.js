import { buildCanonicalViewModel, selectEvidence, selectHealthHierarchy, selectBiologicalAgeHierarchy, selectMolecular, selectCells, selectIntervention, select3DTwin } from './canonical-ui-projections-v1.js';

/** UI semantics for loading, missing, unusable and scientifically unestablished states. */
const LABELS = Object.freeze({
  idle: 'Gotowe do analizy',
  validating: 'Walidacja danych',
  analyzing: 'Analiza w toku',
  ready: 'Analiza zakończona',
  error: 'Błąd analizy',
  missing: 'Brak danych',
  unusable: 'Dane nie nadają się do analizy',
  usable: 'Dane dostępne',
  not_established: 'Nieustalone naukowo',
  validated: 'Zweryfikowane',
  healthy: 'Zdrowe',
  at_risk: 'Podwyższone ryzyko',
  diseased: 'Chorobowe',
  unknown: 'Nieznane',
});

export function presentStatus(status) {
  return LABELS[String(status || '').toLowerCase()] || 'Nieustalone';
}

export function canDisplayBiologicalValue(value) {
  return value != null && Number.isFinite(Number(value));
}

export function modalityState(qc, modelMetadata) {
  const qcStatus = qc?.status || 'missing';
  if (qcStatus !== 'usable') return qcStatus;
  return String(modelMetadata?.validation_status || 'not_established').toLowerCase() === 'validated'
    ? 'validated'
    : 'not_established';
}

/** Resolve the rendering state before a module chooses its visual component. */
export function presentAnalysisState(state) {
  const status = String(state?.status || 'idle').toLowerCase();
  if (status === 'error') return { state: 'error', label: presentStatus('error'), message: state?.error || 'Analiza nie powiodła się.' };
  if (status === 'validating') return { state: 'loading', label: presentStatus('validating'), message: 'Sprawdzanie danych wejściowych.' };
  if (status === 'analyzing') return { state: 'loading', label: presentStatus('analyzing'), message: 'Obliczanie wyniku.' };
  return { state: status === 'ready' ? 'ready' : 'empty', label: presentStatus(status), message: status === 'ready' ? null : 'Brak wyniku analizy.' };
}

export const canonicalViews = Object.freeze({
  buildCanonicalViewModel,
  selectEvidence,
  selectHealthHierarchy,
  selectBiologicalAgeHierarchy,
  selectMolecular,
  selectCells,
  selectIntervention,
  select3DTwin,
});

window.TestHPCanonicalViews = canonicalViews;
window.TestHPAnalysisPresentation = Object.freeze({ presentStatus, canDisplayBiologicalValue, modalityState, presentAnalysisState });

window.addEventListener('testhp:canonical-state-changed', event => {
  const state = event.detail;
  const viewModel = buildCanonicalViewModel(state);
  const events = [
    ['evidence', viewModel.evidence],
    ['health', viewModel.health],
    ['biological-age', viewModel.biologicalAge],
    ['molecular', viewModel.molecular],
    ['cells', viewModel.cells],
    ['intervention', viewModel.intervention],
    ['3d-twin', viewModel.twin3d],
  ];
  window.dispatchEvent(new CustomEvent('testhp:canonical-view-model-changed', { detail: viewModel }));
  events.forEach(([domain, detail]) => {
    window.dispatchEvent(new CustomEvent(`testhp:canonical-${domain}-changed`, { detail }));
  });
});
