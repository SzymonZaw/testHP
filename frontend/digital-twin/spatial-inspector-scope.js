(() => {
  const SUBJECT = 'own_cohort';
  const LEVELS = ['macro', 'tissue', 'cellular', 'molecular'];
  const DATA_STORAGE = 'digitalTwinRegionData.v1';

  const readLocalData = () => {
    try {
      const value = JSON.parse(localStorage.getItem(DATA_STORAGE) || '{}');
      return Array.isArray(value.items) ? value.items : [];
    } catch {
      return [];
    }
  };

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));

  async function fetchObservations(target) {
    const params = new URLSearchParams({ subject_id: SUBJECT, spatial_id: target.spatial_id, include_archived: 'false' });
    const response = await fetch(`/api/observations?${params.toString()}`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return (await response.json()).observations || [];
  }

  async function fetchMacro(target) {
    if (target.level !== 'macro') return [];
    try {
      const response = await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(SUBJECT)}&timepoint=T0`, { cache: 'no-store' });
      if (!response.ok) return [];
      const payload = await response.json();
      return (payload.assets || []).filter(item => String(item.status || '').toLowerCase() === 'ready' || String(item.status || '').toLowerCase() === 'available')
        .filter(item => String(item.region_id || '') === target.id);
    } catch {
      return [];
    }
  }

  function setLayer(type, count, detail, status) {
    const state = document.getElementById(`${type}-state`);
    const text = document.getElementById(`${type}-detail`);
    const badge = document.getElementById(`${type}-status`);
    if (state) state.textContent = count ? `${count} dostępne dane` : 'Niedostępne';
    if (text) text.textContent = detail;
    if (badge) badge.textContent = status;
  }

  async function refresh(detail) {
    const contract = window.testhpSpatialContract;
    const target = contract?.getTarget?.() || detail;
    if (!target?.spatial_id) return;

    const localItems = readLocalData().filter(item => contract.inScope(target.spatial_id, item.target, false));
    let observations = [];
    let macro = [];
    try { observations = await fetchObservations(target); } catch {}
    macro = await fetchMacro(target);

    const byLevel = Object.fromEntries(LEVELS.map(level => [level, []]));
    observations.forEach(item => {
      const level = String(item.biological_level || '').toLowerCase();
      if (byLevel[level]) byLevel[level].push(item);
    });
    localItems.forEach(item => {
      const level = String(item.type || '').toLowerCase();
      if (byLevel[level]) byLevel[level].push(item);
    });
    macro.forEach(item => byLevel.macro.push(item));

    const title = target.label || target.spatial_id;
    document.getElementById('zone-label')?.replaceChildren(document.createTextNode(target.spatial_id));
    const regionTitle = document.getElementById('region-title');
    if (regionTitle) regionTitle.textContent = title;
    const context = document.getElementById('region-context');
    if (context) context.textContent = `Dłoń · T0 · ${target.level}`;

    LEVELS.forEach(level => {
      const count = byLevel[level].length;
      setLayer(
        level,
        count,
        count ? `${count} rekord${count === 1 ? '' : 'y'} biologicznych lub danych jawnie przypisano do ${target.spatial_id}.` : `Brak danych jawnie przypisanych do ${target.spatial_id}.`,
        count ? 'SCOPED' : 'NONE'
      );
    });

    window.dispatchEvent(new CustomEvent('testhp:inspector-scope-updated', {
      detail: {
        target,
        counts: Object.fromEntries(LEVELS.map(level => [level, byLevel[level].length])),
        direct: true,
        descendants: false,
        observation_count: observations.length,
      }
    }));
  }

  window.addEventListener('testhp:spatial-contract-changed', event => refresh(event.detail));
  window.addEventListener('testhp:region-data-changed', () => refresh());
  window.addEventListener('testhp:observation-changed', () => refresh());
  window.addEventListener('testhp:observation-updated', () => refresh());
  document.addEventListener('DOMContentLoaded', () => refresh(), { once: true });
  if (document.readyState !== 'loading') refresh();
})();
