(() => {
  // Public reference catalog. References are never treated as patient/user data.
  // A reference may provide geometry, segmentation, cells, or molecular data;
  // the adapter must not invent missing spatial relationships.
  const REFERENCES = Object.freeze([
    {
      id: 'nih-hand-template-3dpx-017237',
      kind: 'hand_geometry',
      title: 'NIH 3D Healthy Adult Human Hand Template',
      sourceUrl: 'https://3d.nih.gov/entries/3DPX-017237',
      downloadUrl: 'https://3d.nih.gov/entries/download/17237/1',
      upstreamRepository: 'https://github.com/HegdeUSA/Hand_template',
      license: 'MIT (upstream HegdeUSA/Hand_template repository)',
      coordinateSystem: 'source-defined',
      provides: ['hand_surface_geometry'],
      doesNotProvide: ['region_segmentation', 'tissue_geometry', 'cell_geometry', 'cell_ids'],
      provenance: 'T1-weighted MRI template from 27 healthy adult hands from 21 subjects; exported as a segmented hand surface.',
      status: 'reference_geometry_only'
    },
    {
      id: 'nih-hand-bones-3dpx-017249',
      kind: 'hand_geometry',
      title: 'NIH 3D Healthy Adult Human Hand/Wrist Bones',
      sourceUrl: 'https://3d.nih.gov/entries/3DPX-017249',
      downloadUrl: 'https://3d.nih.gov/entries/download/17249/1',
      license: 'GNU GPLv3',
      coordinateSystem: 'source-defined',
      provides: ['bone_geometry'],
      doesNotProvide: ['soft_tissue_geometry', 'cell_geometry', 'cell_ids'],
      provenance: 'Segmented bones from the NIH healthy adult hand template.',
      status: 'reference_bone_geometry'
    },
    {
      id: 'hubmap-human-reference-atlas',
      kind: 'spatial_cell_reference',
      title: 'HuBMAP Human Reference Atlas / Data Portal',
      sourceUrl: 'https://hubmapconsortium.org/hubmap-data/',
      portalUrl: 'https://portal.hubmapconsortium.org/',
      provides: ['tissue_data', 'spatial_cell_data', 'single_cell_data', 'multimodal_assays', 'anatomical_reference_terms'],
      doesNotProvide: ['direct_registration_to_nih_hand_template'],
      provenance: 'Public human tissue data with spatial and single-cell modalities and a common anatomical reference framework.',
      status: 'reference_tissue_cell_molecular'
    },
    {
      id: 'allen-cell-explorer',
      kind: 'cell_reference',
      title: 'Allen Cell Explorer',
      sourceUrl: 'https://www.allencell.org/',
      viewerUrl: 'https://www.allencell.org/3d-cell-viewer.html',
      provides: ['3d_cell_images', 'cell_features', 'cell_structure_data', 'genomics_transcriptomics'],
      doesNotProvide: ['direct_registration_to_nih_hand_template'],
      provenance: 'Public 3D microscopy and cell-structure resources from the Allen Institute for Cell Science.',
      status: 'reference_cell_molecular'
    }
  ]);

  const get = id => REFERENCES.find(item => item.id === id) || null;
  const list = kind => kind ? REFERENCES.filter(item => item.kind === kind) : [...REFERENCES];

  window.testhpSpatialReferenceRegistry = Object.freeze({
    REFERENCES,
    get,
    list
  });
})();
