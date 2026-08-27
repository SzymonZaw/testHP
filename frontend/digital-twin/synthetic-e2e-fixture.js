// Deterministic synthetic fixture for frontend integration smoke tests.
// Synthetic data only; it is not a biological or clinical model.
(() => {
  const regions = ['palm', 'thumb', 'index', 'middle', 'ring'];
  const cells = Array.from({ length: 1000 }, (_, i) => {
    const group = i % 20;
    const worsening = group === 17;
    const improving = group === 18;
    const aging = group >= 14 && group < 17;
    const regionId = regions[i % regions.length];
    const abnormalityT0 = worsening ? 0.45 : improving ? 0.50 : aging ? 0.15 : 0.10;
    const abnormalityT2 = worsening ? 0.75 : improving ? 0.20 : aging ? 0.21 : 0.11;
    const ageT0 = worsening ? 40 : improving ? 45 : aging ? 35 : group === 19 ? 50 : 30;
    const ageT2 = worsening ? 44 : improving ? 43 : aging ? 38 : group === 19 ? 52 : 30;
    return {
      cellId: `cell-${String(i).padStart(4, '0')}`,
      regionId,
      tissueId: `${regionId}-skin`,
      timeline: { T0: { biologicalAge: ageT0, abnormalityScore: abnormalityT0 }, T2: { biologicalAge: ageT2, abnormalityScore: abnormalityT2 } },
      assessment: { healthState: worsening ? 'abnormal' : 'healthy', healthScore: worsening ? 0.70 : 0.85, biologicalAge: ageT2, abnormalityScore: abnormalityT2, uncertainty: 0.10, evidenceCount: 1 },
      priority: worsening ? 'investigate' : 'no_action'
    };
  });

  const summarize = (items, level, identifier) => {
    const sufficient = items.filter(cell => cell.assessment.biologicalAge != null);
    if (!sufficient.length) return { level, identifier, overallAge: null, confidence: 0, evidenceCount: 0, assessedItems: items.length, sufficientItems: 0, coverage: 0, status: 'insufficient_evidence' };
    const confidence = sufficient.reduce((sum, cell) => sum + 0.85, 0) / sufficient.length;
    const overallAge = sufficient.reduce((sum, cell) => sum + cell.assessment.biologicalAge * 0.85, 0) / (sufficient.length * 0.85);
    return { level, identifier, overallAge, confidence, evidenceCount: sufficient.reduce((sum, cell) => sum + cell.assessment.evidenceCount, 0), assessedItems: items.length, sufficientItems: sufficient.length, coverage: sufficient.length / items.length, status: 'estimated' };
  };

  const tissue = Object.fromEntries(regions.map(region => {
    const items = cells.filter(cell => cell.tissueId === `${region}-skin`);
    return [`${region}-skin`, summarize(items, 'tissue', `${region}-skin`)];
  }));
  const region = Object.fromEntries(regions.map(regionId => {
    const items = cells.filter(cell => cell.regionId === regionId);
    return [regionId, summarize(items, 'region', regionId)];
  }));
  const hand = summarize(cells, 'hand', 'hand');

  window.testhpSyntheticE2E = {
    version: '0.2', generatedAt: '2026-01-01T00:00:00Z', cells,
    hierarchy: { tissue, region, hand },
    summary: { cellCount: 1000, timepoints: ['T0', 'T1', 'T2'], investigateCount: 50 }
  };
})();