export function normalizeHuBMAPSkin3DSample(sample) {
  if (!sample?.sampleId) throw new Error('HuBMAP skin sample requires sampleId');
  return Object.freeze({
    sampleId: sample.sampleId,
    region: sample.region ?? null,
    status: sample.status ?? 'public-reference',
    spatialRegistration: sample.spatialRegistration ?? null,
    dataAvailable: Object.freeze([...(sample.dataAvailable ?? [])]),
  });
}

export function createHuBMAPSkin3DReference(samples = []) {
  const normalized = samples.map(normalizeHuBMAPSkin3DSample);
  return Object.freeze({
    layer: 'tissue',
    modality: '3d-skin-reconstruction',
    samples: Object.freeze(normalized),
    coordinateSystem: 'hubmap-hra-skin-rui-v1',
    handRegistrationStatus: 'not-established',
  });
}
