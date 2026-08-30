import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const file = path.join(import.meta.dirname, 'reference-dataset-catalog-v1.json');
const catalog = JSON.parse(fs.readFileSync(file, 'utf8'));

assert.equal(catalog.schemaVersion, '1.0');
assert.ok(Array.isArray(catalog.datasets));
assert.ok(catalog.datasets.length >= 5);

for (const dataset of catalog.datasets) {
  assert.ok(dataset.id);
  assert.ok(dataset.url);
  assert.equal(dataset.status.includes('patient'), false);
  assert.ok(Array.isArray(dataset.provides));
  assert.ok(Array.isArray(dataset.doesNotProvide));
}

const hand = catalog.datasets.find(d => d.id === 'nih-hand-template-3dpx-017237');
assert.ok(hand);
assert.ok(hand.provides.includes('hand_surface_geometry'));
assert.ok(hand.doesNotProvide.includes('patient_specific_geometry'));

const fibroblast = catalog.datasets.find(d => d.id === 'hca-human-dermal-fibroblast-gse109822');
assert.ok(fibroblast);
assert.equal(fibroblast.accession, 'GSE109822');
assert.ok(fibroblast.doesNotProvide.includes('hand_registration'));

console.log('reference-dataset-catalog-v1: OK');
