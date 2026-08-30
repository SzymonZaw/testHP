import { createSpatialRegistration, transformPoint, createCellRegistrationIndex } from './SpatialRegistration.js';

test('registers tissue coordinates into hand coordinates', () => {
  const registration = createSpatialRegistration({
    id: 'hand-skin-r1',
    sourceCoordinateSystem: 'tissue-local-v1',
    targetCoordinateSystem: 'hand-world-v1',
    translation: [10, 20, 30],
    scale: [2, 2, 2],
  });
  expect(transformPoint(registration, [1, 2, 3])).toEqual([12, 24, 36]);
  const index = createCellRegistrationIndex(registration, [
    { cellId: 'cell-17', tissueId: 'sample-1', coordinates: [1, 2, 3], segmentationId: 'seg-17' },
  ]);
  expect(index.cellsById.get('cell-17')).toMatchObject({ coordinates: [12, 24, 36], tissueId: 'sample-1', segmentationId: 'seg-17' });
});

test('rejects invalid registration scale', () => {
  expect(() => createSpatialRegistration({ id: 'bad', sourceCoordinateSystem: 'a', targetCoordinateSystem: 'b', scale: [1, 0, 1] })).toThrow('scale cannot contain zero');
});
