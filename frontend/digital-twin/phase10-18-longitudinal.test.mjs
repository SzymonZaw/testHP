import assert from 'node:assert/strict';
import test from 'node:test';
import { buildTimelineModel, normalizeResultStatus, trajectoryStatusForTimepoint } from './phase10-18-model.js';

test('timeline defaults unknown timepoints to Not established', () => {
  const model = buildTimelineModel({ selection: { timepoint: 'T0' }, timepoint: 'T0', status: 'idle' });
  assert.deepEqual(model.map(item => item.status), ['Not established', 'Not established', 'Not established', 'Not established']);
  assert.equal(model[0].selected, true);
});

test('timeline preserves backend observed and predicted status', () => {
  const state = {
    selection: { timepoint: 'T1' },
    timepoint: 'T1',
    status: 'ready',
    biologicalState: { status: 'Observed' },
    trajectory: { points: [
      { timepoint: 'T0', value: 10, status: 'Observed' },
      { timepoint: 'T1', value: 11, status: 'Predicted' },
    ] },
  };
  assert.equal(trajectoryStatusForTimepoint(state, 'T0'), 'Observed');
  assert.equal(trajectoryStatusForTimepoint(state, 'T1'), 'Predicted');
});

test('timeline never turns an unknown status into a biological claim', () => {
  assert.equal(normalizeResultStatus('healthy'), 'Not established');
  assert.equal(normalizeResultStatus(null), 'Not established');
  assert.equal(normalizeResultStatus('Predicted'), 'Predicted');
});
