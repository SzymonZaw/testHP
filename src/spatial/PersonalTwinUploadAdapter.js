const SUPPORTED = new Set(['glb', 'gltf']);

export function createPersonalTwinAsset({ file, metadata = {} }) {
  if (!file?.name) throw new Error('A GLB/GLTF file is required');
  const extension = file.name.toLowerCase().split('.').pop();
  if (!SUPPORTED.has(extension)) throw new Error('Only .glb and .gltf assets are supported');
  if (!metadata.subjectId) throw new Error('metadata.subjectId is required');

  return {
    id: metadata.assetId ?? `personal-${metadata.subjectId}-hand`,
    type: 'personal',
    subjectId: metadata.subjectId,
    timepoint: metadata.timepoint ?? 'T0',
    asset: { name: file.name, type: extension, file },
    coordinateSystem: metadata.coordinateSystem ?? { name: 'asset-local', units: 'mm' },
    metadata: {
      regions: metadata.regions ?? [],
      mappings: metadata.mappings ?? [],
    },
    provenance: {
      source: 'user-upload',
      filename: file.name,
      importedAt: new Date().toISOString(),
    },
    biologicalState: null,
  };
}

export function createPersonalTwinObjectUrl(file) {
  if (!file) throw new Error('File is required');
  return URL.createObjectURL(file);
}

export function revokePersonalTwinObjectUrl(url) {
  if (url) URL.revokeObjectURL(url);
}
