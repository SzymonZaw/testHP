(() => {
  'use strict';

  // Read-only viewport diagnostics. This script must never mutate spatial state.
  const host = document.getElementById('twin-viewport-debug-host');
  if (!host) return;

  const startedAt = Date.now();
  const trace = [];
  const MAX_TRACE = 20;
  let lastNavigation = null;
  let lastClickRoute = null;
  let lastError = null;
  let lastInput = null;
  let minimized = false;

  const safe = fn => { try { return fn(); } catch { return null; } };
  const pretty = value => JSON.stringify(value, (key, v) => {
    if (typeof v === 'function') return '[Function]';
    if (v instanceof HTMLElement) return `[HTMLElement ${v.tagName.toLowerCase()}#${v.id || ''}]`;
    if (v instanceof Event) return `[${v.type}]`;
    return v;
  }, 2);

  const spatialState = () => safe(() => {
    const target = window.testhpSpatialContract?.getTarget?.() || null;
    const node = window.selectedSpatialNode || null;
    const manager = window.viewportManager || window.testhpViewportManager || null;
    const managerState = manager?.state || null;
    const active = manager?.active || null;
    return {
      level: target?.level || node?.level || managerState?.level || null,
      target: target?.label || target?.name || node?.label || node?.name || managerState?.target || null,
      path: target?.path || node?.path || managerState?.path || null,
      targetSpatialId: target?.spatial_id || null,
      selectedSpatialNode: node?.spatial_id || node?.id || node?.regionId || null,
      activeKey: manager?.activeKey || managerState?.activeKey || null,
      activeLayer: manager?.activeLayer || managerState?.activeLayer || null,
      activeTarget: active?.spatial_id || active?.id || active?.regionId || null
    };
  }) || {};

  const managerInfo = () => safe(() => {
    const manager = window.viewportManager || window.testhpViewportManager || null;
    const canvas = document.getElementById('twin-canvas');
    return {
      present: !!manager,
      keys: manager ? Object.keys(manager).filter(k => !k.startsWith('__')).slice(0, 40) : [],
      activeKey: manager?.activeKey ?? null,
      activeLayer: manager?.activeLayer ?? null,
      active: manager?.active?.spatial_id || manager?.active?.id || manager?.active?.regionId || manager?.active || null,
      canvas: canvas ? `${canvas.clientWidth || canvas.width}×${canvas.clientHeight || canvas.height}` : 'missing'
    };
  }) || {};

  const childrenOf = detail => {
    const children = detail?.children || detail?.target?.children || detail?.node?.children || [];
    return Array.isArray(children) ? children.map(x => typeof x === 'string' ? x : x?.label || x?.name || x?.id || x?.spatial_id).filter(Boolean) : [];
  };

  const navSnapshot = detail => safe(() => {
    const target = detail?.target && typeof detail.target === 'object' ? detail.target : detail;
    if (!target || typeof target !== 'object') return null;
    return {
      level: detail?.level || target.level || null,
      target: target.label || target.name || detail?.targetLabel || null,
      id: target.id || target.regionId || null,
      spatial_id: target.spatial_id || target.spatialId || null,
      path: target.path || detail?.path || null,
      children: childrenOf(detail)
    };
  });

  const record = (type, detail = {}) => {
    const manager = managerInfo();
    const state = spatialState();
    trace.push({
      t: Date.now() - startedAt,
      type,
      level: detail?.level || state.level || null,
      target: detail?.target?.label || detail?.target?.name || detail?.targetLabel || state.target || null,
      path: detail?.path || detail?.target?.path || state.path || null,
      children: childrenOf(detail),
      renderer: detail?.renderer || detail?.rendererName || null,
      reason: detail?.reason || null,
      managerPresent: manager.present,
      activeKey: manager.activeKey,
      activeLayer: manager.activeLayer,
      spatial_id: detail?.spatial_id || detail?.target?.spatial_id || null
    });
    if (trace.length > MAX_TRACE) trace.shift();
    render();
  };

  const routeFromButton = button => safe(() => ({
    label: (button.textContent || '').replace(/\s+/g, ' ').trim(),
    spatialId: button.dataset.spatialId || button.dataset.spatialID || button.dataset.spatialTarget || null,
    targetId: button.dataset.targetId || button.dataset.target || null,
    onclick: button.getAttribute('onclick') || button.onclick?.toString?.() || null
  }));

  document.addEventListener('click', event => {
    const button = event.target?.closest?.('#spatial-children button, #spatial-children [role="button"], .spatial-children button');
    if (!button) return;
    lastClickRoute = { t: Date.now() - startedAt, ...routeFromButton(button), spatialState: spatialState() };
    render();
  }, true);

  document.addEventListener('input', event => {
    const el = event.target;
    if (!el || !el.matches?.('input,select,textarea')) return;
    lastInput = { t: Date.now() - startedAt, type: el.type || el.tagName.toLowerCase(), id: el.id || null, name: el.name || null, value: el.type === 'password' ? '[redacted]' : String(el.value ?? '').slice(0, 160) };
    render();
  }, true);

  window.addEventListener('error', event => {
    lastError = { t: Date.now() - startedAt, message: event.message || 'Unknown error', source: event.filename || null, line: event.lineno || null, column: event.colno || null };
    render();
  });
  window.addEventListener('unhandledrejection', event => {
    lastError = { t: Date.now() - startedAt, message: String(event.reason?.stack || event.reason || 'Unhandled rejection') };
    render();
  });

  ['testhp:viewport-rendered','testhp:spatial-layer-changed','testhp:spatial-contract-changed','testhp:spatial-target-changed']
    .forEach(type => window.addEventListener(type, event => {
      const detail = event.detail || {};
      if (type === 'testhp:spatial-layer-changed' || type === 'testhp:spatial-contract-changed') {
        const snapshot = navSnapshot(detail);
        if (snapshot) lastNavigation = snapshot;
      }
      record(type, detail);
    }));

  const buttonRoutes = () => [...document.querySelectorAll('#spatial-children button, #spatial-children [role="button"], .spatial-children button')].map(routeFromButton).filter(Boolean);
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  const block = (title, body) => `<section class="tvd-section"><h4>${title}</h4>${body}</section>`;
  const kv = (k, v) => `<div class="tvd-kv"><span>${escapeHtml(k)}</span><b>${escapeHtml(v ?? '—')}</b></div>`;

  function render() {
    const state = spatialState();
    const manager = managerInfo();
    const routes = buttonRoutes();
    const elapsed = Date.now() - startedAt;
    host.innerHTML = `<div class="tvd ${minimized ? 'is-minimized' : ''}">
      <style>
        #twin-viewport-debug-host .tvd{box-sizing:border-box;max-height:min(78vh,760px);overflow:auto;background:rgba(16,22,28,.96);color:#dce5ea;border:1px solid rgba(255,255,255,.16);border-radius:12px;box-shadow:0 12px 36px rgba(0,0,0,.28);font:11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace;backdrop-filter:blur(8px)}
        #twin-viewport-debug-host .tvd-head{position:sticky;top:0;z-index:2;display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(16,22,28,.98);border-bottom:1px solid rgba(255,255,255,.12)}
        #twin-viewport-debug-host .tvd-title{font-weight:800;letter-spacing:.08em}.tvd-title span{opacity:.65}
        #twin-viewport-debug-host .tvd-btn{border:1px solid rgba(255,255,255,.18);background:transparent;color:#dce5ea;border-radius:6px;padding:3px 7px;cursor:pointer}
        #twin-viewport-debug-host .tvd-body{padding:8px 10px}.tvd-section{margin:0 0 10px}.tvd-section h4{margin:0 0 5px;color:#8fa5b1;font-size:10px;letter-spacing:.08em}.tvd-kv{display:flex;gap:10px;justify-content:space-between;padding:2px 0}.tvd-kv span{opacity:.65}.tvd-kv b{font-weight:600;text-align:right;max-width:70%;word-break:break-word}.tvd-pre{margin:0;white-space:pre-wrap;word-break:break-word;color:#cbd7dd}.tvd-list{margin:0;padding-left:20px}.tvd-list li{margin:3px 0}.tvd-error{color:#ff9b9b}.tvd-ok{color:#8ee0b3}.tvd-muted{opacity:.55}
      </style>
      <div class="tvd-head"><span class="tvd-title">TWIN VIEWPORT · <span>DEBUG</span></span><button class="tvd-btn" type="button" data-tvd-minimize>${minimized ? 'OPEN' : 'MINIMIZE'}</button></div>
      ${minimized ? '' : `<div class="tvd-body">
        ${block('RUNTIME', kv('status','READY')+kv('init age',`${elapsed} ms`)+kv('manager',manager.present?'present':'missing')+kv('manager keys',manager.keys.join(', ')||'—')+kv('canvas',manager.canvas))}
        ${block('SPATIAL STATE',kv('level',state.level)+kv('target',state.target)+kv('path',Array.isArray(state.path)?state.path.join(' > '):state.path)+kv('target spatial_id',state.targetSpatialId)+kv('selectedSpatialNode',state.selectedSpatialNode)+kv('active key',state.activeKey)+kv('active layer',state.activeLayer))}
        ${block('BUTTON ROUTING',routes.length?`<ol class="tvd-list">${routes.map(r=>`<li>${escapeHtml(r.label)} | spatialId=${escapeHtml(r.spatialId||'NULL')} | targetId=${escapeHtml(r.targetId||'NULL')} | onclick=${escapeHtml(r.onclick||'—')}</li>`).join('')}</ol>`:'<span class="tvd-muted">(none)</span>')}
        ${block('LAST NAVIGATION',`<pre class="tvd-pre">${escapeHtml(pretty(lastNavigation||'(none)'))}</pre>`)}
        ${block('LAST CLICK ROUTE',`<pre class="tvd-pre">${escapeHtml(pretty(lastClickRoute||'(none)'))}</pre>`)}
        ${block('EVENT TRACE (latest 20)',`<pre class="tvd-pre">${escapeHtml(pretty(trace.slice(-20)))}</pre>`)}
        ${block('ERROR / INTERACTION',`<div class="${lastError?'tvd-error':'tvd-ok'}">last error: ${escapeHtml(lastError?pretty(lastError):'(none)')}</div><pre class="tvd-pre">last input: ${escapeHtml(pretty(lastInput||'(none)'))}</pre>`)}
      </div>`}
    </div>`;
    host.querySelector('[data-tvd-minimize]')?.addEventListener('click',()=>{minimized=!minimized;render();});
  }

  window.__testhpViewportDebug = Object.freeze({
    getState: () => spatialState(),
    getManager: () => managerInfo(),
    getTrace: () => trace.slice(),
    getLastNavigation: () => lastNavigation,
    getLastClickRoute: () => lastClickRoute,
    getLastError: () => lastError
  });

  render();
})();
