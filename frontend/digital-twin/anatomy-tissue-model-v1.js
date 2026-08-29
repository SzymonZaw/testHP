(() => {
  'use strict';

  const KEY = '__testhpAnatomyTissueModelV1';
  if (window[KEY]) return;

  const VERSION = '1.0.0';
  const LEVELS = ['structure', 'tissue'];
  const TISSUE_TYPES = ['skin', 'connective', 'muscle', 'tendon', 'ligament', 'nerve', 'artery', 'vein', 'bone', 'other'];

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

  function validate(entity) {
    const errors = [];
    if (!entity?.id) errors.push('id');
    if (!entity?.spatialId) errors.push('spatialId');
    if (!entity?.source) errors.push('source');
    if (!entity?.status) errors.push('status');
    return { ok: errors.length === 0, errors };
  }

  const api = Object.freeze({ VERSION, LEVELS, TISSUE_TYPES, structure, tissue, validate });
  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:anatomy-tissue-model-ready', { detail: { version: VERSION } }));
})();
