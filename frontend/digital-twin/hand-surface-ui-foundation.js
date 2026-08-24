(() => {
  const target = () => {
    const t = window.testhpSpatialContract?.getTarget?.() || window.selectedSpatialNode || window.spatialEvidenceTarget || 'hand';
    if (t && typeof t === 'object') return { spatial_id: t.spatial_id || t.spatialId || t.id || 'hand', label: t.label || t.path?.join(' > ') || t.spatial_id || t.id || 'Dłoń' };
    return { spatial_id: String(t || 'hand'), label: String(t || 'Dłoń') };
  };
  const movePhotoPanel = () => {
    const shell = document.getElementById('hand-surface-unified');
    const material = shell?.querySelector('[data-hsu-section="material"]');
    const photo = document.getElementById('photo-3d-reconstruction');
    if (!shell || !material || !photo) return false;
    if (photo.parentElement !== material) material.appendChild(photo);
    photo.querySelector('.panel-title')?.remove();
    photo.style.marginTop = '0';
    return true;
  };
  const uploadFallback = files => {
    const t = target();
    const status = document.getElementById('hand-surface-photo-action-status');
    const setStatus = text => { if (status) status.textContent = text; };
    (async () => {
      try {
        for (const file of files) {
          const form = new FormData();
          form.append('file', file);
          form.append('subject_id', window.testhpPhotoReconstructionSubject || 'own_cohort');
          form.append('timepoint', window.testhpPhotoReconstructionTimepoint || 'T0');
          form.append('spatial_node_id', t.spatial_id);
          const response = await fetch('/api/hand/photo-reconstruction/upload', { method: 'POST', body: form });
          const body = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(body.detail || `Nie udało się dodać ${file.name}`);
        }
        setStatus(`${files.length} ${files.length === 1 ? 'zdjęcie dodane' : 'zdjęcia dodane'}.`);
        window.dispatchEvent(new CustomEvent('testhp:evidence-attached'));
      } catch (error) { setStatus(error.message || 'Nie udało się dodać zdjęć.'); }
    })();
  };
  const ensurePhotoAction = () => {
    const shell = document.getElementById('hand-surface-unified');
    const material = shell?.querySelector('[data-hsu-section="material"]');
    if (!material || material.querySelector('#hand-surface-add-photo-action')) return;
    const subnav = material.querySelector('.hsu-subnav');
    if (!subnav) return;
    const action = document.createElement('div');
    action.id = 'hand-surface-add-photo-action';
    action.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:10px 0 12px;padding:10px 12px;border:1px solid var(--border,#d8dee8);border-radius:10px;background:var(--panel,#fff)';
    action.innerHTML = '<div><strong style="display:block;font-size:13px">Zdjęcia / źródła</strong><span style="font-size:12px;color:#667085">Dodaj zdjęcia dla aktualnie wybranego celu przestrzennego.</span><span id="hand-surface-photo-action-status" style="display:block;font-size:12px;color:#667085;margin-top:4px"></span></div><button type="button" id="hand-surface-add-photo-btn" class="primary">＋ Dodaj zdjęcia</button><input id="hand-surface-fallback-files" type="file" accept="image/jpeg,image/png,image/webp,image/tiff" multiple hidden>';
    subnav.insertAdjacentElement('afterend', action);
    action.querySelector('#hand-surface-add-photo-btn').addEventListener('click', () => {
      const input = document.getElementById('p3r-clean-files');
      if (input) { input.click(); return; }
      action.querySelector('#hand-surface-fallback-files').click();
    });
    action.querySelector('#hand-surface-fallback-files').addEventListener('change', event => {
      const files = [...(event.target.files || [])];
      if (files.length) uploadFallback(files);
      event.target.value = '';
    });
  };
  const hideLegacySurfacePanels = () => {
    const shell = document.getElementById('hand-surface-unified');
    if (!shell) return;
    ['hand-surface-studio','hand-surface-stages-20-22'].forEach(id => {
      const el = document.getElementById(id);
      if (el && !shell.contains(el)) el.style.display = 'none';
    });
  };
  const ensurePreparationSourceBridge = () => {
    if (document.getElementById('hand-surface-preparation-source-bridge')) return;
    const script = document.createElement('script');
    script.id = 'hand-surface-preparation-source-bridge';
    script.src = '/digital-twin/hand-surface-preparation-source-bridge.js?v=prep-source-bridge-1';
    document.head.appendChild(script);
  };
  const ensureGeometryLive = () => {
    if (document.getElementById('hand-surface-geometry-live-script')) return;
    const script = document.createElement('script');
    script.id = 'hand-surface-geometry-live-script';
    script.src = '/digital-twin/hand-surface-geometry-live.js?v=geometry-live-2';
    document.head.appendChild(script);
  };
  const run = () => { movePhotoPanel(); hideLegacySurfacePanels(); ensurePhotoAction(); ensurePreparationSourceBridge(); ensureGeometryLive(); };
  const schedule = () => requestAnimationFrame(run);
  window.addEventListener('testhp:spatial-layer-changed', schedule);
  window.addEventListener('testhp:spatial-contract-changed', schedule);
  window.addEventListener('testhp:evidence-attached', schedule);
  const observer = new MutationObserver(schedule);
  if (document.body) observer.observe(document.body, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true }); else run();
})();
