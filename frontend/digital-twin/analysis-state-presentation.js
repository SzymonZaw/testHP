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
