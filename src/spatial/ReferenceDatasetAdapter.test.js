import assert from 'node:assert/strict';
import {
  buildReferenceManifest,
  createSpatialRegistryFromReference,
  getReferenceDataset,
} from './ReferenceDatasetAdapter.js';

const catalog = {
  datasets: [
    {
      id: 'geo-gse109822',
      layer: 'cell_and_molecular',
      type: 'human_dermal_fibroblast_spatial_and_single_cell_rna',
      source: 'NCBI GEO',
      accession: 'GSE109822',
      url: 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE109822',
      usable_for: ['dermal_fibroblast_cell_types', 'single_cell_rna_reference'],
      limitations: ['not_hand_specific'],
    },
  ],
};

assert.equal(getReferenceDataset(catalog, 'geo-gse109822').accession, 'GSE109822');
assert.equal(getReferenceDataset(catalog, 'missing'), null);

const registry = createSpatialRegistryFromReference(catalog, 'geo-gse109822', {
  metadata: { regions: [{ regionId: 'palm', geometryId: 'ref.palm' }], mappings: [] },
});
assert.equal(registry.sourceId, 'geo-gse109822');
assert.equal(registry.provenance.accession, 'GSE109822');
assert.equal(buildReferenceManifest(catalog)[0].layer, 'cell_and_molecular');

console.log('ReferenceDatasetAdapter tests passed');
