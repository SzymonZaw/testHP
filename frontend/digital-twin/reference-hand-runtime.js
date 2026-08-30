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
    accession: '3DPX-017237'
  });

  function publishUiState() {
    if (!window.__testhpReferenceHandState?.active) return;
    const host = document.getElementById('testhp-end-user-layer');
    if (!host) return;

    host.dataset.referenceHandActive = 'true';
    host.dataset.referenceHandSource = REFERENCE_HAND.sourceId;
    host.dataset.referenceHandRegion = 'palm';

    const head = host.querySelector('.viewer-head');
    if (head) {
      let context = head.querySelector('.dt-explore-context');
      if (!context) {
        context = document.createElement('div');
        context.className = 'dt-explore-context';
        head.prepend(context);
      }
      context.innerHTML = '<strong>REFERENCE HAND</strong><span>NIH 3D · 3DPX-017237 · reference geometry</span><em>Reference data · not user health data</em>';
    }

    const viewport = host.querySelector('.viewport');
    if (viewport) {
      let badge = viewport.querySelector('.dt-reference-active');
      if (!badge) {
        badge = document.createElement('div');
        badge.className = 'dt-reference-active';
        viewport.appendChild(badge);
      }
      badge.textContent = 'REFERENCE HAND · NIH 3D · 3DPX-017237';
    }
  }

  function activate() {
    window.__testhpReferenceHandActivated = true;
    window.__testhpReferenceHandState = Object.freeze({
      active: true,
      sourceId: REFERENCE_HAND.sourceId,
      regionId: 'palm',
      provenance: 'public_reference'
    });
    publishUiState();
    window.dispatchEvent(new CustomEvent('testhp:reference-hand-activated', {
      detail: window.__testhpReferenceHandState
    }));
    return true;
  }

  window.testhpReferenceHand = Object.freeze({ REFERENCE_HAND, activate });
  window.addEventListener('testhp:reference-hand-requested', activate);

  const observer = new MutationObserver(() => publishUiState());
  if (document.documentElement) {
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }
  if (window.__testhpReferenceHandActivated) publishUiState();
})();
