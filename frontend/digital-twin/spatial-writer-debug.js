(() => {
  if (window.__testhpSpatialWriterDebugBootstrapInstalled) return;
  window.__testhpSpatialWriterDebugBootstrapInstalled = true;

  const safe = value => {
    try { return JSON.stringify(value); } catch { return String(value); }
  };
  const stack = () => (new Error().stack || '').split('\n').slice(2, 12).join(' <- ');
  const buffer = () => (window.__testhpSpatialWriterDebug ||= []);
  const emit = (kind, detail = {}) => {
    const payload = { kind, at: Math.round(performance.now()), ...detail, stack: stack() };
    buffer().push(payload);
    if (buffer().length > 200) buffer().shift();
    window.dispatchEvent(new CustomEvent('testhp:spatial-writer-debug', { detail: payload }));
    console.debug('[Twin spatial writer debug]', payload);
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

  function installGlobalTargetDebug() {
    if (window.__testhpSpatialGlobalWriterDebugInstalled) return;
    window.__testhpSpatialGlobalWriterDebugInstalled = true;

    ['selectedSpatialNode', 'spatialEvidenceTarget', 'testhpSpatialTarget'].forEach(property => {
      const descriptor = Object.getOwnPropertyDescriptor(window, property);
      if (descriptor && !descriptor.configurable) {
        emit('GLOBAL PROPERTY PATCH SKIPPED', { property, reason: 'not-configurable', value: window[property], navigation: nav() });
        return;
      }
      const originalGet = descriptor?.get;
      const originalSet = descriptor?.set;
      let value = originalGet ? originalGet.call(window) : descriptor ? descriptor.value : window[property];
      Object.defineProperty(window, property, {
        configurable: true,
        enumerable: descriptor?.enumerable ?? true,
        get() { return originalGet ? originalGet.call(this) : value; },
        set(next) {
          const before = originalGet ? originalGet.call(this) : value;
          if (before !== next) emit('GLOBAL TARGET WRITE', { property, before, after: next, navigation: nav() });
          if (originalSet) originalSet.call(this, next); else value = next;
        }
      });
      emit('GLOBAL PROPERTY DEBUG INSTALLED', { property, initial: value, navigation: nav() });
    });
  }

  function installBodyTargetDebug() {
    const body = document.body;
    if (!body || body.__testhpSpatialBodyWriterDebugInstalled) return;
    body.__testhpSpatialBodyWriterDebugInstalled = true;
    const observer = new MutationObserver(records => {
      records.forEach(record => {
        if (record.type === 'attributes' && record.attributeName === 'data-spatial-target') {
          emit('BODY TARGET ATTRIBUTE WRITE', { after: body.dataset.spatialTarget || null, navigation: nav() });
        }
      });
    });
    observer.observe(body, { attributes: true, attributeFilter: ['data-spatial-target'] });
    window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });
    emit('BODY TARGET DEBUG INSTALLED', { value: body.dataset.spatialTarget || null, navigation: nav() });
  }

  function installManagerDebug(manager) {
    if (!manager || manager.__testhpSpatialWriterDebugInstalled) return;
    manager.__testhpSpatialWriterDebugInstalled = true;
    emit('MANAGER DEBUG INSTALLED', { navigation: nav(), managerKeys: Object.keys(manager) });

    ['activeKey', 'activeLayer'].forEach(prop => {
      let descriptor = Object.getOwnPropertyDescriptor(manager, prop);
      let owner = manager;
      while (!descriptor && owner) {
        owner = Object.getPrototypeOf(owner);
        descriptor = owner && Object.getOwnPropertyDescriptor(owner, prop);
      }
      if (!descriptor || !descriptor.configurable) {
        emit('PROPERTY PATCH SKIPPED', { property: prop, reason: 'not-configurable-or-not-found', navigation: nav() });
        return;
      }
      const originalGet = descriptor.get;
      const originalSet = descriptor.set;
      let value = originalGet ? originalGet.call(manager) : manager[prop];
      Object.defineProperty(manager, prop, {
        configurable: true,
        enumerable: descriptor.enumerable,
        get() { return originalGet ? originalGet.call(this) : value; },
        set(next) {
          const before = originalGet ? originalGet.call(this) : value;
          if (before !== next) emit('MANAGER PROPERTY WRITE', { property: prop, before, after: next, navigation: nav() });
          if (originalSet) originalSet.call(this, next); else value = next;
        }
      });
    });

    if (typeof manager.setSpatialTarget === 'function' && !manager.setSpatialTarget.__testhpDebugWrapped) {
      const original = manager.setSpatialTarget.bind(manager);
      const wrapped = function(target, ...args) {
        emit('SET SPATIAL TARGET CALL', { target, args, navigation: nav() });
        let result;
        try {
          result = original(target, ...args);
          emit('SET SPATIAL TARGET RETURN', { target, result, navigation: nav() });
          return result;
        } catch (error) {
          emit('SET SPATIAL TARGET THROW', { target, error: String(error?.stack || error), navigation: nav() });
          throw error;
        }
      };
      wrapped.__testhpDebugWrapped = true;
      manager.setSpatialTarget = wrapped;
    }
  }

  function install() {
    installGlobalTargetDebug();
    installBodyTargetDebug();
    const manager = window.spatialViewportManager;
    if (!manager) return false;
    installManagerDebug(manager);
    const snapshot = () => safe(nav());
    let previous = snapshot();
    const sample = reason => {
      const current = snapshot();
      if (current !== previous) {
        emit('STATE CHANGE', { reason, before: JSON.parse(previous), after: JSON.parse(current) });
        previous = current;
      }
    };

    if (!window.__testhpSpatialWriterDebugListenersInstalled) {
      window.__testhpSpatialWriterDebugListenersInstalled = true;
      ['spatial-layer-changed','spatial-target-changed','viewport-rendered','deep-3d-active'].forEach(name => {
        window.addEventListener(`testhp:${name}`, e => emit(`EVENT ${name}`, { detail: e.detail || {}, navigation: nav() }));
      });
      document.addEventListener('pointerdown', e => {
        const button = e.target?.closest?.('.spatial-target');
        if (button) emit('POINTERDOWN', { button: button.textContent.trim(), spatialId: button.dataset?.spatialId || null, navigation: nav() });
      }, true);
      document.addEventListener('click', e => {
        const button = e.target?.closest?.('.spatial-target');
        if (button) emit('CLICK', { button: button.textContent.trim(), spatialId: button.dataset?.spatialId || null, navigation: nav() });
      }, true);
      ['load','pageshow','pagehide','visibilitychange'].forEach(type => window.addEventListener(type, () => emit(`LIFECYCLE ${type}`, { navigation: nav() }), true));
      window.__testhpSpatialWriterDebugSnapshot = nav;
    }
    sample('manager-install');
    return true;
  }

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (install() || attempts >= 240) clearInterval(timer);
  }, 25);
  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
  emit('BOOTSTRAP INSTALLED', { navigation: nav() });
})();
