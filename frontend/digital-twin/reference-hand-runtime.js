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

  function activate() {
    if (window.__testhpReferenceHandActivated) return true;
    window.__testhpReferenceHandActivated = true;
    window.__testhpReferenceHandState = Object.freeze({
      active: true,
      source: REFERENCE_HAND,
      regionId: 'palm',
      provenance: 'public_reference'
    });
    window.dispatchEvent(new CustomEvent('testhp:reference-hand-activated', {
      detail: { reference: REFERENCE_HAND, regionId: 'palm' }
    }));
    return true;
  }

  window.testhpReferenceHand = Object.freeze({ REFERENCE_HAND, activate });
  window.addEventListener('testhp:reference-hand-requested', activate);
})();
