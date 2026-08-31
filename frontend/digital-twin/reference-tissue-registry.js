(() => {
  'use strict';
  if (window.__testhpReferenceTissueRegistryInstalled) return;
  window.__testhpReferenceTissueRegistryInstalled = true;

  const VERSION = 'reference-tissue-safe-6';
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
      verification: Object.freeze({
        status: 'verified_public_source',
        study: 'Nature Genetics 2026',
        cellCountApprox: 1200000,
        donorCount: 22,
        sampleCount: 114,
        anatomicSiteCount: 15,
        spatialMethod: 'MERFISH',
        histologyIncluded: true,
        sourceUrl: 'https://www.ebi.ac.uk/biostudies/arrayexpress/studies/S-BIAD2376',
        publicationUrl: 'https://doi.org/10.1038/s41588-026-02552-8'
      }),
      verifiedAnatomicalSites: Object.freeze([
        Object.freeze({ regionId: 'palm', sourceSite: 'palm', approxCellCount: 2600 }),
        Object.freeze({ regionId: 'hand', sourceSite: 'hand', approxCellCount: 1148 })
      ]),
      spatialCoordinateScope: 'sample_local',
      registrationReadiness: 'anatomical_match_verified_transform_missing',
      registrationStatus: 'unregistered_to_hand',
      handRegionIds: [],
      provenance: 'public_reference',
      notes: 'Real human skin spatial data. Palm and hand samples are present. Spatial coordinates remain dataset/sample-local; no transform into the NIH hand-template frame is claimed.'
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
      verification: Object.freeze({
        status: 'verified_public_source',
        spatialMethod: '10x Genomics Visium',
        sourceUrl: 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8238470'
      }),
      registrationStatus: 'unregistered_to_hand',
      handRegionIds: [],
      spatialCoordinateScope: 'sample_local',
      registrationReadiness: 'no_verified_hand_registration',
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
      verification: Object.freeze({
        status: 'verified_public_source',
        sourceUrl: 'https://hubmapconsortium.org/'
      }),
      registrationStatus: 'unregistered_to_hand',
      handRegionIds: [],
      spatialCoordinateScope: 'resource_dependent',
      registrationReadiness: 'resource_dependent',
      provenance: 'public_reference',
      notes: 'Reference atlas/resource collection. Individual datasets require explicit anatomical and coordinate registration.'
    })
  });

  let selectedSourceId = null;
  let selectedRegionId = 'palm';

  function sourceById(id) {
    const key = Object.keys(SOURCES).find(key => key === id || SOURCES[key].id === id);
    return key ? SOURCES[key] : null;
  }

  function makeState(sourceId = selectedSourceId, regionId = selectedRegionId) {
    const item = sourceById(sourceId);
    const anatomicalMatch = item?.verifiedAnatomicalSites?.find(site => site.regionId === regionId) || null;
    return Object.freeze({
      version: VERSION,
      sourceId: item?.id || null,
      label: item?.label || null,
      modality: item?.modality || null,
      tissueScope: item?.tissueScope || null,
      regionId: regionId || 'palm',
      registrationStatus: item?.registrationStatus || 'no_source_selected',
      verificationStatus: item?.verification?.status || null,
      verification: item?.verification || null,
      provenance: item?.provenance || 'public_reference',
      handReferenceId: HAND_REFERENCE,
      anatomicalMatch: anatomicalMatch ? Object.freeze({ ...anatomicalMatch }) : null,
      handRegionMapped: Boolean(item?.handRegionIds?.includes(regionId)),
      registrationReadiness: item?.registrationReadiness || null,
      registrationEvidence: Object.freeze({
        transformAvailable: false,
        transformVerified: false,
        sourceCoordinateScope: item?.spatialCoordinateScope || null,
        targetCoordinateFrame: item ? HAND_REFERENCE : null,
        reason: item ? 'no_verified_transform_between_dataset_local_space_and_nih_hand_template' : null,
        evidenceLevel: item ? 'anatomical_match_only' : null
      }),
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
    const item = sourceById(id);
    if (id && !item) throw new Error(`Unknown reference tissue source: ${id}`);
    selectedSourceId = item?.id || null;
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
    getSource: sourceById,
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
