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

  async function fetchMacro(target) {
    if (target.level !== 'macro') return [];
    try {
      const response = await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(SUBJECT)}&timepoint=T0`, { cache: 'no-store' });
      if (!response.ok) return [];
      const payload = await response.json();
      return (payload.assets || [])
        .filter(item => ['ready', 'available'].includes(String(item.status || '').toLowerCase()))
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
    const macro = await fetchMacro(target);
    const byLevel = Object.fromEntries(LEVELS.map(level => [level, []]));

    localItems.forEach(item => {
      const level = String(item.type || '').toLowerCase();
      if (byLevel[level]) byLevel[level].push(item);
    });
    macro.forEach(item => byLevel.macro.push(item));

    const title = target.label || target.spatial_id;
    const zone = document.getElementById('zone-label');
    if (zone) zone.textContent = target.spatial_id;
    const regionTitle = document.getElementById('region-title');
    if (regionTitle) regionTitle.textContent = title;
    const context = document.getElementById('region-context');
    if (context) context.textContent = `Dłoń · T0 · ${target.level}`;

    LEVELS.forEach(level => {
      const count = byLevel[level].length;
      setLayer(
        level,
        count,
        count ? `${count} dane jawnie przypisano do ${target.spatial_id}.` : `Brak danych jawnie przypisanych do ${target.spatial_id}.`,
        count ? 'SCOPED' : 'NONE'
      );
    });

    window.dispatchEvent(new CustomEvent('testhp:inspector-scope-updated', {
      detail: {
        target,
        counts: Object.fromEntries(LEVELS.map(level => [level, byLevel[level].length])),
        direct: true,
        descendants: false,
      }
    }));
  }

  window.addEventListener('testhp:spatial-contract-changed', event => refresh(event.detail));
  window.addEventListener('testhp:region-data-changed', () => refresh());
  document.addEventListener('DOMContentLoaded', () => refresh(), { once: true });
  if (document.readyState !== 'loading') refresh();
})();
