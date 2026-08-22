(() => {
  // Single source of truth for spatial identity. Human-readable labels are
  // never valid spatial IDs. Legacy aliases are normalized to the canonical
  // path used by the viewport manager and backend registry.
  const SEGMENT_RE = /[^a-z0-9_-]+/gi;
  const LEVELS = new Set(['macro', 'tissue', 'cellular', 'molecular', 'cell']);
  const SEGMENT_ALIASES = Object.freeze({
    'hypothenar-eminence': 'hypothenar',
    'thenar-eminence': 'thenar',
    'central-palm-eminence': 'central-palm'
  });
  const normalizeSegment = value => {
    const segment = String(value ?? '').trim().toLowerCase().replaceAll(' ', '-').replace(SEGMENT_RE, '-');
    return SEGMENT_ALIASES[segment] || segment;
  };
  const normalizeId = value => String(value ?? '').split('/').map(normalizeSegment).filter(Boolean).join('/');
  const buildSpatialId = path => (Array.isArray(path) ? path : [])
    .map(item => typeof item === 'string' ? item : item?.id)
    .map(normalizeSegment).filter(Boolean).join('/');
  const relation = (selectedId, candidateId) => {
    const selected = normalizeId(selectedId), candidate = normalizeId(candidateId);
    if (!selected || !candidate) return 'unknown';
    if (candidate === selected) return 'direct';
    if (candidate.startsWith(`${selected}/`)) return 'descendant';
    if (selected.startsWith(`${candidate}/`)) return 'ancestor';
    const parent = selected.includes('/') ? selected.slice(0, selected.lastIndexOf('/')) : '';
    if (parent && candidate.startsWith(`${parent}/`) && candidate.split('/').length === selected.split('/').length) return 'sibling';
    return 'other';
  };
  const inScope = (selectedId, candidateId, includeDescendants = false) => {
    const r = relation(selectedId, candidateId);
    return r === 'direct' || (includeDescendants && r === 'descendant');
  };
  const scope = (selectedId, ids, includeDescendants = false) => (Array.isArray(ids) ? ids : []).filter(id => inScope(selectedId, id, includeDescendants));

  const migrateEvidenceTargets = () => {
    try {
      const key = 'digitalTwinEvidenceUX.v2';
      const raw = JSON.parse(localStorage.getItem(key) || '{}');
      if (!Array.isArray(raw.evidence)) return;
      let changed = false;
      raw.evidence = raw.evidence.map(item => {
        if (!item || typeof item !== 'object') return item;
        const next = { ...item };
        const source = next.target ?? next.spatial_id ?? next.spatialId;
        const normalized = normalizeId(source);
        if (normalized && normalized !== source) {
          next.target = normalized;
          next.spatial_id = normalized;
          changed = true;
        }
        return next;
      });
      if (changed) localStorage.setItem(key, JSON.stringify(raw));
    } catch (_) {}
  };

  const normalizeTarget = detail => {
    const source = detail || {};
    const path = Array.isArray(source.path) ? source.path.map(String) : [];
    const spatialId = normalizeId(source.spatial_id || source.spatialId || buildSpatialId(path) || source.id || 'hand');
    const segments = spatialId.split('/').filter(Boolean);
    const rawLevel = String(source.level || '').toLowerCase();
    const level = LEVELS.has(rawLevel) ? rawLevel : rawLevel === 'single cell' ? 'cell' : rawLevel || 'macro';
    return Object.freeze({
      spatial_id: spatialId,
      id: normalizeSegment(source.id || segments.at(-1) || 'hand'),
      label: source.target || source.label || path.at(-1) || segments.at(-1) || 'Hand',
      level,
      path: path.length ? path : segments,
      parent_spatial_id: segments.length > 1 ? segments.slice(0, -1).join('/') : null,
      children: Array.isArray(source.children) ? source.children : []
    });
  };

  let current = normalizeTarget({ spatial_id: 'hand', id: 'hand', target: 'Hand', level: 'macro', path: ['Hand'] });

  const managerSpatialId = manager => normalizeId(
    manager?.state?.spatial_id || manager?.state?.spatialId ||
    manager?.active?.spatial_id || manager?.active?.spatialId || current.spatial_id
  );

  // Compatibility channels are synchronized only at explicit lifecycle/target
  // events. Do not observe the DOM or poll: doing so can react to our own
  // data-spatial-target write and create a self-triggering reconciliation loop.
  const syncCompatibility = () => {
    const manager = window.spatialViewportManager;
    const canonical = managerSpatialId(manager);
    if (!canonical) return;
    if (manager?.state && typeof manager.state === 'object') {
      manager.state.spatial_id = canonical;
      manager.state.spatialId = canonical;
      manager.state.spatialTarget = canonical;
      if (manager.state.target && typeof manager.state.target === 'object') {
        manager.state.target.spatial_id = canonical;
        manager.state.target.spatialId = canonical;
      }
    }
    if (manager && typeof manager === 'object') manager.spatialTarget = canonical;
    if (manager?.active && typeof manager.active === 'object') {
      if (typeof manager.active.spatial_id === 'string') manager.active.spatial_id = canonical;
      if (typeof manager.active.spatialId === 'string') manager.active.spatialId = canonical;
    }
    window.selectedSpatialNode = canonical;
    window.spatialEvidenceTarget = canonical;
    window.testhpSpatialTarget = canonical;
    if (document.body?.dataset && document.body.dataset.spatialTarget !== canonical) {
      document.body.dataset.spatialTarget = canonical;
    }
    migrateEvidenceTargets();
  };

  const publish = detail => {
    current = normalizeTarget(detail);
    syncCompatibility();
    window.dispatchEvent(new CustomEvent('testhp:spatial-contract-changed', { detail: current }));
    return current;
  };

  window.testhpSpatialContract = Object.freeze({
    normalizeId, buildSpatialId, relation, inScope, scope,
    getTarget: () => current,
    publish,
    reconcile: syncCompatibility,
    LEVELS: [...LEVELS],
    SEGMENT_ALIASES
  });

  window.addEventListener('testhp:spatial-layer-changed', event => publish(event.detail || {}));
  window.addEventListener('testhp:spatial-contract-request', event => event?.detail?.callback?.(current));
  window.addEventListener('testhp:viewport-manager-ready', syncCompatibility);
  window.addEventListener('testhp:spatial-target-changed', syncCompatibility);
  // This event is emitted by publish and is intentionally not used as a
  // reconciliation trigger; publish already synchronized before dispatch.

  publish(current);
})();
