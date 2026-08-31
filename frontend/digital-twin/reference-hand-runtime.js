(() => {
  'use strict';
  if (window.__testhpReferenceHandRuntimeInstalled) return;
  window.__testhpReferenceHandRuntimeInstalled = true;

  const REFERENCE_HAND = Object.freeze({
    id: 'nih3d-hand-template-3DPX-017237-v2',
    sourceId: 'nih-hand-template-3DPX-017237',
    label: 'NIH 3D · Healthy Adult Human Hand Template',
    ownership: 'reference',
    status: 'available',
    modality: 'hand_3d',
    sourceUrl: 'https://3d.nih.gov/entries/3DPX-017237',
    assetUrl: 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811',
    assetFormat: 'glb',
    accession: '3DPX-017237',
    provenance: 'public_reference',
    userHealthData: false
  });

  function currentRegion() {
    const region = window.TestHPCanonicalState?.get?.()?.selection?.region;
    return region || window.__testhpReferenceHandState?.regionId || 'palm';
  }

  function publishUiState() {
    if (!window.__testhpReferenceHandState?.active) return;
    const host = document.getElementById('testhp-end-user-layer');
    if (!host) return;

    const regionId = currentRegion();
    host.dataset.referenceHandActive = 'true';
    host.dataset.referenceHandSource = REFERENCE_HAND.sourceId;
    host.dataset.referenceHandRegion = regionId;
    host.dataset.referenceHandAsset = REFERENCE_HAND.assetUrl;

    const head = host.querySelector('.viewer-head');
    if (head) {
      let context = head.querySelector('.dt-explore-context');
      if (!context) {
        context = document.createElement('div');
        context.className = 'dt-explore-context';
        head.prepend(context);
      }
      context.innerHTML = '<strong>REFERENCE HAND</strong><span>NIH 3D · 3DPX-017237 · GLB reference geometry</span><em>Reference data · not user health data</em>';
    }

    const viewport = host.querySelector('.viewport');
    if (viewport) {
      let badge = viewport.querySelector('.dt-reference-active');
      if (!badge) {
        badge = document.createElement('div');
        badge.className = 'dt-reference-active';
        viewport.appendChild(badge);
      }
      badge.textContent = 'REFERENCE HAND · NIH 3D · 3DPX-017237 · GLB';
    }

    if (!head && !viewport && !host.querySelector('.dt-reference-runtime-state')) {
      const status = document.createElement('section');
      status.className = 'dt-reference-runtime-state';
      status.setAttribute('aria-label', 'Active reference hand');
      status.innerHTML = '<strong>REFERENCE HAND</strong><span>NIH 3D · 3DPX-017237 · GLB reference geometry</span><em>Public reference data · not user health data</em>';
      host.prepend(status);
    }
  }

  function syncRegionFromCanonicalState() {
    if (!window.__testhpReferenceHandState?.active) return;
    const regionId = currentRegion();
    window.__testhpReferenceHandState = Object.freeze({
      ...window.__testhpReferenceHandState,
      regionId
    });
    publishUiState();
  }

  function activate() {
    const regionId = currentRegion();
    window.__testhpReferenceHandActivated = true;
    window.__testhpReferenceHandState = Object.freeze({
      active: true,
      sourceId: REFERENCE_HAND.sourceId,
      regionId,
      provenance: 'public_reference',
      assetUrl: REFERENCE_HAND.assetUrl,
      assetFormat: REFERENCE_HAND.assetFormat,
      userHealthData: false
    });
    publishUiState();
    window.dispatchEvent(new CustomEvent('testhp:reference-hand-activated', {
      detail: window.__testhpReferenceHandState
    }));
    return true;
  }

  window.testhpReferenceHand = Object.freeze({ REFERENCE_HAND, activate });
  window.addEventListener('testhp:reference-hand-requested', activate);
  window.addEventListener('testhp:canonical-state-changed', syncRegionFromCanonicalState);

  if (window.__testhpReferenceHandActivated) publishUiState();
})();
