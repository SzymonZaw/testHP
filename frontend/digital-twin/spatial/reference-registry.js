/**
 * Curated external reference-data registry for the Digital Twin.
 *
 * References are not user evidence and must never be copied into a user's
 * biological state. They are discoverable sources/templates/atlases with
 * explicit provenance, scope and intended use.
 */

export const REFERENCE_ROLES = Object.freeze([
  'reference',
  'template',
  'training_data',
  'user_evidence',
]);

export const REFERENCE_MODALITIES = Object.freeze([
  'anatomy_3d',
  'imaging',
  'tissue',
  'cellular',
  'molecular',
  'longitudinal',
]);

export const REFERENCE_DATASETS = Object.freeze([
  Object.freeze({
    datasetId: 'nih3d-3DPX-017237',
    title: 'Anatomical Template of Healthy Adult Human Hand',
    provider: 'NIH 3D',
    url: 'https://3d.nih.gov/entries/3DPX-017237',
    modality: 'anatomy_3d',
    roles: Object.freeze(['reference', 'template']),
    scope: 'healthy adult human hand anatomical template',
    subjectCount: 21,
    handCount: 27,
    provenance: 'T1-weighted MRI-derived anatomical template',
    coordinateSystem: 'dataset-defined; verify before spatial registration',
    license: 'See provider record',
    notes: 'Reference/template only; not a subject-specific Digital Twin.',
  }),
  Object.freeze({
    datasetId: 'nih3d-3DPX-017249',
    title: 'Bones of the Healthy Adult Human Hand/Wrist',
    provider: 'NIH 3D',
    url: 'https://3d.nih.gov/entries/17249',
    modality: 'anatomy_3d',
    roles: Object.freeze(['reference', 'template']),
    scope: 'hand and wrist bone segmentation',
    subjectCount: null,
    handCount: null,
    provenance: 'MRI-derived bone segmentation',
    coordinateSystem: 'dataset-defined; verify before spatial registration',
    license: 'See provider record',
    notes: 'Bone geometry only; does not establish soft tissue or cellular state.',
  }),
  Object.freeze({
    datasetId: 'openneuro',
    title: 'OpenNeuro',
    provider: 'OpenNeuro',
    url: 'https://openneuro.org/',
    modality: 'imaging',
    roles: Object.freeze(['reference']),
    scope: 'public neuroimaging and related datasets; organizational reference',
    subjectCount: null,
    handCount: null,
    provenance: 'Public research datasets using BIDS conventions where applicable',
    coordinateSystem: 'dataset-specific',
    license: 'Dataset-specific',
    notes: 'Use as a data-organization/provenance reference; select individual datasets before use.',
  }),
  Object.freeze({
    datasetId: 'human-protein-atlas',
    title: 'Human Protein Atlas',
    provider: 'Human Protein Atlas',
    url: 'https://www.proteinatlas.org/',
    modality: 'molecular',
    roles: Object.freeze(['reference']),
    scope: 'human gene/protein expression and cell-type reference data',
    subjectCount: null,
    handCount: null,
    provenance: 'Provider-curated transcriptomic, proteomic and cell-type resources',
    coordinateSystem: null,
    license: 'See provider terms for each resource',
    notes: 'Population/reference information must not be assigned to a specific user cell without supporting evidence.',
  }),
]);

function trim(value) {
  return typeof value === 'string' ? value.trim() : '';
}

export function getReferenceDataset(datasetId) {
  return REFERENCE_DATASETS.find((dataset) => dataset.datasetId === trim(datasetId)) || null;
}

export function listReferenceDatasets({ modality, role } = {}) {
  return REFERENCE_DATASETS.filter((dataset) => {
    const modalityMatch = !modality || dataset.modality === modality;
    const roleMatch = !role || dataset.roles.includes(role);
    return modalityMatch && roleMatch;
  });
}

export function validateReferenceRecord(record = {}) {
  const errors = [];
  if (!trim(record.datasetId)) errors.push('Reference requires datasetId');
  if (!trim(record.title)) errors.push('Reference requires title');
  if (!trim(record.provider)) errors.push('Reference requires provider');
  if (!trim(record.url)) errors.push('Reference requires URL');
  if (!REFERENCE_MODALITIES.includes(record.modality)) errors.push(`Unknown reference modality: ${record.modality || 'missing'}`);
  if (!Array.isArray(record.roles) || record.roles.length === 0) errors.push('Reference requires at least one role');
  if (Array.isArray(record.roles)) {
    for (const role of record.roles) {
      if (!REFERENCE_ROLES.includes(role)) errors.push(`Unknown reference role: ${role}`);
    }
  }
  return { valid: errors.length === 0, errors };
}

export function referenceToProvenance(record = {}) {
  return {
    datasetId: record.datasetId || null,
    provider: record.provider || null,
    source: record.url || null,
    version: record.version || null,
    license: record.license || null,
    modality: record.modality || null,
    scope: record.scope || null,
    provenance: record.provenance || null,
  };
}

export function isReferenceOnly(record = {}) {
  return Array.isArray(record.roles) && record.roles.length > 0 && !record.roles.includes('user_evidence');
}
