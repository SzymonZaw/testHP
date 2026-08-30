export function normalizeSkinTissueSample(sample = {}) {
  return {
    tissueId: sample.tissueId ?? sample.sampleId ?? sample.id ?? null,
    coordinateSystem: sample.coordinateSystem ?? 'unknown',
    coordinates: sample.coordinates ?? null,
    segmentation: sample.segmentation ?? null,
    anatomy: sample.anatomy ?? null,
    sourceDatasetId: sample.sourceDatasetId ?? null,
    provenance: sample.provenance ?? null,
  };
}

export function createSkinTissueReference(sample) {
  const normalized = normalizeSkinTissueSample(sample);
  if (!normalized.tissueId) throw new Error('Skin tissue sample requires tissueId');
  if (!normalized.coordinates) throw new Error('Skin tissue sample requires explicit coordinates');
  return Object.freeze(normalized);
}

export function registerSkinTissueToHand(registration, sample, handRegionId) {
  const tissue = createSkinTissueReference(sample);
  if (!handRegionId) throw new Error('handRegionId is required');
  const handCoordinates = registration.transformPoint(tissue.coordinates);
  return Object.freeze({ ...tissue, handRegionId, handCoordinates, registrationId: registration.id ?? null, registrationStatus: 'registered-reference' });
}
