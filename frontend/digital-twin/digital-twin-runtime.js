(() => {
  'use strict';

  const KEY = '__testhpDigitalTwinRuntime';
  if (window[KEY]) return;

  const core = () => window.__testhpDigitalTwinCore;
  const contract = () => window.__testhpDigitalTwinDataContractV2;
  const hierarchy = () => window.__testhpSpatialHierarchy;
  const evidencePipeline = () => window.__testhpEvidencePipelineV2;

  let twin = null;
  let activePath = ['hand'];

  function ensureTwin(input = {}) {
    if (!core()) throw new Error('Digital twin core is not loaded');
    if (!twin || input.subjectId || input.timepoint) {
      twin = core().createDigitalTwin({
        subjectId: input.subjectId || twin?.subjectId || 'unknown-subject',
        timepoint: input.timepoint || twin?.timepoint || 'T0',
        hand: input.hand || twin?.hand || {},
        spatial: input.spatial || twin?.spatial || { rootId: 'hand', path: ['hand'], nodes: [] },
        evidence: input.evidence || twin?.evidence || [],
        assessments: input.assessments || twin?.assessments || [],
        timeline: input.timeline || twin?.timeline || []
      });
    }
    return twin;
  }

  function setActivePath(path) {
    const normalized = hierarchy() ? hierarchy().normalizePath(path) : String(path || '').split('/').filter(Boolean);
    activePath = normalized.length ? normalized : ['hand'];
    ensureTwin();
    twin.spatial.path = activePath.slice();
    twin.hand.canonicalSpatialId = activePath.join('/');
    return activePath.slice();
  }

  function activeSpatialId() {
    return activePath.join('/');
  }

  function ingestEvidence(records = []) {
    if (!contract()) throw new Error('Digital twin data contract v2 is not loaded');
    ensureTwin();
    const normalized = records.map(record => {
      if (record?.target) return contract().evidence(record);
      const spatialId = record?.spatial_id || record?.spatialId || record?.targetSpatialId || '';
      const level = record?.level || (spatialId.split('/').length > 1 ? 'structure' : 'macro');
      return contract().evidence({
        id: record?.id || record?.asset_id || record?.assetId,
        modality: record?.modality,
        source: record?.source || 'real',
        status: record?.status || 'available',
        subjectId: record?.subject_id || record?.subjectId || twin.subjectId,
        timepoint: record?.timepoint || twin.timepoint,
        spatialId,
        level,
        regionId: record?.region_id || record?.regionId,
        assetId: record?.asset_id || record?.assetId,
        provenance: record?.provenance,
        measurements: record?.measurements
      });
    });
    twin.evidence = normalized;
    return normalized.slice();
  }

  function evidenceForActiveTarget() {
    ensureTwin();
    return evidencePipeline()
      ? evidencePipeline().forTarget(twin.evidence, activeSpatialId())
      : twin.evidence.filter(item => item?.target?.spatialId === activeSpatialId());
  }

  function setAssessment(input = {}) {
    if (!contract()) throw new Error('Digital twin data contract v2 is not loaded');
    ensureTwin();
    const item = contract().assessment({ ...input, spatialId: input.spatialId || activeSpatialId(), level: input.level || 'structure' });
    twin.assessments = twin.assessments.filter(existing => existing.id !== item.id);
    twin.assessments.push(item);
    return item;
  }

  function snapshot() {
    ensureTwin();
    return core().clone(twin);
  }

  function validate() {
    ensureTwin();
    const coreResult = core().validate(twin);
    const contractResult = contract() ? contract().validateTwin(twin) : { ok: false, errors: ['contract-not-loaded'] };
    return {
      ok: coreResult.ok && contractResult.ok,
      core: coreResult,
      contract: contractResult
    };
  }

  function handleSpatialChange(event) {
    const detail = event?.detail || {};
    const path = Array.isArray(detail.path) && detail.path.length ? detail.path : String(detail.spatial_id || detail.id || 'hand').split('/');
    setActivePath(path.map((value, index) => {
      if (index === 0 && value === 'Hand') return 'hand';
      return String(value).trim();
    }).filter(Boolean));
    window.dispatchEvent(new CustomEvent('testhp:digital-twin-runtime-updated', {
      detail: { spatialId: activeSpatialId(), level: detail.level || null }
    }));
  }

  window.addEventListener('testhp:spatial-layer-changed', handleSpatialChange);

  const api = Object.freeze({
    version: '1.0.0',
    ensureTwin,
    setActivePath,
    activeSpatialId,
    ingestEvidence,
    evidenceForActiveTarget,
    setAssessment,
    snapshot,
    validate
  });

  window[KEY] = api;
  ensureTwin();
  window.dispatchEvent(new CustomEvent('testhp:digital-twin-runtime-ready', { detail: { version: api.version } }));
})();
