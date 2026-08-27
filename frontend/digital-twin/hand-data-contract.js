(() => {
  'use strict';

  const KEY = '__testhpHandDataContract';
  if (window[KEY]) return;

  const VERSION = '1.0.0';
  const SOURCE_PRIORITY = ['real', 'computed', 'default'];
  const IMAGE_STAGES = ['upload', 'source', 'view-assignment', 'preparation', 'registration', 'surface-projection'];

  const makeField = (value = null, source = null, status = 'missing') => ({ value, source, status });

  function createLayer(id, input = {}) {
    const geometry = input.geometry || {};
    const measurements = input.measurements || {};
    const images = Array.isArray(input.images) ? input.images : [];
    const observations = Array.isArray(input.observations) ? input.observations : [];
    const projection = input.projection || {};

    return {
      id: String(id),
      geometry: {
        value: geometry.value ?? null,
        source: geometry.source ?? null,
        status: geometry.status ?? 'missing'
      },
      measurements: {
        value: measurements.value ?? null,
        source: measurements.source ?? null,
        status: measurements.status ?? 'missing'
      },
      images: images.map(image => ({
        id: String(image.id ?? ''),
        source: image.source ?? 'upload',
        view: image.view ?? null,
        status: image.status ?? 'missing',
        spatial: {
          layerId: String(image.spatial?.layerId ?? id),
          coordinateSystem: image.spatial?.coordinateSystem ?? null,
          transform: image.spatial?.transform ?? null,
          anchor: image.spatial?.anchor ?? null
        }
      })),
      observations,
      projection: {
        value: projection.value ?? null,
        source: projection.source ?? null,
        status: projection.status ?? 'missing',
        coordinateSystem: projection.coordinateSystem ?? null,
        transform: projection.transform ?? null,
        anchor: projection.anchor ?? null
      }
    };
  }

  function resolveField(field, fallback = null) {
    if (!field) return { value: fallback, source: 'default', status: fallback == null ? 'missing' : 'available' };
    return field.value != null
      ? field
      : { value: fallback, source: 'default', status: fallback == null ? 'missing' : 'available' };
  }

  function hasRealData(layer) {
    return !!layer && (
      layer.geometry?.source === 'real' ||
      layer.measurements?.source === 'real' ||
      layer.images?.some(image => image.source === 'upload' || image.source === 'real') ||
      layer.projection?.source === 'real'
    );
  }

  function canUseRealMode(layers = []) {
    return layers.some(hasRealData);
  }

  const api = {
    version: VERSION,
    sourcePriority: SOURCE_PRIORITY.slice(),
    imageStages: IMAGE_STAGES.slice(),
    createLayer,
    resolveField,
    hasRealData,
    canUseRealMode,
    validateLayer(layer) {
      const errors = [];
      if (!layer?.id) errors.push('layer.id');
      if (layer?.projection?.status === 'available' && !layer.projection.coordinateSystem) errors.push('projection.coordinateSystem');
      for (const image of layer?.images || []) {
        if (image.spatial?.layerId !== layer.id) errors.push(`image:${image.id}:spatial.layerId`);
        if (image.status === 'surface-projected' && !image.spatial?.transform) errors.push(`image:${image.id}:spatial.transform`);
      }
      return { ok: errors.length === 0, errors };
    }
  };

  window[KEY] = api;
  window.dispatchEvent(new CustomEvent('testhp:hand-data-contract-ready', { detail: { version: VERSION } }));
})();
