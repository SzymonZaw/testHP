import assert from 'node:assert/strict';
import test from 'node:test';
import { createDigitalTwinState, reduceAnalysisResult } from './canonical-state.js';
import { normalizeAnalysisResult } from './backend-contracts.js';
import { buildCanonicalViewModel } from './canonical-ui-projections-v1.js';

const baseResult = {
  provenance: { input_id: 'input-1', analysis_id: 'analysis-1' },
  qc: [{ modality: 'hand_images', status: 'usable' }],
  evidence: { coverage: 0.25, confidence: 0.7, missing_modalities: ['rna'] },
  health_state: { state: 'unknown', confidence: null },
  biological_age: { status: 'not_established', biological_age: null },
  molecular_states: [],
  multimodal_state: { status: 'not_established' },
  intervention_priority: { status: 'not_established', clinical_validation: false },
};

test('canonical state preserves no-data semantics', () => {
  const state = createDigitalTwinState();
  const view = buildCanonicalViewModel(state);
  assert.equal(view.health.hand.health, 'unknown');
  assert.equal(view.biologicalAge.status, 'not_established');
  assert.equal(view.molecular.rna.availability, 'missing');
  assert.equal(view.intervention.status, 'not_established');
});

test('AnalysisResult is normalized once into canonical state', () => {
  const state = reduceAnalysisResult(createDigitalTwinState(), normalizeAnalysisResult(baseResult));
  assert.equal(state.status, 'ready');
  assert.equal(state.input.input_id, 'input-1');
  assert.equal(state.qc[0].status, 'usable');
  assert.equal(state.evidence.coverage, 0.25);
  assert.deepEqual(state.evidence.missingModalities, ['rna']);
});

test('validated status may be displayed but never invented', () => {
  const result = { ...baseResult, biological_age: { status: 'validated', biological_age: 52 } };
  const state = reduceAnalysisResult(createDigitalTwinState(), normalizeAnalysisResult(result));
  assert.equal(state.biologicalAge.status, 'validated');
  assert.equal(state.biologicalAge.biological_age, 52);
});
