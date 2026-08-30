(() => {
  // Evidence-first manifest for real spatial mapping. This file deliberately
  // describes what is and is not established; it never invents anatomy.
  const REGION_IDS = Object.freeze([
    'palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'
  ]);

  const SEGMENTATION_SOURCES = Object.freeze([
    {
      id: 'nih-hand-template',
      sourceId: 'nih-hand-template-3dpx-017237',
      role: 'hand_surface_reference',
      expectedInputs: ['STL', 'NIfTI'],
      establishes: ['hand_surface_geometry'],
      doesNotEstablish: ['palm_id', 'thumb_id', 'index_id', 'middle_id', 'ring_id', 'little_id', 'wrist_id', 'tissue_geometry', 'cell_geometry'],
      registrationRequired: true
    },
    {
      id: 'nih-hand-bones',
      sourceId: 'nih-hand-bones-3dpx-017249',
      role: 'bone_reference',
      expectedInputs: ['segmented bone mesh'],
      establishes: ['bone_geometry'],
      doesNotEstablish: ['soft_tissue_geometry', 'cell_geometry'],
      registrationRequired: true
    },
    {
      id: 'hubmap-spatial',
      sourceId: 'hubmap-human-reference-atlas',
      role: 'tissue_cell_reference',
      expectedInputs: ['spatial dataset', 'segmentation/coordinates', 'metadata'],
      establishes: ['dataset_specific_cells', 'dataset_specific_spatial_coordinates', 'dataset_specific_tissue_annotations'],
      doesNotEstablish: ['registration_to_nih_hand_template'],
      registrationRequired: true
    }
  ]);

  const REQUIRED_REGION_MAPPING = Object.freeze(REGION_IDS.map(regionId => ({
    regionId,
    geometryIds: Object.freeze([]),
    status: 'not_established',
    evidenceIds: Object.freeze([])
  })));

  function validateMapping(mapping) {
    const errors = [];
    const seen = new Set();
    for (const item of mapping || []) {
      if (!item || !REGION_IDS.includes(item.regionId)) errors.push(`Unknown regionId: ${item && item.regionId}`);
      if (item && seen.has(item.regionId)) errors.push(`Duplicate regionId: ${item.regionId}`);
      if (item) seen.add(item.regionId);
      if (item && !Array.isArray(item.geometryIds)) errors.push(`geometryIds must be an array: ${item.regionId}`);
      if (item && !Array.isArray(item.evidenceIds)) errors.push(`evidenceIds must be an array: ${item.regionId}`);
      if (item && item.status === 'established' && (!item.geometryIds.length || !item.evidenceIds.length)) {
        errors.push(`Established mapping requires geometryIds and evidenceIds: ${item.regionId}`);
      }
    }
    return Object.freeze({ valid: errors.length === 0, errors: Object.freeze(errors) });
  }

  window.testhpSpatialSegmentation = Object.freeze({
    REGION_IDS,
    SEGMENTATION_SOURCES,
    REQUIRED_REGION_MAPPING,
    validateMapping
  });
})();
