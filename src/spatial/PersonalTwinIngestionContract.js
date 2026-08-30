export const PERSONAL_TWIN = 'personal';

const SUPPORTED_MODALITIES = new Set([
  '3d_scan',
  'mri',
  'ct',
  'histology',
  'whole_slide_image',
  'spatial_transcriptomics',
  'single_cell_rna',
  'proteomics',
  'epigenetics',
  'genomics',
]);

export function validatePersonalManifest(manifest = {}) {
  const errors = [];
  if (!manifest.subjectId) errors.push('Missing subjectId');
  if (!manifest.timepointId) errors.push('Missing timepointId');
  if (!Array.isArray(manifest.inputs)) errors.push('inputs must be an array');

  for (const input of manifest.inputs ?? []) {
    if (!input.id) errors.push('Input is missing id');
    if (!SUPPORTED_MODALITIES.has(input.modality)) {
      errors.push(`Unsupported modality: ${input.modality ?? '(missing)'}`);
    }
    if (!input.source) errors.push(`Missing source for ${input.id ?? '(missing)'}`);
  }
  return { valid: errors.length === 0, errors };
}

export function buildPersonalTwinSource(manifest) {
  const validation = validatePersonalManifest(manifest);
  if (!validation.valid) throw new Error(validation.errors.join('; '));

  return {
    id: `personal:${manifest.subjectId}:${manifest.timepointId}`,
    type: PERSONAL_TWIN,
    subjectId: manifest.subjectId,
    timepointId: manifest.timepointId,
    inputs: manifest.inputs.map((input) => ({
      id: input.id,
      modality: input.modality,
      source: input.source,
      provenance: input.provenance ?? null,
      coordinateSystem: input.coordinateSystem ?? null,
    })),
    status: 'INGESTED_MANIFEST',
    biologicalState: null,
  };
}

export function createPersonalTwinManifest({ subjectId, timepointId, inputs = [] }) {
  return {
    schemaVersion: 1,
    subjectId,
    timepointId,
    inputs,
  };
}
