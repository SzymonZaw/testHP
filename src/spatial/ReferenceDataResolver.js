import { buildReferenceBiologyRegistry, findReferencesByLayer } from './ReferenceBiologyRegistry.js';

export function createReferenceResolver(entries = []) {
  const registry = buildReferenceBiologyRegistry(entries);
  return {
    registry,
    resolveLayer(layer) {
      return findReferencesByLayer(registry, layer);
    },
    resolveDataset(datasetId) {
      return registry.layers.find((entry) => entry.id === datasetId) ?? null;
    },
    resolveDownloadDescriptor(datasetId) {
      const entry = registry.layers.find((item) => item.id === datasetId);
      if (!entry) return null;
      return {
        datasetId: entry.id,
        accession: entry.accession,
        sourceUrl: entry.sourceUrl,
        modality: entry.modality,
        species: entry.species,
        tissue: entry.tissue,
        provenance: entry.provenance ?? null,
        limitations: entry.limitations ?? [],
        status: 'external-reference',
      };
    },
  };
}

export async function resolveJsonReference(fetchImpl, dataset) {
  if (!dataset?.sourceUrl) throw new Error('Reference dataset has no sourceUrl');
  const response = await fetchImpl(dataset.sourceUrl);
  if (!response?.ok) throw new Error(`Reference fetch failed: ${response?.status ?? 'unknown'}`);
  return response.json();
}
