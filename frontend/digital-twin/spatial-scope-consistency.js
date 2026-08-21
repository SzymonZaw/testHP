(() => {
  const LEVELS = ['macro', 'tissue', 'cellular', 'molecular'];
  const labels = { macro: 'Makro', tissue: 'Tkanka', cellular: 'Komórkowe', molecular: 'Molekularne' };
  const get = id => document.getElementById(id);
  const setText = (id, value) => { const el = get(id); if (el) el.textContent = value; };

  function canonicalSpatialId(detail = {}) {
    const raw = detail?.spatial_id || detail?.spatialId;
    if (raw) {
      const value = String(raw).replace(/^\/+|\/+$/g, '');
      if (value === 'hand' || value.startsWith('hand/')) return value;
    }
    if (Array.isArray(detail?.path) && detail.path.length) {
      const ids = detail.path.map(item => typeof item === 'object' ? item.id : item).filter(Boolean).map(String);
      if (ids.length) return ids[0] === 'hand' ? ids.join('/') : ['hand', ...ids].join('/');
    }
    if (detail?.id) {
      const id = String(detail.id).replace(/^\/+|\/+$/g, '');
      if (id === 'hand' || id.startsWith('hand/')) return id;
      return `hand/${id}`;
    }
    const selected = window.__testhpCanonicalSpatialSelection || window.selectedSpatialNode;
    const selectedId = selected?.spatial_id || selected?.id;
    if (selectedId) return canonicalSpatialId({ spatial_id: selectedId });
    return 'hand';
  }

  function canonicalNode(detail = {}) {
    const spatialId = canonicalSpatialId(detail);
    const breadcrumb = [...document.querySelectorAll('#spatial-breadcrumb button')].map(button => button.textContent.trim()).filter(Boolean);
    const path = Array.isArray(detail.path) && detail.path.length
      ? detail.path.map(item => typeof item === 'object' ? item.label : item).filter(Boolean).map(String)
      : breadcrumb;
    const label = String(detail.target || detail.label || path[path.length - 1] || (spatialId === 'hand' ? 'Dłoń' : spatialId.split('/').pop()));
    const level = String(detail.level || 'macro').toLowerCase();
    const parent_id = spatialId === 'hand' ? null : spatialId.split('/').slice(0, -1).join('/') || 'hand';
    return { id: spatialId, spatial_id: spatialId, label, level, parent_id, path };
  }

  function normalizeNavigationIds() {
    const children = get('spatial-children');
    if (!children) return;
    [...children.querySelectorAll('.spatial-target')].forEach(button => {
      const explicit = button.dataset.spatialId || button.getAttribute('data-spatial-id');
      if (explicit) {
        button.dataset.spatialId = explicit.startsWith('hand') ? explicit : `hand/${explicit}`;
      }
    });
  }

  function publishSelection(detail = {}) {
    const node = canonicalNode(detail);
    window.selectedSpatialNode = node;
    window.spatialEvidenceTarget = node;
    window.__testhpCanonicalSpatialSelection = node;
    normalizeNavigationIds();
    return node;
  }

  function currentDetail() {
    const selected = window.__testhpCanonicalSpatialSelection || window.selectedSpatialNode;
    if (selected && typeof selected === 'object') return selected;
    return { spatial_id: 'hand' };
  }

  function layerCount(summary, level) {
    const direct = Number(summary?.direct_by_level?.[level] || 0);
    const descendants = Number(summary?.descendant_by_level?.[level] || 0);
    return { direct, descendants, total: direct + descendants };
  }

  function renderLayer(level, counts) {
    const state = get(`${level}-state`), status = get(`${level}-status`), detail = get(`${level}-detail`);
    if (!state || !status || !detail) return;
    if (!counts.total) {
      state.textContent = 'Brak danych w zakresie';
      status.textContent = 'NONE';
      detail.textContent = `Brak obserwacji ${labels[level].toLowerCase()} dla wybranego spatial_id ani jego potomków.`;
      return;
    }
    state.textContent = `${counts.total} ${counts.total === 1 ? 'dane' : 'danych'} w zakresie`;
    if (counts.direct && counts.descendants) status.textContent = 'DIRECT + CHILDREN';
    else if (counts.direct) status.textContent = 'DIRECT';
    else status.textContent = 'CHILDREN';
    const parts = [];
    if (counts.direct) parts.push(`bezpośrednio: ${counts.direct}`);
    if (counts.descendants) parts.push(`w potomkach: ${counts.descendants}`);
    detail.textContent = `${labels[level]} · ${parts.join(' · ')}. Liczba pochodzi z obserwacji w scope przestrzennym; evidence jest rozliczane osobno.`;
  }

  async function refresh(detail = currentDetail()) {
    const node = publishSelection(detail);
    const spatialId = node.spatial_id;
    const params = new URLSearchParams({ subject_id: 'own_cohort', timepoint: 'T0', spatial_id: spatialId, include_descendants: 'true' });
    try {
      const response = await fetch(`/api/biological-state?${params.toString()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json(), summary = payload?.summary || {};
      LEVELS.forEach(level => renderLayer(level, layerCount(summary, level)));
      const observationCount = Number(summary.observation_count || summary.observations || 0);
      const evidenceCount = Number(summary.explicit_evidence || 0);
      setText('evidence-count', `${observationCount} ${observationCount === 1 ? 'element' : 'elementów'}`);
      setText('evidence-level', observationCount ? 'Dane obserwowane' : 'Niewystarczające dane');
      setText('evidence-breakdown', `Scope: ${spatialId} · obserwacje: ${observationCount} · evidence: ${evidenceCount} · direct: ${summary.direct_observations || 0} · descendants: ${summary.descendant_observations || 0}`);
      window.dispatchEvent(new CustomEvent('testhp:spatial-scope-consistency-updated', { detail: { spatial_id: spatialId, summary, payload } }));
    } catch (error) {
      console.warn('[SpatialScope] biological-state scope refresh failed', { spatialId, error });
    }
  }

  function onSpatialChange(event) {
    const detail = event?.detail || currentDetail();
    publishSelection(detail);
    window.setTimeout(() => refresh(detail), 0);
  }

  window.spatialSelectionContract = {
    get: () => currentDetail(),
    normalize: canonicalSpatialId,
    publish: publishSelection,
    refresh
  };

  window.addEventListener('testhp:spatial-layer-changed', onSpatialChange);
  window.addEventListener('testhp:spatial-change', onSpatialChange);
  window.addEventListener('testhp:observation-updated', () => refresh());
  window.addEventListener('testhp:biological-state-refresh', () => refresh());

  const observerTarget = get('spatial-children');
  if (observerTarget) {
    const observer = new MutationObserver(() => normalizeNavigationIds());
    observer.observe(observerTarget, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => refresh(), { once: true });
  else refresh();
})();