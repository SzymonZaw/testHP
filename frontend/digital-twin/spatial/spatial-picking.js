import { SPATIAL_REGIONS } from "./spatial-types.js";

/**
 * Resolve a Three.js object to authoritative spatial identity.
 * Geometry metadata is preferred over display labels. No anatomy is inferred.
 */
export function resolveSpatialPick(object, adapter = null) {
  let node = object || null;
  while (node) {
    const u = node.userData || {};
    const geometryId = normalize(u.geometryId ?? u.geometry_id ?? node.name);
    const cellId = normalize(u.cellId ?? u.cell_id ?? u.cell);
    const tissueId = normalize(u.tissueId ?? u.tissue_id ?? u.tissue);
    const regionId = normalize(u.regionId ?? u.region_id ?? u.region);

    if (cellId || tissueId || regionId) {
      return {
        geometryId,
        regionId: regionId || null,
        tissueId: tissueId || null,
        cellId: cellId || null,
        source: "geometry-metadata",
      };
    }

    if (geometryId && adapter?.getRegionByGeometryId) {
      const region = adapter.getRegionByGeometryId(geometryId);
      if (region) {
        return {
          geometryId,
          regionId: normalize(region.id),
          tissueId: normalize(region.tissueId ?? region.tissue_id) || null,
          cellId: normalize(region.cellId ?? region.cell_id) || null,
          source: "spatial-adapter",
        };
      }
    }

    node = node.parent || null;
  }

  return null;
}

export function isCanonicalRegion(regionId) {
  return SPATIAL_REGIONS.includes(normalize(regionId));
}

function normalize(value) {
  return String(value ?? "").trim().toLowerCase();
}

if (!window.TestHPSpatialPicking) {
  window.TestHPSpatialPicking = { resolveSpatialPick, isCanonicalRegion, version: 1 };
}
