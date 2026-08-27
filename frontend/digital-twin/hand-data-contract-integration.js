(() => {
  'use strict';

  const KEY = '__testhpHandDataRuntime';
  if (window[KEY]) return;

  const CONTRACT_SRC = '/digital-twin/hand-data-contract.js?v=1';
  const read = key => { try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch { return null; } };
  const normalize = value => String(value ?? '').trim().replace(/^\/+|\/+$/g, '').toLowerCase();

  function ensureContract() {
    if (window.__testhpHandDataContract) return Promise.resolve(window.__testhpHandDataContract);
    return new Promise(resolve => {
      const onReady = () => resolve(window.__testhpHandDataContract || null);
      window.addEventListener('testhp:hand-data-contract-ready', onReady, { once: true });
      const existing = [...document.scripts].find(s => s.src && new URL(s.src, location.href).pathname === '/digital-twin/hand-data-contract.js');
      if (!existing) {
        const script = document.createElement('script');
        script.src = CONTRACT_SRC;
        script.dataset.handDataContract = 'true';
        document.head.appendChild(script);
      } else {
        setTimeout(onReady, 0);
      }
    });
  }

  function spatialTarget() {
    return normalize(
      window.testhpSpatialContract?.getTarget?.()?.spatial_id ||
      window.spatialViewportManager?.spatialTarget ||
      window.spatialEvidenceTarget ||
      document.body?.dataset?.spatialTarget || 'hand'
    );
  }

  function snapshot(contract) {
    const target = spatialTarget();
    const surface = read('digitalTwinHandSurface.v1') || {};
    const projection = surface.projection || {};
    const mappings = Array.isArray(surface.mappings) ? surface.mappings : [];
    const images = mappings.map(mapping => ({
      id: mapping.assetId || mapping.preparedAssetId || '',
      source: 'real',
      view: mapping.view || null,
      status: 'surface-projected',
      spatial: {
        layerId: normalize(mapping.spatialTarget || target),
        coordinateSystem: projection.coordinate_system || 'hand-surface-v1',
        transform: mapping.transform || projection.transform || null,
        anchor: mapping.anchor || null
      }
    }));
    const geometryRecord = surface.geometry?.[target] || null;
    const layer = contract.createLayer(target, {
      geometry: geometryRecord ? { value: geometryRecord.parameters || geometryRecord, source: geometryRecord.source === 'photo-registration' ? 'computed' : geometryRecord.source, status: geometryRecord.status || 'available' } : {},
      measurements: surface.measurements?.[target] || {},
      images,
      projection: projection ? { value: projection, source: projection.calibrated ? 'real' : 'computed', status: projection.status || 'missing', coordinateSystem: projection.coordinate_system || 'hand-surface-v1', transform: projection.transform || null } : {}
    });
    const validation = contract.validateLayer(layer);
    return {
      version: contract.version,
      target,
      layer,
      realModeAvailable: contract.canUseRealMode([layer]),
      validation,
      viewport: {
        managerPresent: !!window.spatialViewportManager,
        activeKey: window.spatialViewportManager?.activeKey || null,
        activeLayer: window.spatialViewportManager?.activeLayer || null
      },
      projection: {
        target: normalize(projection.target || target),
        sourceSpatialId: normalize(projection.source_spatial_id || target),
        appliedToModel: !!surface.appliedToModel,
        appliedTarget: normalize(surface.appliedTarget || target),
        appliedViews: Array.isArray(surface.appliedViews) ? surface.appliedViews.slice() : []
      }
    };
  }

  function sync(reason = 'runtime-sync') {
    const contract = window.__testhpHandDataContract;
    if (!contract) return null;
    const state = snapshot(contract);
    state.reason = reason;
    window[KEY].state = state;
    window.dispatchEvent(new CustomEvent('testhp:hand-data-runtime-synced', { detail: state }));
    if (!state.validation.ok) console.warn('[hand-data-contract] validation failed', state.validation.errors);
    return state;
  }

  window[KEY] = {
    version: '1.0.0',
    state: null,
    sync,
    getState: () => window[KEY].state,
    validate: () => window[KEY].state?.validation || null
  };

  ensureContract().then(() => sync('contract-ready'));
  ['testhp:viewport-manager-ready','testhp:spatial-layer-changed','testhp:spatial-target-changed','testhp:surface-projection-plan-changed','testhp:hand-surface-ready'].forEach(name => {
    window.addEventListener(name, () => setTimeout(() => sync(`event:${name}`), 0));
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => setTimeout(() => sync('dom-ready'), 0), { once: true });
  else setTimeout(() => sync('boot'), 0);
})();
