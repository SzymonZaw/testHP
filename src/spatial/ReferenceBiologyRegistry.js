const LAYERS = new Set(['tissue', 'cell', 'molecular']);
const MODALITIES = new Set(['spatial-transcriptomics', 'single-cell-rna', '3d-cell-imaging', 'proteomics', 'epigenetics', 'genomics']);

export function validateReferenceLayer(entry = {}) {
  const errors = [];
  if (!entry.id) errors.push('Missing dataset id');
  if (!LAYERS.has(entry.layer)) errors.push(`Invalid layer: ${entry.layer ?? '(missing)'}`);
  if (!entry.sourceUrl) errors.push('Missing sourceUrl');
  if (!entry.accession) errors.push('Missing accession');
  if (entry.modality && !MODALITIES.has(entry.modality)) errors.push(`Invalid modality: ${entry.modality}`);
  if (!entry.species) errors.push('Missing species');
  if (!entry.tissue) errors.push('Missing tissue');
  return { valid: errors.length === 0, errors };
}

export function buildReferenceBiologyRegistry(entries = []) {
  const validated = entries.map((entry) => ({ entry, validation: validateReferenceLayer(entry) }));
  const errors = validated.flatMap(({ entry, validation }) => validation.errors.map((error) => `${entry.id ?? '(unknown)'}: ${error}`));
  if (errors.length) throw new Error(errors.join('; '));
  return { layers: validated.map(({ entry }) => entry), errors: [] };
}

export function findReferencesByLayer(registry, layer) {
  return registry.layers.filter((entry) => entry.layer === layer);
}

export function resolveCellMolecularReferences(registry, cellId) {
  return registry.layers
    .filter((entry) => entry.layer === 'molecular' && (!entry.cellId || entry.cellId === cellId))
    .map((entry) => ({ datasetId: entry.id, accession: entry.accession, modality: entry.modality, sourceUrl: entry.sourceUrl }));
}

export function resolveTissueCellReferences(registry, tissueId) {
  return registry.layers
    .filter((entry) => (entry.layer === 'tissue' || entry.layer === 'cell') && (!entry.tissueId || entry.tissueId === tissueId))
    .map((entry) => ({ datasetId: entry.id, accession: entry.accession, modality: entry.modality, sourceUrl: entry.sourceUrl }));
}
