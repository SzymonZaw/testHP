import assert from 'node:assert/strict';
import { buildPersonalTwinSource, createPersonalTwinManifest, validatePersonalManifest } from './PersonalTwinIngestionContract.js';

const manifest = createPersonalTwinManifest({
  subjectId: 'subject-demo',
  timepointId: 'T0',
  inputs: [{ id: 'scan-001', modality: '3d_scan', source: 'user-upload', provenance: { filename: 'hand.glb' } }],
});

assert.equal(validatePersonalManifest(manifest).valid, true);
const source = buildPersonalTwinSource(manifest);
assert.equal(source.id, 'personal:subject-demo:T0');
assert.equal(source.type, 'personal');
assert.equal(source.inputs[0].modality, '3d_scan');
assert.equal(source.biologicalState, null);
assert.equal(validatePersonalManifest({}).valid, false);
console.log('PersonalTwinIngestionContract tests passed');
