(() => {
  'use strict';
  if (window.__testhpReferenceRegionGeometryInstalled) return;
  window.__testhpReferenceRegionGeometryInstalled = true;

  const VERSION = 'reference-region-geometry-safe-3';
  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const REGIONS = Object.freeze({
    hand: Object.freeze({ label: 'Hand', mappingMethod: 'whole_model', confidence: 'high', focus: [50, 50], cameraOrbit: '0deg 75deg 105%' }),
    palm: Object.freeze({ label: 'Palm', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [50, 58], cameraOrbit: '0deg 82deg 92%' }),
    thumb: Object.freeze({ label: 'Thumb', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [28, 52], cameraOrbit: '-28deg 74deg 88%' }),
    index: Object.freeze({ label: 'Index', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [42, 28], cameraOrbit: '-8deg 58deg 86%' }),
    middle: Object.freeze({ label: 'Middle', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [51, 22], cameraOrbit: '0deg 55deg 86%' }),
    ring: Object.freeze({ label: 'Ring', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [60, 25], cameraOrbit: '8deg 58deg 86%' }),
    little: Object.freeze({ label: 'Little', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [70, 34], cameraOrbit: '24deg 64deg 87%' }),
    wrist: Object.freeze({ label: 'Wrist', mappingMethod: 'visual_focus_only', confidence: 'low', focus: [50, 82], cameraOrbit: '0deg 96deg 94%' })
  });

  function getModel() {
    return document.querySelector('.dt-reference-3d-model');
  }

  function getCard() {
    return getModel()?.closest('.dt-reference-3d-card') || null;
  }

  function ensureFocusStyle() {
    if (document.getElementById('testhp-reference-region-focus-style')) return;
    const style = document.createElement('style');
    style.id = 'testhp-reference-region-focus-style';
    style.textContent = [
      '.dt-reference-region-focus{position:absolute;z-index:4;pointer-events:none;transform:translate(-50%,-50%);transition:left .25s ease,top .25s ease,opacity .2s ease}',
      '.dt-reference-region-focus-ring{width:54px;height:54px;border:2px solid rgba(155,216,196,.9);border-radius:50%;box-shadow:0 0 0 5px rgba(155,216,196,.12),0 0 22px rgba(155,216,196,.28);box-sizing:border-box;background:rgba(155,216,196,.05)}',
      '.dt-reference-region-focus-label{position:absolute;left:50%;top:calc(100% + 8px);transform:translateX(-50%);white-space:nowrap;padding:5px 8px;border-radius:8px;background:#0d151ee8;color:#dce7f2;font:700 11px/1.2 system-ui,sans-serif;border:1px solid rgba(155,216,196,.35)}',
      '.dt-reference-region-focus-note{position:absolute;left:50%;top:calc(100% + 31px);transform:translateX(-50%);white-space:nowrap;padding:3px 6px;border-radius:6px;background:#0d151ecf;color:#9fb0c2;font:600 9px/1.2 system-ui,sans-serif}'
    ].join('');
    document.head.appendChild(style);
  }

  function renderFocus(payload) {
    const card = getCard();
    if (!card) return;
    ensureFocusStyle();
    let focus = card.querySelector('.dt-reference-region-focus');
    if (!focus) {
      focus = document.createElement('div');
      focus.className = 'dt-reference-region-focus';
      focus.innerHTML = '<div class="dt-reference-region-focus-ring"></div><div class="dt-reference-region-focus-label"></div><div class="dt-reference-region-focus-note">visual focus · low confidence</div>';
      card.appendChild(focus);
    }
    const [left, top] = payload.focus || [50, 50];
    focus.style.left = `${left}%`;
    focus.style.top = `${top}%`;
    focus.querySelector('.dt-reference-region-focus-label').textContent = payload.label;
    focus.hidden = payload.regionId === 'hand';
  }

  function applyCamera(payload) {
    const model = getModel();
    if (!model || !model.loaded) return false;
    if (payload.cameraOrbit) model.cameraOrbit = payload.cameraOrbit;
    model.dataset.referenceCameraFocus = payload.regionId;
    return true;
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
      focus: region.focus,
      cameraOrbit: region.cameraOrbit,
      sourceId: SOURCE_ID,
      provenance: 'public_reference'
    });

    window.__testhpReferenceRegionGeometryState = payload;

    if (model) {
      model.dataset.referenceRegion = payload.regionId;
      model.dataset.referenceMapping = payload.mappingMethod;
      model.dataset.referenceConfidence = payload.confidence;
      applyCamera(payload);
    }

    renderFocus(payload);
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
    focusRegion: setRegion,
    getState: () => window.__testhpReferenceRegionGeometryState || setRegion(currentRegion())
  });

  window.addEventListener('testhp:canonical-state-changed', () => setRegion(currentRegion()));
  window.addEventListener('testhp:reference-hand-activated', () => setRegion(currentRegion()));
  window.addEventListener('testhp:reference-region-geometry-remounted', () => setRegion(currentRegion()));
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setRegion(currentRegion()), { once: true });
  } else {
    setRegion(currentRegion());
  }
})();
