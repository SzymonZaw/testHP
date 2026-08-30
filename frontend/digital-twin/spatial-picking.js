import { resolveGeometryRegion, resolveRegionEvidence } from '../../src/spatial/ReferenceTwinAdapter.js';

export function resolveSpatialPicking(object, { canonicalState = null, spatialRegistry = null } = {}) {
  let node = object;
  const chain = [];
  while (node) {
    chain.push(node);
    node = node.parent;
  }

  const read = (names) => {
    for (const item of chain) {
      const data = item?.userData || {};
      for (const name of names) {
        const value = data[name];
        if (value !== undefined && value !== null && String(value).trim() !== '') return String(value).trim();
      }
    }
    return null;
  };

  const geometryId = read(['geometryId', 'geometry_id', 'geometry']);
  const mappedRegionId = geometryId && spatialRegistry ? resolveGeometryRegion(spatialRegistry, geometryId) : null;
  const regionId = mappedRegionId || read(['regionId', 'region_id', 'region']);
  const tissueId = read(['tissueId', 'tissue_id', 'tissue']);
  const cellId = read(['cellId', 'cell_id', 'cell']);

  if (!regionId && !tissueId && !cellId) return null;

  return {
    geometryId,
    regionId,
    tissueId,
    cellId,
    evidenceIds: regionId && spatialRegistry ? resolveRegionEvidence(spatialRegistry, regionId) : [],
    sourceId: spatialRegistry?.sourceId ?? null,
    sourceType: spatialRegistry?.sourceType ?? null,
    canonicalStateVersion: canonicalState?.version ?? null,
  };
}
