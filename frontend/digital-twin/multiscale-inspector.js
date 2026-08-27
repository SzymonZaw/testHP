(() => {
  const contract = () => window.testhpSpatialContract;
  const adapter = () => window.testhpAssessmentDataAdapter;
  const ensure = () => {
    const host = document.getElementById('cell-assessment-panel') || document.querySelector('.inspector-panel') || document.body;
    if (!host || document.getElementById('multiscale-inspector')) return;
    const panel = document.createElement('div'); panel.id = 'multiscale-inspector'; panel.className = 'assessment-panel';
    panel.innerHTML = '<div id="multiscale-breadcrumbs"></div><div id="multiscale-summary"></div><div id="multiscale-children"></div>';
    host.prepend(panel);
  };
  const target = () => contract()?.getTarget?.() || { spatial_id: window.testhpSpatialTarget || 'hand/palm', level: 'macro' };
  const summary = id => adapter()?.aggregate?.(id, id === 'hand' ? 'macro' : target().level) || null;
  const render = detail => {
    ensure(); const root = document.getElementById('multiscale-inspector'); if (!root) return;
    const current = detail?.spatial_id ? detail : target(); const path = current.path || current.spatial_id.split('/');
    const crumbs = path.map((part, i) => { const id = path.slice(0, i + 1).join('/'); return `<button type="button" data-spatial-id="${id}">${contract()?.labelFor(id, part) || part}</button>`; }).join('<span>›</span>');
    document.getElementById('multiscale-breadcrumbs').innerHTML = crumbs;
    const data = summary(current.spatial_id);
    document.getElementById('multiscale-summary').innerHTML = data ? `<div class="assessment-grid"><div class="assessment-metric"><span>Komórki</span><strong>${data.assessedCells ?? '—'}</strong></div><div class="assessment-metric"><span>Coverage</span><strong>${Math.round((data.coverage ?? 0) * 100)}%</strong></div><div class="assessment-metric"><span>Confidence</span><strong>${Math.round((data.ageConfidence ?? data.confidence ?? 0) * 100)}%</strong></div></div>` : '';
    root.querySelectorAll('[data-spatial-id]').forEach(button => button.addEventListener('click', () => {
      const id = button.dataset.spatialId; const segments = id.split('/'); const level = segments.length >= 4 ? 'cellular' : segments.length === 3 ? 'tissue' : 'macro';
      contract()?.publish?.({ spatial_id: id, id: segments.at(-1), level, path: segments });
    }));
  };
  window.addEventListener('testhp:spatial-contract-changed', e => render(e.detail));
  window.addEventListener('digital-twin:target-changed', e => render(e.detail));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => render(target())); else render(target());
})();
