import { normalizeAnalysisResult } from './backend-contracts.js';

/**
 * Adapt a backend AnalysisResult into the stable frontend Digital Twin shape.
 * This is intentionally a pure adapter: it does not calculate biological
 * results or infer health from missing evidence.
 */
export function adaptAnalysisResult(backendResult) {
  const result = normalizeAnalysisResult(backendResult);

  return {
    ...result,
    evidence: {
      qc: result.qc,
      provenance: result.provenance,
      validation: result.validation,
    },
    scientificStatus: {
      biologicalAge: result.biological_age.status,
      multimodal: result.multimodal_state.status,
      intervention: result.intervention_priority.status,
    },
  };
}
