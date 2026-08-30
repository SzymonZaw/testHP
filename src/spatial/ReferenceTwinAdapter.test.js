import assert from 'node:assert/strict';
import { buildSpatialRegistry, resolveGeometryRegion, resolveRegionEvidence } from './ReferenceTwinAdapter.js';

const source = {
  id: 'reference-hand-demo',
  type: 'reference',
  asset: { path: 'assets/reference-hand.glb' },
  coordinateSystem: { name: 'asset-local', units: 'mm' },
  metadata: {
    regions: [
      { regionId: 'palm', geometryId: 'hand.palm' },
      { regionId: 'thumb', geometryId: 'hand.thumb' },
    ],
    mappings: [{ regionId: 'palm', evidenceId: 'ref-hand-image-001' }],
  },
  provenance: { source: 'reference-catalog' },
};

const registry = buildSpatialRegistry(source);
assert.equal(resolveGeometryRegion(registry, 'hand.palm'), 'palm');
assert.deepEqual(resolveRegionEvidence(registry, 'palm'), ['ref-hand-image-001']);
assert.equal(resolveGeometryRegion(registry, 'unknown'), null);
console.log('ReferenceTwinAdapter tests passed');
