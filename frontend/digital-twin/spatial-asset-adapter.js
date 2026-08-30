/* Spatial asset adapter: reference assets and user-owned GLB/GLTF imports. */
(() => {
  const REGIONS = Object.freeze([
    { id: 'palm', label: 'Palm', parentId: 'hand' },
    { id: 'thumb', label: 'Thumb', parentId: 'hand' },
    { id: 'index', label: 'Index', parentId: 'hand' },
    { id: 'middle', label: 'Middle', parentId: 'hand' },
    { id: 'ring', label: 'Ring', parentId: 'hand' },
    { id: 'little', label: 'Little', parentId: 'hand' },
    { id: 'wrist', label: 'Wrist', parentId: 'hand' }
  ]);

  const normalize = value => String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_');

  function validateMetadata(metadata) {
    const errors = [];
    if (!metadata || typeof metadata !== 'object') errors.push('metadata must be an object');
    if (!metadata?.assetId) errors.push('assetId is required');
    if (!metadata?.coordinateSystem) errors.push('coordinateSystem is required');
    if (!metadata?.sourceType) errors.push('sourceType is required');
    if (metadata?.sourceType === 'reference' && !metadata.sourceUrl) errors.push('reference sourceUrl is required');
    return { valid: errors.length === 0, errors };
  }

  function validateRegionMap(regionMap) {
    const errors = [];
    const entries = regionMap && typeof regionMap === 'object' ? Object.entries(regionMap) : [];
    const allowed = new Set(REGIONS.map(r => r.id));
    if (!entries.length) errors.push('regionMap must contain at least one geometryId → regionId mapping');
    for (const [geometryId, regionId] of entries) {
      if (!geometryId) errors.push('geometryId cannot be empty');
      if (!allowed.has(regionId)) errors.push(`unknown regionId: ${regionId}`);
    }
    return { valid: errors.length === 0, errors };
  }

  function createAsset({ metadata, regionMap = {}, annotations = [] } = {}) {
    const metadataResult = validateMetadata(metadata);
    const regionResult = validateRegionMap(regionMap);
    if (!metadataResult.valid || !regionResult.valid) {
      const error = new Error('Invalid spatial asset metadata');
      error.validation = { metadata: metadataResult, regions: regionResult };
      throw error;
    }
    return Object.freeze({
      id: metadata.assetId,
      source: {
        type: metadata.sourceType,
        url: metadata.sourceUrl || null,
        license: metadata.license || null,
        provenance: metadata.provenance || null
      },
      coordinateSystem: metadata.coordinateSystem,
      format: metadata.format || null,
      geometryUrl: metadata.geometryUrl || null,
      regionMap: Object.freeze({ ...regionMap }),
      annotations: Object.freeze([...annotations]),
      regions: REGIONS
    });
  }

  function mapGeometryToRegion(geometryId, asset) {
    const regionId = asset?.regionMap?.[geometryId];
    if (!regionId) return null;
    return REGIONS.find(region => region.id === regionId) || null;
  }

  function regionForObject(object3d, asset) {
    let node = object3d;
    while (node) {
      const geometryId = node.userData?.geometryId || node.userData?.geometry_id || node.name;
      const region = mapGeometryToRegion(geometryId, asset);
      if (region) return { geometryId, regionId: region.id, region };
      node = node.parent;
    }
    return null;
  }

  async function importUserAsset(file, metadata = {}, regionMap = {}, annotations = []) {
    if (!file) throw new Error('No GLB/GLTF file supplied');
    const name = String(file.name || '').toLowerCase();
    if (!name.endsWith('.glb') && !name.endsWith('.gltf')) throw new Error('Only .glb and .gltf assets are supported');
    const assetId = metadata.assetId || `user-${crypto.randomUUID()}`;
    return createAsset({
      metadata: {
        ...metadata,
        assetId,
        sourceType: 'user_upload',
        format: name.endsWith('.glb') ? 'glb' : 'gltf'
      },
      regionMap,
      annotations
    });
  }

  window.testhpSpatialAssetAdapter = Object.freeze({
    REGIONS,
    normalize,
    validateMetadata,
    validateRegionMap,
    createAsset,
    mapGeometryToRegion,
    regionForObject,
    importUserAsset
  });
})();
