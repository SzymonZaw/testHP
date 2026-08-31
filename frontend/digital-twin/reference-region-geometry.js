(() => {
  'use strict';
  if (window.__testhpReferenceRegionGeometryInstalled) return;
  window.__testhpReferenceRegionGeometryInstalled = true;

  const VERSION = 'reference-region-geometry-safe-1';
  const REGIONS = Object.freeze({
    hand: Object.freeze({ label: 'Hand', mappingMethod: 'whole_model', confidence: 'high' }),
    palm: Object.freeze({ label: 'Palm', mappingMethod: 'visual_focus_only', confidence: 'low' }),
    thumb: Object.freeze({ label: 'Thumb', mappingMethod: 'visual_focus_only', confidence: 'low' }),
    index: Object.freeze({ label: 'Index', mappingMethod: 'visual_focus_only', confidence: 'low' }),
    middle: Object.freeze({ label: 'Middle', mappingMethod: 'visual_focus_only', confidence: 'low' }),
    ring: Object.freeze({ label: 'Ring', mappingMethod: 'visual_focus_only', confidence: 'low' }),
    little: Object.freeze({ label: 'Little', mappingMethod: 'visual_focus_only', confidence: 'low' }),
    wrist: Object.freeze({ label: 'Wrist', mappingMethod: 'visual_focus_only', confidence: 'low' })
  });

  function getModel() {
    return document.querySelector('.dt-reference-3d-model');
  }

  function setRegion(regionId) {
    const region = REGIONS[regionId] || REGIONS.palm;
    const model = getModel();
    const payload = Object.freeze({
      version: VERSION,
      regionId: regionId || 'palm',
      label: region.label,
      mappingMethod: region.mappingMethod,
      confidence: region.confidence,
      meshSegmented: false,
      sourceId: 'nih-hand-template-3DPX-017237',
      provenance: 'public_reference'
    });

    window.__testhpReferenceRegionGeometryState = payload;

    if (model) {
      model.dataset.referenceRegion = payload.regionId;
      model.dataset.referenceMapping = payload.mappingMethod;
      model.dataset.referenceConfidence = payload.confidence;
    }

    window.dispatchEvent(new CustomEvent('testhp:reference-region-geometry-changed', { detail: payload }));
    return payload;
  }

  function currentRegion() {
    return window.TestHPCanonicalState?.get?.()?.selection?.region
      || window.__testhpReferenceHandState?.regionId
      || 'palm';
  }

  window.testhpReferenceRegionGeometry = Object.freeze({
    version: VERSION,
    regions: REGIONS,
    setRegion,
    getState: () => window.__testhpReferenceRegionGeometryState || setRegion(currentRegion())
  });

  window.addEventListener('testhp:canonical-state-changed', () => setRegion(currentRegion()));
  window.addEventListener('testhp:reference-hand-activated', () => setRegion(currentRegion()));
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setRegion(currentRegion()), { once: true });
  } else {
    setRegion(currentRegion());
  }
})();
