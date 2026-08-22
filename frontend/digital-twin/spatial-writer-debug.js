(() => {
  if (window.__testhpSpatialWriterDebugInstalled) return;
  window.__testhpSpatialWriterDebugInstalled = true;

  const safe = value => {
    try { return JSON.stringify(value); } catch { return String(value); }
  };
  const stack = () => (new Error().stack || '').split('\n').slice(2, 9).join(' <- ');
  const emit = (kind, detail = {}) => {
    const payload = { kind, at: Math.round(performance.now()), ...detail, stack: stack() };
    window.__testhpSpatialWriterDebug = window.__testhpSpatialWriterDebug || [];
    window.__testhpSpatialWriterDebug.push(payload);
    if (window.__testhpSpatialWriterDebug.length > 100) window.__testhpSpatialWriterDebug.shift();
    window.dispatchEvent(new CustomEvent('testhp:spatial-writer-debug', { detail: payload }));
  };
  const nav = () => ({
    path: [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean),
    level: document.getElementById('spatial-level-badge')?.textContent?.trim() || '?',
    target: document.getElementById('spatial-node strong')?.textContent?.trim() || '?',
    activeKey: window.spatialViewportManager?.activeKey || null,
    activeLayer: window.spatialViewportManager?.activeLayer || null,
    selected: window.selectedSpatialNode || null,
    evidenceTarget: window.spatialEvidenceTarget || null
  });

  const snapshot = () => safe(nav());
  let previous = snapshot();
  const sample = reason => {
    const current = snapshot();
    if (current !== previous) {
      emit('STATE CHANGE', { reason, before: JSON.parse(previous), after: JSON.parse(current) });
      previous = current;
    }
  };

  const manager = window.spatialViewportManager;
  if (manager) {
    ['activeKey', 'activeLayer'].forEach(prop => {
      const descriptor = Object.getOwnPropertyDescriptor(manager, prop);
      if (!descriptor || !descriptor.configurable) return;
      let value = manager[prop];
      Object.defineProperty(manager, prop, {
        configurable: true,
        enumerable: descriptor.enumerable,
        get() { return value; },
        set(next) {
          const before = value;
          if (before !== next) emit('MANAGER PROPERTY WRITE', { property: prop, before, after: next, navigation: nav() });
          value = next;
        }
      });
    });
  }

  window.addEventListener('testhp:spatial-layer-changed', e => emit('EVENT spatial-layer-changed', { detail: e.detail || {}, navigation: nav() }));
  window.addEventListener('testhp:spatial-target-changed', e => emit('EVENT spatial-target-changed', { detail: e.detail || {}, navigation: nav() }));
  window.addEventListener('testhp:viewport-rendered', e => emit('EVENT viewport-rendered', { detail: e.detail || {}, navigation: nav() }));
  window.addEventListener('testhp:deep-3d-active', e => emit('EVENT deep-3d-active', { detail: e.detail || {}, navigation: nav() }));

  document.addEventListener('pointerdown', e => {
    const button = e.target?.closest?.('.spatial-target');
    if (!button) return;
    emit('POINTERDOWN', { button: button.textContent.trim(), spatialId: button.dataset?.spatialId || null, navigation: nav() });
  }, true);

  document.addEventListener('click', e => {
    const button = e.target?.closest?.('.spatial-target');
    if (!button) return;
    emit('CLICK', { button: button.textContent.trim(), spatialId: button.dataset?.spatialId || null, navigation: nav() });
  }, true);

  const lifecycle = ['load', 'pageshow', 'pagehide', 'visibilitychange'];
  lifecycle.forEach(type => window.addEventListener(type, () => emit(`LIFECYCLE ${type}`, { navigation: nav() }), true));

  let lastActiveKey = manager?.activeKey || null;
  let lastPath = snapshot();
  const timer = setInterval(() => {
    const currentKey = manager?.activeKey || null;
    const currentPath = snapshot();
    if (currentKey !== lastActiveKey) {
      emit('ACTIVE KEY CHANGE DETECTED', { before: lastActiveKey, after: currentKey, navigation: nav() });
      lastActiveKey = currentKey;
    }
    if (currentPath !== lastPath) {
      emit('PATH CHANGE DETECTED', { before: JSON.parse(lastPath), after: JSON.parse(currentPath) });
      lastPath = currentPath;
    }
    sample('poll');
  }, 25);

  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
  window.__testhpSpatialWriterDebugSnapshot = nav;
  emit('INSTALLED', { navigation: nav() });
})();
