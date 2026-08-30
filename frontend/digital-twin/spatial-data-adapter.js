/* Spatial data boundary for reference datasets and user-owned Digital Twin data. */
(() => {
  'use strict';
  if (window.__testhpSpatialDataAdapterInstalled) return;
  window.__testhpSpatialDataAdapterInstalled = true;

  const REGION_IDS = Object.freeze(['palm','thumb','index','middle','ring','little','wrist']);
  const MODALITIES = Object.freeze(['hand_3d','tissue_segmentation','cell_segmentation','spatial_transcriptomics','rna','proteomics','epigenetics','genomics','imaging','wsi','3d_scan']);
  const STATUS = Object.freeze(['reference','user','available','missing']);
  const asString = value => typeof value === 'string' ? value.trim() : '';
  const normalizeId = value => asString(value).toLowerCase().replace(/\s+/g,'_');
  const unique = values => [...new Set(values.filter(Boolean))];

  function validateCoordinateSystem(input) {
    const c = input && typeof input === 'object' ? input : {};
    const errors = [];
    if (!asString(c.id)) errors.push('coordinateSystem.id is required');
    if (!asString(c.units)) errors.push('coordinateSystem.units is required');
    if (!asString(c.axisOrder)) errors.push('coordinateSystem.axisOrder is required');
    if (!asString(c.orientation)) errors.push('coordinateSystem.orientation is required');
    return { valid: errors.length === 0, errors, value: c };
  }

  function validateRegion(region) {
    const r = region && typeof region === 'object' ? region : {};
    const regionId = normalizeId(r.regionId ?? r.region_id ?? r.id);
    const geometryId = asString(r.geometryId ?? r.geometry_id);
    const errors = [];
    if (!regionId) errors.push('regionId is required');
    else if (!REGION_IDS.includes(regionId)) errors.push(`unsupported regionId: ${regionId}`);
    if (!geometryId) errors.push(`geometryId is required for ${regionId || 'region'}`);
    return { valid: errors.length === 0, errors, value: { ...r, regionId, geometryId } };
  }

  function validateSpatialManifest(manifest) {
    const m = manifest && typeof manifest === 'object' ? manifest : {};
    const errors = [];
    if (!asString(m.schemaVersion)) errors.push('schemaVersion is required');
    if (!asString(m.assetId)) errors.push('assetId is required');
    if (!asString(m.sourceId)) errors.push('sourceId is required');
    errors.push(...validateCoordinateSystem(m.coordinateSystem).errors);
    if (!asString(m.assetUrl)) errors.push('assetUrl is required');
    const regions = Array.isArray(m.regions) ? m.regions.map(validateRegion) : [];
    if (!regions.length) errors.push('at least one spatial region is required');
    regions.forEach(r => errors.push(...r.errors));
    const ids = regions.map(r => r.value.regionId).filter(Boolean);
    const duplicateIds = ids.filter((id,i) => ids.indexOf(id) !== i);
    if (duplicateIds.length) errors.push(`duplicate regionId: ${unique(duplicateIds).join(', ')}`);
    return { valid: errors.length === 0, errors: unique(errors), manifest: { ...m, coordinateSystem: m.coordinateSystem, regions: regions.map(r => r.value) } };
  }

  function mapGeometryToRegions(manifest) {
    const validation = validateSpatialManifest(manifest);
    if (!validation.valid) return { valid:false, errors:validation.errors, geometryToRegion:{}, regionToGeometry:{} };
    const geometryToRegion = {};
    const regionToGeometry = {};
    validation.manifest.regions.forEach(region => {
      if (geometryToRegion[region.geometryId]) throw new Error(`geometryId mapped more than once: ${region.geometryId}`);
      geometryToRegion[region.geometryId] = region.regionId;
      regionToGeometry[region.regionId] = region.geometryId;
    });
    return { valid:true, errors:[], geometryToRegion, regionToGeometry };
  }

  function normalizeImportMetadata(metadata, assetUrl) {
    const validation = validateSpatialManifest({ ...metadata, assetUrl });
    if (!validation.valid) throw new Error(validation.errors.join('; '));
    return validation.manifest;
  }

  function makeReferenceSource(source) { return { ...source, status:'reference', readOnly:true, userData:false }; }

  window.TestHPSpatialData = Object.freeze({
    REGION_IDS, MODALITIES, STATUS, normalizeId, validateCoordinateSystem, validateRegion,
    validateSpatialManifest, mapGeometryToRegions, normalizeImportMetadata, makeReferenceSource,
    setActiveAsset(asset) {
      if (!asset?.url) throw new Error('Active spatial asset requires a browser-loadable url');
      window.__testhpSpatialActiveAsset = asset;
      window.dispatchEvent(new CustomEvent('testhp:spatial-asset-selected',{detail:{asset}}));
    },
    clearActiveAsset() { delete window.__testhpSpatialActiveAsset; window.dispatchEvent(new CustomEvent('testhp:spatial-asset-cleared')); }
  });
})();
