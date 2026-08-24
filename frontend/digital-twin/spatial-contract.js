(() => {
  // Single source of truth for spatial identity. Human-readable labels are display-only.
  const SEGMENT_RE = /[^a-z0-9_-]+/gi;
  const LEVELS = new Set(['macro', 'tissue', 'cellular', 'molecular']);
  const SEGMENT_ALIASES = Object.freeze({
    'hypothenar-eminence': 'hypothenar',
    'thenar-eminence': 'thenar',
    'central-palm-eminence': 'central-palm'
  });
  const ROOT_ALIASES = Object.freeze({
    palm: 'hand/palm',
    'śródręcze': 'hand/palm',
    srodrecze: 'hand/palm'
  });
  const LABELS = Object.freeze({
    'hand/palm': 'Śródręcze',
    hand: 'Dłoń',
    wrist: 'Nadgarstek',
    palm: 'Śródręcze',
    thumb: 'Kciuk',
    index: 'Palec wskazujący',
    middle: 'Palec środkowy',
    ring: 'Palec serdeczny',
    little: 'Mały palec'
  });
  const normalizeSegment = value => {
    const raw = String(value ?? '').trim().toLowerCase();
    const segment = raw.replaceAll(' ', '-').replace(SEGMENT_RE, '-');
    return SEGMENT_ALIASES[segment] || segment;
  };

  // Guard the canonical identity against accidental path accumulation. A
  // broken writer must not turn hand/palm into hand/palm/hand/palm/... and
  // thereby create an endless stream of increasingly long API requests.
  const collapseRepeatedPrefix = segments => {
    const result = [...segments];
    for (let size = Math.min(3, Math.floor(result.length / 2)); size >= 1; size -= 1) {
      let changed = true;
      while (changed && result.length >= size * 2) {
        changed = false;
        const prefix = result.slice(0, size).join('/');
        const next = result.slice(size, size * 2).join('/');
        if (prefix && prefix === next) {
          result.splice(size, size);
          changed = true;
        }
      }
    }
    return result;
  };

  const normalizeId = value => {
    const raw = String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();
    if (ROOT_ALIASES[raw]) return ROOT_ALIASES[raw];
    const segments = raw.split('/').map(normalizeSegment).filter(Boolean);
    return collapseRepeatedPrefix(segments).join('/');
  };
  const buildSpatialId = path => (Array.isArray(path) ? path : [])
    .map(item => typeof item === 'string' ? item : item?.id)
    .map(normalizeSegment).filter(Boolean).join('/');
  const canonicalTargetId = target => normalizeId(
    typeof target === 'object'
      ? (target?.spatial_id || target?.spatialId || target?.spatial_node_id || target?.targetSpatialId || target?.id)
      : target
  );
  const labelFor = (id, fallback) => {
    const canonical = normalizeId(id);
    if (LABELS[canonical]) return LABELS[canonical];
    const leaf = canonical.split('/').at(-1);
    return LABELS[leaf] || fallback || leaf || 'Region';
  };
  const sameTarget = (a, b) => {
    const left = canonicalTargetId(a), right = canonicalTargetId(b);
    return !!left && !!right && left === right;
  };
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
          next.spatialId = normalized;
          changed = true;
        }
        return next;
      });
      if (changed) localStorage.setItem(key, JSON.stringify(raw));
    } catch (_) {}
  };

  const normalizeTarget = detail => {
    const source = detail && typeof detail === 'object' ? detail : { spatial_id: detail };
    const path = Array.isArray(source.path) ? source.path.map(String) : [];
    const spatialId = canonicalTargetId(source) || normalizeId(buildSpatialId(path)) || 'hand/palm';
    const segments = spatialId.split('/').filter(Boolean);
    const rawLevel = String(source.level || '').toLowerCase();
    const level = LEVELS.has(rawLevel) ? rawLevel : rawLevel === 'single cell' ? 'cellular' : rawLevel || 'macro';
    const label = labelFor(spatialId, source.target || source.label || path.at(-1));
    return Object.freeze({
      spatial_id: spatialId,
      spatialId,
      id: normalizeSegment(source.id || segments.at(-1) || 'palm'),
      label,
      level,
      path: path.length ? path : segments,
      parent_spatial_id: segments.length > 1 ? segments.slice(0, -1).join('/') : null,
      children: Array.isArray(source.children) ? source.children : []
    });
  };

  let current = normalizeTarget({ spatial_id: 'hand/palm', id: 'palm', target: 'Śródręcze', level: 'macro', path: ['hand', 'palm'] });

  const managerTarget = manager => {
    const state = manager?.state || {};
    const active = manager?.active || {};
    const candidate = state.target && typeof state.target === 'object'
      ? state.target
      : active && typeof active === 'object'
        ? active
        : { spatial_id: state.spatial_id || state.spatialId || manager?.spatialTarget };
    const id = canonicalTargetId(candidate);
    if (!id) return null;
    return {
      ...candidate,
      spatial_id: id,
      spatialId: id,
      id: candidate.id || id.split('/').at(-1),
      target: candidate.target || candidate.label || labelFor(id, current.label),
      label: candidate.label || candidate.target || labelFor(id, current.label),
      level: candidate.level || manager?.activeLayer || current.level,
      path: Array.isArray(candidate.path) && candidate.path.length ? candidate.path : id.split('/'),
      children: Array.isArray(candidate.children) ? candidate.children : []
    };
  };

  const managerSpatialId = manager => canonicalTargetId(
    manager?.state?.spatial_id || manager?.state?.spatialId ||
    manager?.active?.spatial_id || manager?.active?.spatialId || manager?.spatialTarget || current.spatial_id
  );

  const syncCompatibility = () => {
    const manager = window.spatialViewportManager;
    const observed = managerTarget(manager);
    const canonical = canonicalTargetId(observed) || managerSpatialId(manager) || current.spatial_id;

    if (observed && canonical !== current.spatial_id) current = normalizeTarget(observed);
    else current = normalizeTarget({ ...current, spatial_id: canonical, spatialId: canonical, target: labelFor(canonical, current.label) });

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
      manager.active.spatial_id = canonical;
      manager.active.spatialId = canonical;
    }
    window.selectedSpatialNode = canonical;
    window.spatialEvidenceTarget = canonical;
    window.testhpSpatialTarget = canonical;
    if (document.body?.dataset && document.body.dataset.spatialTarget !== canonical) {
      document.body.dataset.spatialTarget = canonical;
    }
    migrateEvidenceTargets();
    window.dispatchEvent(new CustomEvent('digital-twin:target-changed', { detail: { id: canonical, spatial_id: canonical, target: current.label, level: current.level } }));
  };

  const publish = detail => {
    current = normalizeTarget(detail);
    syncCompatibility();
    window.dispatchEvent(new CustomEvent('testhp:spatial-contract-changed', { detail: current }));
    return current;
  };

  window.testhpSpatialContract = Object.freeze({
    normalizeId,
    canonicalTargetId,
    labelFor,
    sameTarget,
    buildSpatialId,
    relation,
    inScope,
    scope,
    getTarget: () => current,
    publish,
    reconcile: syncCompatibility,
    LEVELS: [...LEVELS],
    SEGMENT_ALIASES,
    ROOT_ALIASES
  });

  window.addEventListener('testhp:spatial-layer-changed', event => publish(event.detail || {}));
  window.addEventListener('testhp:spatial-contract-request', event => event?.detail?.callback?.(current));
  window.addEventListener('testhp:viewport-manager-ready', syncCompatibility);
  window.addEventListener('testhp:spatial-target-changed', syncCompatibility);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncCompatibility, { once: true });
  else setTimeout(syncCompatibility, 0);
  publish(current);
})();
