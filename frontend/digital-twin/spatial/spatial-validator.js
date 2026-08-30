import { SPATIAL_REGIONS, SPATIAL_NODE_TYPES, SPATIAL_SOURCE_TYPES } from "./spatial-types.js";

export function validateCoordinateSystem(coordinateSystem) {
  const errors = [];
  if (!coordinateSystem?.id) errors.push("Coordinate system id is required.");
  if (!Array.isArray(coordinateSystem?.origin) || coordinateSystem.origin.length !== 3) {
    errors.push("Coordinate system origin must contain three values.");
  }
  if (!coordinateSystem?.units) errors.push("Coordinate system units are required.");
  return { valid: errors.length === 0, errors };
}

export function validateSpatialSource(source) {
  const errors = [];
  if (!source?.id) errors.push("Spatial source id is required.");
  if (!SPATIAL_SOURCE_TYPES.includes(source?.type)) errors.push(`Unsupported spatial source type: ${source?.type || "missing"}.`);
  return { valid: errors.length === 0, errors };
}

export function validateSpatialAsset(asset) {
  const errors = [];
  const warnings = [];
  if (!asset?.id) errors.push("Spatial asset id is required.");
  if (!asset?.sourceId) errors.push("Spatial asset sourceId is required.");
  if (!asset?.coordinateSystemId) errors.push("Spatial asset coordinateSystemId is required.");
  if (!Array.isArray(asset?.regions)) errors.push("Spatial asset regions must be an array.");

  const ids = new Set();
  const geometryIds = new Set();
  for (const region of asset?.regions || []) {
    if (!region?.id) errors.push("Every spatial region requires an id.");
    if (!SPATIAL_REGIONS.includes(region?.id)) warnings.push(`Unknown region id: ${region?.id || "missing"}.`);
    if (ids.has(region?.id)) errors.push(`Duplicate region id: ${region.id}.`);
    ids.add(region?.id);
    if (!region?.geometryId) errors.push(`Region ${region?.id || "unknown"} requires geometryId.`);
    if (geometryIds.has(region?.geometryId)) errors.push(`Duplicate geometryId: ${region.geometryId}.`);
    geometryIds.add(region?.geometryId);
  }

  for (const required of SPATIAL_REGIONS) {
    if (!ids.has(required)) warnings.push(`Region ${required} is not supplied by this asset.`);
  }
  return { valid: errors.length === 0, errors, warnings };
}

export function validateSpatialNode(node) {
  const errors = [];
  if (!node?.id) errors.push("Spatial node id is required.");
  if (!SPATIAL_NODE_TYPES.includes(node?.type)) errors.push(`Unsupported spatial node type: ${node?.type || "missing"}.`);
  if (node?.type !== "hand" && !node?.parentId) errors.push(`Node ${node?.id || "unknown"} requires parentId.`);
  return { valid: errors.length === 0, errors };
}
