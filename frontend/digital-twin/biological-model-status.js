/** Frontend registry view: describes scientific model availability without inventing validation. */
export const MODEL_STATUS = Object.freeze({
  wsi_cell_type: 'not_established',
  rna_biological_state: 'not_established',
  proteomics_biological_state: 'not_established',
  epigenetics_biological_age: 'not_established',
  cell_biological_age: 'not_established',
  tissue_biological_age: 'not_established',
  hand_biological_age: 'not_established',
  hand_health_classification: 'not_established',
  multimodal_fusion: 'not_established',
  intervention_recommendation: 'not_established',
});

export function modelIsEstablished(metadata) {
  return String(metadata?.validation_status || metadata?.status || '').toLowerCase() === 'validated';
}

export function presentModelStatus(metadata = {}) {
  if (!modelIsEstablished(metadata)) return 'not_established';
  return 'available';
}
