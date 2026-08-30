import { buildCanonicalViewModel, selectEvidence, selectHealthHierarchy, selectBiologicalAgeHierarchy, selectMolecular, selectCells, selectIntervention, select3DTwin } from './canonical-ui-projections-v1.js';

/** UI semantics for missing, unusable and scientifically unestablished states. */
const LABELS = Object.freeze({
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
