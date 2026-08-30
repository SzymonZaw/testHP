/**
 * Reference descriptor for the public NIH 3D healthy-adult hand template.
 *
 * This module deliberately describes an external source; it does not copy the
 * source asset into the repository and it does not invent semantic region IDs.
 */

export const NIH_REFERENCE_HAND = Object.freeze({
  datasetId: 'nih3d-hand-template-017237',
  accession: '3DPX-017237',
  source: 'NIH 3D Print Exchange',
  sourceUrl: 'https://3d.nih.gov/entries/3DPX-017237',
  downloadUrl: 'https://3d.nih.gov/entries/download/17237/1',
  version: '2',
  species: 'Homo sapiens',
  anatomy: 'hand',
  modality: ['T1-weighted MRI', '3D segmentation', 'STL'],
  license: 'CC-BY; verify current source terms before redistribution',
  coordinateSystem: 'registration-template voxel space; source-specific',
  provenance: {
    sourceRecord: 'NIH 3DPX-017237',
    sampleDescription: 'Healthy adult hand registration template from T1-weighted MR images of 27 hands from 21 subjects',
    segmentation: '3D Slicer; hand segment exported as STL'
  },
  regionSchema: {
    status: 'NOT_ESTABLISHED',
    reason: 'The public source record provides a segmented hand template but does not establish our Palm/Thumb/Index/Middle/Ring/Little/Wrist semantic IDs.',
    expectedIds: ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist']
  },
  capabilities: {
    referenceHandGeometry: true,
    spatialRegistration: true,
    semanticRegionPicking: false,
    tissueGeometry: false,
    cellGeometry: false,
    molecularMapping: false
  }
});

export function createReferenceHandSource(overrides = {}) {
  return Object.freeze({
    ...NIH_REFERENCE_HAND,
    ...overrides,
    provenance: {
      ...NIH_REFERENCE_HAND.provenance,
      ...(overrides.provenance || {})
    },
    regionSchema: {
      ...NIH_REFERENCE_HAND.regionSchema,
      ...(overrides.regionSchema || {})
    },
    capabilities: {
      ...NIH_REFERENCE_HAND.capabilities,
      ...(overrides.capabilities || {})
    }
  });
}

export function createThreeJsLoadDescriptor(source = NIH_REFERENCE_HAND) {
  return Object.freeze({
    datasetId: source.datasetId,
    url: source.downloadUrl,
    format: 'stl',
    coordinateSystem: source.coordinateSystem,
    provenance: source.provenance,
    regionSchema: source.regionSchema
  });
}
