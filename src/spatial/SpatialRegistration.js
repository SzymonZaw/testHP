const EPSILON = 1e-9;

function assertVector3(value, name) {
  if (!Array.isArray(value) || value.length !== 3 || value.some((n) => !Number.isFinite(n))) {
    throw new Error(`${name} must be a finite [x, y, z] vector`);
  }
}

export function createSpatialRegistration({ id, sourceCoordinateSystem, targetCoordinateSystem, translation = [0, 0, 0], scale = [1, 1, 1] } = {}) {
  if (!id) throw new Error('Registration requires id');
  if (!sourceCoordinateSystem || !targetCoordinateSystem) throw new Error('Registration requires source and target coordinate systems');
  assertVector3(translation, 'translation');
  assertVector3(scale, 'scale');
  if (scale.some((n) => Math.abs(n) < EPSILON)) throw new Error('Registration scale cannot contain zero');
  return Object.freeze({ id, sourceCoordinateSystem, targetCoordinateSystem, translation: [...translation], scale: [...scale] });
}

export function transformPoint(registration, point) {
  assertVector3(point, 'point');
  return point.map((value, index) => value * registration.scale[index] + registration.translation[index]);
}

export function registerCell(registration, { cellId, coordinates, tissueId = null, segmentationId = null } = {}) {
  if (!cellId) throw new Error('Cell registration requires cellId');
  return Object.freeze({ cellId, tissueId, segmentationId, sourceCoordinates: [...coordinates], coordinates: transformPoint(registration, coordinates), registrationId: registration.id, coordinateSystem: registration.targetCoordinateSystem });
}

export function createCellRegistrationIndex(registration, cells = []) {
  const cellsById = new Map();
  for (const cell of cells) {
    const registered = registerCell(registration, cell);
    if (cellsById.has(registered.cellId)) throw new Error(`Duplicate cellId: ${registered.cellId}`);
    cellsById.set(registered.cellId, registered);
  }
  return { registration, cellsById };
}
