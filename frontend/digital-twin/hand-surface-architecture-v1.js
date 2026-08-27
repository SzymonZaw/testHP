/*
 * Canonical hand-surface architecture v1.
 *
 * Stages 1-5:
 *  1. Explicit hand modes: classic vs real-data.
 *  2. Canonical input-source taxonomy for every layer.
 *  3. Stable layer data contract with explicit ownership/provenance.
 *  4. Projection anchor owned by the scene, never by a deep layer.
 *  5. Deterministic mode resolution; no silent mixing of classic and real geometry.
 */
(() => {
  const VERSION = 'hand-surface-architecture-v1';
  const STORAGE_KEY = 'digitalTwinHandSurfaceArchitecture.v1';
  const MODES = Object.freeze({ CLASSIC: 'classic', REAL: 'real' });
  const LAYERS = Object.freeze(['macro', 'tissue', 'cellular', 'cell']);
  const SOURCE_KINDS = Object.freeze([
    'default',
    'classic-geometry',
    'measurement',
    'photo',
    'prepared-photo',
    'registered-photo',
    'reconstruction',
    'observation',
    'microscopy',
    'molecular'
  ]);
  const REAL_SOURCES = new Set([
    'measurement',
    'photo',
    'prepared-photo',
    'registered-photo',
    'reconstruction',
    'observation',
    'microscopy',
    'molecular'
  ]);

  const normalize = value => String(value ?? '').trim();
  const now = () => new Date().toISOString();

  function readLocal() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null'); }
    catch { return null; }
  }

  function writeLocal(value) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  }

  function normalizeSource(source, fallbackLayer = 'macro') {
    const s = source && typeof source === 'object' ? source : {};
    const kind = SOURCE_KINDS.includes(s.kind) ? s.kind : 'default';
    return {
      kind,
      layer: LAYERS.includes(s.layer) ? s.layer : fallbackLayer,
      id: normalize(s.id) || null,
      status: normalize(s.status) || 'available',
      spatial_id: normalize(s.spatial_id) || null,
      asset_id: normalize(s.asset_id) || null,
      provenance: normalize(s.provenance) || kind,
      updated_at: normalize(s.updated_at) || now()
    };
  }

  function createLayerContract(layer, input = {}) {
    if (!LAYERS.includes(layer)) throw new Error(`Unknown hand layer: ${layer}`);
    const sources = Array.isArray(input.sources)
      ? input.sources.map(x => normalizeSource(x, layer))
      : [];
    return {
      schema: 'hand-layer-contract-v1',
      layer,
      spatial_id: normalize(input.spatial_id) || 'hand',
      geometry: normalizeSource(input.geometry || { kind: 'default', layer }, layer),
      measurements: sources.filter(x => x.kind === 'measurement'),
      images: sources.filter(x => ['photo', 'prepared-photo', 'registered-photo'].includes(x.kind)),
      observations: sources.filter(x => x.kind === 'observation'),
      microscopy: sources.filter(x => x.kind === 'microscopy'),
      molecular: sources.filter(x => x.kind === 'molecular'),
      all_sources: sources,
      boundary: 'Research visualization only; data provenance is explicit and no clinical inference is implied.'
    };
  }

  function summarizeEvidence(evidence = []) {
    const items = Array.isArray(evidence) ? evidence : [];
    const mapped = items.map(item => {
      const x = item && typeof item === 'object' ? item : {};
      const prepared = !!(x.prepared || x.prepared_asset || x.preparedAsset);
      const registered = !!(x.registration?.status === 'registered' || x.registered === true);
      const kind = registered ? 'registered-photo' : prepared ? 'prepared-photo' : 'photo';
      return normalizeSource({
        kind,
        layer: 'macro',
        id: x.evidence_id,
        asset_id: x.asset_id,
        spatial_id: x.spatial_node_id || x.spatial_id,
        status: x.status || 'available',
        provenance: x.source || 'evidence-registry'
      });
    });
    return {
      sources: mapped,
      hasPhoto: mapped.some(x => REAL_SOURCES.has(x.kind)),
      hasPreparedPhoto: mapped.some(x => ['prepared-photo', 'registered-photo'].includes(x.kind)),
      hasRegisteredPhoto: mapped.some(x => x.kind === 'registered-photo'),
      photoCount: mapped.length
    };
  }

  function summarizeAnalysis(analysis) {
    const assets = Array.isArray(analysis?.assets) ? analysis.assets : [];
    const sources = assets.map(asset => {
      const modality = normalize(asset?.modality).toLowerCase();
      const kind = modality === 'hand' ? 'photo'
        : modality === 'wsi' ? 'microscopy'
        : modality === 'rna' ? 'molecular'
        : modality === 'metadata' ? 'measurement'
        : 'observation';
      return normalizeSource({
        kind,
        layer: modality === 'hand' || modality === 'metadata' ? 'macro' : modality === 'wsi' ? 'tissue' : 'cellular',
        id: asset?.id || asset?.asset_id,
        asset_id: asset?.asset_id || asset?.id,
        spatial_id: asset?.spatial_id || asset?.spatial_node_id,
        status: asset?.status,
        provenance: `analysis:${modality || 'unknown'}`
      });
    });
    return {
      sources,
      hasRealData: sources.some(x => REAL_SOURCES.has(x.kind)),
      hasPhoto: sources.some(x => x.kind === 'photo'),
      hasMeasurement: sources.some(x => x.kind === 'measurement'),
      counts: sources.reduce((out, x) => { out[x.kind] = (out[x.kind] || 0) + 1; return out; }, {})
    };
  }

  function resolveMode({ requested, evidence, analysis, current } = {}) {
    const requestedMode = requested === MODES.CLASSIC || requested === MODES.REAL ? requested : null;
    const evidenceSummary = summarizeEvidence(evidence);
    const analysisSummary = summarizeAnalysis(analysis);
    const hasReal = evidenceSummary.hasPhoto || analysisSummary.hasRealData;
    const selected = requestedMode || (current === MODES.REAL && hasReal ? MODES.REAL : MODES.CLASSIC);
    const effective = selected === MODES.REAL && hasReal ? MODES.REAL : MODES.CLASSIC;
    return {
      requested: requestedMode,
      effective,
      available: { classic: true, real: hasReal },
      reason: effective === MODES.REAL
        ? 'real-data-selected'
        : selected === MODES.REAL
          ? 'real-data-requested-but-unavailable'
          : 'classic-selected',
      evidence: evidenceSummary,
      analysis: analysisSummary,
      resolved_at: now()
    };
  }

  function getState() {
    return readLocal() || {
      schema: VERSION,
      mode: MODES.CLASSIC,
      mode_resolution: null,
      layers: {},
      projection: { anchor: 'scene', source_spatial_id: 'hand', target_spatial_id: 'hand', invariant: true },
      updated_at: now()
    };
  }

  function setMode(mode, context = {}) {
    const current = getState();
    const resolution = resolveMode({ ...context, requested: mode, current: current.mode });
    const next = { ...current, mode: resolution.effective, mode_resolution: resolution, updated_at: now() };
    writeLocal(next);
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-mode-changed', { detail: next }));
    return next;
  }

  function registerLayer(layer, contract) {
    const current = getState();
    const nextContract = createLayerContract(layer, contract);
    const next = { ...current, layers: { ...current.layers, [layer]: nextContract }, updated_at: now() };
    writeLocal(next);
    window.dispatchEvent(new CustomEvent('testhp:hand-surface-layer-contract-changed', { detail: nextContract }));
    return nextContract;
  }

  function bindViewport({ scene, macroRoot, deepRoot } = {}) {
    if (!scene) return null;
    let anchor = scene.getObjectByName?.('__hand_surface_projection_anchor__');
    if (!anchor) {
      anchor = new (window.THREE?.Group || class { constructor(){ this.name=''; this.children=[]; } })();
      anchor.name = '__hand_surface_projection_anchor__';
      if (typeof scene.add === 'function') scene.add(anchor);
    }
    anchor.userData = {
      ...(anchor.userData || {}),
      architecture: VERSION,
      ownership: 'scene',
      invariant: 'Projection is anchored to scene and does not move with deep-layer selection.'
    };
    const state = getState();
    state.projection = {
      schema: 'hand-surface-projection-anchor-v1',
      anchor: 'scene',
      anchor_name: anchor.name,
      source_spatial_id: state.projection?.source_spatial_id || 'hand',
      target_spatial_id: state.projection?.target_spatial_id || 'hand',
      invariant: true,
      macro_root: macroRoot?.name || null,
      deep_root: deepRoot?.name || null,
      updated_at: now()
    };
    writeLocal({ ...state, projection: state.projection, updated_at: now() });
    return anchor;
  }

  function keepProjectionOutOfDeepLayer(scene, deepRoot) {
    if (!scene || !deepRoot) return false;
    const anchor = scene.getObjectByName?.('__hand_surface_projection_anchor__');
    if (!anchor) return false;
    if (anchor.parent !== scene && typeof scene.add === 'function') scene.add(anchor);
    if (anchor.parent === deepRoot && typeof scene.add === 'function') scene.add(anchor);
    return anchor.parent === scene;
  }

  const API = {
    version: VERSION,
    MODES,
    LAYERS,
    SOURCE_KINDS,
    createLayerContract,
    summarizeEvidence,
    summarizeAnalysis,
    resolveMode,
    getState,
    setMode,
    registerLayer,
    bindViewport,
    keepProjectionOutOfDeepLayer,
    setEvidenceSnapshot(snapshot) {
      const current = getState();
      const resolution = resolveMode({
        evidence: snapshot?.evidence || [],
        analysis: snapshot?.analysis || null,
        current: current.mode
      });
      const next = { ...current, mode_resolution: resolution, updated_at: now() };
      writeLocal(next);
      window.dispatchEvent(new CustomEvent('testhp:hand-surface-architecture-synced', { detail: next }));
      return next;
    }
  };

  window.testhpHandSurfaceArchitecture = API;
})();
