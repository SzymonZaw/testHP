(() => {
  const labels = {
    biological_age: 'age-state',
    structural_functional_state: 'structure-state',
    damage: 'damage-state',
    pathology: 'pathology-state',
  };
  const defaults = {
    biological_age: 'Nieustalony',
    structural_functional_state: 'Nieustalony',
    damage: 'Nieustalone',
    pathology: 'Nieustalona',
  };

  function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  }

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

  async function refresh(detail = {}) {
    const spatialId = stateSpatialId(detail);
    const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: spatialId, include_descendants: 'true' });
    try {
      const response = await fetch(`/api/biological-state?${params.toString()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      const state = payload?.state || {};
      const interpretations = state.interpretations || {};
      Object.entries(labels).forEach(([dimension, id]) => setText(id, displayInterpretation(interpretations[dimension], dimension)));
      setText('evidence-count', `${state.evidence_count || 0} element${state.evidence_count === 1 ? '' : 'ów'}`);
      setText('evidence-level', state.availability === 'observed' ? 'Dane obserwowane' : 'Niewystarczające dane');
      setText('confidence-state', state.confidence?.label || 'Nieustalona');
      window.dispatchEvent(new CustomEvent('testhp:biological-state-updated', { detail: payload }));
    } catch (error) {
      Object.entries(labels).forEach(([dimension, id]) => setText(id, defaults[dimension]));
      setText('evidence-count', '0 elementów');
      setText('evidence-level', 'Niewystarczające dane');
      setText('confidence-state', 'Nieustalona');
      console.warn('[BiologicalState] API unavailable; safe fallback kept.', error);
    }
  }

  window.addEventListener('testhp:spatial-layer-changed', event => refresh(event.detail || {}));
  window.addEventListener('testhp:spatial-change', event => refresh(event.detail || {}));
  window.addEventListener('testhp:observation-updated', () => refresh());
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => refresh());
  else refresh();
  window.biologicalStateUI = { refresh };
})();
