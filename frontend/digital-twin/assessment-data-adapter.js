// Canonical adapter from spatial target to assessment records.
// Synthetic fixture is used only when no application assessment source exists.
(() => {
  const contract = () => window.testhpSpatialContract;
  const fixture = () => window.testhpSyntheticE2E;
  const cache = new Map();

  const findCell = id => {
    const data = fixture();
    return data?.cells?.find(cell => cell.cellId === id || cell.cellId === contract()?.canonicalTargetId(id));
  };

  const aggregate = (targetId, level) => {
    const data = fixture();
    const cells = data?.cells || [];
    const prefix = contract()?.canonicalTargetId(targetId) || targetId;
    let scoped = cells;
    if (level === 'cellular') return findCell(prefix);
    if (level === 'tissue') scoped = cells.filter(c => c.tissueId === prefix || c.tissueId?.startsWith(`${prefix}/`));
    else if (level === 'macro') scoped = cells.filter(c => c.regionId === prefix || c.regionId?.startsWith(`${prefix}/`));
    else scoped = cells;
    if (!scoped.length) return null;
    const withAge = scoped.filter(c => c.assessment?.biologicalAge != null);
    const totalConfidence = withAge.reduce((sum, c) => sum + (c.assessment.ageConfidence ?? 0.8), 0);
    const age = totalConfidence ? withAge.reduce((sum, c) => sum + c.assessment.biologicalAge * (c.assessment.ageConfidence ?? 0.8), 0) / totalConfidence : null;
    const evidence = withAge.reduce((sum, c) => sum + (c.assessment.evidenceCount || 0), 0);
    return {
      biologicalAge: age == null ? null : Number(age.toFixed(2)),
      ageConfidence: withAge.length ? totalConfidence / withAge.length : 0,
      evidenceCount: evidence,
      coverage: scoped.length ? withAge.length / scoped.length : 0,
      assessedCells: scoped.length,
      sufficientCells: withAge.length,
      status: withAge.length ? 'estimated' : 'insufficient_evidence'
    };
  };

  const get = target => {
    const id = contract()?.canonicalTargetId(target) || target;
    const level = target?.level || contract()?.getTarget?.().level || 'macro';
    const key = `${level}:${id}`;
    if (cache.has(key)) return cache.get(key);
    const value = aggregate(id, level);
    cache.set(key, value);
    return value;
  };

  window.testhpAssessmentDataAdapter = Object.freeze({ get, findCell, aggregate, clear: () => cache.clear() });
})();
