(() => {
  'use strict';
  if (window.__testhpReferenceHand3DViewerInstalled) return;
  window.__testhpReferenceHand3DViewerInstalled = true;

  const SOURCE_ID = 'nih-hand-template-3DPX-017237';
  const NIH_ENTRY_URL = 'https://3d.nih.gov/entries/3DPX-017237';
  const NIH_GLB_URL = 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811';
  const PROXY_URL = '/api/hand/photo-reconstruction/reference-glb';
  const VIEWER_VERSION = 'reference-glb-safe-17';
  let observer = null;
  let retryTimer = null;
  let bootToken = 0;
  let loadingPromise = null;

  function setState(p = {}) {
    window.__testhpReferenceHand3DViewerState = Object.freeze({
      installed: true,
      version: VIEWER_VERSION,
      active: false,
      loading: false,
      loaded: false,
      sourceId: SOURCE_ID,
      entryUrl: NIH_ENTRY_URL,
      assetUrl: NIH_GLB_URL,
      proxyUrl: PROXY_URL,
      assetFormat: 'nih_interactive',
      provenance: 'public_reference',
      ownership: 'reference',
      userHealthData: false,
      regionId: window.__testhpReferenceHandState?.regionId || 'palm',
      error: null,
      ...p,
    });
    return window.__testhpReferenceHand3DViewerState;
  }

  function installStyles() {
    if (document.getElementById('testhp-reference-hand-3d-style')) return;
    const s = document.createElement('style');
    s.id = 'testhp-reference-hand-3d-style';
    s.textContent = `
      .dt-reference-3d-card{position:relative;min-height:520px;width:100%;margin:16px 0;border:1px solid #263545;border-radius:16px;background:#0b1118;overflow:hidden;isolation:isolate;box-sizing:border-box}
      .dt-reference-3d-embed{display:block;width:100%;height:520px;border:0;background:#0b1118}
      .dt-reference-3d-overlay{position:absolute;inset:0;pointer-events:none;z-index:2}
      .dt-reference-3d-title,.dt-reference-3d-source,.dt-reference-3d-status,.dt-reference-3d-mapping{position:absolute;padding:7px 9px;border-radius:9px;background:#0d151ee8;color:#9fb0c2;font:600 11px/1.35 system-ui,sans-serif}
      .dt-reference-3d-title{left:16px;top:14px;color:#dce7f2}.dt-reference-3d-source{right:16px;top:14px}.dt-reference-3d-status{left:16px;bottom:14px}.dt-reference-3d-mapping{right:16px;bottom:14px}
      .dt-reference-3d-fallback{position:absolute;inset:0;display:grid;place-items:center;padding:32px;text-align:center;color:#9fb0c2;font:600 12px/1.5 system-ui,sans-serif;background:#0b1118;z-index:3}.dt-reference-3d-fallback strong{display:block;color:#dce7f2;margin-bottom:6px;font-size:13px}.dt-reference-3d-fallback a{color:#9bd8c4;pointer-events:auto}
    `;
    document.head.appendChild(s);
  }

  function getHost() { return document.getElementById('testhp-end-user-layer'); }
  function findMount() {
    const h = getHost();
    return h ? (h.querySelector('.center .viewport') || h.querySelector('.viewport') || h) : null;
  }

  function ensureCard(m) {
    if (!m) return null;
    let c = m.querySelector(':scope > .dt-reference-3d-card');
    if (c) return c;
    c = document.createElement('section');
    c.className = 'dt-reference-3d-card';
    c.setAttribute('aria-label', 'NIH 3D reference hand');
    c.innerHTML = `
      <div class="dt-reference-3d-overlay"><div class="dt-reference-3d-title">REFERENCE HAND · NIH 3D · 3DPX-017237</div><div class="dt-reference-3d-source">PUBLIC REFERENCE</div><div class="dt-reference-3d-status">Opening NIH interactive reference viewer…</div><div class="dt-reference-3d-mapping">Region geometry mapping · NOT ESTABLISHED</div></div>`;
    c.style.display = 'block';
    c.style.position = 'relative';
    m === getHost() ? m.prepend(c) : m.appendChild(c);
    return c;
  }

  function stopWaiting() {
    if (observer) { observer.disconnect(); observer = null; }
    if (retryTimer) { clearInterval(retryTimer); retryTimer = null; }
  }

  function openInteractive(card, token) {
    if (!card || token !== bootToken) return false;
    let embed = card.querySelector('.dt-reference-3d-embed');
    if (embed) return true;
    embed = document.createElement('iframe');
    embed.className = 'dt-reference-3d-embed';
    embed.title = 'NIH 3D interactive reference hand';
    embed.loading = 'eager';
    embed.referrerPolicy = 'strict-origin-when-cross-origin';
    embed.allow = 'fullscreen; xr-spatial-tracking';
    embed.src = NIH_ENTRY_URL;
    const status = card.querySelector('.dt-reference-3d-status');
    embed.addEventListener('load', () => {
      if (token !== bootToken) return;
      stopWaiting();
      setState({active:true,loading:false,loaded:true,error:null,loadMethod:'nih_interactive_fallback'});
      if (status) status.textContent = 'Loaded NIH interactive reference viewer · public reference geometry';
    }, {once:true});
    embed.addEventListener('error', () => {
      if (token !== bootToken) return;
      stopWaiting();
      setState({active:true,loading:false,loaded:false,error:'NIH interactive reference viewer failed to load',loadMethod:'nih_interactive_fallback'});
      showFallback(card, 'NIH interactive reference viewer could not be loaded.');
    }, {once:true});
    card.insertBefore(embed, card.firstChild);
    return true;
  }

  function showFallback(card, msg) {
    if (!card) return;
    let f = card.querySelector('.dt-reference-3d-fallback');
    if (!f) {
      f = document.createElement('div');
      f.className = 'dt-reference-3d-fallback';
      f.innerHTML = '<div><strong>Reference 3D viewer unavailable</strong><span></span><br><a href="' + NIH_ENTRY_URL + '" target="_blank" rel="noopener noreferrer">Open NIH 3D reference</a></div>';
      card.appendChild(f);
    }
    const sp = f.querySelector('span');
    if (sp) sp.textContent = msg;
  }

  function mount(token) {
    const m = findMount();
    if (!m) return false;
    const c = ensureCard(m);
    if (!c) return false;
    if (c.querySelector('.dt-reference-3d-embed')) return true;
    return openInteractive(c, token);
  }

  function boot() {
    if (window.__testhpReferenceHand3DViewerState?.active && (window.__testhpReferenceHand3DViewerState?.loading || window.__testhpReferenceHand3DViewerState?.loaded)) return;
    installStyles();
    const token = ++bootToken;
    stopWaiting();
    loadingPromise = null;
    setState({active:true,loading:true,loaded:false,error:null,loadMethod:'nih_interactive_fallback'});
    if (mount(token)) return;
    const root = document.documentElement || document;
    observer = new MutationObserver(() => { if (mount(token)) stopWaiting(); });
    observer.observe(root, {childList:true,subtree:true});
    let attempts = 0;
    retryTimer = setInterval(() => {
      attempts++;
      if (mount(token)) { stopWaiting(); return; }
      if (attempts >= 30) {
        stopWaiting();
        setState({active:true,loading:false,loaded:false,error:'Reference viewer host is not available',loadMethod:'nih_interactive_fallback'});
      }
    }, 250);
  }

  window.testhpReferenceHand3D = Object.freeze({
    version: VIEWER_VERSION,
    sourceId: SOURCE_ID,
    entryUrl: NIH_ENTRY_URL,
    assetUrl: NIH_GLB_URL,
    proxyUrl: PROXY_URL,
    assetFormat: 'nih_interactive',
    activate: boot,
    getState: () => window.__testhpReferenceHand3DViewerState,
  });

  setState();
  window.addEventListener('testhp:reference-hand-activated', boot);
  window.addEventListener('DOMContentLoaded', () => { if (window.__testhpReferenceHandState?.active) boot(); }, {once:true});
  if (window.__testhpReferenceHandState?.active) boot();
})();