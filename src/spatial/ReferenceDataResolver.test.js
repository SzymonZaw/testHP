import { createReferenceResolver } from './ReferenceDataResolver.js';

test('resolves curated external references by layer and dataset id', () => {
  const resolver = createReferenceResolver([
    { id: 't1', layer: 'tissue', sourceUrl: 'https://example.test/tissue.json', accession: 'T1', species: 'Homo sapiens', tissue: 'skin', modality: 'spatial-transcriptomics' },
    { id: 'c1', layer: 'cell', sourceUrl: 'https://example.test/cell.json', accession: 'C1', species: 'Homo sapiens', tissue: 'skin', modality: 'single-cell-rna' },
    { id: 'm1', layer: 'molecular', sourceUrl: 'https://example.test/molecular.json', accession: 'M1', species: 'Homo sapiens', tissue: 'skin', modality: 'genomics' },
  ]);

  expect(resolver.resolveLayer('cell')).toHaveLength(1);
  expect(resolver.resolveDataset('c1').accession).toBe('C1');
  expect(resolver.resolveDownloadDescriptor('m1')).toMatchObject({ datasetId: 'm1', status: 'external-reference' });
  expect(resolver.resolveDataset('missing')).toBeNull();
});
