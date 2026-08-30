(() => {
  const REGION_IDS = Object.freeze(['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist']);
  const CELL_REQUIRED_FIELDS = Object.freeze(['cellId', 'x', 'y', 'z']);

  const asArray = value => Array.isArray(value) ? value : [];
  const nonEmpty = value => typeof value === 'string' && value.trim().length > 0;

  const validateRegionMappings = mappings => {
    const errors = [];
    const seenRegions = new Set();
    const seenGeometry = new Set();

    for (const item of asArray(mappings)) {
      const regionId = String(item?.regionId || '').trim().toLowerCase();
      const geometryId = String(item?.geometryId || '').trim();
      if (!REGION_IDS.includes(regionId)) errors.push(`Unknown regionId: ${regionId || '<empty>'}`);
      if (!geometryId) errors.push(`Missing geometryId for ${regionId || '<empty>'}`);
      if (seenRegions.has(regionId)) errors.push(`Duplicate regionId: ${regionId}`);
      if (seenGeometry.has(geometryId)) errors.push(`Duplicate geometryId: ${geometryId}`);
      if (regionId) seenRegions.add(regionId);
      if (geometryId) seenGeometry.add(geometryId);
    }

    return { valid: errors.length === 0, errors, mappings: asArray(mappings) };
  };

  const validateCell = cell => {
    const errors = [];
    for (const field of CELL_REQUIRED_FIELDS) {
      if (field === 'cellId') {
        if (!nonEmpty(cell?.cellId)) errors.push('Missing cellId');
      } else if (!Number.isFinite(Number(cell?.[field]))) {
        errors.push(`Missing numeric coordinate: ${field}`);
      }
    }
    return { valid: errors.length === 0, errors };
  };

  const createSpatialDataAdapter = ({ manifest, assetUrl = null, regionMappings = null, evidenceId = null } = {}) => {
    const mappings = regionMappings ?? manifest?.regions?.mappings ?? [];
    const regionValidation = validateRegionMappings(mappings);
    const geometryToRegion = new Map(mappings.map(item => [String(item.geometryId), String(item.regionId)]));
    const regionToGeometry = new Map(mappings.map(item => [String(item.regionId), String(item.geometryId)]));

    return Object.freeze({
      manifest,
      assetUrl,
      evidenceId,
      regionIds: REGION_IDS,
      regionValidation,
      geometryToRegion: geometryId => geometryToRegion.get(String(geometryId)) || null,
      regionToGeometry: regionId => regionToGeometry.get(String(regionId)) || null,
      hasRealRegionMapping: regionValidation.valid && mappings.length > 0,
      validateCell,
      validateRegionMappings,
      mapPickingResult: picking => {
        const geometryId = picking?.geometryId ?? picking?.object?.userData?.geometryId ?? picking?.object?.name;
        const regionId = geometryToRegion.get(String(geometryId)) || null;
        return { geometryId: geometryId || null, regionId, evidenceId };
      }
    });
  };

  window.testhpCreateSpatialDataAdapter = createSpatialDataAdapter;
  window.testhpSpatialRegionIds = REGION_IDS;
})();
