(() => {
  const render = target => {
    const adapter = window.testhpAssessmentDataAdapter;
    const host = document.getElementById('cell-assessment-panel');
    if (!adapter || !host) return;
    const level = String(target?.level || '').toLowerCase();
    if (level !== 'cellular' && level !== 'cell') return;
    const cell = adapter.findCell(target?.spatial_id || target?.spatialId);
    if (!cell) return;
    let panel = document.getElementById('cell-evidence-panel');
    if (!panel) { panel = document.createElement('div'); panel.id = 'cell-evidence-panel'; panel.className = 'assessment-panel'; host.appendChild(panel); }
    const assessment = cell.assessment || {};
    const evidence = assessment.evidence || [];
    const count = assessment.evidenceCount ?? evidence.length;
    const confidence = assessment.confidence ?? assessment.ageConfidence;
    panel.innerHTML = `<h3>EVIDENCE I PROWENIENCJA</h3><div class="assessment-grid"><div class="assessment-metric"><span>Liczba źródeł</span><strong>${count}</strong></div><div class="assessment-metric"><span>Confidence</span><strong>${confidence != null ? Math.round(confidence * 100) + '%' : '—'}</strong></div></div><div class="assessment-evidence">Źródła: ${evidence.length ? evidence.map(item => `${item.sourceType || item.source_type || 'unknown'}${item.feature ? ` · ${item.feature}` : ''}`).join(' · ') : 'Brak szczegółowych rekordów evidence w bieżącym fixture.'}</div>`;
  };
  window.addEventListener('testhp:spatial-contract-changed', e => render(e.detail)); window.addEventListener('testhp:spatial-layer-changed', e => render(e.detail)); window.addEventListener('testhp:assessment-data-updated', e => render(e.detail));
})();
