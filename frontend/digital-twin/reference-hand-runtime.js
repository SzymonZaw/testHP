(() => {
  'use strict';
  if (window.__testhpReferenceHandRuntimeInstalled) return;
  window.__testhpReferenceHandRuntimeInstalled = true;

  // NIH3D 3DPX-017237, processed version 2. The output-file endpoint serves
  // the real NIH3D GLB; the repository stores only the reference, never a copy.
  const REFERENCE_HAND = Object.freeze({
    id: 'nih3d-hand-template-3DPX-017237-v2',
    sourceId: 'nih3d-hand-template-3DPX-017237',
    label: 'NIH 3D · Healthy Adult Human Hand Template',
    ownership: 'reference',
    status: 'available',
    modality: 'hand_3d',
    sourceUrl: 'https://3d.nih.gov/entries/3DPX-017237',
    downloadPage: 'https://3d.nih.gov/entries/download/17237/2',
    url: 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811',
    accession: '3DPX-017237',
    processedVersion: '2',
    species: 'Homo sapiens',
    anatomy: 'hand',
    coordinateSystem: { id: 'nih3d-reference-template', units: 'mm', axisOrder: 'source-defined', orientation: 'source-defined' },
    provenance: {
      sourceType: 'public_reference',
      provider: 'NIH 3D',
      accession: '3DPX-017237',
      sourceUrl: 'https://3d.nih.gov/entries/3DPX-017237',
      downloadPage: 'https://3d.nih.gov/entries/download/17237/2'
    },
    limitations: [
      'Reference anatomy only; not a personal twin.',
      'The source is a segmented hand template derived from T1-weighted MRI of 27 healthy adult hands from 21 subjects.',
      'Semantic Palm/Thumb/Index/Middle/Ring/Little/Wrist geometry IDs are not asserted by this runtime.',
      'No tissue, cell, molecular, health, disease, age, trajectory, or intervention result is inferred from this asset.'
    ]
  });

  function hasPersonalOrActiveAsset() {
    const active = window.__testhpSpatialActiveAsset;
    if (active?.ownership === 'user' || active?.ownership === 'personal') return true;
    try {
      const state = window.TestHPCanonicalState?.get?.();
      return Array.isArray(state?.assets) && state.assets.some(asset => asset?.ownership === 'user' || asset?.ownership === 'personal');
    } catch {
      return false;
    }
  }

  function activate() {
    if (!window.TestHPSpatialData?.setActiveAsset) return false;
    if (hasPersonalOrActiveAsset() || window.__testhpReferenceHandActivated) return true;

    const asset = {
      id: REFERENCE_HAND.id,
      url: REFERENCE_HAND.url,
      sourceId: REFERENCE_HAND.sourceId,
      status: REFERENCE_HAND.status,
      ownership: REFERENCE_HAND.ownership,
      metadata: {
        schemaVersion: '1.0',
        assetId: REFERENCE_HAND.id,
        sourceId: REFERENCE_HAND.sourceId,
        sourceUrl: REFERENCE_HAND.sourceUrl,
        accession: REFERENCE_HAND.accession,
        processedVersion: REFERENCE_HAND.processedVersion,
        modality: REFERENCE_HAND.modality,
        coordinateSystem: REFERENCE_HAND.coordinateSystem,
        provenance: REFERENCE_HAND.provenance,
        limitations: REFERENCE_HAND.limitations,
        // Deliberately empty: no semantic region mapping is claimed from the source mesh.
        regions: [],
        mappings: []
      },
      mapping: { valid: true, geometryToRegion: {}, regionToGeometry: {} }
    };

    window.__testhpReferenceHandActivated = true;
    window.TestHPSpatialData.setActiveAsset(asset);
    window.dispatchEvent(new CustomEvent('testhp:reference-hand-activated', { detail: { asset, reference: REFERENCE_HAND } }));
    return true;
  }

  function boot() {
    if (activate()) return;
    setTimeout(boot, 100);
  }

  window.testhpReferenceHand = Object.freeze({ REFERENCE_HAND, activate });
  boot();
})();
