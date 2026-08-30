import { buildSpatialRegistry, REFERENCE_TWIN } from './ReferenceTwinAdapter.js';

const DEFAULT_CATALOG_URL = '/data/reference-datasets/spatial-biology-catalog-v2.json';

export async function loadReferenceCatalog(fetchImpl = globalThis.fetch, url = DEFAULT_CATALOG_URL) {
  if (typeof fetchImpl !== 'function') throw new Error('A fetch implementation is required');
  const response = await fetchImpl(url);
  if (!response.ok) throw new Error(`Reference catalog request failed: ${response.status}`);
  const payload = await response.json();
  if (!Array.isArray(payload.datasets)) throw new Error('Invalid reference catalog: datasets[] missing');
  return payload;
}

export function getReferenceDataset(catalog, id) {
  return catalog?.datasets?.find((dataset) => dataset.id === id) ?? null;
}

export function createReferenceSource(dataset, overrides = {}) {
  if (!dataset?.id) throw new Error('Reference dataset id is required');
  return {
    id: dataset.id,
    type: REFERENCE_TWIN,
    asset: overrides.asset ?? null,
    coordinateSystem: overrides.coordinateSystem ?? null,
    metadata: overrides.metadata ?? { regions: [], mappings: [] },
    provenance: {
      source: dataset.source,
      url: dataset.url,
      accession: dataset.accession ?? null,
      datasetId: dataset.id,
      ...overrides.provenance,
    },
  };
}

export function createSpatialRegistryFromReference(catalog, datasetId, overrides = {}) {
  const dataset = getReferenceDataset(catalog, datasetId);
  if (!dataset) throw new Error(`Unknown reference dataset: ${datasetId}`);
  return buildSpatialRegistry(createReferenceSource(dataset, overrides));
}

export function buildReferenceManifest(catalog) {
  return (catalog?.datasets ?? []).map((dataset) => ({
    id: dataset.id,
    layer: dataset.layer,
    type: dataset.type,
    source: dataset.source,
    url: dataset.url,
    accession: dataset.accession ?? null,
    usableFor: dataset.usable_for ?? [],
    limitations: dataset.limitations ?? [],
  }));
}
