(() => {
  'use strict';

  const KEY = '__testhpAnatomyTissueModelV1';
  if (window[KEY]) return;

  const VERSION = '1.1.0';
  const LEVELS = ['structure', 'tissue', 'cell'];
  const TISSUE_TYPES = ['skin', 'connective', 'muscle', 'tendon', 'ligament', 'nerve', 'artery', 'vein', 'bone', 'other'];
  const REGION_IDS = ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'];

  function structure(input = {}) {
    return {
      id: String(input.id || ''),
      spatialId: String(input.spatialId || ''),
      type: String(input.type || 'unknown'),
      label: String(input.label || input.type || 'Structure'),
      geometryAssetId: input.geometryAssetId || null,
      source: input.source || 'missing',
      status: input.status || 'missing'
    };
  }

  function tissue(input = {}) {
    return {
      id: String(input.id || ''),
      spatialId: String(input.spatialId || ''),
      type: TISSUE_TYPES.includes(input.type) ? input.type : 'other',
      parentStructureId: input.parentStructureId || null,
      geometryAssetId: input.geometryAssetId || null,
      evidenceIds: Array.isArray(input.evidenceIds) ? input.evidenceIds.map(String) : [],
      source: input.source || 'missing',
      status: input.status || 'missing'
    };
  }

  function cell(input = {}) {
    return {
      id: String(input.id || ''),
      spatialId: String(input.spatialId || ''),
      type: String(input.type || 'unknown'),
      tissueId: input.tissueId || null,
      geometryAssetId: input.geometryAssetId || null,
      coordinates: input.coordinates && ['x', 'y', 'z'].every(key => Number.isFinite(Number(input.coordinates[key])))
        ? { x: Number(input.coordinates.x), y: Number(input.coordinates.y), z: Number(input.coordinates.z) }
        : null,
      evidenceIds: Array.isArray(input.evidenceIds) ? input.evidenceIds.map(String) : [],
      source: input.source || 'missing',
      status: input.status || 'missing'
    };
  }

  function validate(entity) {
    const errors = [];
    if (!entity?.id) errors.push('id');
    if (!entity?.spatialId) errors.push('spatialId');
    if (!entity?.source) errors.push('source');
    if (!entity?.status) errors.push('status');
    return { ok: errors.length === 0, errors };
  }

  function validateRegionMappings(mappings = []) {
    const errors = [];
    const seenGeometry = new Set();
    const seenRegion = new Set();
    for (const mapping of mappings) {
      const geometryId = String(mapping?.geometryId || '');
      const regionId = String(mapping?.regionId || '');
      if (!geometryId) errors.push('missing geometryId');
      if (!REGION_IDS.includes(regionId)) errors.push(`invalid regionId: ${regionId || '(empty)'}`);
      if (seenGeometry.has(geometryId)) errors.push(`duplicate geometryId: ${geometryId}`);
      if (geometryId) seenGeometry.add(geometryId);
      if (regionId) seenRegion.add(regionId);
    }
    return { ok: errors.length === 0, errors, mappedRegions: [...seenRegion] };
  }

  function validateDataset(dataset = {}) {
    const errors = [];
    if (!dataset.id) errors.push('id');
    if (!dataset.name) errors.push('name');
    if (!dataset.coordinateSystem) errors.push('coordinateSystem');
    if (!Array.isArray(dataset.geometry)) errors.push('geometry[]');
    if (!Array.isArray(dataset.regionMappings)) errors.push('regionMappings[]');
    else errors.push(...validateRegionMappings(dataset.regionMappings).errors);
    return { ok: errors.length === 0, errors };
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  class SpatialReferenceRegistry {
    constructor() {
      this.reference = new Map();
      this.personal = new Map();
    }
    register(dataset) {
      const checked = validateDataset(dataset);
      if (!checked.ok) throw new Error(`Invalid reference dataset: ${checked.errors.join(', ')}`);
      const entry = clone(dataset);
      entry.kind = 'reference';
      entry.referenceOnly = true;
      this.reference.set(entry.id, entry);
      return clone(entry);
    }
    registerPersonal(dataset) {
      const checked = validateDataset(dataset);
      if (!checked.ok) throw new Error(`Invalid personal dataset: ${checked.errors.join(', ')}`);
      const entry = clone(dataset);
      entry.kind = 'personal';
      entry.referenceOnly = false;
      this.personal.set(entry.id, entry);
      return clone(entry);
    }
    get(id, mode = 'reference') {
      const value = (mode === 'personal' ? this.personal : this.reference).get(id);
      return value ? clone(value) : null;
    }
    list(mode = 'reference') {
      return [...(mode === 'personal' ? this.personal : this.reference).values()].map(clone);
    }
  }

  async function importSpatialAsset(file, metadata = {}) {
    if (!file || typeof file.arrayBuffer !== 'function') throw new Error('A GLB/GLTF File is required');
    const name = String(file.name || '').toLowerCase();
    const supported = name.endsWith('.glb') || name.endsWith('.gltf');
    if (!supported) throw new Error('Supported spatial assets: .glb or .gltf');

    const buffer = await file.arrayBuffer();
    if (name.endsWith('.glb')) {
      const view = new DataView(buffer);
      if (view.byteLength < 12 || view.getUint32(0, true) !== 0x46546c67) throw new Error('Invalid GLB header');
    } else {
      try { JSON.parse(new TextDecoder().decode(new Uint8Array(buffer))); }
      catch { throw new Error('Invalid GLTF JSON'); }
    }

    const dataset = {
      id: String(metadata.id || `personal-${Date.now()}`),
      name: String(metadata.name || file.name),
      version: String(metadata.version || '1.0.0'),
      coordinateSystem: metadata.coordinateSystem || null,
      geometry: Array.isArray(metadata.geometry) ? metadata.geometry : [],
      regionMappings: Array.isArray(metadata.regionMappings) ? metadata.regionMappings : [],
      tissueMappings: Array.isArray(metadata.tissueMappings) ? metadata.tissueMappings : [],
      cellMappings: Array.isArray(metadata.cellMappings) ? metadata.cellMappings : [],
      evidenceMappings: Array.isArray(metadata.evidenceMappings) ? metadata.evidenceMappings : [],
      provenance: metadata.provenance || { source: 'user-upload', filename: file.name },
      asset: { filename: file.name, mimeType: file.type || 'model/gltf-binary', size: file.size }
    };
    const checked = validateDataset(dataset);
    if (!checked.ok) throw new Error(`Invalid spatial metadata: ${checked.errors.join(', ')}`);
    dataset.assetUrl = URL.createObjectURL(file);
    return dataset;
  }

  const registry = new SpatialReferenceRegistry();
  const api = Object.freeze({
    VERSION,
    LEVELS,
    TISSUE_TYPES,
    REGION_IDS,
    structure,
    tissue,
    cell,
    validate,
    validateRegionMappings,
    validateDataset,
    SpatialReferenceRegistry,
    registry,
    importSpatialAsset
  });

  window[KEY] = api;
  window.testhpSpatialReferenceRegistry = registry;
  window.testhpImportSpatialAsset = importSpatialAsset;
  window.dispatchEvent(new CustomEvent('testhp:anatomy-tissue-model-ready', { detail: { version: VERSION } }));
  window.dispatchEvent(new CustomEvent('testhp:spatial-reference-registry-ready', { detail: { registry, version: VERSION } }));
})();
