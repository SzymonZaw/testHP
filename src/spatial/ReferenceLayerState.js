export const REFERENCE_LAYER_ORDER = Object.freeze(['tissue', 'cell', 'molecular']);

export function createReferenceLayerState(resolver, datasetIds = []) {
  const datasets = datasetIds.map((id) => resolver.resolveDownloadDescriptor(id)).filter(Boolean);
  return Object.freeze({
    mode: 'reference',
    layers: Object.freeze(Object.fromEntries(
      REFERENCE_LAYER_ORDER.map((layer) => [layer, Object.freeze(datasets.filter((d) => resolver.resolveDataset(d.datasetId)?.layer === layer))])
    )),
    datasetIds: Object.freeze(datasets.map((d) => d.datasetId)),
    limitations: Object.freeze(datasets.flatMap((d) => d.limitations || [])),
  });
}

export function createReferenceLayerProjection(state) {
  return Object.freeze({
    spatialMode: state.mode,
    referenceLayers: state.layers,
    referenceDatasetIds: state.datasetIds,
    referenceLimitations: state.limitations,
  });
}

export function activateReferenceDatasets(resolver, datasetIds, dispatch = null) {
  const state = createReferenceLayerState(resolver, datasetIds);
  const projection = createReferenceLayerProjection(state);
  if (typeof dispatch === 'function') dispatch({ type: 'SPATIAL_REFERENCE_LAYERS_ACTIVATED', payload: projection });
  return projection;
}
