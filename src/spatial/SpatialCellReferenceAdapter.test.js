import { normalizeSpatialCell, createSpatialCellAdapter } from './SpatialCellReferenceAdapter.js';

test('normalizes a real spatial-cell-shaped record', () => {
  const cell = normalizeSpatialCell({ cell_ID: 17, centerXGlobal: 12.5, centerYGlobal: 7.25, zSlice: 3, label: 17, cell_type: 'fibroblast', evidence: { gene: 'COL1A1' } });
  expect(cell.valid).toBe(true);
  expect(cell.cellId).toBe('17');
  expect(cell.coordinates).toEqual([12.5, 7.25, 3]);
  expect(cell.segmentationId).toBe(17);
});

test('rejects missing spatial coordinates', () => {
  const cell = normalizeSpatialCell({ cellId: 'A17' });
  expect(cell.valid).toBe(false);
  expect(cell.errors).toContain('Missing spatial x/y coordinates');
});

test('indexes cells and exposes molecular evidence', () => {
  const adapter = createSpatialCellAdapter({ datasetId: 'cosmx-example', records: [{ cellId: 'A17', x: 1, y: 2, evidence: { gene: 'COL1A1', expression: 4 } }] });
  expect(adapter.valid).toBe(true);
  expect(adapter.getCell('A17').coordinates).toEqual([1, 2, null]);
  expect(adapter.getEvidence('A17').expression).toBe(4);
});
