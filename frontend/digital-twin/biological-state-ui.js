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
  const defaults = { biological_age: 'Nieustalony', structural_functional_state: 'Nieustalone', damage: 'Nieustalone', pathology: 'Nieustalona' };
  let lastDetail = {};
  const $ = id => document.getElementById(id);
  const setText = (id, value) => { const element = $(id); if (element) element.textContent = value; };
  function displayInterpretation(value, dimension) {
    if (value === null || value === undefined || value === '') return defaults[dimension];
    if (typeof value === 'object' && value !== null) return 'value' in value ? String(value.value) : ('label' in value ? String(value.label) : String(value));
    return String(value);
  }
  function currentTarget(detail = {}) {
    const target = window.testhpSpatialContract?.getTarget?.();
    if (target?.spatial_id) return target;
    if (detail?.spatial_id) return detail;
    return null;
  }
  function editableSources(payload) { return Array.isArray(payload?.state?.editable_observations) ? payload.state.editable_observations : []; }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function renderEditor(payload) {
    const editor = $('biological-state-editor'), editButton = $('biological-state-edit'), source = $('biological-state-source');
    if (!editor || !editButton || !source) return;
    const sources = editableSources(payload);
    editButton.disabled = sources.length === 0;
    editButton.title = sources.length ? 'Edytuj zwalidowaną interpretację' : 'Brak obserwacji z jawnym evidence';
    source.innerHTML = sources.map(item => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)} · ${escapeHtml(item.evidence_id || '')}</option>`).join('');
    if (!sources.length) return;
    const renderSource = selected => {
      const values = selected?.validated_interpretations || {};
      Object.entries(inputs).forEach(([dimension, id]) => { const input = $(id); if (input) { const value = displayInterpretation(values[dimension], dimension); input.value = value === defaults[dimension] ? '' : value; } });
    };
    renderSource(sources[0]);
    source.onchange = () => renderSource(sources.find(item => item.id === source.value));
  }
  async function refresh(detail = lastDetail) {
    lastDetail = detail || {};
    const target = currentTarget(lastDetail);
    if (!target?.spatial_id) return;
    const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: target.spatial_id, include_descendants: 'false' });
    try {
      const response = await fetch(`/api/biological-state?${params.toString()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      const state = payload?.state || {};
      const interpretations = state.interpretations || {};
      Object.entries(labels).forEach(([dimension, id]) => setText(id, displayInterpretation(interpretations[dimension], dimension)));
      setText('observation-count', `${state.observation_count || 0} element${state.observation_count === 1 ? '' : 'ów'}`);
      setText('evidence-count', `${state.evidence_count || 0} element${state.evidence_count === 1 ? '' : 'ów'}`);
      setText('evidence-level', state.availability === 'observed' ? 'Dane obserwowane' : 'Brak obserwacji');
      setText('confidence-state', state.confidence?.label || 'Nieustalona');
      renderEditor(payload);
      window.dispatchEvent(new CustomEvent('testhp:biological-state-updated', { detail: payload }));
    } catch (error) {
      Object.entries(labels).forEach(([dimension, id]) => setText(id, defaults[dimension]));
      setText('observation-count', '0 elementów');
      setText('evidence-count', '0 elementów');
      setText('evidence-level', 'Brak obserwacji');
      setText('confidence-state', 'Nieustalona');
      const editButton = $('biological-state-edit'); if (editButton) editButton.disabled = true;
      console.warn('[BiologicalState] API unavailable; safe fallback kept.', error);
    }
  }
  function openEditor() { const editor = $('biological-state-editor'); if (!editor || !$('biological-state-source')?.options.length) return; editor.hidden = false; $('biological-state-editor-status').textContent = ''; editor.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  function closeEditor() { const editor = $('biological-state-editor'); if (editor) editor.hidden = true; }
  async function saveEditor() {
    const source = $('biological-state-source'), status = $('biological-state-editor-status'), observationId = source?.value;
    if (!observationId) return;
    const interpretations = {};
    Object.entries(inputs).forEach(([dimension, id]) => { const value = $(id)?.value.trim(); if (value) interpretations[dimension] = value; });
    if (status) status.textContent = 'Zapisywanie…';
    try {
      const response = await fetch('/api/biological-state', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ observation_id: observationId, author: 'local-user', interpretations }) });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
      if (status) status.textContent = 'Zapisano.';
      window.dispatchEvent(new CustomEvent('testhp:observation-updated', { detail: payload }));
      await refresh(lastDetail);
      setTimeout(closeEditor, 400);
    } catch (error) { if (status) status.textContent = `Błąd: ${error.message}`; }
  }
  const bind = () => {
    $('biological-state-edit')?.addEventListener('click', openEditor);
    $('biological-state-edit-close')?.addEventListener('click', closeEditor);
    $('biological-state-save')?.addEventListener('click', saveEditor);
    refresh();
  };
  window.addEventListener('testhp:spatial-contract-changed', event => refresh(event.detail || {}));
  window.addEventListener('testhp:observation-changed', () => refresh(lastDetail));
  window.addEventListener('testhp:observation-updated', () => refresh(lastDetail));
  document.addEventListener('DOMContentLoaded', bind, { once: true });
  if (document.readyState !== 'loading') bind();
  window.biologicalStateUI = { refresh, openEditor, closeEditor };
})();
