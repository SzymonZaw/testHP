// UI adapter for the canonical assessment bridge.
(() => {
  const $ = id => document.getElementById(id);
  const text = (id, value) => { const el = $(id); if (el) el.textContent = value; };
  const percent = value => value == null ? '—' : `${Math.round(Number(value) * 100)}%`;
  const render = cellId => {
    const bridge = window.testhpAssessmentBridge;
    const panel = $('cell-assessment-panel');
    if (!bridge || !panel) return;
    const assessment = bridge.getCell(cellId);
    if (!assessment) { panel.hidden = true; return; }
    panel.hidden = false;
    text('cell-assessment-health', assessment.healthState || (assessment.healthScore == null ? '—' : percent(assessment.healthScore)));
    text('cell-assessment-age', assessment.biologicalAge == null ? '—' : `${assessment.biologicalAge} lat`);
    text('cell-assessment-abnormality', percent(assessment.abnormalityScore));
    text('cell-assessment-uncertainty', percent(assessment.uncertainty));
    const trend = bridge.getTrend(cellId);
    text('cell-assessment-trend', `Trend: ${trend ? `zdrowie ${percent(trend.health_score_delta)} · nieprawidłowość ${percent(trend.abnormality_delta)} · wiek ${trend.biological_age_delta == null ? '—' : `${trend.biological_age_delta.toFixed(1)} lat`}` : 'brak poprzedniej oceny'}`);
    const priority = bridge.getPriority(cellId);
    text('cell-assessment-priority', `Priorytet obserwacyjny: ${priority?.priority || '—'}`);
    text('cell-assessment-evidence', `Evidence: ${assessment.evidenceCount}`);
  };
  const currentCell = detail => detail?.spatial_id || detail?.cell_id || detail?.cellId || null;
  const onTarget = event => render(currentCell(event.detail));
  window.addEventListener('testhp:spatial-contract-changed', onTarget);
  window.addEventListener('testhp:spatial-layer-changed', onTarget);
  window.addEventListener('testhp:cell-assessment-updated', event => render(event.detail?.cellId));
  window.addEventListener('testhp:cell-trend-updated', event => render(event.detail?.cellId));
  window.addEventListener('testhp:cell-priority-updated', event => render(event.detail?.cellId));
  document.addEventListener('DOMContentLoaded', () => {
    const target = window.testhpSpatialContract?.getTarget?.();
    render(currentCell(target));
  }, { once: true });
})();
