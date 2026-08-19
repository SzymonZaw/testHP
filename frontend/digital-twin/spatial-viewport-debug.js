(() => {
  const boot = () => {
    const viewport = document.getElementById('twin-viewport');
    const canvas = document.getElementById('twin-canvas');
    if (!viewport || !canvas) return;

    // Keep diagnostics independent from the viewport stacking context. The
    // previous implementation placed the panel inside the WebGL container,
    // which could make the debug UI invisible when another layer owned the
    // viewport stacking context.
    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    host.setAttribute('aria-label', 'Twin Viewport debug');
    Object.assign(host.style, {
      position: 'fixed',
      right: '16px',
      bottom: '16px',
      left: 'auto',
      top: 'auto',
      zIndex: '2147483647',
      width: 'min(720px, calc(100vw - 32px))',
      maxWidth: 'min(720px, calc(100vw - 32px))',
      pointerEvents: 'auto',
      display: 'block'
    });
    if (!host.parentElement) document.body.appendChild(host);

    let panel = document.getElementById('twin-debug-panel');
    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.id = 'twin-debug-toggle';
      toggle.type = 'button';
      toggle.textContent = 'TWIN VIEWPORT DEBUG';
      host.appendChild(toggle);
    }
    Object.assign(toggle.style, {
      display: 'block', padding: '8px 12px', borderRadius: '8px',
      border: '1px solid #4b746b', background: '#0b1514', color: '#9bd8c4',
      font: '800 11px ui-monospace,SFMono-Regular,Consolas,monospace',
      cursor: 'pointer', boxShadow: '0 8px 24px rgba(0,0,0,.45)'
    });

    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'twin-debug-panel';
      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap">
          <strong>TWIN VIEWPORT · DEBUG</strong>
          <div><button id="twin-debug-refresh" type="button">REFRESH</button><button id="twin-debug-clear" type="button">CLEAR</button><button id="twin-debug-close" type="button">MINIMIZE</button></div>
        </div>
        <pre id="twin-debug-runtime"></pre>
        <pre id="twin-debug-state"></pre>
        <pre id="twin-debug-log"></pre>`;
      host.appendChild(panel);
    }
    Object.assign(panel.style, {
      display: 'block', marginTop: '6px', width: '100%', maxHeight: '430px',
      overflow: 'auto', padding: '12px', boxSizing: 'border-box',
      borderRadius: '10px', background: 'rgba(5,12,13,.98)',
      border: '1px solid #4b746b', boxShadow: '0 12px 35px rgba(0,0,0,.55)',
      color: '#dcece6', font: '11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace'
    });

    const refresh = document.getElementById('twin-debug-refresh');
    const clear = document.getElementById('twin-debug-clear');
    const close = document.getElementById('twin-debug-close');
    const runtime = document.getElementById('twin-debug-runtime');
    const state = document.getElementById('twin-debug-state');
    const log = document.getElementById('twin-debug-log');
    if (!runtime || !state || !log) return;

    const lines = [];
    const MAX = 200;
    let initStarted = Date.now();
    let lastTick = 0;
    let lastProgress = 'debug panel initialized';
    let minimized = false;
    const now = () => new Date().toLocaleTimeString();
    const writeLog = message => {
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
      return { manager: !!m, level: badge?.textContent?.trim() || '?', target: node?.querySelector('strong')?.textContent?.trim() || '?', targetId: window.spatialEvidenceTarget || m?.activeKey || '?', path: crumbs.join(' > ') || '(root)', children: children.join(' | ') || '(none)', renderer: m?.active?.constructor?.name || 'none', key: m?.activeKey || 'none' };
    };
    const rendererInfo = () => {
      const m = window.spatialViewportManager, a = m?.active, camera = a?.camera;
      let three = 'module-scoped / not global';
      try { if (window.THREE?.REVISION) three = window.THREE.REVISION; } catch (_) {}
      return { manager: m ? 'present' : 'MISSING', active: a?.constructor?.name || 'none', deep: m?.deepRenderer ? 'present' : 'missing', three, scene: a?.scene?.children?.length ?? '—', root: a?.root?.children?.length ?? '—', clickable: a?.clickable?.length ?? '—', camera: camera ? `z=${Number(camera.position.z).toFixed(2)} aspect=${Number(camera.aspect).toFixed(3)}` : '—' };
    };
    const runtimeInfo = () => {
      const rect = viewport.getBoundingClientRect();
      const cr = canvas.getBoundingClientRect();
      let graphics = 'MISSING';
      try { graphics = canvas.getContext('webgl2') ? 'WebGL2' : canvas.getContext('webgl') ? 'WebGL' : 'NONE'; } catch (e) { graphics = `ERROR: ${e.message}`; }
      return { viewport: `${Math.round(rect.width)}×${Math.round(rect.height)}`, canvas: `${Math.round(cr.width)}×${Math.round(cr.height)} (${canvas.width}×${canvas.height})`, display: getComputedStyle(canvas).display, visibility: getComputedStyle(canvas).visibility, opacity: getComputedStyle(canvas).opacity, graphics, manager: window.spatialViewportManager ? 'present' : 'MISSING', heartbeat: lastTick ? `${Date.now() - lastTick} ms ago` : 'not observed', initAge: `${Date.now() - initStarted} ms`, ready: window.__testhpTwinReady ? 'YES' : 'NO', lastProgress };
    };
    const render = () => {
      const v = runtimeInfo(), s = spatial(), r = rendererInfo();
      runtime.textContent = ['RUNTIME', `status:       ${v.ready === 'YES' ? 'READY' : Date.now() - initStarted > 5000 ? 'INIT TIMEOUT' : 'INITIALIZING'}`, `viewport:     ${v.viewport}`, `canvas:       ${v.canvas}`, `display:      ${v.display}`, `visibility:   ${v.visibility}`, `opacity:      ${v.opacity}`, `graphics:     ${v.graphics}`, `manager:      ${v.manager}`, `heartbeat:    ${v.heartbeat}`, `init age:     ${v.initAge}`, `ready:        ${v.ready}`, `last progress:${v.lastProgress}`].join('\n');
      state.textContent = ['', 'SPATIAL STATE', `level:        ${s.level}`, `target:       ${s.target}`, `spatial_id:   ${s.targetId}`, `path:         ${s.path}`, `children:     ${s.children}`, `renderer:     ${s.renderer}`, `active_key:   ${s.key}`, '', 'RENDERER', `manager:      ${r.manager}`, `active:       ${r.active}`, `deep:         ${r.deep}`, `three:        ${r.three}`, `scene:        ${r.scene}`, `root:         ${r.root}`, `clickable:    ${r.clickable}`, `camera:       ${r.camera}`].join('\n');
    };
    const event = message => { lastProgress = message; writeLog(message); if (!minimized) render(); };

    toggle.onclick = () => { minimized = false; panel.style.display = 'block'; toggle.style.display = 'block'; render(); };
    if (close) close.onclick = () => { minimized = true; panel.style.display = 'none'; };
    if (refresh) refresh.onclick = () => { event('manual refresh'); try { window.spatialViewportManager?.render?.(); } catch (e) { event(`manual render ERROR | ${e?.stack || e}`); } };
    if (clear) clear.onclick = () => { lines.length = 0; event('log cleared'); };

    window.addEventListener('error', e => event(`WINDOW ERROR | ${e.message || 'unknown'} | ${e.filename || ''}:${e.lineno || ''}`));
    window.addEventListener('unhandledrejection', e => event(`UNHANDLED PROMISE | ${e.reason?.stack || e.reason || 'unknown'}`));
    window.addEventListener('testhp:twin-ready', e => { window.__testhpTwinReady = true; event(`TWIN READY | ${JSON.stringify(e.detail || {})}`); });
    window.addEventListener('testhp:twin-error', e => event(`TWIN ERROR | ${e.detail?.error?.stack || e.detail?.error || 'unknown'}`));
    window.addEventListener('testhp:twin-progress', e => event(`INIT | ${e.detail?.step || e.detail?.message || 'progress'}`));
    window.addEventListener('resize', () => event('viewport/window resize observed'), { passive: true });
    ['pointerdown','pointerup','click','wheel'].forEach(type => canvas.addEventListener(type, () => event(`canvas ${type}`), { passive: type === 'wheel' }));

    const observer = new MutationObserver(() => event('spatial navigation DOM mutation detected'));
    ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id => { const el = document.getElementById(id); if (el) observer.observe(el, { childList: true, subtree: true, characterData: true }); });

    // Always expose the debug object, even if the canonical manager has not
    // initialized yet. This makes loader/order failures visible instead of
    // leaving a blank viewport with no diagnostics.
    window.__testhpTwinDebug = { refresh: render, log: writeLog, viewport, canvas };
    event('Twin Viewport debug initialized');
    render();

    const timer = setInterval(() => {
      lastTick = Date.now();
      if (!minimized) render();
    }, 500);
    window.addEventListener('beforeunload', () => { clearInterval(timer); observer.disconnect(); }, { once: true });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();