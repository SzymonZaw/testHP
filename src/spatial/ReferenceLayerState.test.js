import { createReferenceLayerState, activateReferenceDatasets } from './ReferenceLayerState.js';

const entries = [
  { id: 't1', layer: 'tissue', sourceUrl: 'https://example.test/t', accession: 'T1', species: 'Homo sapiens', tissue: 'skin', modality: 'spatial-transcriptomics' },
  { id: 'c1', layer: 'cell', sourceUrl: 'https://example.test/c', accession: 'C1', species: 'Homo sapiens', tissue: 'skin', modality: 'single-cell-rna' },
  { id: 'm1', layer: 'molecular', sourceUrl: 'https://example.test/m', accession: 'M1', species: 'Homo sapiens', tissue: 'multi-tissue', modality: 'genomics' },
];
const resolver = { resolveDownloadDescriptor: (id) => { const e = entries.find((x) => x.id === id); return e && { ...e, datasetId: e.id, status: 'external-reference', limitations: [] }; }, resolveDataset: (id) => entries.find((x) => x.id === id) ?? null };

test('projects external references into tissue, cell and molecular layers', () => {
  const state = createReferenceLayerState(resolver, ['t1', 'c1', 'm1']);
  expect(state.mode).toBe('reference');
  expect(state.layers.tissue).toHaveLength(1);
  expect(state.layers.cell).toHaveLength(1);
  expect(state.layers.molecular).toHaveLength(1);
});

test('can dispatch canonical spatial reference activation', () => {
  let action;
  const projection = activateReferenceDatasets(resolver, ['c1'], (next) => { action = next; });
  expect(projection.referenceDatasetIds).toEqual(['c1']);
  expect(action.type).toBe('SPATIAL_REFERENCE_LAYERS_ACTIVATED');
});
