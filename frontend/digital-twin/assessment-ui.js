// UI adapter for the canonical assessment bridge and live DigitalTwin API.
(() => {
  const $ = id => document.getElementById(id);
  const text = (id, value) => { const el = $(id); if (el) el.textContent = value; };
  const percent = value => value == null ? '—' : `${Math.round(Number(value) * 100)}%`;
  const statusLabel = (status, uncertainty) => {
    if (status === 'live') return 'LIVE';
    if (status === 'uncertain' || (uncertainty != null && Number(uncertainty) >= .5)) return 'UNCERTAIN';
    if (status === 'demo') return 'DEMO';
    return 'NO DATA';
  };
  const render = async cellId => {
    const bridge = window.testhpAssessmentBridge;
    const adapter = window.testhpAssessmentDataAdapter;
    const panel = $('cell-assessment-panel');
    if (!bridge || !panel) return;
    panel.hidden = !cellId;
    if (!cellId) return;

    let live = null;
    if (adapter?.getLive) live = await adapter.getLive(cellId);
    const data = live?.data;
    const assessment = data?.assessment || bridge.getCell(cellId);
    if (!assessment) { panel.hidden = true; return; }

    const uncertaintyValue = data?.uncertainty?.uncertainty ?? assessment.uncertainty;
    const confidence = data?.uncertainty?.confidence ?? assessment.ageConfidence ?? assessment.confidence;
    const status = live?.data ? (confidence != null && Number(confidence) < .5 ? 'uncertain' : 'live') : 'demo';

    text('cell-assessment-health', assessment.healthState || assessment.health_state || (assessment.healthScore == null ? '—' : percent(assessment.healthScore)));
    text('cell-assessment-age', assessment.biologicalAge == null ? '—' : `${assessment.biologicalAge} lat`);
    text('cell-assessment-abnormality', percent(assessment.abnormalityScore ?? assessment.abnormality));
    text('cell-assessment-uncertainty', percent(uncertaintyValue));
    text('cell-assessment-status', statusLabel(status, uncertaintyValue));
    text('cell-assessment-confidence', `Confidence: ${percent(confidence)}`);

    const trend = data?.trend || bridge.getTrend(cellId);
    text('cell-assessment-trend', `Trend: ${trend ? `zdrowie ${percent(trend.health_score_delta ?? trend.healthDelta)} · nieprawidłowość ${percent(trend.abnormality_delta ?? trend.abnormalityDelta)} · wiek ${trend.biological_age_delta == null && trend.ageDelta == null ? '—' : `${Number(trend.biological_age_delta ?? trend.ageDelta).toFixed(1)} lat`}` : 'brak poprzedniej oceny'}`);

    const priority = data?.observation_priority || bridge.getPriority(cellId);
    text('cell-assessment-priority', `Priorytet obserwacyjny: ${priority?.priority || '—'}`);
    const evidence = data?.evidence;
    text('cell-assessment-evidence', `Evidence: ${evidence?.count ?? assessment.evidenceCount ?? 0}`);
  };
  const currentCell = detail => detail?.spatial_id || detail?.cell_id || detail?.cellId || null;
  const onTarget = event => render(currentCell(event.detail));
  window.addEventListener('testhp:spatial-contract-changed', onTarget);
  window.addEventListener('testhp:spatial-layer-changed', onTarget);
  window.addEventListener('testhp:cell-assessment-updated', event => render(event.detail?.cellId));
  window.addEventListener('testhp:cell-trend-updated', event => render(event.detail?.cellId));
  window.addEventListener('testhp:cell-priority-updated', event => render(event.detail?.cellId));
  document.addEventListener('DOMContentLoaded', () => render(currentCell(window.testhpSpatialContract?.getTarget?.())), { once: true });
})();
