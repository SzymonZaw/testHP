import assert from 'node:assert/strict';
import {
  CAPABILITY_STATUS,
  getHandAsset,
  getSpatialGeometry,
  getPredictiveCapability,
  getValidatedBiologicalAge,
  summarizeCapabilities,
} from './biological-capabilities.js';

const empty = {
  assets: [],
  anatomy: { tissues: [], cells: [] },
  biologicalAge: null,
  modelMetadata: null,
  validation: null,
  whatIf: null,
  interventions: null,
};

assert.equal(getHandAsset(empty), null);
assert.equal(getSpatialGeometry(empty, 'cell', 'c1'), undefined);
assert.equal(getPredictiveCapability(empty, 'whatIf').status, CAPABILITY_STATUS.NOT_ESTABLISHED);
assert.equal(getValidatedBiologicalAge(empty).status, CAPABILITY_STATUS.NOT_ESTABLISHED);

const supplied = {
  ...empty,
  assets: [{ id: 'hand-1', modality: 'hand_3d', status: 'verified', url: '/assets/hand.glb' }],
  anatomy: {
    tissues: [{ tissue_id: 't1', geometry: { type: 'mesh' } }],
    cells: [{ cell_id: 'c1', position: [1, 2, 3] }],
  },
  whatIf: { status: 'validated', model_id: 'trajectory-v1' },
  interventions: { status: 'validated', model_id: 'intervention-v1' },
  biologicalAge: { biological_age: 51, model_id: 'age-v1', validation_status: 'validated' },
  modelMetadata: { model_id: 'age-v1', validation_status: 'validated' },
};

assert.ok(getHandAsset(supplied));
assert.deepEqual(getSpatialGeometry(supplied, 'tissue', 't1'), supplied.anatomy.tissues[0]);
assert.deepEqual(getSpatialGeometry(supplied, 'cell', 'c1'), supplied.anatomy.cells[0]);
assert.equal(getPredictiveCapability(supplied, 'whatIf').status, CAPABILITY_STATUS.READY);
assert.equal(getPredictiveCapability(supplied, 'interventions').status, CAPABILITY_STATUS.READY);
assert.equal(getValidatedBiologicalAge(supplied).status, CAPABILITY_STATUS.READY);
assert.deepEqual(summarizeCapabilities(supplied), {
  handAsset: CAPABILITY_STATUS.READY,
  tissueGeometry: CAPABILITY_STATUS.READY,
  cellGeometry: CAPABILITY_STATUS.READY,
  whatIf: CAPABILITY_STATUS.READY,
  intervention: CAPABILITY_STATUS.READY,
  biologicalAge: CAPABILITY_STATUS.READY,
});

console.log('biological capability tests: ok');
