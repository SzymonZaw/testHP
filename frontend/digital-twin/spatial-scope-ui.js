(() => {
  const LEVELS = ['macro', 'tissue', 'cellular', 'molecular'];
  const labels = { macro: 'Makro', tissue: 'Tkanka', cellular: 'Komórkowe', molecular: 'Molekularne' };
  let requestId = 0;

  const get = id => document.getElementById(id);
  function targetId(detail = {}) {
    if (detail.spatial_id) return String(detail.spatial_id);
    if (detail.id) return String(detail.id);
    const node = window.selectedSpatialNode;
    if (node) return String(node.spatial_id || node.id || node.regionId || 'hand');
    return String(window.spatialEvidenceTarget || 'hand');
  }

  async function refresh(detail = {}) {
    const id = ++requestId;
    const spatialId = targetId(detail);
    const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: spatialId, include_descendants: 'true' });
    try {
      const response = await fetch(`/api/biological-state?${params}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (id !== requestId) return;
      const summary = payload.summary || {};
      const byLevel = summary.by_level || {};
      const directByLevel = summary.direct_by_level || {};
      const descendantByLevel = summary.descendant_by_level || {};
      LEVELS.forEach(level => {
        const state = get(`${level}-state`);
        if (!state) return;
        const count = Number(byLevel[level] || 0);
        state.textContent = count ? `${count} ${count === 1 ? 'dane' : 'danych'}` : 'Niedostępne';
        state.dataset.scopeCount = String(count);
        state.dataset.directCount = String(Number(directByLevel[level] || 0));
        state.dataset.descendantCount = String(Number(descendantByLevel[level] || 0));
        state.dataset.scopeSpatialId = spatialId;
        state.title = `${labels[level]}: ${count} w zakresie · bezpośrednio ${Number(directByLevel[level] || 0)} · potomne ${Number(descendantByLevel[level] || 0)}`;
        const row = state.closest('.evidence-row');
        if (row) {
          row.dataset.scopeCount = String(count);
          row.dataset.directCount = String(Number(directByLevel[level] || 0));
          row.dataset.descendantCount = String(Number(descendantByLevel[level] || 0));
        }
      });
      window.dispatchEvent(new CustomEvent('testhp:spatial-scope-updated', { detail: payload }));
    } catch (error) {
      console.warn('[SpatialScope] API scope unavailable; existing UI state preserved.', error);
    }
  }

  window.addEventListener('testhp:spatial-layer-changed', event => refresh(event.detail || {}));
  window.addEventListener('testhp:spatial-change', event => refresh(event.detail || {}));
  window.addEventListener('testhp:observation-changed', () => refresh());
  window.addEventListener('testhp:observation-updated', () => refresh());
  window.addEventListener('testhp:biological-state-refresh', () => refresh());
  document.addEventListener('DOMContentLoaded', () => refresh(), { once: true });
  if (document.readyState !== 'loading') refresh();
  window.spatialScopeUI = { refresh };
})();
