import { createReferenceResolver } from './ReferenceDataResolver.js';

const DEFAULT_LAYERS = ['tissue', 'cell', 'molecular'];

function canonicalId(value) {
  const contract = globalThis?.window?.testhpSpatialContract;
  if (typeof contract?.normalizeId === 'function') return contract.normalizeId(value);
  return String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
}

function publish(detail) {
  if (typeof window === 'undefined') return;
  window.__testhpReferenceLayers = detail;
  window.dispatchEvent(new CustomEvent('testhp:reference-layers-changed', { detail }));
}

export function createCanonicalReferenceBridge(entries = []) {
  const resolver = createReferenceResolver(entries);
  return {
    resolver,
    activate(datasetId, options = {}) {
      const dataset = resolver.resolveDataset(datasetId);
      if (!dataset) throw new Error(`Unknown reference dataset: ${datasetId}`);
      const target = canonicalId(options.spatialId || options.spatial_id || options.target || 'hand');
      const layer = dataset.layer;
      const descriptor = resolver.resolveDownloadDescriptor(datasetId);
      const state = {
        source: 'reference',
        datasetId: dataset.id,
        accession: dataset.accession,
        layer,
        target,
        status: 'external-reference',
        descriptor,
        limitations: dataset.limitations ?? [],
      };
      publish({ active: state, layers: { [layer]: state } });
      return state;
    },
    activateLayers(selection = {}) {
      const layers = {};
      for (const layer of DEFAULT_LAYERS) {
        const datasetId = selection[layer];
        if (!datasetId) continue;
        const dataset = resolver.resolveDataset(datasetId);
        if (!dataset || dataset.layer !== layer) throw new Error(`Dataset ${datasetId} is not a ${layer} reference`);
        layers[layer] = this.activate(datasetId, selection).descriptor;
      }
      const target = canonicalId(selection.spatialId || selection.spatial_id || selection.target || 'hand');
      const detail = {
        active: { source: 'reference', target, status: 'external-reference' },
        layers,
      };
      publish(detail);
      return detail;
    },
  };
}

export function installCanonicalReferenceBridge(entries = []) {
  const bridge = createCanonicalReferenceBridge(entries);
  if (typeof window !== 'undefined') window.testhpReferenceCanonicalBridge = bridge;
  return bridge;
}
