(() => {
  const clean = value => String(value ?? '').replace(/^\/+|\/+$/g, '');

  function canonical(value) {
    const raw = typeof value === 'object' ? (value.spatial_id || value.spatialId || value.id) : value;
    const id = clean(raw || 'hand');
    if (!id) return 'hand';
    return id === 'hand' || id.startsWith('hand/') ? id : `hand/${id}`;
  }

  function parent(spatialId) {
    const id = canonical(spatialId);
    if (id === 'hand') return null;
    const parts = id.split('/');
    return parts.length === 2 ? 'hand' : parts.slice(0, -1).join('/');
  }

  function isDirect(spatialId, selectedSpatialId) {
    return canonical(spatialId) === canonical(selectedSpatialId);
  }

  function isDescendant(spatialId, selectedSpatialId) {
    const child = canonical(spatialId);
    const selected = canonical(selectedSpatialId);
    return child !== selected && child.startsWith(`${selected}/`);
  }

  function classify(spatialId, selectedSpatialId) {
    if (isDirect(spatialId, selectedSpatialId)) return 'direct';
    if (isDescendant(spatialId, selectedSpatialId)) return 'descendant';
    return 'outside';
  }

  function inScope(spatialId, selectedSpatialId, includeDescendants = true) {
    const relation = classify(spatialId, selectedSpatialId);
    return relation === 'direct' || (includeDescendants && relation === 'descendant');
  }

  function filter(items, selectedSpatialId, { includeDescendants = true, biologicalLevel = null, subjectId = null, timepoint = null } = {}) {
    return (Array.isArray(items) ? items : []).filter(item => {
      if (!inScope(item?.spatial_id, selectedSpatialId, includeDescendants)) return false;
      if (biologicalLevel && String(item.biological_level || '').toLowerCase() !== String(biologicalLevel).toLowerCase()) return false;
      if (subjectId && item.subject_id !== subjectId) return false;
      if (timepoint && item.timepoint !== timepoint) return false;
      return item?.status !== 'archived';
    });
  }

  function split(items, selectedSpatialId, options = {}) {
    const selected = canonical(selectedSpatialId);
    const scoped = filter(items, selected, options);
    return {
      direct: scoped.filter(item => isDirect(item?.spatial_id, selected)),
      descendants: scoped.filter(item => isDescendant(item?.spatial_id, selected)),
      scoped
    };
  }

  function countByLevel(items, selectedSpatialId, options = {}) {
    const levels = ['macro', 'tissue', 'cellular', 'molecular'];
    const result = {};
    for (const level of levels) {
      const part = split(items, selectedSpatialId, { ...options, biologicalLevel: level });
      result[level] = { direct: part.direct.length, descendants: part.descendants.length, total: part.scoped.length };
    }
    return result;
  }

  function selection(detail = {}) {
    const selected = window.__testhpCanonicalSpatialSelection || window.selectedSpatialNode;
    const spatialId = canonical(detail.spatial_id || detail.spatialId || detail.id || selected?.spatial_id || selected?.id || 'hand');
    const path = Array.isArray(detail.path) ? detail.path : (Array.isArray(selected?.path) ? selected.path : []);
    return {
      id: spatialId,
      spatial_id: spatialId,
      parent_id: parent(spatialId),
      label: String(detail.target || detail.label || selected?.label || spatialId.split('/').pop()),
      path
    };
  }

  window.testhpSpatialScope = Object.freeze({ canonical, parent, isDirect, isDescendant, classify, inScope, filter, split, countByLevel, selection });
  window.dispatchEvent(new CustomEvent('testhp:spatial-scope-resolver-ready'));
})();
