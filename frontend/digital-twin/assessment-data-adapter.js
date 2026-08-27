// Canonical adapter from spatial target to assessment records.
// Live API is preferred; synthetic fixture remains a demo fallback.
(() => {
  const contract = () => window.testhpSpatialContract;
  const fixture = () => window.testhpSyntheticE2E;
  const cache = new Map();
  const apiBase = () => window.testhpDigitalTwinApiBase || '/api/digital-twin';

  const findCell = id => {
    const data = fixture();
    return data?.cells?.find(cell => cell.cellId === id || cell.cellId === contract()?.canonicalTargetId(id));
  };

  const cellTimeline = id => {
    const cell = findCell(id);
    if (!cell) return null;
    const timeline = cell.timeline || {};
    const points = ['T0', 'T1', 'T2'].filter(key => timeline[key]).map(key => ({ timepoint: key, biologicalAge: timeline[key].biologicalAge ?? null, abnormality: timeline[key].abnormalityScore ?? timeline[key].abnormality ?? null, healthScore: timeline[key].healthScore ?? null, uncertainty: timeline[key].uncertainty ?? null }));
    const first = points[0], last = points[points.length - 1];
    const delta = (a, b) => a != null && b != null ? Number((b - a).toFixed(3)) : null;
    const abnormalityDelta = first && last ? delta(first.abnormality, last.abnormality) : null;
    const healthDelta = first && last ? delta(first.healthScore, last.healthScore) : null;
    let direction = 'uncertain';
    if (points.length >= 2) {
      if (abnormalityDelta != null && healthDelta != null && abnormalityDelta >= .15 && healthDelta <= -.10) direction = 'worsening';
      else if (abnormalityDelta != null && healthDelta != null && abnormalityDelta <= -.15 && healthDelta >= .10) direction = 'improving';
      else if (first?.biologicalAge != null && last?.biologicalAge != null && last.biologicalAge > first.biologicalAge) direction = 'aging';
      else direction = 'stable';
    }
    return { points, direction, ageDelta: first && last ? delta(first.biologicalAge, last.biologicalAge) : null, abnormalityDelta, healthDelta };
  };

  const aggregate = (targetId, level) => {
    const data = fixture(); const cells = data?.cells || [];
    const prefix = contract()?.canonicalTargetId(targetId) || targetId;
    let scoped = cells;
    if (level === 'cellular') return findCell(prefix);
    if (level === 'tissue') scoped = cells.filter(c => c.tissueId === prefix || c.tissueId?.startsWith(`${prefix}/`));
    else if (level === 'macro') scoped = cells.filter(c => c.regionId === prefix || c.regionId?.startsWith(`${prefix}/`));
    if (!scoped.length) return null;
    const withAge = scoped.filter(c => c.assessment?.biologicalAge != null);
    const totalConfidence = withAge.reduce((sum, c) => sum + (c.assessment.ageConfidence ?? 0.8), 0);
    const age = totalConfidence ? withAge.reduce((sum, c) => sum + c.assessment.biologicalAge * (c.assessment.ageConfidence ?? 0.8), 0) / totalConfidence : null;
    const evidence = withAge.reduce((sum, c) => sum + (c.assessment.evidenceCount || 0), 0);
    return { biologicalAge: age == null ? null : Number(age.toFixed(2)), ageConfidence: withAge.length ? totalConfidence / withAge.length : 0, evidenceCount: evidence, coverage: scoped.length ? withAge.length / scoped.length : 0, assessedCells: scoped.length, sufficientCells: withAge.length, status: withAge.length ? 'estimated' : 'insufficient_evidence' };
  };

  const liveCell = async id => {
    const response = await fetch(`${apiBase()}/cells/${encodeURIComponent(id)}/assessment`, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`assessment_api_${response.status}`);
    return response.json();
  };

  const getLive = async target => {
    const id = contract()?.canonicalTargetId(target) || target;
    const key = `live:${id}`;
    if (cache.has(key)) return cache.get(key);
    const promise = liveCell(id).catch(() => null);
    cache.set(key, promise);
    return promise;
  };

  const get = target => aggregate(contract()?.canonicalTargetId(target) || target, target?.level || contract()?.getTarget?.().level || 'macro');
  window.testhpAssessmentDataAdapter = Object.freeze({ get, getLive, findCell, cellTimeline, aggregate, clear: () => cache.clear() });
})();
