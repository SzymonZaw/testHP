(() => {
  const adapter = () => window.testhpAssessmentDataAdapter;
  const ensurePanel = () => {
    const host = document.getElementById('cell-assessment-panel');
    if (!host || document.getElementById('cell-timeline-panel')) return;
    const panel = document.createElement('div');
    panel.id = 'cell-timeline-panel'; panel.className = 'assessment-panel';
    panel.innerHTML = '<h3>HISTORIA KOMÓRKI</h3><div id="cell-timeline-points"></div><div id="cell-timeline-summary" class="assessment-evidence">Trend: —</div>';
    host.appendChild(panel);
  };
  const render = target => {
    ensurePanel(); const panel = document.getElementById('cell-timeline-panel'); if (!panel) return;
    const level = String(target?.level || '').toLowerCase();
    if (level !== 'cellular' && level !== 'cell') { panel.hidden = true; return; }
    const id = target?.spatial_id || target?.spatialId; const timeline = adapter()?.cellTimeline(id);
    panel.hidden = !timeline; if (!timeline) return;
    const points = document.getElementById('cell-timeline-points');
    const chart = window.testhpRenderTimelineChart?.(timeline);
    points.innerHTML = chart || timeline.points.map(point => `<div class="assessment-metric" style="margin-bottom:6px"><span>${point.timepoint}</span><strong>Wiek ${point.biologicalAge ?? '—'} · abnormality ${point.abnormality ?? '—'}</strong><span>Health ${point.healthScore ?? '—'} · uncertainty ${point.uncertainty ?? '—'}</span></div>`).join('');
    document.getElementById('cell-timeline-summary').textContent = `Trend: ${timeline.direction} · Δ wieku ${timeline.ageDelta ?? '—'} · Δ abnormality ${timeline.abnormalityDelta ?? '—'} · Δ health ${timeline.healthDelta ?? '—'}`;
  };
  window.addEventListener('testhp:spatial-contract-changed', e => render(e.detail)); window.addEventListener('testhp:spatial-layer-changed', e => render(e.detail)); window.addEventListener('testhp:assessment-data-updated', e => render(e.detail));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => render(window.testhpSpatialContract?.getTarget?.())); else render(window.testhpSpatialContract?.getTarget?.());
})();
