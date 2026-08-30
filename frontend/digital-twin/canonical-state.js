import { normalizeAnalysisResult } from './backend-contracts.js';

/**
 * Single source of truth for the frontend Digital Twin.
 * UI modules should consume this state rather than maintaining independent
 * interpretations of the backend AnalysisResult.
 */
export const DIGITAL_TWIN_STATE_VERSION = '2';

export function createDigitalTwinState(initial = {}) {
  return {
    stateVersion: DIGITAL_TWIN_STATE_VERSION,
    status: 'idle',
    error: null,
    input: {
      input_id: null,
      modalities: {},
      ...initial.input,
    },
    modalities: initial.modalities ?? {},
    qc: initial.qc ?? [],
    anatomy: initial.anatomy ?? {
      hand: null,
      regions: [],
      tissues: [],
      cells: [],
    },
    molecular: initial.molecular ?? {
      rna: null,
      proteomics: null,
      epigenetics: null,
      genomics: null,
      states: [],
    },
    health: initial.health ?? null,
    biologicalAge: initial.biologicalAge ?? null,
    evidence: initial.evidence ?? {
      coverage: null,
      confidence: null,
      missingModalities: [],
      items: [],
    },
    uncertainty: initial.uncertainty ?? null,
    provenance: initial.provenance ?? null,
    validation: initial.validation ?? null,
    interventions: initial.interventions ?? null,
    selection: initial.selection ?? null,
  };
}

export function reduceAnalysisResult(state, backendResult) {
  const result = normalizeAnalysisResult(backendResult);
  const next = createDigitalTwinState(state);

  next.status = 'ready';
  next.input.input_id = result.provenance.input_id;
  next.qc = result.qc;
  next.biologicalAge = result.biological_age;
  next.health = result.health_state;
  next.molecular = {
    ...next.molecular,
    states: result.molecular_states,
  };
  next.provenance = result.provenance;
  next.validation = result.validation;
  next.uncertainty = result.multimodal_state.uncertainty ?? null;
  next.interventions = result.intervention_priority;
  next.evidence = {
    ...next.evidence,
    coverage: result.evidence?.coverage ?? next.evidence.coverage,
    confidence: result.evidence?.confidence ?? next.evidence.confidence,
    missingModalities: Array.isArray(result.evidence?.missing_modalities)
      ? result.evidence.missing_modalities
      : next.evidence.missingModalities,
    items: Array.isArray(result.evidence?.items)
      ? result.evidence.items
      : (result.provenance ? [result.provenance] : []),
    validation: result.validation,
  };
  next.anatomy = result.anatomy && typeof result.anatomy === 'object'
    ? result.anatomy
    : next.anatomy;
  next.modalities = result.modalities && typeof result.modalities === 'object'
    ? result.modalities
    : next.modalities;

  return next;
}

export function setDigitalTwinError(state, error) {
  return { ...state, status: 'error', error: String(error) };
}
