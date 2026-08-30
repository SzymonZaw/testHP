import assert from 'node:assert/strict';
import test from 'node:test';

import {
  NIH_REFERENCE_HAND,
  createReferenceHandSource,
  createThreeJsLoadDescriptor
} from './ReferenceHandSource.js';

test('NIH reference hand keeps source provenance', () => {
  assert.equal(NIH_REFERENCE_HAND.datasetId, 'nih3d-hand-template-017237');
  assert.equal(NIH_REFERENCE_HAND.accession, '3DPX-017237');
  assert.equal(NIH_REFERENCE_HAND.version, '2');
  assert.equal(NIH_REFERENCE_HAND.species, 'Homo sapiens');
  assert.equal(NIH_REFERENCE_HAND.capabilities.referenceHandGeometry, true);
});

test('semantic hand regions remain explicitly unestablished', () => {
  assert.equal(NIH_REFERENCE_HAND.regionSchema.status, 'NOT_ESTABLISHED');
  assert.deepEqual(NIH_REFERENCE_HAND.regionSchema.expectedIds, [
    'palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'
  ]);
  assert.equal(NIH_REFERENCE_HAND.capabilities.semanticRegionPicking, false);
});

test('descriptor can be passed to a Three.js loader layer without losing provenance', () => {
  const source = createReferenceHandSource({ timepoint: 'REFERENCE-T0' });
  const descriptor = createThreeJsLoadDescriptor(source);

  assert.equal(descriptor.format, 'stl');
  assert.equal(descriptor.url, 'https://3d.nih.gov/entries/download/17237/1');
  assert.equal(descriptor.datasetId, source.datasetId);
  assert.equal(descriptor.coordinateSystem, source.coordinateSystem);
  assert.equal(descriptor.provenance.sourceRecord, 'NIH 3DPX-017237');
});
