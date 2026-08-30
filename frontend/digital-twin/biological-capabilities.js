/**
 * Capability gates for geometry and predictive features.
 *
 * The frontend never invents a scientific asset/model. A capability is usable
 * only when the backend explicitly supplies the required object and status.
 */

export const CAPABILITY_STATUS = Object.freeze({
  READY: 'ready',
  NOT_ESTABLISHED: 'Not established',
});

const ready = value => ['ready', 'available', 'verified', 'usable'].includes(String(value ?? '').toLowerCase());

export function getHandAsset(state) {
  const assets = Array.isArray(state?.assets) ? state.assets : [];
  return assets.find(asset => {
    const modality = String(asset?.modality ?? '').toLowerCase();
    return ready(asset?.status) && ['hand_3d', '3d', 'mesh', 'gltf', 'glb'].includes(modality)
      && Boolean(asset?.url ?? asset?.uri ?? asset?.asset_url ?? asset?.assetUrl ?? asset?.source_url);
  }) ?? null;
}

export function getSpatialGeometry(state, level, id) {
  const anatomy = state?.anatomy && typeof state.anatomy === 'object' ? state.anatomy : {};
  const collection = Array.isArray(anatomy?.[`${level}s`]) ? anatomy[`${level}s`] : [];
  const wanted = String(id ?? '').toLowerCase();
  return collection.find(item => String(item?.id ?? item?.[`${level}_id`] ?? item?.[`${level}Id`] ?? '').toLowerCase() === wanted
    && (item?.geometry || item?.mesh || item?.position || item?.coordinates)) ?? null;
}

export function getPredictiveCapability(state, key) {
  const value = state?.[key];
  if (!value || typeof value !== 'object') return { status: CAPABILITY_STATUS.NOT_ESTABLISHED, value: null };
  const status = value.status ?? value.validation_status ?? value.validationStatus;
  const model = value.model ?? value.model_id ?? value.modelId ?? state?.modelMetadata?.model_id;
  if (!model || !ready(status) && status !== 'validated') {
    return { status: CAPABILITY_STATUS.NOT_ESTABLISHED, value: null };
  }
  return { status: CAPABILITY_STATUS.READY, value };
}

export function getValidatedBiologicalAge(state) {
  const age = state?.biologicalAge;
  const metadata = state?.modelMetadata;
  const validation = state?.validation;
  const value = age?.biological_age ?? age?.value;
  const validationStatus = age?.validation_status ?? metadata?.validation_status ?? validation?.validation_status;
  const model = age?.model_id ?? metadata?.model_id;
  if (value == null || !model || String(validationStatus ?? '').toLowerCase() !== 'validated') {
    return { status: CAPABILITY_STATUS.NOT_ESTABLISHED, value: null };
  }
  return { status: CAPABILITY_STATUS.READY, value: age };
}

export function summarizeCapabilities(state) {
  return {
    handAsset: getHandAsset(state) ? CAPABILITY_STATUS.READY : CAPABILITY_STATUS.NOT_ESTABLISHED,
    tissueGeometry: state?.anatomy?.tissues?.some(t => t?.geometry || t?.mesh || t?.position || t?.coordinates) ? CAPABILITY_STATUS.READY : CAPABILITY_STATUS.NOT_ESTABLISHED,
    cellGeometry: state?.anatomy?.cells?.some(c => c?.geometry || c?.mesh || c?.position || c?.coordinates) ? CAPABILITY_STATUS.READY : CAPABILITY_STATUS.NOT_ESTABLISHED,
    whatIf: getPredictiveCapability(state, 'whatIf').status,
    intervention: getPredictiveCapability(state, 'interventions').status,
    biologicalAge: getValidatedBiologicalAge(state).status,
  };
}
