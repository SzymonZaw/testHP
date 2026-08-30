import { mapGeometryToRegion } from './HandRegionRegistry.js';
import { transformPoint } from './SpatialRegistration.js';

export function createSpatialPicker({ regionRegistry, cellIndex = null, registration = null } = {}) {
  return {
    resolveIntersection(intersection) {
      if (!intersection?.object) return null;
      const geometryId = intersection.object.userData?.geometryId ?? intersection.object.name ?? null;
      const regionId = geometryId ? mapGeometryToRegion(regionRegistry, geometryId) : null;
      const point = intersection.point?.toArray ? intersection.point.toArray() : intersection.point;
      const result = { geometryId, regionId, worldPoint: point ?? null };
      if (!registration || !point || !cellIndex) return result;
      const sourcePoint = [
        (point[0] - registration.translation[0]) / registration.scale[0],
        (point[1] - registration.translation[1]) / registration.scale[1],
        (point[2] - registration.translation[2]) / registration.scale[2],
      ];
      let nearest = null;
      let nearestDistance = Infinity;
      for (const cell of cellIndex.cellsById.values()) {
        const d = Math.hypot(cell.sourceCoordinates[0] - sourcePoint[0], cell.sourceCoordinates[1] - sourcePoint[1], cell.sourceCoordinates[2] - sourcePoint[2]);
        if (d < nearestDistance) { nearestDistance = d; nearest = cell; }
      }
      return { ...result, cellId: nearest?.cellId ?? null, tissueId: nearest?.tissueId ?? null, sourcePoint, cellDistance: nearest ? nearestDistance : null };
    },
    projectCell(cellId) {
      const cell = cellIndex?.cellsById.get(cellId);
      return cell ? transformPoint(registration, cell.sourceCoordinates) : null;
    },
  };
}
