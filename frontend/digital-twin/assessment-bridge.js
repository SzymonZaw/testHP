// Canonical frontend bridge for evidence-aware cell assessments.
// This module only normalizes and publishes assessment state; it does not
// make clinical decisions or create a second spatial model.
(() => {
  const state = {
    assessments: new Map(),
    trends: new Map(),
    priorities: new Map(),
    hierarchy: null
  };

  const finite = value => Number.isFinite(Number(value)) ? Number(value) : null;

  const normalizeAssessment = item => ({
    cellId: item?.cell_id || item?.cellId || null,
    healthState: item?.health_state || item?.healthState || 'unknown',
    healthScore: finite(item?.health_score ?? item?.healthScore),
    biologicalAge: finite(item?.biological_age ?? item?.biologicalAge),
    abnormalityScore: finite(item?.abnormality_score ?? item?.abnormalityScore),
    uncertainty: finite(item?.uncertainty),
    evidenceCount: Array.isArray(item?.evidence) ? item.evidence.length : finite(item?.evidence_count) || 0,
    observedAt: item?.observed_at || item?.observedAt || null,
    evidence: Array.isArray(item?.evidence) ? item.evidence : []
  });

  const setAssessment = item => {
    const assessment = normalizeAssessment(item);
    if (!assessment.cellId) return null;
    state.assessments.set(assessment.cellId, assessment);
    window.dispatchEvent(new CustomEvent('testhp:cell-assessment-updated', { detail: assessment }));
    return assessment;
  };

  const setTrend = (cellId, trend) => {
    if (!cellId) return null;
    state.trends.set(cellId, trend || null);
    window.dispatchEvent(new CustomEvent('testhp:cell-trend-updated', { detail: { cellId, trend: trend || null } }));
    return trend;
  };

  const setPriority = (cellId, priority) => {
    if (!cellId) return null;
    state.priorities.set(cellId, priority || null);
    window.dispatchEvent(new CustomEvent('testhp:cell-priority-updated', { detail: { cellId, priority: priority || null } }));
    return priority;
  };

  const setHierarchy = hierarchy => {
    state.hierarchy = hierarchy || null;
    window.dispatchEvent(new CustomEvent('testhp:hierarchical-assessment-updated', { detail: state.hierarchy }));
    return state.hierarchy;
  };

  const getCell = cellId => state.assessments.get(cellId) || null;
  const getTrend = cellId => state.trends.get(cellId) || null;
  const getPriority = cellId => state.priorities.get(cellId) || null;

  window.testhpAssessmentBridge = {
    state,
    setAssessment,
    setTrend,
    setPriority,
    setHierarchy,
    getCell,
    getTrend,
    getPriority,
    snapshot: () => ({
      assessments: Object.fromEntries(state.assessments),
      trends: Object.fromEntries(state.trends),
      priorities: Object.fromEntries(state.priorities),
      hierarchy: state.hierarchy
    })
  };
})();
