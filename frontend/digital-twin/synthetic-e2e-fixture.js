// Deterministic synthetic fixture for frontend integration smoke tests.
// Synthetic data only; it is not a biological or clinical model.
(() => {
  const cells = Array.from({ length: 1000 }, (_, i) => {
    const group = i % 20;
    const worsening = group === 17;
    const improving = group === 18;
    const aging = group >= 14 && group < 17;
    const abnormalityT0 = worsening ? 0.45 : improving ? 0.50 : aging ? 0.15 : 0.10;
    const abnormalityT2 = worsening ? 0.75 : improving ? 0.20 : aging ? 0.21 : 0.11;
    const ageT0 = worsening ? 40 : improving ? 45 : aging ? 35 : group === 19 ? 50 : 30;
    const ageT2 = worsening ? 44 : improving ? 43 : aging ? 38 : group === 19 ? 52 : 30;
    return {
      cellId: `cell-${String(i).padStart(4, '0')}`,
      regionId: ['palm', 'thumb', 'index', 'middle', 'ring'][i % 5],
      tissueId: `${['palm', 'thumb', 'index', 'middle', 'ring'][i % 5]}-skin`,
      timeline: {
        T0: { biologicalAge: ageT0, abnormalityScore: abnormalityT0 },
        T2: { biologicalAge: ageT2, abnormalityScore: abnormalityT2 }
      },
      assessment: {
        healthState: worsening ? 'abnormal' : 'healthy',
        healthScore: worsening ? 0.70 : 0.85,
        biologicalAge: ageT2,
        abnormalityScore: abnormalityT2,
        uncertainty: 0.10,
        evidenceCount: 1
      },
      priority: worsening ? 'investigate' : 'no_action'
    };
  });

  window.testhpSyntheticE2E = {
    version: '0.1',
    generatedAt: '2026-01-01T00:00:00Z',
    cells,
    summary: { cellCount: 1000, timepoints: ['T0', 'T1', 'T2'], investigateCount: 50 }
  };
})();
