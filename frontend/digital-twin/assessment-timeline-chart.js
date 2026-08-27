(() => {
  const render = target => {
    const adapter = window.testhpAssessmentDataAdapter;
    const host = document.getElementById('cell-timeline-points');
    if (!adapter || !host) return;
    const level = String(target?.level || '').toLowerCase();
    if (level !== 'cellular' && level !== 'cell') return;
    const id = target?.spatial_id || target?.spatialId;
    const timeline = adapter.cellTimeline(id);
    if (!timeline?.points?.length) return;
    const width = 360, height = 150, pad = 28;
    const values = timeline.points.map(p => p.abnormality).filter(v => v != null);
    if (!values.length) return;
    const min = Math.min(...values, 0), max = Math.max(...values, 1);
    const x = i => pad + (i * (width - pad * 2) / Math.max(timeline.points.length - 1, 1));
    const y = v => height - pad - ((v - min) / Math.max(max - min, .001)) * (height - pad * 2);
    const path = timeline.points.map((p,i) => `${i ? 'L' : 'M'} ${x(i).toFixed(1)} ${y(p.abnormality ?? min).toFixed(1)}`).join(' ');
    const dots = timeline.points.map((p,i) => `<circle cx="${x(i)}" cy="${y(p.abnormality ?? min)}" r="4"/><text x="${x(i)}" y="${height-7}" text-anchor="middle">${p.timepoint}</text>`).join('');
    host.innerHTML = `<div class="timeline-chart-wrap"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Trend abnormality w czasie"><line x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}"/><line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height-pad}"/><path d="${path}" fill="none"/><g>${dots}</g></svg><div class="timeline-chart-caption">Abnormality · ${timeline.direction}</div></div>`;
  };
  window.addEventListener('testhp:spatial-contract-changed', e => render(e.detail));
  window.addEventListener('testhp:spatial-layer-changed', e => render(e.detail));
  window.addEventListener('testhp:assessment-data-updated', e => render(e.detail));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => render(window.testhpSpatialContract?.getTarget?.()));
  else render(window.testhpSpatialContract?.getTarget?.());
})();
