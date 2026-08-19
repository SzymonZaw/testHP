(() => {
  const boot = () => {
    const viewport = document.getElementById('twin-viewport');
    const canvas = document.getElementById('twin-canvas');
    if (!viewport || !canvas) return;

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    host.setAttribute('aria-label', 'Twin Viewport debug');
    Object.assign(host.style, {
      position: 'fixed', right: '16px', bottom: '16px', left: 'auto', top: 'auto',
      zIndex: '2147483647', width: 'min(820px, calc(100vw - 32px))',
      maxWidth: 'min(820px, calc(100vw - 32px))', pointerEvents: 'auto', display: 'block'
    });
    if (host.parentElement !== document.body) document.body.appendChild(host);

    let panel = document.getElementById('twin-debug-panel');
    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.id = 'twin-debug-toggle';
      toggle.type = 'button';
      toggle.textContent = 'TWIN VIEWPORT DEBUG';
      host.appendChild(toggle);
    }
    Object.assign(toggle.style, { display: 'block', padding: '8px 12px', borderRadius: '8px', border: '1px solid #4b746b', background: '#0b1514', color: '#9bd8c4', font: '800 11px ui-monospace,SFMono-Regular,Consolas,monospace', cursor: 'pointer', boxShadow: '0 8px 24px rgba(0,0,0,.45)' });

    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'twin-debug-panel';
      panel.innerHTML = `<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap"><strong>TWIN VIEWPORT · DEBUG</strong><div><button id="twin-debug-refresh" type="button">REFRESH</button><button id="twin-debug-clear" type="button">CLEAR</button><button id="twin-debug-close" type="button">MINIMIZE</button></div></div><pre id="twin-debug-runtime"></pre><pre id="twin-debug-state"></pre><pre id="twin-debug-display"></pre><pre id="twin-debug-interaction"></pre><pre id="twin-debug-log"></pre>`;
      host.appendChild(panel);
    }
    Object.assign(panel.style, { display: 'block', marginTop: '6px', width: '100%', maxHeight: '620px', overflow: 'auto', padding: '12px', boxSizing: 'border-box', borderRadius: '10px', background: 'rgba(5,12,13,.98)', border: '1px solid #4b746b', boxShadow: '0 12px 35px rgba(0,0,0,.55)', color: '#dcece6', font: '11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace' });

    const refresh = document.getElementById('twin-debug-refresh');
    const clear = document.getElementById('twin-debug-clear');
    const close = document.getElementById('twin-debug-close');
    const runtime = document.getElementById('twin-debug-runtime');
    const state = document.getElementById('twin-debug-state');
    const display = document.getElementById('twin-debug-display');
    const interaction = document.getElementById('twin-debug-interaction');
    const log = document.getElementById('twin-debug-log');
    if (!runtime || !state || !display || !interaction || !log) return;

    const lines = [];
    let initStarted = Date.now();
    let lastTick = 0;
    let lastProgress = 'debug panel initialized';
    let minimized = false;
    let lastSpatialSnapshot = null;
    let lastInteraction = null;
    const now = () => new Date().toLocaleTimeString();
    const writeLog = message => { lines.push(`[${now()}] ${message}`); while (lines.length > 250) lines.shift(); log.textContent = lines.join('\n'); log.scrollTop = log.scrollHeight; };

    const domText = id => document.getElementById(id)?.textContent?.trim() || '';
    const spatial = () => {
      const m = window.spatialViewportManager;
      const badge = document.getElementById('spatial-level-badge');
      const node = document.getElementById('spatial-node');
      const crumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
      const children = [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(x => x.textContent.trim()).filter(Boolean);
      const level = badge?.textContent?.trim() || '?';
      const target = node?.querySelector('strong')?.textContent?.trim() || '?';
      const targetId = window.spatialEvidenceTarget || m?.activeKey || '?';
      return {
        manager: !!m,
        level,
        target,
        targetId,
        path: crumbs.join(' > ') || '(root)',
        children: children.join(' | ') || '(none)',
        renderer: m?.active?.constructor?.name || 'none',
        key: m?.activeKey || 'none',
        nodeText: node?.textContent?.trim().replace(/\s+/g, ' ') || '(none)'
      };
    };

    const objectLabel = obj => {
      if (!obj) return 'none';
      const ud = obj.userData || {};
      return [obj.name && `name=${obj.name}`, ud.spatialId && `spatialId=${ud.spatialId}`, ud.targetId && `targetId=${ud.targetId}`, ud.spatialKey && `spatialKey=${ud.spatialKey}`, ud.layer && `layer=${ud.layer}`, ud.label && `label=${ud.label}`].filter(Boolean).join(' | ') || obj.type || 'Object3D';
    };

    const rendererInfo = () => {
      const m = window.spatialViewportManager, a = m?.active, camera = a?.camera;
      let three = 'module-scoped / not global';
      try { if (window.THREE?.REVISION) three = window.THREE.REVISION; } catch (_) {}
      const clickable = Array.isArray(a?.clickable) ? a.clickable : [];
      const clickablePreview = clickable.slice(0, 12).map(objectLabel);
      const sceneChildren = a?.scene?.children || [];
      return {
        manager: m ? 'present' : 'MISSING', active: a?.constructor?.name || 'none', deep: m?.deepRenderer ? 'present' : 'missing', three,
        scene: a?.scene?.children?.length ?? '—', root: a?.root?.children?.length ?? '—', clickable: clickable.length || '—',
        clickablePreview: clickablePreview.join(' || ') || '(none)',
        scenePreview: sceneChildren.slice(0, 12).map(objectLabel).join(' || ') || '(none)',
        camera: camera ? `z=${Number(camera.position.z).toFixed(2)} aspect=${Number(camera.aspect).toFixed(3)} pos=${Number(camera.position.x).toFixed(2)},${Number(camera.position.y).toFixed(2)},${Number(camera.position.z).toFixed(2)}` : '—'
      };
    };

    const runtimeInfo = () => {
      const rect = viewport.getBoundingClientRect(), cr = canvas.getBoundingClientRect(); let graphics = 'MISSING';
      try { graphics = canvas.getContext('webgl2') ? 'WebGL2' : canvas.getContext('webgl') ? 'WebGL' : 'NONE'; } catch (e) { graphics = `ERROR: ${e.message}`; }
      return { viewport: `${Math.round(rect.width)}×${Math.round(rect.height)}`, canvas: `${Math.round(cr.width)}×${Math.round(cr.height)} (${canvas.width}×${canvas.height})`, display: getComputedStyle(canvas).display, visibility: getComputedStyle(canvas).visibility, opacity: getComputedStyle(canvas).opacity, graphics, manager: window.spatialViewportManager ? 'present' : 'MISSING', heartbeat: lastTick ? `${Date.now() - lastTick} ms ago` : 'not observed', initAge: `${Date.now() - initStarted} ms`, ready: window.__testhpTwinReady ? 'YES' : 'NO', lastProgress };
    };

    const render = () => {
      const v = runtimeInfo(), s = spatial(), r = rendererInfo();
      runtime.textContent = ['RUNTIME', `status:       ${v.ready === 'YES' ? 'READY' : Date.now() - initStarted > 10000 ? 'INIT TIMEOUT' : 'INITIALIZING'}`, `viewport:     ${v.viewport}`, `canvas:       ${v.canvas}`, `display:      ${v.display}`, `visibility:   ${v.visibility}`, `opacity:      ${v.opacity}`, `graphics:     ${v.graphics}`, `manager:      ${v.manager}`, `heartbeat:    ${v.heartbeat}`, `init age:     ${v.initAge}`, `ready:        ${v.ready}`, `last progress:${v.lastProgress}`].join('\n');
      state.textContent = ['', 'SPATIAL STATE', `level:        ${s.level}`, `target:       ${s.target}`, `spatial_id:   ${s.targetId}`, `path:         ${s.path}`, `children:     ${s.children}`, `renderer:     ${s.renderer}`, `active_key:   ${s.key}`].join('\n');
      state.textContent += `\nnode:         ${s.nodeText}`;
      state.textContent += `\nlayer chain:  ${s.path} > ${s.target}`;
      state.textContent += `\nnext layer:   ${s.children}`;
      state.textContent += `\n\nRENDERER\n${[`manager:      ${r.manager}`, `active:       ${r.active}`, `deep:         ${r.deep}`, `three:        ${r.three}`, `scene:        ${r.scene}`, `root:         ${r.root}`, `clickable:    ${r.clickable}`, `camera:       ${r.camera}`].join('\n')}`;
      display.textContent = ['', 'DISPLAYED VISUALIZATION', `layer:        ${s.level}`, `target:       ${s.target}`, `spatial_id:   ${s.targetId}`, `renderer:     ${r.active}`, `scene objects: ${r.scene}`, `root objects:  ${r.root}`, `clickable:     ${r.clickable}`, `visualization: ${r.deep === 'present' ? 'deep renderer available' : 'deep renderer missing'}`, `evidence link: ${window.spatialEvidenceTarget || 'none'}`, `visible DOM:   ${canvas.getAttribute('aria-label') || 'canvas'}`].join('\n');
      interaction.textContent = ['', 'LAST INTERACTION', lastInteraction ? [`type:         ${lastInteraction.type}`, `source:       ${lastInteraction.source}`, `time:         ${lastInteraction.time}`, `coordinates:  client=${lastInteraction.clientX},${lastInteraction.clientY} local=${lastInteraction.localX},${lastInteraction.localY}`, `ndc:          ${lastInteraction.ndcX},${lastInteraction.ndcY}`, `before:       ${lastInteraction.before}`, `after:        ${lastInteraction.after}`, `hit:          ${lastInteraction.hit}`, `navigation:   ${lastInteraction.navigation}`].join('\n') : 'No canvas/DOM interaction captured yet.'].join('\n');
    };

    const snapshot = () => JSON.stringify(spatial());
    const event = message => { lastProgress = message; writeLog(message); if (!minimized) render(); };

    toggle.onclick = () => { minimized = false; panel.style.display = 'block'; render(); };
    if (close) close.onclick = () => { minimized = true; panel.style.display = 'none'; };
    if (refresh) refresh.onclick = () => { event('manual refresh'); try { window.spatialViewportManager?.render?.(); } catch (e) { event(`manual render ERROR | ${e?.stack || e}`); } };
    if (clear) clear.onclick = () => { lines.length = 0; event('log cleared'); };

    window.addEventListener('error', e => event(`WINDOW ERROR | ${e.message || 'unknown'} | ${e.filename || ''}:${e.lineno || ''}`));
    window.addEventListener('unhandledrejection', e => event(`UNHANDLED PROMISE | ${e.reason?.stack || e.reason || 'unknown'}`));
    window.addEventListener('testhp:twin-ready', e => { window.__testhpTwinReady = true; event(`TWIN READY | ${JSON.stringify(e.detail || {})}`); });
    window.addEventListener('testhp:twin-error', e => event(`TWIN ERROR | ${e.detail?.error?.stack || e.detail?.error || 'unknown'}`));
    window.addEventListener('testhp:twin-progress', e => event(`INIT | ${e.detail?.step || e.detail?.message || 'progress'}`));
    window.addEventListener('testhp:viewport-rendered', e => event(`VIEW RENDERED | ${JSON.stringify(e.detail || {})}`));
    window.addEventListener('resize', () => event('viewport/window resize observed'), { passive: true });

    const capture = (type, e) => {
      const before = spatial();
      const rect = canvas.getBoundingClientRect();
      const localX = e.clientX - rect.left, localY = e.clientY - rect.top;
      const ndcX = ((localX / rect.width) * 2 - 1).toFixed(3);
      const ndcY = (-((localY / rect.height) * 2 - 1)).toFixed(3);
      let hit = 'raycast unavailable (Three.js module-scoped)';
      const clickable = window.spatialViewportManager?.active?.clickable;
      if (Array.isArray(clickable) && clickable.length) hit = `clickable pool=${clickable.length}; direct object metadata unavailable`;
      lastInteraction = { type, source: 'Twin Viewport canvas', time: now(), clientX: Math.round(e.clientX), clientY: Math.round(e.clientY), localX: Math.round(localX), localY: Math.round(localY), ndcX, ndcY, before: `${before.level} / ${before.target} / ${before.targetId}`, after: `${spatial().level} / ${spatial().target} / ${spatial().targetId}`, hit, navigation: 'pending DOM/viewport mutation check' };
      event(`canvas ${type} | layer=${before.level} | target=${before.target} | id=${before.targetId} | local=${Math.round(localX)},${Math.round(localY)} | ndc=${ndcX},${ndcY}`);
      setTimeout(() => {
        const after = spatial();
        const changed = snapshot() !== JSON.stringify(before);
        if (lastInteraction && lastInteraction.time === now()) return;
        if (lastInteraction) { lastInteraction.after = `${after.level} / ${after.target} / ${after.targetId}`; lastInteraction.navigation = changed ? 'YES — spatial target/layer changed' : 'NO — same spatial target/layer'; }
        event(`canvas ${type} RESULT | ${before.target} -> ${after.target} | navigation=${changed ? 'YES' : 'NO'}`);
      }, 80);
    };

    ['pointerdown','pointerup','click'].forEach(type => canvas.addEventListener(type, e => capture(type, e), { passive: true }));
    canvas.addEventListener('wheel', e => event(`canvas wheel | layer=${spatial().level} | target=${spatial().target} | deltaY=${Math.round(e.deltaY)}`), { passive: true });

    const observer = new MutationObserver(() => {
      const before = lastSpatialSnapshot;
      const after = snapshot();
      if (before && before !== after) {
        const s = spatial();
        event(`SPATIAL CHANGE | layer=${s.level} | target=${s.target} | id=${s.targetId} | path=${s.path} | children=${s.children}`);
        if (lastInteraction) lastInteraction.navigation = `YES — DOM navigation mutation: ${s.path}`;
      } else event('spatial navigation DOM mutation detected');
      lastSpatialSnapshot = after;
    });
    ['spatial-level-badge','spatial-breadcrumb','spatial-node','spatial-children'].forEach(id => { const el = document.getElementById(id); if (el) observer.observe(el, { childList: true, subtree: true, characterData: true }); });

    window.__testhpTwinDebug = { refresh: render, log: writeLog, viewport, canvas };
    lastSpatialSnapshot = snapshot();
    event('Twin Viewport debug initialized'); render();
    const timer = setInterval(() => { lastTick = Date.now(); if (!minimized) render(); }, 500);
    window.addEventListener('beforeunload', () => { clearInterval(timer); observer.disconnect(); }, { once: true });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();