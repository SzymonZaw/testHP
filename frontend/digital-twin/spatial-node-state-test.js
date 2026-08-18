import { createSpatialNodeState, spatialNodeKey, hasEvidenceForResolution } from './spatial-node-state.js';

const state = createSpatialNodeState({
  resolution: 'tissue',
  target: 'Middle segment',
  path: ['Hand', 'Ring finger', 'Middle segment'],
  parent: { target: 'Ring finger', resolution: 'macro' },
  children: [{ label: 'Microscopy field A' }],
  evidence: [{ resolution: 'tissue' }],
});

if (state.resolution !== 'tissue') throw new Error('resolution mismatch');
if (state.target !== 'Middle segment') throw new Error('target mismatch');
if (spatialNodeKey(state) !== 'tissue|Hand>Ring finger>Middle segment|Middle segment|Microscopy field A') throw new Error('key mismatch');
if (!hasEvidenceForResolution(state)) throw new Error('evidence mismatch');
console.log('spatial node state: OK');
