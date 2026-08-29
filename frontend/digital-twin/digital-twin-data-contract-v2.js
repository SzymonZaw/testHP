(() => {
  'use strict';

  const KEY = '__testhpDigitalTwinDataContractV2';
  if (window[KEY]) return;

  const VERSION = '2.0.0';
  const LEVELS = ['macro', 'structure', 'tissue', 'cellular', 'cell', 'subcellular', 'molecular'];
  const SOURCES = ['real', 'computed', 'simulated', 'default', 'missing'];
  const STATUSES = ['missing', 'available', 'partial', 'unverified', 'verified'];

  const normalizeSource = source => SOURCES.includes(source) ? source : 'missing';
  const normalizeStatus = status => STATUSES.includes(status) ? status : 'missing';

  function target(spatialId, level, regionId = null) {
    return {
      spatialId: String(spatialId || ''),
      level: LEVELS.includes(level) ? level : 'macro',
      regionId: regionId == null ? null : String(regionId)
    };
  }

  function evidence(input = {}) {
    const item = {
      id: String(input.id || crypto.randomUUID()),
      modality: String(input.modality || 'unknown'),
      source: normalizeSource(input.source),
      status: normalizeStatus(input.status),
      subjectId: String(input.subjectId || input.subject_id || ''),
      timepoint: String(input.timepoint || 'T0'),
      target: target(input.target?.spatialId || input.spatialId, input.target?.level || input.level, input.target?.regionId || input.regionId),
      assetId: input.assetId == null ? null : String(input.assetId),
      provenance: input.provenance || null,
      measurements: input.measurements || null
    };
    return item;
  }

  function assessment(input = {}) {
    return {
      id: String(input.id || crypto.randomUUID()),
      target: target(input.target?.spatialId || input.spatialId, input.target?.level || input.level, input.target?.regionId || input.regionId),
      type: String(input.type || 'unknown'),
      value: input.value ?? null,
      unit: input.unit || null,
      confidence: input.confidence == null ? null : Number(input.confidence),
      source: normalizeSource(input.source),
      status: normalizeStatus(input.status),
      evidenceIds: Array.isArray(input.evidenceIds) ? input.evidenceIds.map(String) : [],
      timestamp: input.timestamp || new Date().toISOString()
    };
  }

  function validateTwin(twin) {
    const errors = [];
    if (!twin?.schema) errors.push('schema');
    if (!twin?.subjectId) errors.push('subjectId');
    if (!twin?.timepoint) errors.push('timepoint');
    for (const item of twin?.evidence || []) {
      if (!item.id) errors.push('evidence.id');
      if (!item.target?.spatialId) errors.push(`evidence:${item.id}:target.spatialId`);
      if (!LEVELS.includes(item.target?.level)) errors.push(`evidence:${item.id}:target.level`);
    }
    for (const item of twin?.assessments || []) {
      if (!item.id) errors.push('assessment.id');
      if (!item.target?.spatialId) errors.push(`assessment:${item.id}:target.spatialId`);
    }
    return { ok: errors.length === 0, errors };
  }

  const api = Object.freeze({ VERSION, LEVELS, SOURCES, STATUSES, target, evidence, assessment, validateTwin });
  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:digital-twin-contract-v2-ready', { detail: { version: VERSION } }));
})();
