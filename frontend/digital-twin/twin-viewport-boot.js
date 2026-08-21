(() => {
  const loading = document.getElementById('viewer-loading');
  const canvas = document.getElementById('twin-canvas');
  const viewport = document.getElementById('twin-viewport');
  const status = document.getElementById('twin-status');
  if (!loading || !canvas || !viewport) return;

  // app.js is the sole owner of the canonical Three.js renderer. This boot
  // module only verifies readiness; it must never call render() or dispatch
  // synthetic resize events because both can recursively trigger renderer
  // observers during startup.
  const progress = (step, detail = '') => window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step, detail } }));
  const isCanonical = manager => !!(manager && manager.version === 'canonical-three-1' && manager.active?.scene && manager.active?.camera && manager.deepRenderer);

  const navigationDiagnostics = () => {
    const crumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(el => el.textContent.trim()).filter(Boolean);
    const node = document.getElementById('spatial-node');
    const children = [...document.querySelectorAll('#spatial-children .spatial-target')].map(el => ({
      label: el.querySelector('strong')?.textContent?.trim() || '(missing label)',
      meta: el.querySelector('span')?.textContent?.trim() || '(missing level)',
      disabled: !!el.disabled,
      connected: el.isConnected
    }));
    const level = document.getElementById('spatial-level-badge')?.textContent?.trim() || '?';
    const target = node?.querySelector('strong')?.textContent?.trim() || '?';
    const manager = window.spatialViewportManager;
    const active = manager?.active;
    const evidenceTarget = window.spatialEvidenceTarget || '?';
    const selectedTarget = window.selectedSpatialNode || '?';
    const expectedHandMacro = ['Śródręcze','Mały palec','Palec serdeczny','Palec środkowy','Palec wskazujący','Kciuk','Nadgarstek'];
    const actualLabels = children.map(x => x.label);
    const isHandMacro = crumbs.length === 1 && /^dłoń$/i.test(crumbs[0]) && /macro/i.test(level);
    const fallbackRegionalField = isHandMacro && actualLabels.length === 1 && /^regional field$/i.test(actualLabels[0]);
    const missingExpected = isHandMacro ? expectedHandMacro.filter(label => !actualLabels.includes(label)) : [];
    const diagnostics = {
      path: crumbs.join(' > ') || '(root)',
      level,
      target,
      evidenceTarget,
      selectedTarget,
      children: actualLabels,
      childCount: children.length,
      expectedHandMacro,
      missingExpected,
      fallbackRegionalField,
      managerPresent: !!manager,
      managerVersion: manager?.version || 'missing',
      activeKey: manager?.activeKey || 'none',
      activeLayer: manager?.activeLayer || active?.activeLayer || 'none',
      activeRenderer: active?.constructor?.name || 'none',
      activeScene: !!active?.scene,
      activeCamera: !!active?.camera,
      deepRenderer: !!manager?.deepRenderer
    };
    const detail = [
      `path=${diagnostics.path}`,
      `level=${diagnostics.level}`,
      `target=${diagnostics.target}`,
      `spatialEvidenceTarget=${diagnostics.evidenceTarget}`,
      `selectedSpatialNode=${diagnostics.selectedTarget}`,
      `children=${diagnostics.children.length ? diagnostics.children.join(' | ') : '(none)'}`,
      `manager=${diagnostics.managerPresent ? 'present' : 'MISSING'}`,
      `manager.version=${diagnostics.managerVersion}`,
      `manager.activeKey=${diagnostics.activeKey}`,
      `manager.activeLayer=${diagnostics.activeLayer}`,
      `active.scene=${diagnostics.activeScene ? 'yes' : 'NO'}`,
      `active.camera=${diagnostics.activeCamera ? 'yes' : 'NO'}`,
      `deepRenderer=${diagnostics.deepRenderer ? 'present' : 'missing'}`
    ];
    if (fallbackRegionalField) {
      detail.push('NAVIGATION DEFECT: Hand/Macro exposes only "Regional field" instead of the 7 expected hand macro regions.');
      detail.push(`missing expected: ${missingExpected.join(' | ')}`);
      detail.push('Likely source: macro child-target generation for the root hand node, not the 3D renderer.');
    } else if (isHandMacro && missingExpected.length) {
      detail.push(`NAVIGATION WARNING: Hand/Macro children differ from expected list; missing=${missingExpected.join(' | ')}`);
    } else if (isHandMacro) {
      detail.push('NAVIGATION OK: Hand/Macro exposes all 7 expected macro regions.');
    }
    progress('navigation-diagnostics', detail.join('; '));
    window.__testhpSpatialNavigationDiagnostics = diagnostics;
    return diagnostics;
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
      navigationDiagnostics();
      progress('manager-check');
      const manager = window.spatialViewportManager;
      if (!manager) return false;
      if (!isCanonical(manager)) {
        progress('manager-rejected', `version=${manager.version || 'unknown'}; waiting for canonical-three-1`);
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