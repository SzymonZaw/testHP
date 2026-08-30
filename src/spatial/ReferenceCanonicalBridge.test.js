import { createCanonicalReferenceBridge } from './ReferenceCanonicalBridge.js';

test('activates reference datasets into canonical spatial layers', () => {
  const bridge = createCanonicalReferenceBridge([
    { id: 't1', layer: 'tissue', sourceUrl: 'https://example.test/tissue', accession: 'T1', species: 'Homo sapiens', tissue: 'skin', modality: 'spatial-transcriptomics' },
    { id: 'c1', layer: 'cell', sourceUrl: 'https://example.test/cell', accession: 'C1', species: 'Homo sapiens', tissue: 'skin', modality: 'single-cell-rna' },
    { id: 'm1', layer: 'molecular', sourceUrl: 'https://example.test/molecular', accession: 'M1', species: 'Homo sapiens', tissue: 'multi-tissue', modality: 'genomics' },
  ]);

  const result = bridge.activateLayers({ tissue: 't1', cell: 'c1', molecular: 'm1', spatialId: 'hand/palm' });

  expect(result.active).toMatchObject({ source: 'reference', target: 'hand/palm', status: 'external-reference' });
  expect(result.layers.tissue.datasetId).toBe('t1');
  expect(result.layers.cell.datasetId).toBe('c1');
  expect(result.layers.molecular.datasetId).toBe('m1');
});
