import { createCoordinateSystem, createSpatialAsset, createSpatialSource } from "./spatial-types.js";
import { validateCoordinateSystem, validateSpatialAsset, validateSpatialSource } from "./spatial-validator.js";
import { buildRegionEvidenceIndex, getEvidenceForRegion } from "./spatial-evidence.js";

export class SpatialDataAdapter {
  constructor({ source, asset, coordinateSystem, evidence = [] } = {}) {
    this.source = createSpatialSource(source);
    this.coordinateSystem = createCoordinateSystem(coordinateSystem);
    this.asset = createSpatialAsset({ ...asset, sourceId: asset?.sourceId || this.source.id });
    this.evidence = evidence;
    this.evidenceByRegion = buildRegionEvidenceIndex(evidence);
  }

  validate() {
    const source = validateSpatialSource(this.source);
    const coordinateSystem = validateCoordinateSystem(this.coordinateSystem);
    const asset = validateSpatialAsset(this.asset);
    return {
      valid: source.valid && coordinateSystem.valid && asset.valid,
      source,
      coordinateSystem,
      asset,
    };
  }

  getRegion(regionId) {
    return this.asset.regions.find((region) => region.id === regionId) || null;
  }

  getRegionByGeometryId(geometryId) {
    return this.asset.regions.find((region) => region.geometryId === geometryId) || null;
  }

  getEvidence(regionId) {
    return getEvidenceForRegion(this.evidenceByRegion, regionId);
  }

  toSpatialSelection({ regionId = null, tissueId = null, cellId = null } = {}) {
    return { regionId, tissueId, cellId };
  }

  toCanonicalSpatialState(selection = {}) {
    return {
      region: selection.regionId || null,
      tissue: selection.tissueId || null,
      cell: selection.cellId || null,
    };
  }
}
