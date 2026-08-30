const HEALTH_STATES = new Set(['healthy', 'at_risk', 'diseased', 'unknown']);
const QC_STATES = new Set(['usable', 'unusable', 'missing']);

function statusForQC(item) {
  return QC_STATES.has(item?.status) ? item.status : 'missing';
}

function modelStatus(value) {
  return value?.status ?? 'not_established';
}

function normalizeLevel(value, fallback = 'unknown') {
  return HEALTH_STATES.has(value) ? value : fallback;
}

export function selectEvidence(state) {
  const qc = Array.isArray(state?.qc) ? state.qc : [];
  const modalities = state?.modalities && typeof state.modalities === 'object' ? state.modalities : {};
  const evidence = state?.evidence ?? {};
  const usable = qc.filter(item => statusForQC(item) === 'usable').length;
  const unusable = qc.filter(item => statusForQC(item) === 'unusable').length;
  const missing = qc.filter(item => statusForQC(item) === 'missing').length;
  return { coverage: evidence.coverage ?? null, confidence: evidence.confidence ?? null, missingModalities: Array.isArray(evidence.missingModalities) ? evidence.missingModalities : [], qc: { usable, unusable, missing }, modalities, provenance: state?.provenance ?? null, validation: state?.validation ?? null, uncertainty: state?.uncertainty ?? null };
}

export function selectHealthHierarchy(state) {
  const anatomy = state?.anatomy ?? {};
  const health = state?.health ?? {};
  return { hand: { id: 'hand', label: 'Whole Hand', health: normalizeLevel(health.state), confidence: health.confidence ?? null, uncertainty: health.uncertainty ?? state?.uncertainty ?? null, evidence: health.evidence ?? state?.evidence ?? null }, regions: Array.isArray(anatomy.regions) ? anatomy.regions : [], tissues: Array.isArray(anatomy.tissues) ? anatomy.tissues : [], cells: Array.isArray(anatomy.cells) ? anatomy.cells : [] };
}

export function selectBiologicalAgeHierarchy(state) {
  const age = state?.biologicalAge ?? {};
  const levels = Array.isArray(age.levels) ? age.levels : [];
  return { status: modelStatus(age), modelId: age.model_id ?? null, modelVersion: age.model_version ?? null, levels: levels.map(level => ({ id: level.id ?? null, level: level.level ?? null, label: level.label ?? level.level ?? 'Unknown', age: level.age ?? null, uncertainty: level.uncertainty ?? null, confidence: level.confidence ?? null, evidence: level.evidence ?? null, status: level.status ?? modelStatus(age) })) };
}

export function selectMolecular(state) {
  const states = Array.isArray(state?.molecular?.states) ? state.molecular.states : [];
  const byModality = { rna: null, proteomics: null, epigenetics: null, genomics: null };
  states.forEach(item => { const key = String(item?.modality ?? '').toLowerCase(); if (key in byModality) byModality[key] = item; });
  return Object.fromEntries(Object.entries(byModality).map(([key, item]) => [key, { availability: item?.availability ?? (item ? 'available' : 'missing'), qc: item?.qc ?? null, features: item?.features ?? [], biological_state: item?.biological_state ?? null, confidence: item?.confidence ?? null, evidence: item?.evidence ?? null }]));
}

export function selectCells(state) {
  const cells = Array.isArray(state?.anatomy?.cells) ? state.anatomy.cells : [];
  return cells.map(cell => ({ id: cell.id ?? null, cell_type: cell.cell_type ?? cell.type ?? 'unknown', location: cell.location ?? null, tissue: cell.tissue ?? null, count: cell.count ?? null, health: cell.health ?? { state: 'unknown' }, age: cell.age ?? null, molecular_state: cell.molecular_state ?? null, confidence: cell.confidence ?? null, evidence: cell.evidence ?? null }));
}

export function selectIntervention(state) {
  const value = state?.interventions ?? {};
  return { status: modelStatus(value), priority: value.priority ?? null, confidence: value.confidence ?? null, evidence: value.evidence ?? null, validation_status: value.validation_status ?? null, clinical_validation: value.clinical_validation ?? false };
}

export function select3DTwin(state) {
  const hierarchy = selectHealthHierarchy(state);
  const selected = state?.selectedRegion ?? state?.selection ?? null;
  return { selected, health: hierarchy.hand, regions: hierarchy.regions.map(region => ({ id: region.id ?? null, label: region.label ?? region.name ?? 'Unknown', health: normalizeLevel(region.health?.state ?? region.health), confidence: region.health?.confidence ?? region.confidence ?? null, uncertainty: region.health?.uncertainty ?? null, evidence: region.health?.evidence ?? region.evidence ?? null })) };
}

export function buildCanonicalViewModel(state) {
  return { evidence: selectEvidence(state), health: selectHealthHierarchy(state), biologicalAge: selectBiologicalAgeHierarchy(state), molecular: selectMolecular(state), cells: selectCells(state), intervention: selectIntervention(state), twin3d: select3DTwin(state) };
}

window.TestHPCanonicalViews = Object.freeze({ selectEvidence, selectHealthHierarchy, selectBiologicalAgeHierarchy, selectMolecular, selectCells, selectIntervention, select3DTwin, buildCanonicalViewModel });
