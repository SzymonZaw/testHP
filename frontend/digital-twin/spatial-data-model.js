(() => {
  if (window.__testhpSpatialDataModelInstalled) return;
  window.__testhpSpatialDataModelInstalled = true;

  const REGION_IDS = Object.freeze([
    'palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'
  ]);

  const DATA_STATUSES = Object.freeze(['available', 'missing']);
  const RESULT_STATUSES = Object.freeze([
    'observed', 'computed', 'estimated', 'predicted', 'hypothetical', 'not_established'
  ]);

  const normalizeId = value => String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();

  const normalizeRegionId = value => {
    const id = normalizeId(value).replace(/^hand\//, '');
    return REGION_IDS.includes(id) ? id : null;
  };

  const normalizeCoordinateSystem = value => {
    const source = value && typeof value === 'object' ? value : {};
    return Object.freeze({
      id: String(source.id || 'unknown'),
      units: String(source.units || 'unknown'),
      handedness: String(source.handedness || 'unknown'),
      origin: Array.isArray(source.origin) ? source.origin.slice(0, 3) : null,
      axes: source.axes && typeof source.axes === 'object' ? { ...source.axes } : null
    });
  };

  const normalizeEvidenceRefs = value => Array.isArray(value)
    ? value.map(item => {
        if (!item || typeof item !== 'object') return null;
        const id = String(item.id || '').trim();
        if (!id) return null;
        return Object.freeze({
          id,
          source: item.source ? String(item.source) : null,
          timepoint: item.timepoint ? String(item.timepoint) : null,
          regionId: normalizeRegionId(item.regionId || item.region_id),
          tissueId: item.tissueId ? String(item.tissueId) : null,
          cellId: item.cellId ? String(item.cellId) : null
        });
      }).filter(Boolean)
    : [];

  const validateSpatialAsset = asset => {
    const errors = [];
    const warnings = [];
    if (!asset || typeof asset !== 'object') return { valid: false, errors: ['asset must be an object'], warnings };
    if (!asset.id) errors.push('asset.id is required');
    if (!asset.uri) errors.push('asset.uri is required');
    if (!asset.format || !['glb', 'gltf'].includes(String(asset.format).toLowerCase())) {
      errors.push('asset.format must be glb or gltf');
    }
    if (!asset.coordinateSystem) warnings.push('coordinateSystem is not declared; spatial coordinates cannot be treated as authoritative');
    if (!Array.isArray(asset.regions)) warnings.push('regions[] is missing; geometry cannot be mapped to canonical region IDs');

    const seen = new Set();
    for (const region of Array.isArray(asset.regions) ? asset.regions : []) {
      const regionId = normalizeRegionId(region?.regionId || region?.region_id);
      if (!regionId) { errors.push(`invalid regionId: ${region?.regionId || region?.region_id || '(empty)'}`); continue; }
      if (seen.has(regionId)) errors.push(`duplicate regionId: ${regionId}`);
      seen.add(regionId);
      if (!region.geometryId) errors.push(`missing geometryId for region ${regionId}`);
    }
    return { valid: errors.length === 0, errors, warnings };
  };

  const createSpatialAsset = input => {
    const source = input && typeof input === 'object' ? input : {};
    const asset = {
      id: String(source.id || ''),
      uri: String(source.uri || ''),
      format: String(source.format || '').toLowerCase(),
      sourceId: source.sourceId ? String(source.sourceId) : null,
      license: source.license ? String(source.license) : null,
      coordinateSystem: normalizeCoordinateSystem(source.coordinateSystem),
      regions: (Array.isArray(source.regions) ? source.regions : []).map(region => Object.freeze({
        geometryId: String(region?.geometryId || ''),
        regionId: normalizeRegionId(region?.regionId || region?.region_id),
        evidenceIds: normalizeEvidenceRefs(region?.evidenceIds || region?.evidence_ids)
      }))
    };
    const validation = validateSpatialAsset(asset);
    return Object.freeze({ ...asset, validation });
  };

  const createSpatialSource = input => {
    const source = input && typeof input === 'object' ? input : {};
    return Object.freeze({
      id: String(source.id || ''),
      type: source.type ? String(source.type) : 'unknown',
      label: source.label ? String(source.label) : null,
      uri: source.uri ? String(source.uri) : null,
      license: source.license ? String(source.license) : null,
      provenance: source.provenance && typeof source.provenance === 'object' ? { ...source.provenance } : null
    });
  };

  const createSpatialAnnotation = input => {
    const source = input && typeof input === 'object' ? input : {};
    return Object.freeze({
      id: String(source.id || ''),
      type: ['point', 'mask', 'segmentation', 'polyline', 'bbox'].includes(source.type) ? source.type : 'point',
      coordinateSystem: normalizeCoordinateSystem(source.coordinateSystem),
      coordinates: Array.isArray(source.coordinates) ? source.coordinates : [],
      regionId: normalizeRegionId(source.regionId || source.region_id),
      tissueId: source.tissueId ? String(source.tissueId) : null,
      cellId: source.cellId ? String(source.cellId) : null,
      sourceId: source.sourceId ? String(source.sourceId) : null
    });
  };

  const mapGeometryToRegion = (asset, geometryId) => {
    const match = asset?.regions?.find(region => region.geometryId === geometryId);
    return match?.regionId || null;
  };

  const evidenceForRegion = (asset, regionId) => {
    const canonical = normalizeRegionId(regionId);
    return (asset?.regions || [])
      .filter(region => region.regionId === canonical)
      .flatMap(region => region.evidenceIds || []);
  };

  const importManifest = payload => {
    const source = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (!source || typeof source !== 'object') throw new Error('Spatial manifest must be an object');
    const spatialSource = createSpatialSource(source.spatialSource || source.source || {});
    const asset = createSpatialAsset({ ...(source.spatialAsset || source.asset || {}), sourceId: spatialSource.id });
    const annotations = (Array.isArray(source.annotations) ? source.annotations : []).map(createSpatialAnnotation);
    return Object.freeze({ spatialSource, spatialAsset: asset, annotations });
  };

  const registerWithCanonicalState = state => {
    const current = state && typeof state === 'object' ? state : {};
    return Object.freeze({
      subject: current.subject ?? null,
      timepoint: current.timepoint ?? null,
      region: current.region ?? null,
      tissue: current.tissue ?? null,
      cell: current.cell ?? null,
      molecularLayer: current.molecularLayer ?? null,
      evidence: current.evidence ?? null,
      biologicalState: current.biologicalState ?? null
    });
  };

  window.testhpSpatialDataModel = Object.freeze({
    REGION_IDS,
    DATA_STATUSES,
    RESULT_STATUSES,
    normalizeId,
    normalizeRegionId,
    createSpatialSource,
    createSpatialAsset,
    createSpatialAnnotation,
    validateSpatialAsset,
    mapGeometryToRegion,
    evidenceForRegion,
    importManifest,
    registerWithCanonicalState
  });
})();
