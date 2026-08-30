import assert from 'node:assert/strict';
import { createPersonalTwinAsset } from './PersonalTwinUploadAdapter.js';

const file = { name: 'my-hand.glb' };
const asset = createPersonalTwinAsset({
  file,
  metadata: { subjectId: 'subject-001', timepoint: 'T0', regions: [{ regionId: 'palm', geometryId: 'palm' }] },
});

assert.equal(asset.type, 'personal');
assert.equal(asset.subjectId, 'subject-001');
assert.equal(asset.timepoint, 'T0');
assert.equal(asset.asset.type, 'glb');
assert.equal(asset.biologicalState, null);
assert.equal(asset.metadata.regions[0].regionId, 'palm');

assert.throws(() => createPersonalTwinAsset({ file: { name: 'scan.obj' }, metadata: { subjectId: 's' } }));
assert.throws(() => createPersonalTwinAsset({ file, metadata: {} }));

console.log('PersonalTwinUploadAdapter tests passed');
