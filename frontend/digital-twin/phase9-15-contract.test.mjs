import test from 'node:test';
import assert from 'node:assert/strict';
import { createDigitalTwinState, reduceAnalysisResult } from './canonical-state.js';
import { normalizeAnalysisResult } from './backend-contracts.js';

test('initial state has no invented biological values', () => {
  const state = createDigitalTwinState();
  assert.equal(state.selection.timepoint, 'T0');
  assert.equal(state.biologicalAge, null);
  assert.equal(state.trajectory, null);
  assert.equal(state.diseaseTrajectory, null);
  assert.equal(state.whatIf, null);
  assert.equal(state.interventions, null);
});

test('partial evidence does not become confidence', () => {
  const state = reduceAnalysisResult(createDigitalTwinState(), {
    evidence: { coverage: 0.125, missing_modalities: ['rna'] },
    biological_age: { status: 'not_established', biological_age: null },
    multimodal_state: { status: 'not_established', confidence: null, uncertainty: null },
    provenance: { source: 'fixture', model_id: null, model_version: null },
  });
  assert.equal(state.evidence.coverage, 0.125);
  assert.equal(state.biologicalState.confidence, null);
  assert.equal(state.biologicalAge.biological_age, null);
});

test('backend supplied trajectory and hypothetical data are preserved verbatim', () => {
  const payload = {
    trajectory: { points: [{ timepoint: 'T0', value: 52, status: 'Observed' }, { timepoint: 'T1', value: 53, status: 'Predicted', uncertainty: 2 }] },
    disease_trajectory: { points: [{ timepoint: 'T0', value: 0.1, status: 'Observed' }] },
    what_if: { status: 'hypothetical', scenario_a: { value: 1 } },
    provenance: { model_id: 'm1', model_version: '1.0', source: 'test' },
  };
  const normalized = normalizeAnalysisResult(payload);
  const state = reduceAnalysisResult(createDigitalTwinState(), payload);
  assert.deepEqual(state.trajectory, normalized.trajectory);
  assert.deepEqual(state.diseaseTrajectory, normalized.disease_trajectory);
  assert.deepEqual(state.whatIf, normalized.what_if);
  assert.equal(state.provenance.model_id, 'm1');
});

test('reload selection can restore timepoint without inventing analysis', () => {
  const first = createDigitalTwinState({ selection: { subject: 'own_cohort', timepoint: 'T2', region: 'palm' } });
  const restored = createDigitalTwinState({ selection: first.selection });
  assert.equal(restored.selection.timepoint, 'T2');
  assert.equal(restored.selection.subject, 'own_cohort');
  assert.equal(restored.biologicalAge, null);
});
