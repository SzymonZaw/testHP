const REQUIRED = ['cellId', 'coordinates'];

export function normalizeSpatialCell(record = {}) {
  const cellId = record.cellId ?? record.cell_ID ?? record.id;
  const x = record.x ?? record.centerX ?? record.center_x ?? record.globalX ?? record.centerXGlobal;
  const y = record.y ?? record.centerY ?? record.center_y ?? record.globalY ?? record.centerYGlobal;
  const z = record.z ?? record.centerZ ?? record.zSlice ?? record.z_slice ?? null;
  const coordinates = [x, y, z];
  const errors = [];
  if (!cellId) errors.push('Missing cellId');
  if (x == null || y == null) errors.push('Missing spatial x/y coordinates');
  if ([x, y].some((value) => typeof value !== 'number' || !Number.isFinite(value))) errors.push('Spatial x/y coordinates must be finite numbers');
  return {
    valid: errors.length === 0,
    errors,
    cellId: cellId == null ? null : String(cellId),
    coordinates,
    segmentationId: record.segmentationId ?? record.label ?? record.cellLabel ?? null,
    morphology: record.morphology ?? null,
    cellType: record.cellType ?? record.cell_type ?? record.annotation ?? null,
    evidence: record.evidence ?? null,
  };
}

export function createSpatialCellAdapter({ datasetId, records = [] } = {}) {
  const cells = records.map(normalizeSpatialCell);
  return {
    datasetId,
    cells,
    valid: cells.every((cell) => cell.valid),
    getCell(cellId) { return cells.find((cell) => cell.cellId === String(cellId)) ?? null; },
    getEvidence(cellId) { return this.getCell(cellId)?.evidence ?? null; },
  };
}

export const SPATIAL_CELL_REFERENCE_CAPABILITIES = Object.freeze({
  cellId: true,
  coordinates: true,
  segmentation: true,
  morphology: true,
  cellType: true,
  molecularEvidence: true,
});
