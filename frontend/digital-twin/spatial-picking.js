export function resolveSpatialPicking(object, { canonicalState = null } = {}) {
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

  const regionId = read(['regionId', 'region_id', 'region']);
  const tissueId = read(['tissueId', 'tissue_id', 'tissue']);
  const cellId = read(['cellId', 'cell_id', 'cell']);
  const geometryId = read(['geometryId', 'geometry_id', 'geometry']);

  if (!regionId && !tissueId && !cellId) return null;

  return {
    geometryId,
    regionId,
    tissueId,
    cellId,
    canonicalStateVersion: canonicalState?.version ?? null,
  };
}
