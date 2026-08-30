export const SPATIAL_REGIONS = Object.freeze([
  "palm",
  "thumb",
  "index",
  "middle",
  "ring",
  "little",
  "wrist",
]);

export const SPATIAL_NODE_TYPES = Object.freeze([
  "hand",
  "region",
  "tissue",
  "cell",
]);

export const SPATIAL_SOURCE_TYPES = Object.freeze([
  "own_scan",
  "own_dataset",
  "research_dataset",
  "reference_model",
  "reconstructed",
]);

export const SPATIAL_STATUSES = Object.freeze([
  "observed",
  "computed",
  "estimated",
  "predicted",
  "hypothetical",
  "not_established",
]);

export function createSpatialRegion(input = {}) {
  return {
    id: input.id,
    label: input.label || input.id,
    parentId: input.parentId ?? "hand",
    geometryId: input.geometryId,
    evidenceIds: Array.isArray(input.evidenceIds) ? [...input.evidenceIds] : [],
    annotations: Array.isArray(input.annotations) ? [...input.annotations] : [],
    tissueIds: Array.isArray(input.tissueIds) ? [...input.tissueIds] : [],
  };
}

export function createSpatialAsset(input = {}) {
  return {
    id: input.id,
    version: input.version || "1.0.0",
    format: input.format || "gltf",
    sourceId: input.sourceId,
    assetUrl: input.assetUrl,
    coordinateSystemId: input.coordinateSystemId,
    regions: Array.isArray(input.regions) ? input.regions.map(createSpatialRegion) : [],
    metadata: input.metadata || {},
  };
}

export function createCoordinateSystem(input = {}) {
  return {
    id: input.id || "canonical-hand-v1",
    units: input.units || "unknown",
    axis: input.axis || { x: "x", y: "y", z: "z" },
    origin: input.origin || [0, 0, 0],
    handedness: input.handedness || "unknown",
    description: input.description || "",
  };
}

export function createSpatialSource(input = {}) {
  return {
    id: input.id,
    type: input.type || "own_dataset",
    label: input.label || input.id,
    uri: input.uri,
    version: input.version || "",
    license: input.license || "",
    provenance: input.provenance || {},
  };
}
