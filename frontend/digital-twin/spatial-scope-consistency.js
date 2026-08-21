(() => {
  const LEVELS = ['macro', 'tissue', 'cellular', 'molecular'];
  const labels = { macro: 'Makro', tissue: 'Tkanka', cellular: 'Komórkowe', molecular: 'Molekularne' };
  const get = id => document.getElementById(id);
  const setText = (id, value) => { const el = get(id); if (el) el.textContent = value; };

  function currentDetail() {
    const node = window.selectedSpatialNode;
    if (node && typeof node === 'object') return node;
    return { spatial_id: 'hand' };
  }

  function canonicalSpatialId(detail) {
    if (detail?.spatial_id) return String(detail.spatial_id).replace(/^\/+|\/+$/g, '') || 'hand';
    if (detail?.id && String(detail.id).startsWith('hand/')) return String(detail.id);
    if (Array.isArray(detail?.path) && detail.path.length) {
      const ids = detail.path.map(item => typeof item === 'object' ? item.id : item).filter(Boolean);
      if (ids.length) return ids.join('/');
    }
    return 'hand';
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
    const spatialId = canonicalSpatialId(detail);
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

  function onSpatialChange(event) { window.setTimeout(() => refresh(event?.detail || currentDetail()), 0); }
  window.addEventListener('testhp:spatial-layer-changed', onSpatialChange);
  window.addEventListener('testhp:spatial-change', onSpatialChange);
  window.addEventListener('testhp:observation-updated', () => refresh());
  window.addEventListener('testhp:biological-state-refresh', () => refresh());
  window.spatialScopeConsistency = { refresh };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => refresh(), { once: true });
  else refresh();
})();
