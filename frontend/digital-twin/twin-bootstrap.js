(() => {
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const log = (step, detail = '') => {
    const line = document.createElement('div');
    line.className = 'twin-boot-line';
    line.innerHTML = `<span class="twin-boot-mark">…</span><strong>${escapeHtml(step)}</strong><span>${escapeHtml(detail)}</span>`;
    document.getElementById('twin-boot-lines')?.appendChild(line);
    window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step, detail } }));
  };
  const mark = (step, ok = true, detail = '') => {
    const rows = [...document.querySelectorAll('#twin-boot-lines .twin-boot-line')];
    const row = rows.find(x => x.querySelector('strong')?.textContent === step);
    if (!row) return;
    row.querySelector('.twin-boot-mark').textContent = ok ? '✓' : '✕';
    row.classList.toggle('ok', ok);
    row.classList.toggle('error', !ok);
    if (detail) row.querySelector('span:last-child').textContent = detail;
  };
  const withTimeout = (promise, ms, label) => Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`${label} timed out after ${ms / 1000}s`)), ms))
  ]);

  function showBootUi() {
    if (document.getElementById('twin-boot-diagnostics')) return;
    const style = document.createElement('style');
    style.id = 'twin-boot-diagnostics-css';
    style.textContent = `
      #twin-boot-diagnostics{position:absolute;inset:16px auto auto 16px;z-index:50;width:min(520px,calc(100% - 32px));padding:14px 16px;border:1px solid rgba(130,145,165,.35);border-radius:12px;background:rgba(13,17,23,.94);color:#e6edf3;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;box-shadow:0 12px 40px rgba(0,0,0,.25)}
      #twin-boot-diagnostics h3{margin:0 0 8px;font:700 13px/1.2 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase}
      .twin-boot-line{display:grid;grid-template-columns:18px 150px 1fr;gap:6px;align-items:start;padding:3px 0;color:#9da7b3}.twin-boot-line strong{color:#d8dee4}.twin-boot-line.ok .twin-boot-mark{color:#56d364}.twin-boot-line.ok strong{color:#e6edf3}.twin-boot-line.error .twin-boot-mark,.twin-boot-line.error strong{color:#ff7b72}.twin-boot-summary{margin-top:8px;color:#8b949e}
    `;
    document.head.appendChild(style);
    const box = document.createElement('section');
    box.id = 'twin-boot-diagnostics';
    box.innerHTML = '<h3>Digital Twin · boot diagnostics</h3><div id="twin-boot-lines"></div><div class="twin-boot-summary">Heavy modules are loaded only after the canonical viewport is ready.</div>';
    document.getElementById('twin-viewport')?.appendChild(box);
  }

  async function loadClassic(src, label, timeout = 10000) {
    log(label);
    await withTimeout(new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.body.appendChild(script);
    }), timeout, label);
    mark(label, true, 'loaded');
  }

  async function boot() {
    showBootUi();
    try {
      log('DOM', 'ready');
      mark('DOM', true, 'ready');

      log('Three.js + canonical viewport');
      await withTimeout(import('./app.js?v=progressive-inspector-24'), 15000, 'Canonical viewport');
      mark('Three.js + canonical viewport', true, 'app.js loaded');

      await loadClassic('/digital-twin/spatial-layer-viewport.js?v=canonical-8', 'Spatial bridge');
      await loadClassic('/digital-twin/spatial-evidence-renderer.js?v=evidence-5', 'Evidence renderer');
      await loadClassic('/digital-twin/spatial-viewport-debug.js?v=twin-debug-10', 'Viewport debug');
      await loadClassic('/digital-twin/evidence-registry-bridge.js?v=registry-bridge-5', 'Evidence registry');
      await loadClassic('/digital-twin/stages-2-4.js?v=stage-2-4-9', 'Spatial stages 2–4');
      await loadClassic('/digital-twin/assets/stages-5-8.js?v=stage-5-8-3', 'Stages 5–8');
      await loadClassic('/digital-twin/evidence-ux.js?v=evidence-ux-7', 'Evidence UX');
      await loadClassic('/digital-twin/deep-drill-visualization.js?v=deep-drill-3', 'Deep drill');

      log('Viewport boot verifier');
      await withTimeout(import('./twin-viewport-boot.js?v=boot-4'), 10000, 'Viewport boot verifier');
      mark('Viewport boot verifier', true, 'active');

      await loadClassic('/digital-twin/hand-surface-stages-11-15.js?v=stages-11-15-2', 'Hand surface stages 11–15');
      await loadClassic('/digital-twin/hand-surface-edit-bridge.js?v=edit-bridge-2', 'Hand surface edit bridge');
      await loadClassic('/digital-twin/hand-surface-stages-20-22.js?v=stages-20-22-2', 'Hand surface stages 20–22');

      // Photo reconstruction is deliberately outside the critical path.
      const loadPhoto = async () => {
        log('Photo reconstruction');
        await withTimeout(import('./hand-surface-photo-reconstruction.js?v=photo-reconstruction-2'), 15000, 'Photo reconstruction');
        mark('Photo reconstruction', true, 'available on demand');
      };
      window.testhpLoadPhotoReconstruction = loadPhoto;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'secondary';
      button.textContent = 'Enable photo reconstruction';
      button.style.cssText = 'position:absolute;right:16px;top:16px;z-index:51';
      button.onclick = async () => {
        button.disabled = true;
        try { await loadPhoto(); button.remove(); }
        catch (error) { button.disabled = false; mark('Photo reconstruction', false, error.message); console.error(error); }
      };
      document.getElementById('twin-viewport')?.appendChild(button);

      document.getElementById('viewer-loading')?.setAttribute('hidden', '');
      window.__testhpTwinBootComplete = true;
      window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step: 'BOOT COMPLETE', detail: 'critical path loaded; photo reconstruction is lazy' } }));
    } catch (error) {
      console.error('[Twin Bootstrap]', error);
      const current = [...document.querySelectorAll('#twin-boot-lines .twin-boot-line')].reverse().find(x => !x.classList.contains('ok'))?.querySelector('strong')?.textContent;
      if (current) mark(current, false, error.message);
      const loading = document.getElementById('viewer-loading');
      if (loading) { loading.hidden = false; loading.style.display = 'grid'; loading.textContent = `Digital Twin boot failed: ${error.message}`; loading.classList.add('viewer-loading-error'); }
      window.dispatchEvent(new CustomEvent('testhp:twin-error', { detail: { error } }));
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
