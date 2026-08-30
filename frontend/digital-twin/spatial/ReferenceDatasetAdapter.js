const normalize = value => value == null ? null : String(value).trim() || null;

export function buildSpatialRegistry(source = {}) {
  const metadata = source.metadata || {};
  const mappings = Array.isArray(metadata.mappings) ? metadata.mappings : [];
  const regions = Array.isArray(metadata.regions) ? metadata.regions : [];
  const byGeometryId = new Map();
  for (const mapping of mappings) {
    const geometryId = normalize(mapping.geometryId ?? mapping.geometry_id ?? mapping.geometry);
    const regionId = normalize(mapping.regionId ?? mapping.region_id ?? mapping.region);
    if (geometryId && regionId) byGeometryId.set(geometryId, regionId);
  }
  for (const region of regions) {
    const geometryId = normalize(region.geometryId ?? region.geometry_id ?? region.geometry);
    const regionId = normalize(region.id ?? region.regionId ?? region.region_id);
    if (geometryId && regionId) byGeometryId.set(geometryId, regionId);
  }
  return {
    source,
    byGeometryId,
    getRegionByGeometryId(geometryId) { return byGeometryId.get(normalize(geometryId)) ?? null; }
  };
}

export function resolveGeometryRegion(registry, geometryId) {
  return registry?.getRegionByGeometryId?.(geometryId) ?? null;
}
