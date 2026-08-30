const REQUIRED_REGION_IDS = ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'];

export function createHandRegionRegistry(regions = []) {
  const byId = new Map();
  const errors = [];
  for (const region of regions) {
    if (!region?.regionId) { errors.push('Region is missing regionId'); continue; }
    if (byId.has(region.regionId)) { errors.push(`Duplicate regionId: ${region.regionId}`); continue; }
    if (!REQUIRED_REGION_IDS.includes(region.regionId)) { errors.push(`Unsupported hand region: ${region.regionId}`); continue; }
    if (!Array.isArray(region.geometryIds) || region.geometryIds.length === 0) errors.push(`Region has no geometryIds: ${region.regionId}`);
    byId.set(region.regionId, Object.freeze({ ...region, geometryIds: [...region.geometryIds] }));
  }
  return { regions: [...byId.values()], byId, errors, complete: REQUIRED_REGION_IDS.every((id) => byId.has(id)) && errors.length === 0 };
}

export function mapGeometryToRegion(registry, geometryId) {
  const matches = registry.regions.filter((region) => region.geometryIds.includes(geometryId));
  if (matches.length > 1) throw new Error(`Ambiguous geometryId mapping: ${geometryId}`);
  return matches[0]?.regionId ?? null;
}

export function validateHandRegionRegistry(registry) {
  const missing = REQUIRED_REGION_IDS.filter((id) => !registry.byId.has(id));
  return { valid: registry.errors.length === 0 && missing.length === 0, errors: [...registry.errors], missingRegionIds: missing };
}

export { REQUIRED_REGION_IDS };
