/**
 * User-owned Digital Twin spatial source.
 *
 * This module is deliberately data-only: it does not infer health, age,
 * disease, confidence, trajectory, or treatment recommendations.
 */

export const USER_SPATIAL_SOURCE_TYPES = Object.freeze([
  'user_upload',
  'own_dataset',
]);

export const SUPPORTED_SPATIAL_FORMATS = Object.freeze([
  'glb',
  'gltf',
  'stl',
  'obj',
  'ply',
  'dcm',
  'nii',
  'nii.gz',
]);

export const HAND_REGION_IDS = Object.freeze([
  'palm',
  'thumb',
  'index',
  'middle',
  'ring',
  'little',
  'wrist',
]);

const trim = (value) => (typeof value === 'string' ? value.trim() : '');

export function createUserSpatialSource(input = {}) {
  const sourceId = trim(input.sourceId);
  const subjectId = trim(input.subjectId);
  const assetId = trim(input.assetId);
  const format = trim(input.format).toLowerCase();

  if (!sourceId) throw new Error('SpatialSource requires sourceId');
  if (!subjectId) throw new Error('SpatialSource requires subjectId');
  if (!assetId) throw new Error('SpatialSource requires assetId');
  if (!SUPPORTED_SPATIAL_FORMATS.includes(format)) {
    throw new Error(`Unsupported spatial format: ${format || 'missing'}`);
  }

  return Object.freeze({
    sourceId,
    type: input.type && USER_SPATIAL_SOURCE_TYPES.includes(input.type)
      ? input.type
      : 'user_upload',
    subjectId,
    assetId,
    format,
    fileName: trim(input.fileName) || null,
    coordinateSystem: input.coordinateSystem || null,
    provenance: input.provenance || null,
    metadata: input.metadata || {},
    importedAt: input.importedAt || new Date().toISOString(),
  });
}

export function validateSpatialRegions(regions = []) {
  const errors = [];
  const seen = new Set();

  for (const region of regions) {
    const regionId = trim(region?.regionId);
    const geometryId = trim(region?.geometryId);

    if (!HAND_REGION_IDS.includes(regionId)) {
      errors.push(`Unknown hand region: ${regionId || 'missing'}`);
    }
    if (!geometryId) errors.push(`Missing geometryId for region: ${regionId || 'unknown'}`);
    if (regionId && seen.has(regionId)) errors.push(`Duplicate regionId: ${regionId}`);
    if (regionId) seen.add(regionId);
  }

  return { valid: errors.length === 0, errors };
}

export function createUserSpatialAsset(input = {}) {
  const source = createUserSpatialSource(input.source);
  const regions = Array.isArray(input.regions) ? input.regions.map((region) => ({
    regionId: trim(region.regionId),
    geometryId: trim(region.geometryId),
    label: trim(region.label) || trim(region.regionId),
    coordinates: region.coordinates || null,
    evidenceIds: Array.isArray(region.evidenceIds) ? [...region.evidenceIds] : [],
  })) : [];

  const validation = validateSpatialRegions(regions);
  if (!validation.valid) throw new Error(validation.errors.join('; '));

  return Object.freeze({
    source,
    asset: Object.freeze({
      assetId: source.assetId,
      format: source.format,
      regions: Object.freeze(regions),
      annotations: Array.isArray(input.annotations) ? input.annotations : [],
      tissueIds: Array.isArray(input.tissueIds) ? input.tissueIds : [],
      cellIds: Array.isArray(input.cellIds) ? input.cellIds : [],
    }),
  });
}

export function spatialSelectionToCanonicalState(selection = {}) {
  return {
    subject: selection.subjectId || null,
    timepoint: selection.timepoint || 'T0',
    region: selection.regionId || null,
    tissue: selection.tissueId || null,
    cell: selection.cellId || null,
    molecularLayer: selection.molecularLayer || null,
    evidence: selection.evidenceId || null,
    biologicalState: selection.biologicalState || null,
  };
}

export function regionEvidenceMap(asset) {
  return Object.fromEntries(
    (asset?.asset?.regions || []).map((region) => [region.regionId, [...region.evidenceIds]])
  );
}
