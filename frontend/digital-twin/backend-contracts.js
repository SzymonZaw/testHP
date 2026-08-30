/** Canonical frontend mirrors of backend analysis contracts. */

export const QC_STATUSES = Object.freeze(['missing', 'unusable', 'usable']);
export const BIOLOGICAL_STATUSES = Object.freeze(['not_established', 'available']);
export const HEALTH_STATES = Object.freeze(['healthy', 'at_risk', 'diseased', 'unknown']);

export function normalizeQCResult(value) {
  const status = QC_STATUSES.includes(value?.status) ? value.status : 'missing';
  return {
    modality: value?.modality ?? 'unknown', status,
    reasons: Array.isArray(value?.reasons) ? value.reasons : [],
    metrics: value?.metrics && typeof value.metrics === 'object' ? value.metrics : {},
  };
}

export function normalizeProvenance(value) {
  return {
    input_id: value?.input_id ?? null, analysis_id: value?.analysis_id ?? null,
    model_id: value?.model_id ?? null, model_version: value?.model_version ?? null,
    dataset_version: value?.dataset_version ?? null, pipeline_version: value?.pipeline_version ?? null,
    timestamp: value?.timestamp ?? null, source: value?.source ?? 'unknown',
  };
}

export function normalizeValidationRecord(value) {
  return {
    model_id: value?.model_id ?? null, training_dataset: value?.training_dataset ?? null,
    validation_dataset: value?.validation_dataset ?? null, test_dataset: value?.test_dataset ?? null,
    metrics: value?.metrics && typeof value.metrics === 'object' ? value.metrics : {},
    population: value?.population ?? null, tissue: value?.tissue ?? null,
    cell_type: value?.cell_type ?? null, validation_status: value?.validation_status ?? 'not_validated',
  };
}

export function normalizeModelMetadata(value) {
  return {
    model_id: value?.model_id ?? null, version: value?.version ?? null, task: value?.task ?? null,
    input_modalities: Array.isArray(value?.input_modalities) ? value.input_modalities : [],
    target_level: value?.target_level ?? null,
    tissue_scope: Array.isArray(value?.tissue_scope) ? value.tissue_scope : [],
    cell_type_scope: Array.isArray(value?.cell_type_scope) ? value.cell_type_scope : [],
    training_dataset: value?.training_dataset ?? null, validation_dataset: value?.validation_dataset ?? null,
    performance: value?.performance && typeof value.performance === 'object' ? value.performance : {},
    validation_status: value?.validation_status ?? 'not_validated',
  };
}

export function normalizeAnalysisResult(value) {
  return {
    provenance: normalizeProvenance(value?.provenance),
    validation: value?.validation && typeof value.validation === 'object' ? value.validation : {},
    qc: Array.isArray(value?.qc) ? value.qc.map(normalizeQCResult) : [],
    features: value?.features && typeof value.features === 'object' ? value.features : {},
    evidence: value?.evidence && typeof value.evidence === 'object' ? value.evidence : { coverage: null, confidence: null, missing_modalities: [], items: [] },
    modalities: value?.modalities && typeof value.modalities === 'object' ? value.modalities : {},
    anatomy: value?.anatomy && typeof value.anatomy === 'object' ? value.anatomy : { hand: null, regions: [], tissues: [], cells: [] },
    assets: Array.isArray(value?.assets) ? value.assets : [],
    cells: Array.isArray(value?.cells) ? value.cells : [],
    trajectory: value?.trajectory ?? value?.aging_trajectory ?? null,
    disease_trajectory: value?.disease_trajectory ?? null,
    biological_age: value?.biological_age ?? { status: 'not_established', biological_age: null },
    health_state: value?.health_state ?? { state: 'unknown' },
    molecular_states: Array.isArray(value?.molecular_states) ? value.molecular_states : [],
    multimodal_state: value?.multimodal_state ?? { status: 'not_established' },
    intervention_priority: value?.intervention_priority ?? { status: 'not_established', clinical_validation: false },
  };
}

export function qcSummary(qc = []) {
  return qc.reduce((summary, item) => {
    const status = QC_STATUSES.includes(item.status) ? item.status : 'missing';
    summary[status] += 1;
    return summary;
  }, { missing: 0, unusable: 0, usable: 0 });
}
