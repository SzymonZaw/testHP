(() => {
  'use strict';

  // Stage 3: one read/write contract for the hand surface UI. Existing modules
  // remain compatible; this store becomes the canonical state boundary.
  const VERSION = '1.0.0';
  const KEY = 'testhp.handSurfaceLayerState.v1';
  const VIEWS = ['front', 'back', 'side_left', 'side_right', 'thumb'];
  const MODES = ['classic', 'real'];
  const SOURCES = ['real', 'derived', 'default', 'none'];
  const STATUSES = ['missing', 'partial', 'ready', 'error'];

  const clone = value => value == null ? value : JSON.parse(JSON.stringify(value));
  const listeners = new Set();

  const emptyLayer = (spatialId = 'hand') => ({
    spatial_id: String(spatialId || 'hand'),
    geometry: { source: 'default', status: 'missing', data: null },
    measurements: { source: 'none', status: 'missing', data: null },
    images: [],
    observations: [],
    projection: { source: 'none', status: 'missing', data: null },
    updated_at: null,
  });

  const initial = () => ({
    version: VERSION,
    mode: 'classic',
    subject_id: 'own_cohort',
    timepoint: 'T0',
    target: { spatial_id: 'hand', label: 'Dłoń' },
    layer: emptyLayer('hand'),
    readiness: { real_hand: 'missing', reasons: ['brak danych rzeczywistych'] },
    effective: { geometry: 'default', measurements: 'none', images: 'none', projection: 'none' },
    meta: { updated_at: new Date().toISOString(), revision: 0 },
  });

  let state = initial();
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (saved && saved.version === VERSION) state = saved;
  } catch (_) {}

  const normalizeTarget = value => {
    if (!value) return { spatial_id: 'hand', label: 'Dłoń' };
    if (typeof value === 'string') return { spatial_id: value, label: value };
    return {
      spatial_id: String(value.spatial_id || value.spatialId || value.id || 'hand'),
      label: String(value.label || value.path?.join(' > ') || value.spatial_id || value.id || 'Dłoń'),
    };
  };

  const normalizeMode = mode => MODES.includes(mode) ? mode : 'classic';
  const source = value => SOURCES.includes(value) ? value : 'none';
  const status = value => STATUSES.includes(value) ? value : 'missing';
  const validView = value => VIEWS.includes(value) ? value : null;

  function persist() {
    state.meta = { ...state.meta, updated_at: new Date().toISOString(), revision: Number(state.meta?.revision || 0) + 1 };
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
    const snapshot = clone(state);
    listeners.forEach(fn => { try { fn(snapshot); } catch (_) {} });
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-state-changed', { detail: snapshot }));
  }

  function recompute() {
    const layer = state.layer;
    const measurementData = layer.measurements?.data;
    const measurementReady = !!measurementData && Object.entries(measurementData).some(([k, v]) => k !== 'updatedAt' && v != null && v !== '');
    const imageCount = layer.images.filter(x => x && !x.archived).length;
    const preparedCount = layer.images.filter(x => x && !x.archived && x.prepared === true).length;
    const registeredCount = layer.images.filter(x => x && !x.archived && x.registered === true).length;
    const projectionReady = layer.projection?.status === 'ready';
    const geometryReady = layer.geometry?.status === 'ready';

    const reasons = [];
    if (!geometryReady) reasons.push('brak gotowej geometrii rzeczywistej');
    if (!measurementReady) reasons.push('brak pomiarów');
    if (preparedCount === 0) reasons.push('brak przygotowanych zdjęć');
    if (imageCount > 0 && registeredCount === 0) reasons.push('brak zarejestrowanych zdjęć');

    state.readiness = {
      real_hand: geometryReady && measurementReady ? 'ready' : (imageCount || measurementReady ? 'partial' : 'missing'),
      reasons,
      images: { total: imageCount, prepared: preparedCount, registered: registeredCount },
      geometry: state.layer.geometry.status,
      measurements: state.layer.measurements.status,
      projection: state.layer.projection.status,
    };

    state.effective = {
      geometry: geometryReady ? 'real' : (layer.geometry?.data ? source(layer.geometry.source) : 'default'),
      measurements: measurementReady ? source(layer.measurements.source) : 'none',
      images: imageCount ? 'real' : 'none',
      projection: projectionReady ? source(layer.projection.source) : 'none',
    };
  }

  function setTarget(target, options = {}) {
    const normalized = normalizeTarget(target);
    state.target = normalized;
    if (state.layer.spatial_id !== normalized.spatial_id) state.layer = emptyLayer(normalized.spatial_id);
    if (options.persist !== false) persist();
    return api.snapshot();
  }

  function setMode(mode, options = {}) {
    state.mode = normalizeMode(mode);
    if (options.persist !== false) persist();
    return api.snapshot();
  }

  function setGeometry(data, options = {}) {
    state.layer.geometry = {
      source: source(options.source || (data ? 'real' : 'default')),
      status: status(options.status || (data ? 'ready' : 'missing')),
      data: clone(data),
    };
    recompute(); persist(); return api.snapshot();
  }

  function setMeasurements(data, options = {}) {
    state.layer.measurements = {
      source: source(options.source || (data ? 'real' : 'none')),
      status: status(options.status || (data ? 'ready' : 'missing')),
      data: clone(data),
    };
    recompute(); persist(); return api.snapshot();
  }

  function upsertImage(image) {
    if (!image) return api.snapshot();
    const id = String(image.asset_id || image.evidence_id || image.id || image.name || '');
    if (!id) return api.snapshot();
    const normalized = {
      asset_id: id,
      evidence_id: image.evidence_id || null,
      view: validView(image.view),
      spatial_id: String(image.spatial_id || image.spatial_node_id || state.target.spatial_id),
      prepared: image.prepared === true,
      registered: image.registered === true,
      projection: image.projection || null,
      archived: image.archived === true,
      source: 'real',
    };
    const index = state.layer.images.findIndex(x => x.asset_id === id);
    if (index >= 0) state.layer.images[index] = { ...state.layer.images[index], ...normalized };
    else state.layer.images.push(normalized);
    recompute(); persist(); return api.snapshot();
  }

  function removeImage(assetId) {
    state.layer.images = state.layer.images.filter(x => x.asset_id !== String(assetId));
    recompute(); persist(); return api.snapshot();
  }

  function setProjection(data, options = {}) {
    state.layer.projection = {
      source: source(options.source || (data ? 'derived' : 'none')),
      status: status(options.status || (data ? 'ready' : 'missing')),
      data: clone(data),
    };
    recompute(); persist(); return api.snapshot();
  }

  function setObservations(items) {
    state.layer.observations = Array.isArray(items) ? clone(items) : [];
    persist(); return api.snapshot();
  }

  function ingestLegacyState() {
    const mode = window.testhpHandGeometryMode?.getMode?.();
    if (mode) state.mode = normalizeMode(mode);
    const target = window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || window.spatialEvidenceTarget;
    if (target) state.target = normalizeTarget(target);
    try {
      const measurements = JSON.parse(localStorage.getItem('digitalTwinRealHandMeasurements.v1') || 'null');
      if (measurements && Object.keys(measurements).length) {
        state.layer.measurements = { source: 'real', status: 'ready', data: measurements };
      }
    } catch (_) {}
    recompute();
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {}
  }

  function subscribe(fn) {
    if (typeof fn !== 'function') return () => {};
    listeners.add(fn);
    try { fn(api.snapshot()); } catch (_) {}
    return () => listeners.delete(fn);
  }

  const api = {
    version: VERSION,
    views: VIEWS.slice(),
    modes: MODES.slice(),
    snapshot: () => clone(state),
    getLayer: () => clone(state.layer),
    getMode: () => state.mode,
    getTarget: () => clone(state.target),
    getReadiness: () => clone(state.readiness),
    getEffectiveSources: () => clone(state.effective),
    setTarget,
    setMode,
    setGeometry,
    setMeasurements,
    upsertImage,
    removeImage,
    setProjection,
    setObservations,
    subscribe,
    reset: () => { state = initial(); persist(); return api.snapshot(); },
  };

  window.handSurfaceLayerState = api;
  ingestLegacyState();

  window.addEventListener('testhp:hand-geometry-mode-changed', e => setMode(e.detail?.mode, { persist: true }));
  window.addEventListener('testhp:spatial-contract-changed', e => setTarget(e.detail, { persist: true }));
  window.addEventListener('testhp:spatial-layer-changed', e => setTarget(e.detail, { persist: true }));
  window.addEventListener('testhp:real-hand-geometry-applied', e => {
    const detail = e.detail || {};
    setMeasurements(detail.measurements || null, { source: 'real', status: detail.measurements ? 'ready' : 'missing' });
    setGeometry(detail.geometry || null, { source: 'real', status: detail.geometry ? 'ready' : 'missing' });
  });
  window.addEventListener('testhp:evidence-attached', () => recompute());
  window.addEventListener('testhp:surface-projection-plan-changed', () => recompute());
})();
