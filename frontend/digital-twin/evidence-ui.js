(() => {
  const statusLabel = status => ({usable:'✓ usable',unusable:'⚠ unusable',missing:'— missing',not_established:'? not established',validated:'✓ validated'}[String(status||'').toLowerCase()] || '? not established');
  const renderCanonical = detail => {
    const host = document.getElementById('cell-assessment-panel');
    if (!host || !detail) return;
    let panel = document.getElementById('cell-evidence-panel');
    if (!panel) { panel = document.createElement('div'); panel.id = 'cell-evidence-panel'; panel.className = 'assessment-panel'; host.appendChild(panel); }
    const qc = detail.qc || {};
    const validation = detail.validation?.validation_status || detail.validation?.status || 'not_established';
    const missing = Array.isArray(detail.missingModalities) ? detail.missingModalities : [];
    panel.innerHTML = `<h3>EVIDENCE I WIARYGODNOŚĆ</h3><div class="assessment-grid"><div class="assessment-metric"><span>Coverage</span><strong>${detail.coverage ?? '—'}</strong></div><div class="assessment-metric"><span>Confidence</span><strong>${detail.confidence != null ? Math.round(Number(detail.confidence) * 100) + '%' : '—'}</strong></div><div class="assessment-metric"><span>QC</span><strong>${qc.usable ?? 0} usable · ${qc.unusable ?? 0} unusable · ${qc.missing ?? 0} missing</strong></div><div class="assessment-metric"><span>Validation</span><strong>${statusLabel(validation)}</strong></div></div><div class="assessment-evidence">Brakujące modalności: ${missing.length ? missing.join(', ') : 'brak jawnie zgłoszonych'}</div>`;
  };
  const renderLegacy = target => {
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
  window.addEventListener('testhp:canonical-evidence-changed', e => renderCanonical(e.detail));
  window.addEventListener('testhp:spatial-contract-changed', e => renderLegacy(e.detail));
  window.addEventListener('testhp:spatial-layer-changed', e => renderLegacy(e.detail));
  window.addEventListener('testhp:assessment-data-updated', e => renderLegacy(e.detail));
})();
