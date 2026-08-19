(() => {
  const viewport = document.getElementById('twin-viewport');
  const host = document.getElementById('twin-viewport-debug-host');
  if (!viewport || !host) return;

  const panel = document.getElementById('twin-debug-panel');
  const toggle = document.getElementById('twin-debug-toggle');
  const refresh = document.getElementById('twin-debug-refresh');
  const clear = document.getElementById('twin-debug-clear');
  const close = document.getElementById('twin-debug-close');
  const runtime = document.getElementById('twin-debug-runtime');
  const state = document.getElementById('twin-debug-state');
  const log = document.getElementById('twin-debug-log');
  if (!panel || !toggle || !runtime || !state || !log) return;

  const lines = [];
  const MAX = 160;
  let wrapped = false;
  let ticks = 0;
  let lastTick = 0;
  let initStarted = Date.now();
  let lastProgress = 'debug panel initialized';

  const now = () => new Date().toLocaleTimeString();
  const writeLog = (message) => {
    lines.push(`[${now()}] ${message}`);
    while (lines.length > MAX) lines.shift();
    log.textContent = lines.join('\n');
    log.scrollTop = log.scrollHeight;
  };

  const spatial = () => {
    const m = window.spatialViewportManager;
    const badge = document.getElementById('spatial-level-badge');
    const node = document.getElementById('spatial-node');
    const crumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
    const children = [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);
    return {
      manager: !!m,
      level: badge?.textContent?.trim() || '?',
      target: node?.querySelector('strong')?.textContent?.trim() || '?',
      targetId: window.spatialEvidenceTarget || m?.activeKey || '?',
      path: crumbs.join(' > ') || '(root)',
      children: children.join(' | ') || '(none)',
      renderer: m?.active?.constructor?.name || 'none',
      key: m?.activeKey || 'none'
    };
  };

  const rendererInfo = () => {
    const m = window.spatialViewportManager;
    const a = m?.active;
    const camera = a?.camera;
    let three = 'not exposed';
    try { three = window.THREE?.REVISION || 'module-scoped / not global'; } catch (_) {}
    return {
      manager: m ? 'present' : 'MISSING',
      active: a?.constructor?.name || 'none',
      deep: m?.deepRenderer ? 'present' : 'missing',
      three,
      scene: a?.scene?.children?.length ?? '—',
      root: a?.root?.children?.length ?? '—',
      clickable: a?.clickable?.length ?? '—',
      camera: camera ? `z=${Number(camera.position.z).toFixed(2)} aspect=${Number(camera.aspect).toFixed(3)}` : '—'
    };
  };

  const runtimeInfo = () => {
    const canvas = document.getElementById('twin-canvas');
    const rect = viewport.getBoundingClientRect();
    const cr = canvas?.getBoundingClientRect();
    let graphics = 'MISSING';
    try { graphics = canvas?.getContext('webgl2') ? 'WebGL2' : canvas?.getContext('webgl') ? 'WebGL' : 'NONE'; } catch (e) { graphics = `ERROR: ${e.message}`; }
    const age = Date.now() - initStarted;
    return {
      viewport: `${Math.round(rect.width)}×${Math.round(rect.height)}`,
      canvas: canvas ? `${Math.round(cr.width)}×${Math.round(cr.height)} (${canvas.width}×${canvas.height})` : 'MISSING',
      display: canvas ? getComputedStyle(canvas).display : 'MISSING',
      visibility: canvas ? getComputedStyle(canvas).visibility : 'MISSING',
      graphics,
      manager: window.spatialViewportManager ? 'present' : 'MISSING',
      heartbeat: lastTick ? `${Date.now() - lastTick} ms ago` : 'not observed',
      initAge: `${age} ms`,
      lastProgress
    };
  };

  const render = () => {
    const s = spatial();
    const v = runtimeInfo();
    const r = rendererInfo();
    const timeout = !window.__testhpTwinReady && Date.now() - initStarted > 5000;
    runtime.textContent = [
      'RUNTIME',
      `status:       ${window.__testhpTwinReady ? 'READY' : timeout ? 'INIT TIMEOUT' : 'INITIALIZING'}`,
      `viewport:     ${v.viewport}`,
      `canvas:       ${v.canvas}`,
      `display:      ${v.display}`,
      `visibility:   ${v.visibility}`,
      `graphics:     ${v.graphics}`,
      `manager:      ${v.manager}`,
      `heartbeat:    ${v.heartbeat}`,
      `init age:     ${v.initAge}`,
      `last progress:${v.lastProgress}`
    ].join('\n');
    state.textContent = [
      '',
      'SPATIAL STATE',
      `level:        ${s.level}`,
      `target:       ${s.target}`,
      `spatial_id:   ${s.targetId}`,
      `path:         ${s.path}`,
      `children:     ${s.children}`,
      `renderer:     ${s.renderer}`,
      `active_key:   ${s.key}`,
      '',
      'RENDERER',
      `manager:      ${r.manager}`,
      `active:       ${r.active}`,
      `deep:         ${r.deep}`,
      `three:        ${r.three}`,
      `scene:        ${r.scene}`,
      `root:         ${r.root}`,
      `clickable:    ${r.clickable}`,
      `camera:       ${r.camera}`
    ].join('\n');
  };

  const event = (message) => { lastProgress = message; writeLog(message); render(); };

  const attachManager = () => {
    const m = window.spatialViewportManager;
    if (!m || wrapped) return !!m;
    if (typeof m.render === 'function') {
      const original = m.render.bind(m);
      m.render = (...args) => {
        const before = spatial();
        event(`render BEFORE | ${before.level} ${before.target} ${before.key}`);
        try {
          const result = original(...args);
          const after = spatial();
          event(`render AFTER | ${after.level} ${after.target} ${after.key}`);
          return result;
        } catch (error) {
          event(`render ERROR | ${error?.stack || error}`);
          throw error;
        }
      };
    }
    wrapped = true;
    event(`debug attached to SpatialViewportManager | renderer=${m.active?.constructor?.name || 'none'}`);
    return true;
  };

  toggle.onclick = () => { panel.hidden = false; toggle.hidden = true; render(); };
  close.onclick = () => { panel.hidden = true; toggle.hidden = false; };
  refresh.onclick = () => { event('manual refresh'); try { window.spatialViewportManager?.render?.(); } catch (e) { event(`manual render ERROR | ${e?.stack || e}`); } };
  clear.onclick = () => { lines.length = 0; event('log cleared'); };

  window.addEventListener('error', e => event(`WINDOW ERROR | ${e.message || 'unknown'} | ${e.filename || ''}:${e.lineno || ''}`));
  window.addEventListener('unhandledrejection', e => event(`UNHANDLED PROMISE | ${e.reason?.stack || e.reason || 'unknown'}`));
  window.addEventListener('testhp:twin-ready', e => { window.__testhpTwinReady = true; lastProgress = 'twin-ready event received'; event(`TWIN READY | ${JSON.stringify(e.detail || {})}`); });
  window.addEventListener('testhp:twin-error', e => { lastProgress = 'twin-error event received'; event(`TWIN ERROR | ${e.detail?.error?.stack || e.detail?.error || 'unknown'}`); });
  window.addEventListener('testhp:twin-progress', e => event(`INIT | ${e.detail?.step || e.detail?.message || 'progress'}`));
  window.addEventListener('resize', () => event('viewport/window resize observed'), { passive: true });

  const canvas = document.getElementById('twin-canvas');
  if (canvas) ['pointerdown','pointerup','click','wheel'].forEach(type => canvas.addEventListener(type, () => event(`canvas ${type}`), { passive: type === 'wheel' }));

  const observer = new MutationObserver(() => event('spatial navigation DOM mutation detected'));
  ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
  });

  const timer = setInterval(() => {
    ticks += 1;
    lastTick = Date.now();
    attachManager();
    if (!window.__testhpTwinReady && Date.now() - initStarted > 5000 && !window.__testhpTwinTimeoutLogged) {
      window.__testhpTwinTimeoutLogged = true;
      event('INIT TIMEOUT | Twin Viewport has not reported ready after 5s');
    }
    if (!panel.hidden) render();
  }, 500);

  window.addEventListener('beforeunload', () => { clearInterval(timer); observer.disconnect(); }, { once: true });
  event('Twin Viewport debug initialized');
})();
