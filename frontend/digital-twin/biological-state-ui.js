(() => {
  const labels = {
    biological_age: 'age-state',
    structural_functional_state: 'structure-state',
    damage: 'damage-state',
    pathology: 'pathology-state',
  };
  const inputs = {
    biological_age: 'biological-age-input',
    structural_functional_state: 'biological-structure-input',
    damage: 'biological-damage-input',
    pathology: 'biological-pathology-input',
  };
  const defaults = {
    biological_age: 'Nieustalony',
    structural_functional_state: 'Nieustalone',
    damage: 'Nieustalone',
    pathology: 'Nieustalona',
  };
  let lastDetail = {};
  let lastPayload = null;
  const $ = id => document.getElementById(id);
  function setText(id, value) { const element = $(id); if (element) element.textContent = value; }
  function displayInterpretation(value, dimension) {
    if (value === null || value === undefined || value === '') return defaults[dimension];
    if (typeof value === 'object' && value !== null) {
      if ('value' in value) return String(value.value);
      if ('label' in value) return String(value.label);
    }
    return String(value);
  }
  function stateSpatialId(detail) {
    if (detail?.spatial_id) return detail.spatial_id;
    if (detail?.path?.length) return detail.path.map(String).join('/').toLowerCase().replaceAll(' ', '-');
    return 'hand/palm';
  }
  function editableSources(payload) { return Array.isArray(payload?.state?.editable_observations) ? payload.state.editable_observations : []; }
  function renderEvidenceBreakdown(payload) {
    const summary = payload?.summary || {};
    const observations = Number(summary.observations || 0);
    const direct = Number(summary.direct_evidence || 0);
    const descendants = Number(summary.descendant_evidence || 0);
    const locations = Array.isArray(summary.by_location) ? summary.by_location : [];
    const element = $('evidence-breakdown');
    if (!element) return;
    if (observations === 0) { element.textContent = 'Brak danych przypisanych bezpośrednio lub w podregionach.'; return; }
    const parts = [`Dane w zakresie: ${observations}`, `Evidence bezpośrednio: ${direct}`, `Evidence w podregionach: ${descendants}`];
    if (locations.length > 1) {
      const details = locations.filter(item => Number(item.count) > 0).map(item => `${item.name || item.spatial_id}: ${item.count}`);
      if (details.length) parts.push(`Lokalizacje: ${details.join(' · ')}`);
    }
    element.textContent = parts.join(' · ');
  }
  function renderEditor(payload) {
    const editor = $('biological-state-editor'); const editButton = $('biological-state-edit'); const source = $('biological-state-source');
    if (!editor || !editButton || !source) return;
    const sources = editableSources(payload);
    editButton.disabled = sources.length === 0;
    editButton.title = sources.length ? 'Edytuj zwalidowaną interpretację' : 'Brak obserwacji z jawnym evidence';
    source.innerHTML = sources.map(item => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)} · ${escapeHtml(item.evidence_id || '')}</option>`).join('');
    if (!sources.length) return;
    const current = sources[0].validated_interpretations || {};
    Object.entries(inputs).forEach(([dimension, id]) => { const input = $(id); if (input) input.value = displayInterpretation(current[dimension], dimension) === defaults[dimension] ? '' : displayInterpretation(current[dimension], dimension); });
    source.onchange = () => { const selected = sources.find(item => item.id === source.value); const values = selected?.validated_interpretations || {}; Object.entries(inputs).forEach(([dimension, id]) => { const input = $(id); if (input) input.value = values[dimension] == null ? '' : displayInterpretation(values[dimension], dimension); }); };
  }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  async function refresh(detail = lastDetail) {
    lastDetail = detail || {};
    const spatialId = stateSpatialId(lastDetail);
    const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: spatialId, include_descendants: 'true' });
    try {
      const response = await fetch(`/api/biological-state?${params.toString()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json(); lastPayload = payload;
      const state = payload?.state || {}; const interpretations = state.interpretations || {};
      Object.entries(labels).forEach(([dimension, id]) => setText(id, displayInterpretation(interpretations[dimension], dimension)));
      const count = Number(state.observation_count ?? payload?.summary?.observations ?? 0);
      setText('evidence-count', `${count} ${count === 1 ? 'element' : 'elementów'}`);
      setText('evidence-level', state.availability === 'observed' ? 'Dane obserwowane' : 'Niewystarczające dane');
      setText('confidence-state', state.confidence?.label || 'Nieustalona');
      renderEvidenceBreakdown(payload); renderEditor(payload);
      window.dispatchEvent(new CustomEvent('testhp:biological-state-updated', { detail: payload }));
    } catch (error) {
      lastPayload = null; Object.entries(labels).forEach(([dimension, id]) => setText(id, defaults[dimension]));
      setText('evidence-count', '0 elementów'); setText('evidence-level', 'Niewystarczające dane'); setText('confidence-state', 'Nieustalona'); setText('evidence-breakdown', 'Nie udało się pobrać zakresu danych.');
      const editButton = $('biological-state-edit'); if (editButton) editButton.disabled = true;
      console.warn('[BiologicalState] API unavailable; safe fallback kept.', error);
    }
  }
  function openEditor() { const editor = $('biological-state-editor'); if (!editor || !$('biological-state-source')?.options.length) return; editor.hidden = false; $('biological-state-editor-status').textContent = ''; editor.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  function closeEditor() { const editor = $('biological-state-editor'); if (editor) editor.hidden = true; }
  async function saveEditor() {
    const source = $('biological-state-source'); const status = $('biological-state-editor-status'); const observationId = source?.value; if (!observationId) return;
    const interpretations = {}; Object.entries(inputs).forEach(([dimension, id]) => { const value = $(id)?.value.trim(); if (value) interpretations[dimension] = value; });
    if (status) status.textContent = 'Zapisywanie…';
    try {
      const response = await fetch('/api/biological-state', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ observation_id: observationId, author: 'local-user', interpretations }) });
      const payload = await response.json().catch(() => ({})); if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
      if (status) status.textContent = 'Zapisano.'; window.dispatchEvent(new CustomEvent('testhp:observation-updated', { detail: payload })); await refresh(lastDetail); setTimeout(closeEditor, 400);
    } catch (error) { if (status) status.textContent = `Błąd: ${error.message}`; }
  }
  window.addEventListener('testhp:spatial-layer-changed', event => refresh(event.detail || {}));
  window.addEventListener('testhp:spatial-change', event => refresh(event.detail || {}));
  window.addEventListener('testhp:observation-updated', () => refresh(lastDetail));
  document.addEventListener('DOMContentLoaded', () => { $('biological-state-edit')?.addEventListener('click', openEditor); $('biological-state-edit-close')?.addEventListener('click', closeEditor); $('biological-state-save')?.addEventListener('click', saveEditor); refresh(); }, { once: true });
  if (document.readyState !== 'loading') { $('biological-state-edit')?.addEventListener('click', openEditor); $('biological-state-edit-close')?.addEventListener('click', closeEditor); $('biological-state-save')?.addEventListener('click', saveEditor); refresh(); }
  window.biologicalStateUI = { refresh, openEditor, closeEditor };
})();