(() => {
  'use strict';
  if (window.__testhpReferenceTissueRegistryInstalled) return;
  window.__testhpReferenceTissueRegistryInstalled = true;

  const VERSION = 'reference-tissue-safe-2';
  const HAND_REFERENCE = 'nih-hand-template-3DPX-017237';
  const SOURCES = Object.freeze({
    human_skin_spatial_census: Object.freeze({
      id: 'human-skin-spatial-census',
      label: 'Single-cell spatial transcriptomic analysis of human skin anatomy',
      modality: 'spatial_transcriptomics',
      organism: 'Homo sapiens',
      tissueScope: 'human_skin',
      sourceType: 'public_reference',
      accessions: ['S-BIAD2376'],
      geospatial: 'dataset-local',
      registrationStatus: 'unregistered_to_hand',
      handRegionIds: [],
      provenance: 'public_reference',
      notes: 'Real human skin spatial data. No automatic registration to NIH hand geometry is claimed.'
    }),
    geo_skin_spatial_visium: Object.freeze({
      id: 'geo-skin-spatial-visium',
      label: 'GEO human skin spatial transcriptomics sample',
      modality: 'spatial_transcriptomics',
      organism: 'Homo sapiens',
      tissueScope: 'human_skin',
      sourceType: 'public_reference',
      accessions: ['GSM8238470'],
      geospatial: 'dataset-local',
      registrationStatus: 'unregistered_to_hand',
      handRegionIds: [],
      provenance: 'public_reference',
      notes: 'Real Visium skin sample. The source provides local spatial coordinates, not coordinates in the NIH hand-template frame.'
    }),
    hubmap_human_reference_atlas: Object.freeze({
      id: 'hubmap-human-reference-atlas',
      label: 'HuBMAP Human Reference Atlas resources',
      modality: 'multimodal_tissue_reference',
      organism: 'Homo sapiens',
      tissueScope: 'human_tissues',
      sourceType: 'public_reference',
      accessions: [],
      geospatial: 'resource-dependent',
      registrationStatus: 'unregistered_to_hand',
      handRegionIds: [],
      provenance: 'public_reference',
      notes: 'Reference atlas/resource collection. Individual datasets require explicit anatomical and coordinate registration.'
    })
  });

  let selectedSourceId = null;
  let selectedRegionId = 'palm';

  function source(id) {
    return SOURCES[id] || null;
  }

  function makeState(sourceId = selectedSourceId, regionId = selectedRegionId) {
    const item = source(sourceId);
    return Object.freeze({
      version: VERSION,
      sourceId: item?.id || null,
      label: item?.label || null,
      modality: item?.modality || null,
      tissueScope: item?.tissueScope || null,
      regionId: regionId || 'palm',
      registrationStatus: item?.registrationStatus || 'no_source_selected',
      provenance: item?.provenance || 'public_reference',
      handReferenceId: HAND_REFERENCE,
      handRegionMapped: Boolean(item?.handRegionIds?.includes(regionId)),
      tissueIds: [],
      spatialCoordinates: [],
      evidenceIds: [],
      notes: item?.notes || null
    });
  }

  function publish() {
    window.__testhpReferenceTissueRegistryState = makeState();
    window.dispatchEvent(new CustomEvent('testhp:reference-tissue-changed', { detail: window.__testhpReferenceTissueRegistryState }));
    return window.__testhpReferenceTissueRegistryState;
  }

  function selectSource(id) {
    if (id && !source(id)) throw new Error(`Unknown reference tissue source: ${id}`);
    selectedSourceId = id || null;
    return publish();
  }

  function setRegion(regionId) {
    selectedRegionId = String(regionId || 'palm');
    return publish();
  }

  window.testhpReferenceTissueRegistry = Object.freeze({
    version: VERSION,
    handReferenceId: HAND_REFERENCE,
    sources: SOURCES,
    list: () => Object.values(SOURCES),
    selectSource,
    select: selectSource,
    setRegion,
    getState: () => window.__testhpReferenceTissueRegistryState || makeState()
  });

  window.addEventListener('testhp:canonical-state-changed', event => {
    const region = event?.detail?.selection?.region || 'palm';
    setRegion(region);
  });
  window.addEventListener('testhp:reference-region-geometry-changed', event => {
    if (event?.detail?.regionId) setRegion(event.detail.regionId);
  });
  publish();
})();
