(() => {
  function render(payload) {
    const state = payload?.state || {};
    const observationCount = Number(state.observation_count ?? payload?.summary?.observation_count ?? 0);
    const evidenceCount = Number(state.evidence_count ?? payload?.summary?.evidence_count ?? 0);
    const count = document.getElementById('evidence-count');
    const availability = document.getElementById('evidence-level');
    if (count) count.textContent = `${observationCount} element${observationCount === 1 ? '' : 'ów'}`;
    if (availability) availability.textContent = observationCount > 0 ? (evidenceCount > 0 ? 'Dane obserwowane + evidence' : 'Dane obserwowane') : 'Brak obserwacji';
  }

  window.addEventListener('testhp:biological-state-updated', event => render(event.detail));
  window.addEventListener('testhp:spatial-contract-changed', () => {
    const target = window.testhpSpatialContract?.getTarget?.();
    if (!target?.spatial_id) return;
    const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: target.spatial_id, include_descendants: 'true' });
    fetch(`/api/biological-state?${params.toString()}`, { cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(render).catch(() => {});
  });
})();
