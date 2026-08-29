(() => {
  'use strict';

  const KEY = '__testhpSpatialHierarchy';
  if (window[KEY]) return;

  const VERSION = '1.0.0';
  const LEVELS = Object.freeze(['macro', 'structure', 'tissue', 'cellular', 'cell', 'subcellular', 'molecular']);
  const LABELS = Object.freeze({
    macro: 'Macro anatomy',
    structure: 'Anatomical structure',
    tissue: 'Tissue',
    cellular: 'Cellular field',
    cell: 'Single cell',
    subcellular: 'Subcellular',
    molecular: 'Molecular'
  });

  function normalizePath(path) {
    const parts = Array.isArray(path) ? path : String(path || '').split('/');
    return parts.map(x => String(x ?? '').trim()).filter(Boolean);
  }

  function spatialId(path) { return normalizePath(path).join('/'); }

  function makeNode({ id, label, level, parentId = null, regionId = null, evidenceRequired = true } = {}) {
    if (!id || !LEVELS.includes(level)) throw new Error('Invalid spatial node');
    const parentPath = parentId ? normalizePath(parentId) : [];
    const path = [...parentPath, String(id)];
    return {
      id: String(id),
      label: label || String(id),
      level,
      regionId: regionId || null,
      parentId: parentId || null,
      path,
      spatialId: spatialId(path),
      evidenceRequired,
      navigationOnly: evidenceRequired
    };
  }

  function isDeeper(childLevel, parentLevel) {
    return LEVELS.indexOf(childLevel) > LEVELS.indexOf(parentLevel);
  }

  function canNavigate(node, evidence = []) {
    if (!node?.evidenceRequired) return true;
    return evidence.some(item => item?.spatialId === node.spatialId || item?.target?.spatialId === node.spatialId);
  }

  function buildDefaultHandTree() {
    const root = makeNode({ id: 'hand', label: 'Hand', level: 'macro', evidenceRequired: false });
    const regions = ['wrist', 'palm', 'thumb', 'index', 'middle', 'ring', 'little'];
    return [root, ...regions.map(id => makeNode({ id, label: id, level: 'structure', parentId: root.spatialId, regionId: id }))];
  }

  const api = Object.freeze({
    version: VERSION,
    levels: LEVELS.slice(),
    labels: { ...LABELS },
    normalizePath,
    spatialId,
    makeNode,
    isDeeper,
    canNavigate,
    buildDefaultHandTree
  });

  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:spatial-hierarchy-ready', { detail: { version: VERSION } }));
})();
