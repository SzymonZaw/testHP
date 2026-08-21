(() => {
  const $ = id => document.getElementById(id);
  const clean = value => String(value ?? '').replace(/^\/+|\/+$/g, '');

  function canonicalSpatialId(detail = {}) {
    const raw = detail.spatial_id || detail.spatialId;
    if (raw) {
      const value = clean(raw);
      if (value === 'hand' || value.startsWith('hand/')) return value;
    }
    if (Array.isArray(detail.path) && detail.path.length) {
      const ids = detail.path.map(item => typeof item === 'object' ? item.id : item).filter(Boolean).map(clean);
      if (ids.length) return ids[0] === 'hand' ? ids.join('/') : ['hand', ...ids].join('/');
    }
    if (detail.id) {
      const id = clean(detail.id);
      return id === 'hand' || id.startsWith('hand/') ? id : `hand/${id}`;
    }
    const selected = window.__testhpCanonicalSpatialSelection || window.selectedSpatialNode;
    const selectedId = selected?.spatial_id || selected?.id;
    return selectedId ? canonicalSpatialId({ spatial_id: selectedId }) : 'hand';
  }

  function canonicalNode(detail = {}) {
    const spatial_id = canonicalSpatialId(detail);
    const breadcrumb = [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
    const path = Array.isArray(detail.path) && detail.path.length
      ? detail.path.map(item => typeof item === 'object' ? item.label : item).filter(Boolean).map(String)
      : breadcrumb;
    return {
      id: spatial_id,
      spatial_id,
      label: String(detail.target || detail.label || path[path.length - 1] || (spatial_id === 'hand' ? 'Dłoń' : spatial_id.split('/').pop())),
      level: String(detail.level || 'macro').toLowerCase(),
      parent_id: spatial_id === 'hand' ? null : spatial_id.split('/').slice(0, -1).join('/') || 'hand',
      path
    };
  }

  function normalizeNavigationIds() {
    const children = $('spatial-children');
    if (!children) return;
    [...children.querySelectorAll('.spatial-target')].forEach(button => {
      const explicit = button.dataset.spatialId || button.getAttribute('data-spatial-id');
      if (explicit) button.dataset.spatialId = explicit.startsWith('hand') ? explicit : `hand/${explicit}`;
    });
  }

  function publish(detail = {}) {
    const node = canonicalNode(detail);
    window.selectedSpatialNode = node;
    window.spatialEvidenceTarget = node;
    window.__testhpCanonicalSpatialSelection = node;
    normalizeNavigationIds();
    window.dispatchEvent(new CustomEvent('testhp:spatial-selection-contract-updated', { detail: node }));
    return node;
  }

  function onSpatialChange(event) {
    publish(event?.detail || {});
  }

  window.spatialSelectionContract = {
    get: () => window.__testhpCanonicalSpatialSelection || publish({}),
    normalize: canonicalSpatialId,
    publish
  };

  window.addEventListener('testhp:spatial-layer-changed', onSpatialChange);
  window.addEventListener('testhp:spatial-change', onSpatialChange);
  window.addEventListener('testhp:viewport-manager-ready', () => normalizeNavigationIds());

  const children = $('spatial-children');
  if (children) {
    const observer = new MutationObserver(normalizeNavigationIds);
    observer.observe(children, { childList: true, subtree: true });
  }
})();
