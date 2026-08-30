import { normalizeAnalysisResult } from './backend-contracts.js';

export const DIGITAL_TWIN_STATE_VERSION = '6';
export const RESULT_STATUSES = Object.freeze(['Observed', 'Computed', 'Estimated', 'Predicted', 'Hypothetical', 'Not established']);
export const NOT_ESTABLISHED = 'Not established';

const emptyResult = () => ({ status: NOT_ESTABLISHED, value: null, confidence: null, uncertainty: null, provenance: null });
const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
const normalizeSelection = (initial = {}) => ({
  subject: initial.subject ?? 'own_cohort', timepoint: initial.timepoint ?? 'T0', region: initial.region ?? 'palm',
  tissue: initial.tissue ?? null, cell: initial.cell ?? null, molecularLayer: initial.molecularLayer ?? null,
});

export function createDigitalTwinState(initial = {}) {
  const selection = normalizeSelection({
    ...initial.selection,
    subject: initial.subject ?? initial.selection?.subject ?? initial.input?.subject_id,
    timepoint: initial.timepoint ?? initial.selection?.timepoint ?? initial.input?.timepoint,
    region: initial.region ?? initial.selection?.region,
    tissue: initial.tissue ?? initial.selection?.tissue,
    cell: initial.cell ?? initial.selection?.cell,
    molecularLayer: initial.molecularLayer ?? initial.selection?.molecularLayer,
  });
  return {
    stateVersion: DIGITAL_TWIN_STATE_VERSION, status: initial.status ?? 'idle', error: initial.error ?? null,
    subject: selection.subject, timepoint: selection.timepoint, region: selection.region, tissue: selection.tissue,
    cell: selection.cell, molecularLayer: selection.molecularLayer, selection,
    input: { input_id: null, modalities: {}, ...initial.input }, modalities: initial.modalities ?? {}, qc: initial.qc ?? [],
    anatomy: initial.anatomy ?? { hand: null, regions: [], tissues: [], cells: [] }, assets: Array.isArray(initial.assets) ? initial.assets : [],
    cells: Array.isArray(initial.cells) ? initial.cells : [], trajectory: initial.trajectory ?? null, diseaseTrajectory: initial.diseaseTrajectory ?? null,
    whatIf: initial.whatIf ?? null, molecular: initial.molecular ?? { rna: null, proteomics: null, epigenetics: null, genomics: null, states: [] },
    health: initial.health ?? null, biologicalAge: initial.biologicalAge ?? null,
    evidence: initial.evidence ?? { coverage: null, confidence: null, missingModalities: [], items: [] },
    biologicalState: initial.biologicalState ?? { health: emptyResult(), diseaseState: emptyResult(), biologicalAge: emptyResult(), confidence: null, uncertainty: null, status: NOT_ESTABLISHED },
    uncertainty: initial.uncertainty ?? null, provenance: initial.provenance ?? null, validation: initial.validation ?? null,
    interventions: initial.interventions ?? null, modelMetadata: initial.modelMetadata ?? null,
  };
}

export function reduceAnalysisResult(state, backendResult) {
  const result = normalizeAnalysisResult(backendResult), next = createDigitalTwinState(state);
  next.status = 'ready'; next.error = null; next.input.input_id = result.provenance.input_id;
  next.input.subject_id = next.subject; next.input.timepoint = next.timepoint; next.qc = result.qc;
  next.biologicalAge = result.biological_age; next.health = result.health_state; next.molecular = { ...next.molecular, states: result.molecular_states };
  next.provenance = result.provenance; next.validation = result.validation; next.modelMetadata = result.model_metadata;
  next.uncertainty = result.multimodal_state?.uncertainty ?? null; next.interventions = result.intervention_priority;
  next.whatIf = result.what_if; next.assets = result.assets; next.cells = result.cells; next.trajectory = result.trajectory; next.diseaseTrajectory = result.disease_trajectory;
  next.evidence = { ...next.evidence, coverage: result.evidence?.coverage ?? null, confidence: result.evidence?.confidence ?? null,
    missingModalities: Array.isArray(result.evidence?.missing_modalities) ? result.evidence.missing_modalities : [],
    items: Array.isArray(result.evidence?.items) ? result.evidence.items : (result.provenance ? [result.provenance] : []), validation: result.validation };
  next.biologicalState = { health: result.health_state ?? emptyResult(),
    diseaseState: result.multimodal_state?.disease_state ?? result.multimodal_state?.diseaseState ?? emptyResult(),
    biologicalAge: result.biological_age ?? emptyResult(),
    confidence: result.multimodal_state?.confidence ?? result.health_state?.confidence ?? result.biological_age?.confidence ?? null,
    uncertainty: result.multimodal_state?.uncertainty ?? null,
    status: result.multimodal_state?.status ?? result.biological_age?.status ?? NOT_ESTABLISHED };
  const anatomy = result.anatomy && typeof result.anatomy === 'object' ? result.anatomy : {};
  next.anatomy = { hand: anatomy.hand ?? next.anatomy.hand, regions: Array.isArray(anatomy.regions) ? anatomy.regions : next.anatomy.regions,
    tissues: Array.isArray(anatomy.tissues) ? anatomy.tissues : next.anatomy.tissues, cells: Array.isArray(anatomy.cells) ? anatomy.cells : result.cells };
  next.modalities = result.modalities && typeof result.modalities === 'object' ? result.modalities : next.modalities;
  return createDigitalTwinState(next);
}

export function setDigitalTwinError(state, error) { return { ...state, status: 'error', error: String(error) }; }

export function setSelection(state, patch = {}) {
  const current = createDigitalTwinState(state);
  const selection = {
    subject: has(patch, 'subject') ? patch.subject : current.subject,
    timepoint: has(patch, 'timepoint') ? patch.timepoint : current.timepoint,
    region: has(patch, 'region') ? patch.region : current.region,
    tissue: has(patch, 'tissue') ? patch.tissue : current.tissue,
    cell: has(patch, 'cell') ? patch.cell : current.cell,
    molecularLayer: has(patch, 'molecularLayer') ? patch.molecularLayer : current.molecularLayer,
  };
  if (has(patch, 'region')) { selection.tissue = null; selection.cell = null; selection.molecularLayer = null; }
  if (has(patch, 'tissue')) { selection.cell = null; selection.molecularLayer = null; }
  if (has(patch, 'cell') && !patch.cell) selection.molecularLayer = null;
  return { ...current, ...selection, selection };
}
