(() => {
  const $ = id => document.getElementById(id);
  const clean = value => String(value ?? '').replace(/^\/+|\/+$/g, '');
  const childSlug = {
    'Kłąb kciuka': 'thenar-eminence',
    'Kłębik dłoni': 'hypothenar-eminence',
    'Centralna część dłoni': 'central-palm',
    'Thenar eminence': 'thenar-eminence',
    'Hypothenar eminence': 'hypothenar-eminence',
    'Central palm': 'central-palm',
    'Regional field': 'regional-field',
    'Microscopy field A': 'field-a',
    'Microscopy field B': 'field-b',
    'Microscopy field C': 'field-c',
    'Pole mikroskopowe A': 'field-a',
    'Pole mikroskopowe B': 'field-b',
    'Pole mikroskopowe C': 'field-c',
    'Cell target 1': 'cell-1',
    'Cell target 2': 'cell-2',
    'Cell target 3': 'cell-3'
  };

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
    const selected = window.__testhpCanonicalSpatialSelection || window.selectedSpatialNode;
    const parentId = selected?.spatial_id || 'hand';
    [...children.querySelectorAll('.spatial-target')].forEach((button, index) => {
      const explicit = button.dataset.spatialId || button.getAttribute('data-spatial-id');
      if (explicit) {
        button.dataset.spatialId = explicit.startsWith('hand') ? explicit : `hand/${explicit}`;
        return;
      }
      const label = button.querySelector('strong')?.textContent?.trim() || '';
      const slug = childSlug[label] || label.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || `child-${index + 1}`;
      button.dataset.spatialId = `${parentId}/${slug}`;
      button.dataset.spatialParentId = parentId;
      button.dataset.spatialLevel = button.dataset.spatialLevel || 'unknown';
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

  function bridgeManager() {
    const manager = window.spatialViewportManager;
    if (!manager || typeof manager.setSpatialTarget !== 'function' || manager.__testhpSpatialContractWrapped) return;
    const original = manager.setSpatialTarget.bind(manager);
    manager.setSpatialTarget = target => {
      publish({
        ...target,
        spatial_id: target?.spatial_id || (target?.id ? `hand/${clean(target.id)}` : undefined),
        path: target?.path || ['Dłoń', target?.label || target?.id || 'Cel']
      });
      return original(target);
    };
    manager.__testhpSpatialContractWrapped = true;
    window.__testhpSpatialContractManagerBridge = 'installed';
  }

  function onSpatialChange(event) {
    publish(event?.detail || {});
    bridgeManager();
  }

  window.spatialSelectionContract = {
    get: () => window.__testhpCanonicalSpatialSelection || publish({}),
    normalize: canonicalSpatialId,
    publish
  };

  window.addEventListener('testhp:spatial-layer-changed', onSpatialChange);
  window.addEventListener('testhp:spatial-change', onSpatialChange);
  window.addEventListener('testhp:viewport-manager-ready', () => { normalizeNavigationIds(); bridgeManager(); });

  const children = $('spatial-children');
  if (children) {
    const observer = new MutationObserver(() => normalizeNavigationIds());
    observer.observe(children, { childList: true, subtree: true });
  }

  const timer = window.setInterval(() => {
    bridgeManager();
    normalizeNavigationIds();
  }, 500);
  window.addEventListener('beforeunload', () => window.clearInterval(timer), { once: true });
})();
