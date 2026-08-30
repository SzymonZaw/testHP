const DEFAULT_ROOT = 'data/hubmap';

export function createHuBMAPSpatialDataImporter({ datasetId, root = DEFAULT_ROOT } = {}) {
  if (!datasetId) throw new Error('datasetId is required');
  return {
    datasetId,
    root,
    manifestEntry(path = '/') {
      return `${datasetId} ${path}`;
    },
    expectedResources() {
      return {
        metadata: `${root}/${datasetId}/metadata.tsv`,
        segmentation: `${root}/${datasetId}/derived/segmentation_masks/`,
        transformations: `${root}/${datasetId}/derived/segmentation_masks/transformations/`,
        meshes: `${root}/${datasetId}/derived/segmentation_masks/*-mesh.glb`,
      };
    },
    normalizeObject(row = {}) {
      const id = row.cell_id ?? row.cell_ID ?? row.object_id ?? row.id;
      if (id == null) throw new Error('Spatial object is missing cell/object id');
      const x = Number(row.x ?? row.center_x ?? row.centroid_x);
      const y = Number(row.y ?? row.center_y ?? row.centroid_y);
      const z = Number(row.z ?? row.center_z ?? row.centroid_z ?? 0);
      if (![x, y, z].every(Number.isFinite)) throw new Error(`Invalid coordinates for ${id}`);
      return {
        cellId: String(id),
        coordinates: [x, y, z],
        segmentationId: row.segmentation_id ?? row.mask_id ?? null,
        cellType: row.cell_type ?? row.type ?? null,
        morphology: row.morphology ?? null,
        source: { datasetId, raw: row },
      };
    },
  };
}

export function parseTabSeparatedObjects(text, importer) {
  const lines = String(text).trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split('\t');
  return lines.slice(1).map((line) => {
    const values = line.split('\t');
    return importer.normalizeObject(Object.fromEntries(headers.map((h, i) => [h, values[i]])));
  });
}
