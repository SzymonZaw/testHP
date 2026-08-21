(() => {
  const boot = () => {
    const canvas = document.getElementById('twin-canvas');
    if (!canvas) return;

    let minimized = true;
    let started = Date.now();
    let lastError = null;
    let lastNavigation = null;
    let lastInteraction = null;

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    if (host.parentElement !== document.body) document.body.appendChild(host);
    Object.assign(host.style, {
      position: 'fixed', right: '16px', bottom: '16px', zIndex: '2147483647',
      width: 'min(420px,calc(100vw - 32px))', pointerEvents: 'auto', isolation: 'isolate'
    });

    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.id = 'twin-debug-toggle';
      toggle.type = 'button';
      host.appendChild(toggle);
    }
    Object.assign(toggle.style, {
      display: 'block', padding: '8px 12px', borderRadius: '8px',
      border: '1px solid #4b746b', background: '#0b1514', color: '#9bd8c4',
      font: '800 11px ui-monospace,SFMono-Regular,Consolas,monospace',
      cursor: 'pointer', pointerEvents: 'auto'
    });

    let panel = document.getElementById('twin-debug-panel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'twin-debug-panel';
      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
          <strong>TWIN VIEWPORT · DEBUG</strong>
          <button id="twin-debug-close" type="button">MINIMIZE</button>
        </div>
        <pre id="twin-debug-runtime"></pre>
        <pre id="twin-debug-state"></pre>
        <pre id="twin-debug-errors"></pre>`;
      host.appendChild(panel);
    }
    Object.assign(panel.style, {
      display: 'none', marginTop: '6px', maxHeight: '500px', overflow: 'auto',
      padding: '12px', boxSizing: 'border-box', borderRadius: '10px',
      background: 'rgba(5,12,13,.98)', border: '1px solid #4b746b',
      boxShadow: '0 12px 35px rgba(0,0,0,.55)', color: '#dcece6',
      font: '11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',
      pointerEvents: 'auto'
    });

    const runtime = document.getElementById('twin-debug-runtime');
    const state = document.getElementById('twin-debug-state');
    const errors = document.getElementById('twin-debug-errors');
    if (!runtime || !state || !errors) return;

    const readState = () => {
      const manager = window.spatialViewportManager;
      const node = document.getElementById('spatial-node');
      const badge = document.getElementById('spatial-level-badge');
      const breadcrumb = [...document.querySelectorAll('#spatial-breadcrumb button')]
        .map(x => x.textContent.trim()).filter(Boolean);
      const children = [...document.querySelectorAll('#spatial-children .spatial-target')]
        .map(x => x.querySelector('strong')?.textContent?.trim() || x.textContent.trim());
      return {
        manager: !!manager,
        level: badge?.textContent?.trim() || '?',
        target: node?.querySelector('strong')?.textContent?.trim() || '?',
        path: breadcrumb.join(' > ') || '(root)',
        children,
        renderer: manager?.active?.constructor?.name || 'none',
        activeKey: manager?.activeKey || 'none'
      };
    };

    const render = () => {
      if (minimized) return;
      const s = readState();
      runtime.textContent = [
        'RUNTIME',
        `status:       ${window.__testhpTwinReady ? 'READY' : 'INITIALIZING'}`,
        `init age:     ${Date.now() - started} ms`,
        `manager:      ${s.manager ? 'present' : 'missing'}`,
        `canvas:       ${canvas.width}×${canvas.height}`
      ].join('\n');
      state.textContent = [
        '', 'SPATIAL STATE',
        `level:        ${s.level}`,
        `target:       ${s.target}`,
        `path:         ${s.path}`,
        `children:     ${s.children.join(' | ') || '(none)'}`,
        `renderer:     ${s.renderer}`,
        `active key:   ${s.activeKey}`,
        '', 'LAST EVENT',
        lastNavigation ? JSON.stringify(lastNavigation, null, 2) : '(none)'
      ].join('\n');
      errors.textContent = [
        '', 'ERROR / INTERACTION',
        `last error:   ${lastError || '(none)'}`,
        `last input:   ${lastInteraction ? JSON.stringify(lastInteraction) : '(none)'}`
      ].join('\n');
    };

    window.addEventListener('error', e => {
      lastError = `${e.message || 'unknown'} | ${e.filename || ''}:${e.lineno || ''}`;
    });
    window.addEventListener('unhandledrejection', e => {
      lastError = String(e.reason?.stack || e.reason || 'Unhandled promise rejection');
    });
    window.addEventListener('testhp:twin-error', e => { lastError = JSON.stringify(e.detail || {}); });
    window.addEventListener('testhp:spatial-layer-changed', e => { lastNavigation = e.detail || {}; });
    window.addEventListener('testhp:viewport-rendered', e => { lastNavigation = e.detail || {}; });

    canvas.addEventListener('click', e => {
      lastInteraction = { type: 'canvas click', x: Math.round(e.clientX), y: Math.round(e.clientY) };
    }, { passive: true });

    const setMinimized = value => {
      minimized = value;
      panel.style.display = minimized ? 'none' : 'block';
      toggle.textContent = minimized ? 'TWIN VIEWPORT DEBUG · ROZWIŃ' : 'TWIN VIEWPORT DEBUG · ZWIŃ';
      if (!minimized) render();
    };

    toggle.onclick = () => setMinimized(!minimized);
    document.getElementById('twin-debug-close')?.addEventListener('click', () => setMinimized(true));
    setMinimized(true);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
