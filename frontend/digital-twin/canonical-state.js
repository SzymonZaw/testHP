import { normalizeAnalysisResult } from './backend-contracts.js';

export const DIGITAL_TWIN_STATE_VERSION = '4';
export const RESULT_STATUSES = Object.freeze(['Observed', 'Computed', 'Estimated', 'Predicted', 'Hypothetical', 'Not established']);
const notEstablished = () => ({ status: 'Not established', value: null, confidence: null, uncertainty: null, provenance: null });

export function createDigitalTwinState(initial = {}) {
  const selection = {
    subject: initial.selection?.subject ?? initial.input?.subject_id ?? 'own_cohort',
    timepoint: initial.selection?.timepoint ?? initial.input?.timepoint ?? 'T0',
    region: initial.selection?.region ?? 'palm', tissue: initial.selection?.tissue ?? null,
    cell: initial.selection?.cell ?? null, molecularLayer: initial.selection?.molecularLayer ?? null,
  };
  return {
    stateVersion: DIGITAL_TWIN_STATE_VERSION, status: initial.status ?? 'idle', error: initial.error ?? null,
    input: { input_id: null, modalities: {}, ...initial.input }, modalities: initial.modalities ?? {}, qc: initial.qc ?? [],
    anatomy: initial.anatomy ?? { hand: null, regions: [], tissues: [], cells: [] },
    assets: Array.isArray(initial.assets) ? initial.assets : [], cells: Array.isArray(initial.cells) ? initial.cells : [],
    trajectory: initial.trajectory ?? null, diseaseTrajectory: initial.diseaseTrajectory ?? null,
    molecular: initial.molecular ?? { rna: null, proteomics: null, epigenetics: null, genomics: null, states: [] },
    health: initial.health ?? null, biologicalAge: initial.biologicalAge ?? null,
    evidence: initial.evidence ?? { coverage: null, confidence: null, missingModalities: [], items: [] },
    biologicalState: initial.biologicalState ?? {
      health: notEstablished(), diseaseState: notEstablished(), biologicalAge: notEstablished(),
      confidence: null, uncertainty: null, status: 'Not established',
    },
    uncertainty: initial.uncertainty ?? null, provenance: initial.provenance ?? null,
    validation: initial.validation ?? null, interventions: initial.interventions ?? null, selection,
  };
}

export function reduceAnalysisResult(state, backendResult) {
  const result = normalizeAnalysisResult(backendResult);
  const next = createDigitalTwinState(state);
  next.status = 'ready'; next.error = null;
  next.input.input_id = result.provenance.input_id; next.input.subject_id = next.selection.subject; next.input.timepoint = next.selection.timepoint;
  next.qc = result.qc; next.biologicalAge = result.biological_age; next.health = result.health_state;
  next.molecular = { ...next.molecular, states: result.molecular_states }; next.provenance = result.provenance; next.validation = result.validation;
  next.uncertainty = result.multimodal_state?.uncertainty ?? null; next.interventions = result.intervention_priority;
  next.assets = result.assets; next.cells = result.cells; next.trajectory = result.trajectory; next.diseaseTrajectory = result.disease_trajectory;
  next.evidence = {
    ...next.evidence, coverage: result.evidence?.coverage ?? null, confidence: result.evidence?.confidence ?? null,
    missingModalities: Array.isArray(result.evidence?.missing_modalities) ? result.evidence.missing_modalities : [],
    items: Array.isArray(result.evidence?.items) ? result.evidence.items : (result.provenance ? [result.provenance] : []), validation: result.validation,
  };
  next.biologicalState = {
    health: result.health_state ?? notEstablished(),
    diseaseState: result.multimodal_state?.disease_state ?? result.multimodal_state?.diseaseState ?? notEstablished(),
    biologicalAge: result.biological_age ?? notEstablished(),
    confidence: result.multimodal_state?.confidence ?? result.health_state?.confidence ?? result.biological_age?.confidence ?? null,
    uncertainty: result.multimodal_state?.uncertainty ?? null,
    status: result.multimodal_state?.status ?? result.biological_age?.status ?? 'Not established',
  };
  const anatomy = result.anatomy && typeof result.anatomy === 'object' ? result.anatomy : {};
  next.anatomy = { hand: anatomy.hand ?? next.anatomy.hand, regions: Array.isArray(anatomy.regions) ? anatomy.regions : next.anatomy.regions,
    tissues: Array.isArray(anatomy.tissues) ? anatomy.tissues : next.anatomy.tissues,
    cells: Array.isArray(anatomy.cells) ? anatomy.cells : result.cells };
  next.modalities = result.modalities && typeof result.modalities === 'object' ? result.modalities : next.modalities;
  return next;
}

export function setDigitalTwinError(state, error) { return { ...state, status: 'error', error: String(error) }; }
export function setSelection(state, patch = {}) {
  const next = createDigitalTwinState(state); next.selection = { ...next.selection, ...patch };
  if ('region' in patch) { next.selection.tissue = null; next.selection.cell = null; next.selection.molecularLayer = null; }
  if ('tissue' in patch) { next.selection.cell = null; next.selection.molecularLayer = null; }
  if ('cell' in patch && !patch.cell) next.selection.molecularLayer = null;
  return next;
}
