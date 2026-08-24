(() => {
  const loading = document.getElementById('viewer-loading');
  const canvas = document.getElementById('twin-canvas');
  const viewport = document.getElementById('twin-viewport');
  const status = document.getElementById('twin-status');
  if (!loading || !canvas || !viewport) return;

  // app.js is the sole owner of the canonical Three.js renderer. This boot
  // module only verifies readiness and installs a tiny state guard around the
  // canonical renderer so auxiliary geometry updates cannot leave a stale
  // render-target / viewport / clear-alpha state behind.
  const progress = (step, detail = '') => window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step, detail } }));
  const isCanonical = manager => !!(manager && manager.version === 'canonical-three-2' && manager.active?.scene && manager.active?.camera && manager.deepRenderer);
  const safe = value => { try { return JSON.stringify(value); } catch { return String(value); } };
  const stack = () => (new Error().stack || '').split('\n').slice(2, 7).join(' <- ');

  let lastNavSnapshot = '';
  let diagnosticsInstalled = false;
  let rendererGuardInstalled = false;

  const readNavigation = () => {
    const crumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(el => el.textContent.trim()).filter(Boolean);
    const node = document.getElementById('spatial-node');
    const children = [...document.querySelectorAll('#spatial-children .spatial-target')].map(el => ({
      label: el.querySelector('strong')?.textContent?.trim() || '(missing label)',
      meta: el.querySelector('span')?.textContent?.trim() || '(missing level)',
      disabled: !!el.disabled,
      connected: el.isConnected,
      id: el.dataset?.spatialId || el.getAttribute('data-spatial-id') || null
    }));
    const level = document.getElementById('spatial-level-badge')?.textContent?.trim() || '?';
    const target = node?.querySelector('strong')?.textContent?.trim() || '?';
    return { crumbs, node, children, level, target };
  };

  const installCanonicalRendererGuard = manager => {
    const renderer = manager?.deepRenderer;
    if (!renderer || rendererGuardInstalled || renderer.__testhpCanonicalStateGuardInstalled) return;
    const originalRender = renderer.render?.bind(renderer);
    if (!originalRender) return;

    renderer.__testhpCanonicalStateGuardInstalled = true;
    rendererGuardInstalled = true;
    renderer.autoClear = true;
    renderer.setClearColor?.(0x0d1117, 1);

    renderer.render = (scene, camera) => {
      renderer.setRenderTarget?.(null);
      renderer.setScissorTest?.(false);
      const width = renderer.domElement?.width || renderer.getDrawingBufferSize?.(new (window.THREE?.Vector2 || class { set() {} })())?.x || 1;
      const height = renderer.domElement?.height || 1;
      renderer.setViewport?.(0, 0, width, height);
      renderer.autoClear = true;
      renderer.setClearColor?.(0x0d1117, 1);
      return originalRender(scene, camera);
    };

    progress('canonical-renderer-guard', 'installed; render target=null; scissor=false; viewport restored; clear alpha=1');
  };

  const navigationDiagnostics = () => {
    const nav = readNavigation();
    const manager = window.spatialViewportManager;
    const active = manager?.active;
    const evidenceTarget = window.spatialEvidenceTarget || '?';
    const selectedTarget = window.selectedSpatialNode || '?';
    const expectedHandMacro = ['Śródręcze','Mały palec','Palec serdeczny','Palec środkowy','Palec wskazujący','Kciuk','Nadgarstek'];
    const actualLabels = nav.children.map(x => x.label);
    const isHandMacro = nav.crumbs.length === 1 && /^dłoń$/i.test(nav.crumbs[0]) && /macro/i.test(nav.level);
    const fallbackRegionalField = isHandMacro && actualLabels.length === 1 && /^regional field$/i.test(actualLabels[0]);
    const missingExpected = isHandMacro ? expectedHandMacro.filter(label => !actualLabels.includes(label)) : [];
    const diagnostics = {
      path: nav.crumbs.join(' > ') || '(root)', level: nav.level, target: nav.target,
      evidenceTarget, selectedTarget, children: actualLabels, childCount: nav.children.length,
      childMeta: nav.children, expectedHandMacro, missingExpected, fallbackRegionalField,
      managerPresent: !!manager, managerVersion: manager?.version || 'missing',
      activeKey: manager?.activeKey || 'none', activeLayer: manager?.activeLayer || active?.activeLayer || 'none',
      activeRenderer: active?.constructor?.name || 'none', activeScene: !!active?.scene,
      activeCamera: !!active?.camera, deepRenderer: !!manager?.deepRenderer,
      managerSetSpatialTarget: typeof manager?.setSpatialTarget === 'function',
      managerRender: typeof manager?.render === 'function'
    };
    const detail = [
      `path=${diagnostics.path}`, `level=${diagnostics.level}`, `target=${diagnostics.target}`,
      `spatialEvidenceTarget=${diagnostics.evidenceTarget}`, `selectedSpatialNode=${diagnostics.selectedTarget}`,
      `children=${actualLabels.length ? actualLabels.join(' | ') : '(none)'}`,
      `manager=${diagnostics.managerPresent ? 'present' : 'MISSING'}`,
      `manager.version=${diagnostics.managerVersion}`, `manager.activeKey=${diagnostics.activeKey}`,
      `manager.activeLayer=${diagnostics.activeLayer}`, `active.scene=${diagnostics.activeScene ? 'yes' : 'NO'}`,
      `active.camera=${diagnostics.activeCamera ? 'yes' : 'NO'}`, `deepRenderer=${diagnostics.deepRenderer ? 'present' : 'missing'}`,
      `setSpatialTarget=${diagnostics.managerSetSpatialTarget ? 'yes' : 'NO'}`, `render=${diagnostics.managerRender ? 'yes' : 'NO'}`
    ];
    if (fallbackRegionalField) {
      detail.push('NAVIGATION DEFECT: Hand/Macro exposes only "Regional field" instead of the 7 expected hand macro regions.');
      detail.push(`missing expected: ${missingExpected.join(' | ')}`);
    } else if (isHandMacro && missingExpected.length) {
      detail.push(`NAVIGATION WARNING: Hand/Macro children differ from expected list; missing=${missingExpected.join(' | ')}`);
    } else if (isHandMacro) {
      detail.push('NAVIGATION OK: Hand/Macro exposes all 7 expected macro regions.');
    }
    progress('navigation-diagnostics', detail.join('; '));
    window.__testhpSpatialNavigationDiagnostics = diagnostics;
    return diagnostics;
  };

  const installMutationDiagnostics = () => {
    if (diagnosticsInstalled) return;
    diagnosticsInstalled = true;
    const container = document.getElementById('spatial-children');
    if (!container) return;

    const snapshot = () => safe(readNavigation().children.map(x => x.label));
    const emitChange = (kind, extra = '') => {
      const after = snapshot();
      if (after === lastNavSnapshot && !extra) return;
      const before = lastNavSnapshot || '(unknown)';
      lastNavSnapshot = after;
      progress('NAV DOM WRITE', `kind=${kind}; before=${before}; after=${after}; ${extra} stack=${stack()}`);
      navigationDiagnostics();
    };

    lastNavSnapshot = snapshot();
    const methods = ['appendChild','prepend','insertBefore','replaceChild','removeChild','replaceChildren'];
    methods.forEach(name => {
      const original = container[name];
      if (typeof original !== 'function') return;
      container[name] = function(...args) {
        const result = original.apply(this, args);
        emitChange(name);
        return result;
      };
    });

    const observer = new MutationObserver(records => {
      const summary = records.map(record => ({
        type: record.type,
        added: record.addedNodes?.length || 0,
        removed: record.removedNodes?.length || 0,
        attribute: record.attributeName || null
      }));
      progress('NAV MUTATION OBSERVED', `records=${safe(summary)}; current=${snapshot()}`);
      navigationDiagnostics();
    });
    observer.observe(container, { childList:true, subtree:true, characterData:true, attributes:true });
    window.addEventListener('beforeunload', () => observer.disconnect(), { once:true });
  };

  const installManagerDiagnostics = manager => {
    if (!manager || manager.__testhpDiagnosticsInstalled) return;
    manager.__testhpDiagnosticsInstalled = true;
    ['render','setSpatialTarget'].forEach(name => {
      const original = manager[name];
      if (typeof original !== 'function') return;
      manager[name] = function(...args) {
        const before = readNavigation();
        progress('MANAGER CALL', `method=${name}; args=${safe(args)}; beforePath=${before.crumbs.join(' > ')}; beforeTarget=${before.target}; beforeChildren=${safe(before.children.map(x => x.label))}; stack=${stack()}`);
        const result = original.apply(this, args);
        const after = readNavigation();
        progress('MANAGER RESULT', `method=${name}; afterPath=${after.crumbs.join(' > ')}; afterTarget=${after.target}; afterChildren=${safe(after.children.map(x => x.label))}`);
        return result;
      };
    });
  };

  const managerValidationDiagnostics = manager => {
    if (!manager) return;
    const checks = {
      exists: true,
      versionExpected: manager.version === 'canonical-three-2',
      scene: !!manager.active?.scene,
      camera: !!manager.active?.camera,
      deepRenderer: !!manager.deepRenderer,
      setSpatialTarget: typeof manager.setSpatialTarget === 'function',
      render: typeof manager.render === 'function'
    };
    const failed = Object.entries(checks).filter(([, ok]) => !ok).map(([key]) => key);
    progress('MANAGER VALIDATION', `checks=${safe(checks)}; failed=${failed.length ? failed.join(' | ') : '(none)'}; version=${manager.version || 'missing'}; activeKey=${manager.activeKey || 'none'}; activeLayer=${manager.activeLayer || manager.active?.activeLayer || 'none'}; activeType=${manager.active?.constructor?.name || 'none'}`);
    if (failed.length) progress('MANAGER REJECTION REASON', `failed=${failed.join(' | ')}; expected=version canonical-three-2 + active.scene + active.camera + deepRenderer`);
  };

  const hideLoading = (message = 'Digital Twin ready') => {
    loading.hidden = true;
    loading.setAttribute('aria-hidden', 'true');
    loading.style.display = 'none';
    loading.classList.remove('viewer-loading-error');
    if (status && (!status.textContent || /starting|building/i.test(status.textContent))) status.textContent = message;
    window.__testhpTwinReady = true;
    window.dispatchEvent(new CustomEvent('testhp:twin-ready', { detail: { width: canvas.width, height: canvas.height, renderer: 'WebGL' } }));
  };

  const showFailure = message => {
    loading.hidden = false;
    loading.style.display = 'grid';
    loading.textContent = message;
    loading.classList.add('viewer-loading-error');
    if (status) status.textContent = 'Twin Viewport error';
    window.dispatchEvent(new CustomEvent('testhp:twin-error', { detail: { error: new Error(message) } }));
  };

  const report = () => {
    try {
      progress('canvas-check');
      if (!canvas.isConnected) throw new Error('Twin canvas is not connected to the DOM');
      installMutationDiagnostics();
      navigationDiagnostics();
      progress('manager-check');
      const manager = window.spatialViewportManager;
      if (!manager) { progress('MANAGER MISSING', 'window.spatialViewportManager is not available'); return false; }
      installManagerDiagnostics(manager);
      installCanonicalRendererGuard(manager);
      managerValidationDiagnostics(manager);
      if (!isCanonical(manager)) {
        progress('manager-rejected', `version=${manager.version || 'unknown'}; waiting for canonical-three-2`);
        return false;
      }
      progress('webgl-check');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) {
        showFailure('3D rendering is unavailable. Check WebGL support in the browser.');
        return true;
      }
      progress('ready');
      hideLoading();
      return true;
    } catch (error) {
      console.error('[Twin Viewport] bootstrap failed', error);
      progress('BOOTSTRAP EXCEPTION', `${error?.message || error}; stack=${error?.stack || 'none'}`);
      showFailure(`Twin Viewport initialization failed: ${error?.message || error}`);
      return true;
    }
  };

  window.addEventListener('error', event => { if (event?.message) progress('WINDOW ERROR', `${event.message} | ${event.filename || ''}:${event.lineno || ''}`); });
  window.addEventListener('unhandledrejection', event => progress('UNHANDLED PROMISE', String(event.reason?.stack || event.reason || 'unknown')));
  window.addEventListener('testhp:viewport-manager-ready', () => report());
  window.addEventListener('testhp:twin-error', event => console.error('[Twin Viewport]', event.detail));
  window.addEventListener('testhp:spatial-layer-changed', event => progress('SPATIAL LAYER CHANGED', JSON.stringify(event.detail || {})));
  window.addEventListener('testhp:spatial-target-changed', event => progress('SPATIAL TARGET CHANGED', JSON.stringify(event.detail || {})));

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    const done = report();
    if (done || attempts >= 40) {
      clearInterval(timer);
      if (!done && !window.__testhpTwinReady) showFailure('Twin Viewport initialization timed out after 10 seconds. Open DEBUG for diagnostics.');
    }
  }, 250);

  window.addEventListener('beforeunload', () => clearInterval(timer), { once: true });
})();
