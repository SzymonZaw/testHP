export const REFERENCE_TWIN = 'reference';
export const PERSONAL_TWIN = 'personal';

const VALID_REGIONS = new Set(['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist']);

export function validateSpatialMetadata(metadata = {}) {
  const errors = [];
  for (const region of metadata.regions ?? []) {
    if (!region.regionId || !VALID_REGIONS.has(region.regionId)) {
      errors.push(`Unknown regionId: ${region.regionId ?? '(missing)'}`);
    }
    if (!region.geometryId) errors.push(`Missing geometryId for ${region.regionId ?? '(missing)'}`);
  }
  return { valid: errors.length === 0, errors };
}

export function buildSpatialRegistry(source) {
  const validation = validateSpatialMetadata(source?.metadata);
  if (!validation.valid) throw new Error(validation.errors.join('; '));
  return {
    sourceId: source.id,
    sourceType: source.type ?? REFERENCE_TWIN,
    asset: source.asset ?? null,
    coordinateSystem: source.coordinateSystem ?? null,
    regions: source.metadata?.regions ?? [],
    mappings: source.metadata?.mappings ?? [],
    provenance: source.provenance ?? null,
  };
}

export function resolveGeometryRegion(registry, geometryId) {
  return registry.regions.find((region) => region.geometryId === geometryId)?.regionId ?? null;
}

export function resolveRegionEvidence(registry, regionId) {
  return registry.mappings
    .filter((mapping) => mapping.regionId === regionId && mapping.evidenceId)
    .map((mapping) => mapping.evidenceId);
}
