// Frontend adapter for hierarchical research-only biological age summaries.
(() => {
  const fixture = () => window.testhpSyntheticE2E;
  const levelOf = target => {
    const value = String(target?.level || 'macro').toLowerCase();
    return value === 'cell' ? 'cellular' : value;
  };
  const summaryFor = target => {
    const data = fixture()?.hierarchy;
    if (!data) return null;
    const level = levelOf(target);
    if (level === 'cellular') return fixture().cells.find(cell => cell.cellId === (target?.spatial_id || target?.cellId)) || null;
    if (level === 'tissue') return data.tissue?.[target?.spatial_id || target?.tissue_id] || null;
    if (level === 'region') return data.region?.[target?.spatial_id || target?.region_id] || null;
    return data.hand || null;
  };
  const ensurePanel = () => {
    let panel = document.getElementById('biological-age-hierarchy-panel');
    if (panel) return panel;
    panel = document.createElement('section');
    panel.id = 'biological-age-hierarchy-panel';
    panel.className = 'assessment-panel';
    panel.innerHTML = '<h3>WIEK BIOLOGICZNY · HIERARCHIA</h3><div class="assessment-grid"><div class="assessment-metric"><span>Poziom</span><strong id="hierarchy-age-level">—</strong></div><div class="assessment-metric"><span>Wiek</span><strong id="hierarchy-age-value">—</strong></div><div class="assessment-metric"><span>Pewność</span><strong id="hierarchy-age-confidence">—</strong></div><div class="assessment-metric"><span>Coverage</span><strong id="hierarchy-age-coverage">—</strong></div></div><div id="hierarchy-age-evidence" class="assessment-evidence">Evidence: —</div><div id="hierarchy-age-status" class="assessment-trend">Status: —</div>';
    document.querySelector('.inspector')?.appendChild(panel);
    return panel;
  };
  const text = (id, value) => { const node = document.getElementById(id); if (node) node.textContent = value; };
  const render = target => {
    const panel = ensurePanel();
    const level = levelOf(target);
    const summary = summaryFor(target);
    if (!summary) { panel.hidden = true; return; }
    panel.hidden = false;
    const labels = { macro: 'Makro', tissue: 'Tkanka', region: 'Region', hand: 'Dłoń', cellular: 'Komórka' };
    if (level === 'cellular') {
      const assessment = summary.assessment;
      text('hierarchy-age-level', labels.cellular);
      text('hierarchy-age-value', assessment?.biologicalAge == null ? 'Nieustalony' : `${assessment.biologicalAge} lat`);
      text('hierarchy-age-confidence', '85%');
      text('hierarchy-age-coverage', '100%');
      text('hierarchy-age-evidence', `Evidence: ${assessment?.evidenceCount ?? 0}`);
      text('hierarchy-age-status', 'Status: estimated · syntetyczne dane');
      return;
    }
    text('hierarchy-age-level', labels[level] || level);
    text('hierarchy-age-value', summary.overallAge == null ? 'Nieustalony' : `${summary.overallAge.toFixed(1)} lat`);
    text('hierarchy-age-confidence', `${Math.round((summary.confidence || 0) * 100)}%`);
    text('hierarchy-age-coverage', `${Math.round((summary.coverage || 0) * 100)}% (${summary.sufficientItems}/${summary.assessedItems})`);
    text('hierarchy-age-evidence', `Evidence: ${summary.evidenceCount}`);
    text('hierarchy-age-status', `Status: ${summary.status} · syntetyczne dane`);
  };
  const onTarget = event => render(event.detail);
  window.addEventListener('testhp:spatial-contract-changed', onTarget);
  window.addEventListener('testhp:spatial-layer-changed', onTarget);
  document.addEventListener('DOMContentLoaded', () => render(window.testhpSpatialContract?.getTarget?.() || { level: 'hand' }), { once: true });
})();
