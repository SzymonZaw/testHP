(() => {
  'use strict';

  const REGION_IDS = ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'];
  const FORMATS = ['glb', 'gltf'];

  function validateSpatialAssetManifest(manifest) {
    const errors = [];
    const warnings = [];
    const m = manifest && typeof manifest === 'object' ? manifest : {};

    for (const key of ['schemaVersion', 'assetId', 'assetUrl', 'format', 'coordinateSystem', 'regions']) {
      if (m[key] === undefined || m[key] === null || m[key] === '') errors.push(`Missing required field: ${key}`);
    }

    const format = String(m.format || '').toLowerCase().replace(/^\./, '');
    if (format && !FORMATS.includes(format)) errors.push(`Unsupported format: ${format}`);

    const cs = m.coordinateSystem;
    if (!cs || typeof cs !== 'object') {
      errors.push('coordinateSystem must describe the source coordinate system');
    } else {
      if (!cs.units) errors.push('coordinateSystem.units is required');
      if (!['X', 'Y', 'Z'].includes(cs.upAxis)) errors.push('coordinateSystem.upAxis must be X, Y or Z');
      if (!['left', 'right'].includes(cs.handedness)) errors.push('coordinateSystem.handedness must be left or right');
    }

    const regions = Array.isArray(m.regions) ? m.regions : [];
    const ids = new Set();
    const geometryIds = new Set();
    regions.forEach((region, index) => {
      if (!region || typeof region !== 'object') {
        errors.push(`regions[${index}] must be an object`);
        return;
      }
      if (!region.regionId) errors.push(`regions[${index}].regionId is required`);
      if (!region.geometryId) errors.push(`regions[${index}].geometryId is required`);
      if (region.regionId) {
        if (ids.has(region.regionId)) errors.push(`Duplicate regionId: ${region.regionId}`);
        ids.add(region.regionId);
        if (!REGION_IDS.includes(region.regionId)) warnings.push(`Unknown regionId: ${region.regionId}`);
      }
      if (region.geometryId) {
        if (geometryIds.has(region.geometryId)) errors.push(`Duplicate geometryId: ${region.geometryId}`);
        geometryIds.add(region.geometryId);
      }
    });

    for (const id of REGION_IDS) if (!ids.has(id)) warnings.push(`Region not supplied: ${id}`);

    return Object.freeze({
      ok: errors.length === 0,
      errors: Object.freeze(errors),
      warnings: Object.freeze(warnings),
      regionCount: regions.length
    });
  }

  function buildRegionEvidenceIndex(manifest) {
    const result = new Map();
    for (const region of (Array.isArray(manifest?.regions) ? manifest.regions : [])) {
      if (!region?.regionId) continue;
      result.set(region.regionId, Object.freeze({
        geometryId: region.geometryId || null,
        tissueId: region.tissueId || null,
        cellId: region.cellId || null,
        evidenceIds: Object.freeze(Array.isArray(region.evidenceIds) ? region.evidenceIds.map(String) : [])
      }));
    }
    return result;
  }

  window.testhpSpatialAssetValidator = Object.freeze({
    REGION_IDS: Object.freeze(REGION_IDS),
    FORMATS: Object.freeze(FORMATS),
    validateSpatialAssetManifest,
    buildRegionEvidenceIndex
  });
})();
