(() => {
  const viewport = document.getElementById('twin-viewport');
  const breadcrumb = document.getElementById('spatial-breadcrumb');
  const node = document.getElementById('spatial-node');
  const badge = document.getElementById('spatial-level-badge');
  if (!viewport || !breadcrumb || !node || !badge) return;

  const IMAGE_EXTENSIONS = new Set(['jpg', 'jpeg', 'png', 'webp', 'gif']);
  let analysis = null;
  let lastState = '';
  let requestToken = 0;
  let activePreview = null;

  const overlay = document.createElement('section');
  overlay.id = 'spatial-evidence-overlay';
  Object.assign(overlay.style, {
    position: 'absolute', inset: '0', zIndex: '35', display: 'none',
    pointerEvents: 'none', color: '#dcece6', fontFamily: 'system-ui, -apple-system, Segoe UI, sans-serif'
  });
  viewport.appendChild(overlay);

  const style = document.createElement('style');
  style.textContent = `
    #spatial-evidence-overlay .evidence-card{position:absolute;right:18px;top:58px;max-width:340px;padding:12px 14px;border:1px solid rgba(155,216,196,.28);border-radius:12px;background:rgba(8,18,19,.92);box-shadow:0 12px 32px rgba(0,0,0,.28);backdrop-filter:blur(8px);pointer-events:auto}
    #spatial-evidence-overlay .eyebrow{display:block;font-size:9px;letter-spacing:.14em;color:#9bd8c4;font-weight:800;margin-bottom:5px}
    #spatial-evidence-overlay .title{font-size:13px;font-weight:800;margin-bottom:5px}
    #spatial-evidence-overlay .meta{font-size:11px;color:#9fb7b0;line-height:1.45}
    #spatial-evidence-overlay .asset{margin-top:8px;padding-top:8px;border-top:1px solid rgba(155,216,196,.12);font-size:10px;color:#b9cbc5;line-height:1.45}
    #spatial-evidence-overlay .preview{position:absolute;left:18px;right:18px;top:58px;bottom:58px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(155,216,196,.24);border-radius:14px;overflow:hidden;background:#081315;box-shadow:0 18px 50px rgba(0,0,0,.34);pointer-events:auto;touch-action:none;cursor:grab}
    #spatial-evidence-overlay .preview.dragging{cursor:grabbing}
    #spatial-evidence-overlay img{position:absolute;max-width:none;max-height:none;display:block;user-select:none;-webkit-user-drag:none;transform-origin:center center}
    #spatial-evidence-overlay .preview-caption{position:absolute;left:0;right:0;bottom:0;padding:24px 12px 9px;background:linear-gradient(transparent,rgba(5,12,13,.94));font-size:10px;color:#dcece6;pointer-events:none}
    #spatial-evidence-overlay .preview-badge{position:absolute;left:12px;top:12px;padding:6px 8px;border-radius:8px;background:rgba(5,12,13,.82);border:1px solid rgba(155,216,196,.25);font-size:9px;letter-spacing:.08em;font-weight:800;color:#9bd8c4;pointer-events:none}
    #spatial-evidence-overlay .warning{color:#d6a64f;font-weight:800}
  `;
  document.head.appendChild(style);

  function text(el) { return el?.textContent?.trim() || ''; }
  function level() {
    const value = text(badge).toUpperCase();
    if (value.includes('SINGLE')) return 'cell';
    if (value.includes('CELLULAR')) return 'cellular';
    if (value.includes('TISSUE')) return 'tissue';
    return 'macro';
  }
  function path() { return [...breadcrumb.querySelectorAll('button')].map(text).filter(Boolean); }
  function target() { return text(node.querySelector('strong')) || 'Spatial target'; }
  function assetRegion(asset) {
    if (asset?.region_id) return String(asset.region_id).toLowerCase();
    if (asset?.zone_id) return String(asset.zone_id).toLowerCase();
    return '';
  }
  function regionFromPath() {
    const known = ['palm','thumb','index','middle','ring','little','wrist'];
    return path().map(x => x.toLowerCase().replaceAll(' ', '_')).find(x => known.includes(x)) || '';
  }
  function artifactName(asset) {
    return asset?.filename || asset?.artifact?.metadata?.filename || asset?.artifact?.uri?.split(/[\\/]/).pop() || asset?.asset_id || 'linked asset';
  }
  function extension(asset) {
    const name = artifactName(asset).toLowerCase();
    if (name.endsWith('.ome.tiff')) return 'ome.tiff';
    if (name.endsWith('.ome.tif')) return 'ome.tif';
    return name.includes('.') ? name.split('.').pop() : '';
  }
  function availableAssets() {
    return (analysis?.assets || []).filter(a => ['ready','available'].includes(String(a.status || '').toLowerCase()));
  }
  function resolution(asset) {
    return String(asset?.resolution || asset?.spatial_resolution || asset?.level || '').toLowerCase();
  }
  function exactSpatialPath(asset) {
    return String(asset?.spatial_path || asset?.path_in_twin || '').toLowerCase().replaceAll('›','>').replaceAll('→','>').replaceAll(' > ','>');
  }
  function matchesResolution(asset, levelName) {
    const value = resolution(asset);
    if (!value) return true;
    const aliases = {
      macro: new Set(['macro','macro anatomy','anatomy']),
      tissue: new Set(['tissue','tissue field','wsi']),
      cellular: new Set(['cellular','cellular field','microscopy']),
      cell: new Set(['cell','single cell'])
    };
    return aliases[levelName]?.has(value) ?? true;
  }
  function assetsFor(levelName) {
    const region = regionFromPath();
    const currentPath = path().map(value => value.toLowerCase().replaceAll(' ','_')).join('>');
    const assets = availableAssets().filter(a => a.subject_id === 'own_cohort' && a.timepoint === 'T0');

    if (levelName === 'macro') {
      return assets.filter(a => a.modality === 'hand' && (!region || assetRegion(a) === region || (region === 'palm' && ['front','back','side_left','side_right'].includes(String(a.view || '').toLowerCase()))));
    }

    const modality = levelName === 'tissue' ? 'wsi' : levelName === 'cellular' || levelName === 'cell' ? null : null;
    const candidates = assets.filter(a => {
      if (modality && a.modality !== modality) return false;
      if (!modality && !['microscopy','cellular'].includes(String(a.modality || '').toLowerCase())) return false;
      if (!matchesResolution(a, levelName)) return false;
      const assetPath = exactSpatialPath(a);
      if (assetPath && currentPath && !assetPath.includes(currentPath)) return false;
      // Deep evidence must be explicitly tied to the selected anatomical region.
      // Never fall back to an unrelated WSI/microscopy asset just because it exists.
      return !!region && assetRegion(a) === region;
    });

    return candidates;
  }
  function clear() { overlay.replaceChildren(); overlay.style.display = 'none'; activePreview = null; }
  function hideSyntheticDeep() {
    const manager = window.spatialViewportManager;
    if (!manager || level() === 'macro') return;
    if (manager.deepCanvas) { manager.deepCanvas.style.opacity = '0'; manager.deepCanvas.style.pointerEvents = 'none'; }
    if (manager.deepLabels) manager.deepLabels.style.opacity = '0';
    if (manager.deepTitle) manager.deepTitle.style.opacity = '0';
  }
  function restoreSyntheticDeep() {
    const manager = window.spatialViewportManager;
    if (!manager) return;
    if (manager.deepCanvas) { manager.deepCanvas.style.opacity = '1'; manager.deepCanvas.style.pointerEvents = 'auto'; }
    if (manager.deepLabels) manager.deepLabels.style.opacity = '1';
    if (manager.deepTitle) manager.deepTitle.style.opacity = '1';
  }
  function card(title, body, asset, warning = false) {
    const el = document.createElement('div');
    el.className = 'evidence-card';
    el.innerHTML = '<span class="eyebrow">REAL LINKED DATA</span><div class="title"></div><div class="meta"></div><div class="asset"></div>';
    el.querySelector('.title').textContent = title;
    el.querySelector('.meta').textContent = body;
    el.querySelector('.asset').textContent = asset ? `${artifactName(asset)} · ${asset.modality || 'unknown'} · ${asset.status || 'unknown'}` : '';
    if (warning) el.querySelector('.meta').classList.add('warning');
    overlay.appendChild(el);
  }
  function fitImage(img, holder) {
    const iw = img.naturalWidth || 1, ih = img.naturalHeight || 1;
    const scale = Math.min(holder.clientWidth / iw, holder.clientHeight / ih) * 0.94;
    img.dataset.scale = String(Math.max(0.05, scale));
    img.dataset.x = '0'; img.dataset.y = '0';
    applyTransform(img);
  }
  function applyTransform(img) {
    const scale = Number(img.dataset.scale || 1);
    const x = Number(img.dataset.x || 0), y = Number(img.dataset.y || 0);
    img.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
  }
  function bindPreview(holder, img) {
    let dragging = false, startX = 0, startY = 0, originX = 0, originY = 0;
    holder.addEventListener('pointerdown', event => { dragging = true; holder.classList.add('dragging'); startX = event.clientX; startY = event.clientY; originX = Number(img.dataset.x || 0); originY = Number(img.dataset.y || 0); holder.setPointerCapture(event.pointerId); });
    holder.addEventListener('pointermove', event => { if (!dragging) return; img.dataset.x = String(originX + event.clientX - startX); img.dataset.y = String(originY + event.clientY - startY); applyTransform(img); });
    holder.addEventListener('pointerup', () => { dragging = false; holder.classList.remove('dragging'); });
    holder.addEventListener('pointercancel', () => { dragging = false; holder.classList.remove('dragging'); });
    holder.addEventListener('wheel', event => { event.preventDefault(); const old = Number(img.dataset.scale || 1); const next = Math.max(0.05, Math.min(20, old * (event.deltaY < 0 ? 1.15 : 0.87))); img.dataset.scale = String(next); applyTransform(img); }, { passive: false });
  }
  function bindControls(img, holder) {
    const bind = (id, fn) => { const button = document.getElementById(id); if (button) button.onclick = fn; };
    bind('reset-view', () => fitImage(img, holder));
    bind('zoom-in', () => { img.dataset.scale = String(Math.min(20, Number(img.dataset.scale || 1) * 1.2)); applyTransform(img); });
    bind('zoom-out', () => { img.dataset.scale = String(Math.max(0.05, Number(img.dataset.scale || 1) * 0.83)); applyTransform(img); });
    bind('rotate-left', () => {}); bind('rotate-right', () => {});
    bind('zoom-region', () => fitImage(img, holder));
  }
  async function showPreview(asset, label) {
    const token = ++requestToken;
    const holder = document.createElement('div'); holder.className = 'preview';
    const img = document.createElement('img'); img.alt = artifactName(asset); img.draggable = false;
    const badgeEl = document.createElement('div'); badgeEl.className = 'preview-badge'; badgeEl.textContent = label.toUpperCase();
    const caption = document.createElement('div'); caption.className = 'preview-caption'; caption.textContent = `${artifactName(asset)} · pan + wheel zoom`;
    holder.append(img, badgeEl, caption); overlay.appendChild(holder);
    overlay.style.display = 'block'; activePreview = { img, holder };
    const usePreview = !IMAGE_EXTENSIONS.has(extension(asset)) || asset.modality === 'wsi';
    img.onload = () => { if (token !== requestToken) return; fitImage(img, holder); bindPreview(holder, img); bindControls(img, holder); };
    img.onerror = () => { if (token !== requestToken) return; holder.remove(); card('Preview unavailable', `The linked asset exists, but this browser/server cannot decode ${artifactName(asset)} into a preview. The original file remains the source of truth.`, asset, true); };
    img.src = usePreview ? `/api/spatial/preview/${encodeURIComponent(asset.asset_id)}` : `/api/spatial/evidence/${encodeURIComponent(asset.asset_id)}`;
  }
  async function render() {
    const currentLevel = level();
    const currentPath = path();
    const currentTarget = target();
    const state = `${currentLevel}|${currentPath.join('>')}|${currentTarget}`;
    if (state === lastState && analysis) return;
    lastState = state; clear();
    if (currentLevel === 'macro') { restoreSyntheticDeep(); return; }
    hideSyntheticDeep();
    const assets = assetsFor(currentLevel);
    if (currentLevel === 'tissue') {
      if (assets.length) await showPreview(assets[0], 'TISSUE / WSI');
      else { card('Tissue navigation only', 'No WSI asset is explicitly linked to this target. No tissue image is fabricated.'); overlay.style.display = 'block'; }
      return;
    }
    if (currentLevel === 'cellular') {
      if (assets.length) await showPreview(assets[0], 'MICROSCOPY FIELD');
      else { card('Cellular navigation only', 'No microscopy asset is explicitly linked to this target.'); overlay.style.display = 'block'; }
      return;
    }
    if (currentLevel === 'cell') {
      if (assets.length) {
        await showPreview(assets[0], 'PARENT MICROSCOPY SOURCE');
        card(currentTarget, 'This cell target is navigation-only until explicit cell coordinates or segmentation are linked. The preview is the real parent microscopy source; no synthetic cell location is claimed.', assets[0]);
      } else {
        card(currentTarget, 'Navigation target only. No cellular evidence is explicitly linked to this region.', null, true); overlay.style.display = 'block';
      }
    }
  }
  async function loadAnalysis() {
    try {
      const response = await fetch('/api/hand/analysis?subject_id=own_cohort&timepoint=T0', { cache: 'no-store' });
      if (!response.ok) return;
      analysis = await response.json(); lastState = ''; render();
    } catch (_) {}
  }
  const observer = new MutationObserver(() => render());
  [breadcrumb, node, badge].forEach(el => observer.observe(el, { childList: true, subtree: true, characterData: true, attributes: true }));
  window.addEventListener('hand-analysis-updated', event => { analysis = event.detail || analysis; lastState = ''; render(); });
  window.addEventListener('resize', () => { if (activePreview) fitImage(activePreview.img, activePreview.holder); });
  loadAnalysis();
})();
