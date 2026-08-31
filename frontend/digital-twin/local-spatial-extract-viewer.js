(() => {
  'use strict';
  if (window.__testhpLocalSpatialExtractViewerInstalled) return;
  window.__testhpLocalSpatialExtractViewerInstalled = true;

  const SOURCE_ID = 'human-skin-spatial-census';
  const ENDPOINT = `/api/reference/tissue/${SOURCE_ID}/cells/local-preview?limit=1000`;
  const CARD_CLASS = 'dt-reference-spatial-extract';
  const MAX_POINTS = 1000;
  let loading = false;
  let loaded = false;

  function host() { return document.getElementById('testhp-end-user-layer'); }
  function mountPoint() {
    const h = host();
    if (!h) return null;
    return h.querySelector('#twin-viewport') || h.querySelector('.dt-viewport') || null;
  }
  function ensureStyles() {
    if (document.getElementById('testhp-local-spatial-extract-style')) return;
    const style = document.createElement('style');
    style.id = 'testhp-local-spatial-extract-style';
    style.textContent = `
      .${CARD_CLASS}{margin-top:16px;border:1px solid rgba(155,216,196,.22);border-radius:16px;background:#0b1118;overflow:hidden}
      .${CARD_CLASS} .dt-local-spatial-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;padding:14px 16px;border-bottom:1px solid rgba(155,216,196,.12)}
      .${CARD_CLASS} .dt-local-spatial-kicker{font-size:9px;letter-spacing:.14em;color:#9bd8c4;font-weight:800;text-transform:uppercase}
      .${CARD_CLASS} .dt-local-spatial-title{font-size:14px;font-weight:800;color:#dce7f2;margin-top:3px}
      .${CARD_CLASS} .dt-local-spatial-meta{font-size:10px;color:#9fb0c2;text-align:right;line-height:1.45}
      .${CARD_CLASS} .dt-local-spatial-note{padding:10px 16px;font-size:10px;color:#9fb0c2;border-bottom:1px solid rgba(155,216,196,.08)}
      .${CARD_CLASS} canvas{display:block;width:100%;height:320px;background:#081015}
      .${CARD_CLASS} .dt-local-spatial-status{padding:9px 16px;font-size:10px;color:#9fb0c2;border-top:1px solid rgba(155,216,196,.08)}
    `;
    document.head.appendChild(style);
  }
  function cardRoot(parent) {
    let card = parent.querySelector(`:scope > .${CARD_CLASS}`);
    if (card) return card;
    card = document.createElement('section');
    card.className = CARD_CLASS;
    card.setAttribute('aria-label', 'Local MERFISH spatial extract');
    card.innerHTML = `
      <div class="dt-local-spatial-head"><div><div class="dt-local-spatial-kicker">REAL LINKED DATA</div><div class="dt-local-spatial-title">MERFISH · LOCAL SPATIAL EXTRACT</div></div><div class="dt-local-spatial-meta">FOREARM · SAMPLE-LOCAL<br>Not registered to NIH hand geometry</div></div>
      <div class="dt-local-spatial-note">Actual cells from the locally materialized H5AD extract. Coordinates are shown in their dataset/sample-local frame only.</div>
      <canvas aria-label="MERFISH sample-local cell coordinates"></canvas>
      <div class="dt-local-spatial-status">Loading local cell extract…</div>`;
    parent.appendChild(card);
    return card;
  }
  function draw(canvas, cells) {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(320, Math.round(rect.width));
    const height = Math.max(240, Math.round(rect.height));
    const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    canvas.width = width * dpr; canvas.height = height * dpr;
    const ctx = canvas.getContext('2d');
    if (!ctx) return 0;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, width, height);
    const points = cells.map(c => Array.isArray(c?.spatial) ? c.spatial : null).filter(p => p && p.length >= 2 && Number.isFinite(Number(p[0])) && Number.isFinite(Number(p[1]))).slice(0, MAX_POINTS).map(p => [Number(p[0]), Number(p[1])]);
    if (!points.length) return 0;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const [x, y] of points) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); }
    const pad = 24, spanX = Math.max(1e-9, maxX - minX), spanY = Math.max(1e-9, maxY - minY), scale = Math.min((width - 2 * pad) / spanX, (height - 2 * pad) / spanY), plotW = spanX * scale, plotH = spanY * scale, ox = (width - plotW) / 2, oy = (height - plotH) / 2;
    ctx.strokeStyle = 'rgba(155,216,196,.14)'; ctx.strokeRect(ox, oy, plotW, plotH); ctx.fillStyle = '#9bd8c4';
    for (const [x, y] of points) { const px = ox + (x - minX) * scale, py = oy + (maxY - y) * scale; ctx.beginPath(); ctx.arc(px, py, 1.7, 0, Math.PI * 2); ctx.fill(); }
    ctx.fillStyle = '#9fb0c2'; ctx.font = '10px system-ui, sans-serif'; ctx.fillText(`n=${points.length}`, 10, height - 10);
    return points.length;
  }
  async function load() {
    const parent = mountPoint();
    if (!parent) return false;
    ensureStyles();
    const card = cardRoot(parent);
    if (loaded || loading) return true;
    loading = true;
    const status = card.querySelector('.dt-local-spatial-status');
    try {
      const response = await fetch(ENDPOINT, { cache: 'no-store', credentials: 'same-origin' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.detail || `local extract endpoint returned ${response.status}`);
      const cells = Array.isArray(payload?.cells) ? payload.cells : [];
      const count = draw(card.querySelector('canvas'), cells);
      const site = payload?.anatomicSite || cells[0]?.anatomic_site || 'unknown site';
      const sample = payload?.sampleId || cells[0]?.sample_id || 'unknown sample';
      if (status) status.textContent = `${count} plotted real cells · ${site} · sample ${sample}`;
      loaded = true;
    } catch (error) {
      if (status) status.textContent = `Local spatial extract unavailable: ${error?.message || error}`;
      loaded = false;
    } finally { loading = false; }
    return true;
  }
  function boot() {
    let observer;
    let attempts = 0;
    const tryMount = () => {
      attempts += 1;
      const mounted = !!document.querySelector(`.${CARD_CLASS}`) || !!mountPoint();
      if (mounted) {
        load();
        if (document.querySelector(`.${CARD_CLASS}`)) {
          observer?.disconnect();
          observer = undefined;
          return;
        }
      }
      if (attempts >= 240) {
        observer?.disconnect();
        observer = undefined;
        return;
      }
      window.requestAnimationFrame(tryMount);
    };
    observer = new MutationObserver(() => {
      if (document.querySelector(`.${CARD_CLASS}`)) {
        observer.disconnect(); observer = undefined;
        return;
      }
      load();
    });
    observer.observe(document.documentElement || document, { childList: true, subtree: true });
    tryMount();
    window.addEventListener('testhp:reference-hand-activated', load);
    window.addEventListener('testhp:canonical-state-changed', load);
  }
  window.testhpLocalSpatialExtract = Object.freeze({ version: 'local-spatial-extract-safe-3', sourceId: SOURCE_ID, load, getState: () => ({ installed: true, loaded, loading, cardPresent: !!document.querySelector(`.${CARD_CLASS}`) }) });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();
