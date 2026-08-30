(() => {
  // Dataset manifest for real public references. It intentionally does not claim
  // that unrelated tissue/cell datasets are spatially registered to the hand.
  const DATASETS = Object.freeze([
    {
      id: 'nih-hand-template-3dpx-017237',
      referenceId: 'nih-hand-template-3dpx-017237',
      scale: 'hand',
      spatialRegistration: 'native-source-space',
      role: 'hand-reference-geometry',
      usableFor: ['hand_surface_geometry'],
      notUsableFor: ['hand_region_segmentation', 'tissue_geometry', 'cell_geometry']
    },
    {
      id: 'nih-hand-bones-3dpx-017249',
      referenceId: 'nih-hand-bones-3dpx-017249',
      scale: 'hand',
      spatialRegistration: 'native-source-space',
      role: 'bone-reference-geometry',
      usableFor: ['bone_geometry'],
      notUsableFor: ['soft_tissue_geometry', 'cell_geometry']
    },
    {
      id: 'hubmap-human-reference-atlas',
      referenceId: 'hubmap-human-reference-atlas',
      scale: 'tissue-cell-molecular',
      spatialRegistration: 'dataset-native',
      role: 'reference-atlas',
      usableFor: ['tissue_data', 'spatial_cell_data', 'single_cell_data', 'multimodal_assays'],
      notUsableFor: ['direct_registration_to_nih_hand_template']
    }
  ]);

  function getDataset(id) {
    return DATASETS.find(item => item.id === id) || null;
  }

  window.testhpSpatialDatasetManifest = Object.freeze({
    DATASETS,
    getDataset
  });
})();
