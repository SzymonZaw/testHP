(() => {
  'use strict';
  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const NIH_VIEWER_URL = 'https://3d.nih.gov/entries/3DPX-017237';
  const VIEWER_VERSION = 'reference-3d-safe-10';
  let observer = null;
  let retryTimer = null;
  let bootToken = 0;

  function setState(patch = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({
      installed: true, version: VIEWER_VERSION, active: false, loading: false,
      loaded: false, sourceId: SOURCE_ID, assetUrl: NIH_VIEWER_URL,
      provenance: 'public_reference',
      regionId: window.__testhpReferenceHandState?.regionId || 'palm',
      error: null, ...patch
    });
    return window.__testhpReferenceHand3DViewerState;
  }

  function installStyles() {
    if (document.getElementById('testhp-reference-hand-3d-style')) return;
    const s = document.createElement('style');
    s.id = 'testhp-reference-hand-3d-style';
    s.textContent = `
      .dt-reference-3d-card{position:relative;min-height:520px;width:100%;margin:16px 0;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;isolation:isolate;box-sizing:border-box}
      .dt-reference-3d-frame{display:block;width:100%;height:520px;border:0;background:#0b1118}
      .dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}
      .dt-reference-3d-title{position:absolute;left:16px;top:14px;padding:8px 10px;border:1px solid #344456;border-radius:10px;background:#0d151ee8;color:#dce7f2;font:700 11px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase}
      .dt-reference-3d-status{position:absolute;left:16px;bottom:14px;max-width:80%;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}
      .dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:#0b1118;z-index:3}.dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}.dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}
    `;
    document.head.appendChild(s);
  }

  function getHost() {
    return document.getElementById('testhp-end-user-layer');
  }

  function findMount() {
    const host = getHost();
    if (!host) return null;
    return host.querySelector('.center .viewport') || host.querySelector('.viewport') || host;
  }

  function ensureCard(mount) {
    if (!mount) return null;
    let card = mount.querySelector(':scope > .dt-reference-3d-card');
    if (card) return card;
    card = document.createElement('section');
    card.className = 'dt-reference-3d-card';
    card.setAttribute('aria-label', 'NIH 3D reference hand');
    card.innerHTML = '<iframe class="dt-reference-3d-frame" title="NIH 3D reference hand" loading="eager" referrerpolicy="strict-origin-when-cross-origin"></iframe><div class="dt-reference-3d-overlay"><div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div><div class="dt-reference-3d-status">Loading NIH 3D reference geometry…</div></div>';
    card.style.display = 'block';
    card.style.position = 'relative';
    if (mount === getHost()) mount.prepend(card); else mount.appendChild(card);
    return card;
  }

  function showFallback(card, message) {
    if (!card) return;
    let f = card.querySelector('.dt-reference-3d-fallback');
    if (!f) {
      f = document.createElement('div');
      f.className = 'dt-reference-3d-fallback';
      f.innerHTML = '<div><strong>Reference 3D viewer unavailable</strong><span></span><br><a href="https://3d.nih.gov/entries/3DPX-017237" target="_blank" rel="noopener noreferrer">Open NIH 3D reference</a></div>';
      card.appendChild(f);
    }
    f.querySelector('span').textContent = message;
  }

  function stopWaiting() {
    if (observer) { observer.disconnect(); observer = null; }
    if (retryTimer) { clearInterval(retryTimer); retryTimer = null; }
  }

  function bindFrame(card, token) {
    const frame = card?.querySelector('.dt-reference-3d-frame');
    if (!frame || frame.dataset.testhpBound === '1') return !!frame;
    frame.dataset.testhpBound = '1';
    frame.addEventListener('load', () => {
      if (token !== bootToken) return;
      stopWaiting();
      setState({active:true, loading:false, loaded:true, error:null, regionId:window.__testhpReferenceHandState?.regionId || 'palm'});
      const status = card.querySelector('.dt-reference-3d-status');
      if (status) status.textContent = 'Loaded in NIH 3D · public reference geometry · not user health data';
    }, {once:true});
    frame.addEventListener('error', () => {
      if (token !== bootToken) return;
      stopWaiting();
      setState({active:true, loading:false, loaded:false, error:'NIH interactive reference viewer could not be loaded'});
      showFallback(card, 'The NIH interactive viewer could not be loaded in this browser.');
    }, {once:true});
    frame.src = NIH_VIEWER_URL;
    return true;
  }

  function tryMount(token) {
    if (token !== bootToken) return true;
    const mount = findMount();
    if (!mount) return false;
    const card = ensureCard(mount);
    if (!card) return false;
    bindFrame(card, token);
    setState({active:true, loading:true, loaded:false, error:null, regionId:window.__testhpReferenceHandState?.regionId || 'palm'});
    return true;
  }

  function boot() {
    installStyles();
    const token = ++bootToken;
    stopWaiting();
    setState({active:true, loading:true, loaded:false, error:null});

    if (tryMount(token)) return;

    const root = document.documentElement || document;
    observer = new MutationObserver(() => { tryMount(token); });
    observer.observe(root, {childList:true, subtree:true});

    // The main UI is rendered dynamically; retry without blocking or throwing.
    let attempts = 0;
    retryTimer = setInterval(() => {
      attempts += 1;
      if (tryMount(token)) {
        stopWaiting();
        return;
      }
      if (attempts >= 30) {
        stopWaiting();
        setState({active:true, loading:false, loaded:false, error:'Reference viewer host is not available'});
      }
    }, 250);
  }

  function activate() { boot(); }

  window.testhpReferenceHand3D = Object.freeze({
    version: VIEWER_VERSION,
    sourceId: SOURCE_ID,
    assetUrl: NIH_VIEWER_URL,
    activate,
    getState: () => window.__testhpReferenceHand3DViewerState
  });

  setState();
  window.addEventListener('testhp:reference-hand-activated', activate);
  window.addEventListener('DOMContentLoaded', () => {
    if (window.__testhpReferenceHandState?.active) activate();
  }, {once:true});
  if (window.__testhpReferenceHandState?.active) activate();
})();