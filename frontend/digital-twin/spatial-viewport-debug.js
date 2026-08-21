(() => {
  const boot = () => {
    const viewport = document.getElementById('twin-viewport');
    const canvas = document.getElementById('twin-canvas');
    if (!viewport || !canvas) return;

    const expected = ['Śródręcze','Mały palec','Palec serdeczny','Palec środkowy','Palec wskazujący','Kciuk','Nadgarstek'];
    let minimized = true;
    let started = performance.now();
    let lastProgress = 'debug initialized';
    let lastInteraction = null;
    let lastWriter = null;
    let lastMutation = null;
    let lastEventAt = 0;
    let pendingEvent = null;
    const lines = [];

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) {
      host = document.createElement('section');
      host.id = 'twin-viewport-debug-host';
      document.body.appendChild(host);
    }
    Object.assign(host.style, {
      position:'fixed', right:'16px', bottom:'16px', zIndex:'2147483647',
      width:'min(900px,calc(100vw - 32px))', maxWidth:'min(900px,calc(100vw - 32px))', pointerEvents:'auto'
    });

    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.id = 'twin-debug-toggle';
      toggle.type = 'button';
      host.appendChild(toggle);
    }
    Object.assign(toggle.style, {
      display:'block', padding:'8px 12px', borderRadius:'8px', border:'1px solid #4b746b',
      background:'#0b1514', color:'#9bd8c4', font:'800 11px ui-monospace,SFMono-Regular,Consolas,monospace', cursor:'pointer'
    });

    let panel = document.getElementById('twin-debug-panel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'twin-debug-panel';
      panel.innerHTML = '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap"><strong>TWIN VIEWPORT · DEBUG</strong><div><button id="twin-debug-refresh" type="button">REFRESH</button><button id="twin-debug-clear" type="button">CLEAR</button><button id="twin-debug-close" type="button">MINIMIZE</button></div></div><pre id="twin-debug-runtime"></pre><pre id="twin-debug-state"></pre><pre id="twin-debug-navigation"></pre><pre id="twin-debug-source"></pre><pre id="twin-debug-renderer"></pre><pre id="twin-debug-interaction"></pre><pre id="twin-debug-log"></pre>';
      host.appendChild(panel);
    }
    Object.assign(panel.style, {
      display:'none', marginTop:'6px', width:'100%', maxHeight:'760px', overflow:'auto', padding:'12px', boxSizing:'border-box',
      borderRadius:'10px', background:'rgba(5,12,13,.98)', border:'1px solid #4b746b', boxShadow:'0 12px 35px rgba(0,0,0,.55)',
      color:'#dcece6', font:'11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace'
    });

    const runtime = document.getElementById('twin-debug-runtime');
    const state = document.getElementById('twin-debug-state');
    const navigation = document.getElementById('twin-debug-navigation');
    const source = document.getElementById('twin-debug-source');
    const renderer = document.getElementById('twin-debug-renderer');
    const interaction = document.getElementById('twin-debug-interaction');
    const log = document.getElementById('twin-debug-log');
    if (!runtime || !state || !navigation || !source || !renderer || !interaction || !log) return;

    const now = () => new Date().toLocaleTimeString();
    const childrenNode = () => document.getElementById('spatial-children');
    const childElements = () => [...document.querySelectorAll('#spatial-children .spatial-target')];
    const childNames = () => childElements().map(x => x.querySelector('strong')?.textContent?.trim() || x.textContent.trim().replace(/\s+/g,' '));
    const spatial = () => {
      const manager = window.spatialViewportManager;
      const node = document.getElementById('spatial-node');
      const badge = document.getElementById('spatial-level-badge');
      const crumbs = [...document.querySelectorAll('#spatial-breadcrumb button')].map(x => x.textContent.trim()).filter(Boolean);
      return {
        manager: !!manager,
        target: node?.querySelector('strong')?.textContent?.trim() || '?',
        id: window.spatialEvidenceTarget || manager?.activeKey || '?',
        level: badge?.textContent?.trim() || '?',
        path: crumbs.join(' > ') || '(root)',
        children: childNames(),
        nodeText: node?.textContent?.trim().replace(/\s+/g,' ') || '(none)',
        active: manager?.active?.constructor?.name || 'none',
        activeKey: manager?.activeKey || 'none'
      };
    };
    const clickable = () => {
      const list = window.spatialViewportManager?.active?.clickable;
      return Array.isArray(list) ? list.map(x => ({name:x?.name||'', spatialTarget:x?.userData?.spatialTarget||'', type:x?.type||''})) : [];
    };
    const isHandRoot = s => {
      const t = String(s.target || '').toLowerCase();
      const id = String(s.id || '').toLowerCase();
      return (t === 'dłoń' || t === 'hand' || id === 'hand') && s.path.split(' > ').length === 1;
    };
    const handFallback = s => isHandRoot(s) && s.children.length === 1 && /regional field/i.test(s.children[0]);

    const writeLog = (message, stack) => {
      lines.push(`[${now()}] ${message}${stack ? `\n  stack: ${String(stack).replace(/\n/g,'\n         ')}` : ''}`);
      while (lines.length > 120) lines.shift();
      log.textContent = lines.join('\n');
      log.scrollTop = log.scrollHeight;
    };
    const event = (message, stack) => {
      lastProgress = message;
      const t = performance.now();
      if (t - lastEventAt < 100) {
        pendingEvent = {message, stack};
        return;
      }
      lastEventAt = t;
      pendingEvent = null;
      writeLog(message, stack);
      if (!minimized) render();
    };
    setInterval(() => {
      if (!pendingEvent) return;
      const p = pendingEvent;
      pendingEvent = null;
      lastEventAt = performance.now();
      writeLog(p.message, p.stack);
      if (!minimized) render();
    }, 150);

    const render = () => {
      const s = spatial();
      const list = clickable();
      const names = list.map(x => x.name || x.spatialTarget || '(unnamed)');
      const manager = window.spatialViewportManager?.active;
      const children = childrenNode();
      const regionIds = childElements().slice(0, 7).map(x => ({label:x.querySelector('strong')?.textContent?.trim()||'', dataset:{...x.dataset}}));
      const macroClickable = list.filter(x => expected.includes(x.name) || expected.includes(x.spatialTarget));
      runtime.textContent = ['RUNTIME',
        `status:       ${window.__testhpTwinReady ? 'READY' : 'INITIALIZING'}`,
        `init age:     ${Math.round(performance.now()-started)} ms`,
        `manager:      ${s.manager ? 'present' : 'MISSING'}`,
        `ready flag:   ${window.__testhpTwinReady ? 'YES' : 'NO'}`,
        `last progress:${lastProgress}`
      ].join('\n');
      state.textContent = ['', 'SPATIAL STATE',
        `level:        ${s.level}`, `target:       ${s.target}`, `spatial_id:   ${s.id}`,
        `path:         ${s.path}`, `children:     ${s.children.join(' | ') || '(none)'}`,
        `active view:  ${s.active}`, `active key:   ${s.activeKey}`, `node:         ${s.nodeText}`,
        `children DOM: ${!!children}`
      ].join('\n');
      navigation.textContent = ['', 'NAVIGATION DIAGNOSTICS',
        `root is Hand:       ${isHandRoot(s) ? 'YES' : 'NO'}`,
        `root fallback:     ${handFallback(s) ? 'YES — Regional field at macro root' : 'NO'}`,
        `expected count:     7`, `actual count:       ${s.children.length}`,
        `expected children:  ${expected.join(' | ')}`, `actual children:    ${s.children.join(' | ') || '(none)'}`,
        `order correct:      ${s.children.join('|') === expected.join('|') ? 'YES' : 'NO'}`,
        `macro targets found: ${macroClickable.length}/7`,
        `manager active key: ${manager?.activeKey || s.activeKey || 'none'}`
      ].join('\n');
      source.textContent = ['', 'SOURCE / WRITER DIAGNOSTICS',
        `last DOM writer:    ${lastWriter?.method || '(none captured)'}`,
        `writer time:        ${lastWriter?.time || '(none)'}`,
        `writer before:      ${lastWriter?.before || '(none)'}`,
        `writer stack:       ${lastWriter?.stack || '(none captured yet)'}`,
        `mutation:            ${lastMutation ? JSON.stringify(lastMutation) : '(none captured)'}`,
        `child metadata:     ${JSON.stringify(regionIds)}`
      ].join('\n');
      renderer.textContent = ['', 'RENDERER / 3D DIAGNOSTICS',
        `renderer:      ${s.active}`, `active key:    ${s.activeKey}`, `clickable:     ${list.length}`,
        `clickable names:${names.join(' | ') || '(none)'}`, `hand macro 3D: ${macroClickable.length}/7`,
        `Regional field 3D: ${list.some(x => /regional field/i.test(x.name) || /regional field/i.test(x.spatialTarget)) ? 'YES' : 'NO'}`,
        `scene:         ${manager?.scene?.children?.length ?? 'unknown'}`, `camera:        ${manager?.camera ? 'present' : 'missing'}`
      ].join('\n');
      interaction.textContent = ['', 'LAST INTERACTION', lastInteraction ? JSON.stringify(lastInteraction,null,2) : 'No navigation interaction captured yet.'].join('\n');
    };

    // IMPORTANT: do not monkey-patch DOM prototypes. The previous diagnostic did that globally and
    // could participate in a feedback loop while the spatial navigation was rebuilding its DOM.
    const observedChildren = childrenNode();
    const observer = new MutationObserver(records => {
      if (!observedChildren) return;
      const relevant = records.some(r => r.target === observedChildren || observedChildren.contains(r.target));
      if (!relevant) return;
      const after = childNames();
      lastMutation = {time:now(), type:records.map(r=>r.type).join(','), children:after};
      event(`DOM MUTATION | spatial-children | children=${after.join(' | ') || '(none)'}`);
      if (handFallback(spatial())) event('ROOT FALLBACK DETECTED | Regional field came back');
      if (!minimized) render();
    });
    if (observedChildren) observer.observe(observedChildren, {childList:true, subtree:true, attributes:true, attributeFilter:['class','data-spatial-target','data-spatial-id']});

    window.addEventListener('error', e => event(`WINDOW ERROR | ${e.message||'unknown'} | ${e.filename||''}:${e.lineno||''}`));
    window.addEventListener('unhandledrejection', e => event(`UNHANDLED PROMISE | ${e.reason?.stack||e.reason||'unknown'}`));
    window.addEventListener('testhp:twin-ready', () => { window.__testhpTwinReady = true; event('TWIN READY'); });
    window.addEventListener('testhp:twin-error', e => event(`TWIN ERROR | ${JSON.stringify(e.detail||{})}`));
    window.addEventListener('testhp:twin-progress', e => event(`INIT | ${e.detail?.step || ''} | ${e.detail?.detail || ''}`));
    window.addEventListener('testhp:viewport-rendered', e => event(`VIEW RENDERED | ${JSON.stringify(e.detail||{})}`));
    window.addEventListener('testhp:spatial-layer-changed', e => event(`SPATIAL LAYER | ${JSON.stringify(e.detail||{})}`));
    canvas.addEventListener('click', e => {
      lastInteraction = {type:'canvas click', x:e.clientX, y:e.clientY, time:now(), target:spatial().target};
      event(`CANVAS CLICK | x=${Math.round(e.clientX)} y=${Math.round(e.clientY)} | target=${spatial().target}`);
    }, {passive:true});

    const setMinimized = value => {
      minimized = value;
      panel.style.display = minimized ? 'none' : 'block';
      toggle.textContent = minimized ? 'TWIN VIEWPORT DEBUG · ROZWIŃ' : 'TWIN VIEWPORT DEBUG · ZWIŃ';
      if (!minimized) render();
    };
    toggle.onclick = () => setMinimized(!minimized);
    document.getElementById('twin-debug-close')?.addEventListener('click', () => setMinimized(true));
    document.getElementById('twin-debug-refresh')?.addEventListener('click', () => render());
    document.getElementById('twin-debug-clear')?.addEventListener('click', () => { lines.length = 0; log.textContent = ''; });

    event('DEBUG READY | non-invasive observer active');
    render();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();