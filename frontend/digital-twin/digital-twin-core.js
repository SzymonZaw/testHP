(() => {
  'use strict';

  const KEY = '__testhpDigitalTwinCore';
  if (window[KEY]) return;

  const VERSION = '1.0.0';
  const LEVELS = Object.freeze(['macro', 'structure', 'tissue', 'cellular', 'cell', 'subcellular', 'molecular']);
  const SOURCES = Object.freeze(['real', 'computed', 'simulated', 'default', 'missing']);

  const clone = value => value == null ? value : JSON.parse(JSON.stringify(value));
  const cleanId = value => String(value ?? '').trim();

  function createDigitalTwin(input = {}) {
    const subjectId = cleanId(input.subjectId || input.subject_id || 'unknown-subject');
    const timepoint = cleanId(input.timepoint || 'T0');
    const hand = input.hand || {};

    return {
      schema: 'testhp.digital-twin',
      schemaVersion: VERSION,
      twinId: cleanId(input.twinId || `${subjectId}:hand`),
      subjectId,
      timepoint,
      hand: {
        id: cleanId(hand.id || 'hand'),
        side: hand.side || 'unknown',
        canonicalSpatialId: cleanId(hand.canonicalSpatialId || 'hand'),
        geometry: clone(hand.geometry) || { status: 'missing', source: 'missing', assetId: null },
        anatomy: clone(hand.anatomy) || [],
        regions: clone(hand.regions) || []
      },
      spatial: clone(input.spatial) || { rootId: 'hand', path: ['hand'] },
      evidence: clone(input.evidence) || [],
      assessments: clone(input.assessments) || [],
      timeline: clone(input.timeline) || [],
      metadata: clone(input.metadata) || {}
    };
  }

  function makeSpatialId(path) {
    const parts = Array.isArray(path) ? path : String(path || '').split('/');
    return parts.map(cleanId).filter(Boolean).join('/');
  }

  function getAtPath(twin, path) {
    const spatialId = makeSpatialId(path);
    if (!spatialId || !twin?.spatial?.nodes) return null;
    return twin.spatial.nodes.find(node => node.spatialId === spatialId) || null;
  }

  function validate(twin) {
    const errors = [];
    if (!twin || twin.schema !== 'testhp.digital-twin') errors.push('schema');
    if (!twin?.schemaVersion) errors.push('schemaVersion');
    if (!twin?.subjectId) errors.push('subjectId');
    if (!twin?.timepoint) errors.push('timepoint');
    if (!twin?.hand?.canonicalSpatialId) errors.push('hand.canonicalSpatialId');
    if (twin?.spatial?.path && makeSpatialId(twin.spatial.path) !== twin.hand.canonicalSpatialId) {
      errors.push('spatial.path');
    }
    return { ok: errors.length === 0, errors };
  }

  const api = Object.freeze({
    version: VERSION,
    levels: LEVELS.slice(),
    sources: SOURCES.slice(),
    createDigitalTwin,
    makeSpatialId,
    getAtPath,
    validate,
    clone
  });

  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:digital-twin-core-ready', { detail: { version: VERSION } }));
})();
