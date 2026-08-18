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

  const overlay = document.createElement('section');
  overlay.id = 'spatial-evidence-overlay';
  Object.assign(overlay.style, {
    position: 'absolute', inset: '58px 18px 58px 18px', zIndex: '35',
    display: 'none', pointerEvents: 'none', color: '#dcece6',
    fontFamily: 'system-ui, -apple-system, Segoe UI, sans-serif'
  });
  viewport.appendChild(overlay);

  const style = document.createElement('style');
  style.textContent = `
    #spatial-evidence-overlay .evidence-card {
      position:absolute; right:0; top:0; max-width:330px; padding:12px 14px;
      border:1px solid rgba(155,216,196,.28); border-radius:12px;
      background:rgba(8,18,19,.92); box-shadow:0 12px 32px rgba(0,0,0,.28);
      backdrop-filter:blur(8px); pointer-events:none;
    }
    #spatial-evidence-overlay .eyebrow {display:block;font-size:9px;letter-spacing:.14em;color:#9bd8c4;font-weight:800;margin-bottom:5px}
    #spatial-evidence-overlay .title {font-size:13px;font-weight:800;margin-bottom:5px}
    #spatial-evidence-overlay .meta {font-size:11px;color:#9fb7b0;line-height:1.45}
    #spatial-evidence-overlay .asset {margin-top:8px;padding-top:8px;border-top:1px solid rgba(155,216,196,.12);font-size:10px;color:#b9cbc5;line-height:1.45}
    #spatial-evidence-overlay .preview {position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:min(72%,720px);height:min(72%,460px);display:flex;align-items:center;justify-content:center;border:1px solid rgba(155,216,196,.24);border-radius:14px;overflow:hidden;background:#081315;box-shadow:0 18px 50px rgba(0,0,0,.34);pointer-events:none}
    #spatial-evidence-overlay img {width:100%;height:100%;object-fit:contain;display:block}
    #spatial-evidence-overlay .preview-caption {position:absolute;left:0;right:0;bottom:0;padding:8px 11px;background:linear-gradient(transparent,rgba(5,12,13,.92));font-size:10px;color:#dcece6}
    #spatial-evidence-overlay .linked {color:#9bd8c4;font-weight:800}
    #spatial-evidence-overlay .warning {color:#d6a64f;font-weight:800}
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
  function regionId(asset) {
    if (asset?.region_id) return String(asset.region_id);
    if (asset?.zone_id) return String(asset.zone_id);
    const mapping = asset?.artifact?.metadata?.anatomical_mapping;
    if (mapping?.region_id) return String(mapping.region_id);
    const location = asset?.observation?.anatomical_location;
    if (location?.id) return String(location.id).split('/').pop();
    if (location?.name) return String(location.name).toLowerCase().replaceAll(' ', '_');
    return '';
  }
  function artifactName(asset) {
    return asset?.filename || asset?.artifact?.metadata?.filename || asset?.artifact?.uri?.split(/[\\/]/).pop() || asset?.asset_id || 'linked asset';
  }
  function extension(asset) {
    const name = artifactName(asset).toLowerCase();
    return name.includes('.') ? name.split('.').pop() : '';
  }
  function assetsFor(levelName, region) {
    const assets = (analysis?.assets || []).filter(a => ['ready', 'available'].includes(String(a.status || '').toLowerCase()));
    if (levelName === 'macro') return assets.filter(a => a.modality === 'hand' && (regionId(a) === region || (region === 'palm' && ['front','back','side_left','side_right'].includes(String(a.view || '').toLowerCase()))));
    if (levelName === 'tissue') return assets.filter(a => a.modality === 'wsi' && (!region || regionId(a) === region));
    if (levelName === 'cellular' || levelName === 'cell') return assets.filter(a => ['microscopy','cellular'].includes(String(a.modality || '').toLowerCase()) && (!region || regionId(a) === region));
    return [];
  }
  function clear() { overlay.replaceChildren(); overlay.style.display = 'none'; }
  function card(title, body, asset) {
    const el = document.createElement('div');
    el.className = 'evidence-card';
    el.innerHTML = `<span class="eyebrow">LINKED RESEARCH DATA</span><div class="title"></div><div class="meta"></div><div class="asset"></div>`;
    el.querySelector('.title').textContent = title;
    el.querySelector('.meta').textContent = body;
    el.querySelector('.asset').textContent = asset ? `${artifactName(asset)} · ${asset.modality || 'unknown'} · ${asset.status || 'unknown'}` : '';
    overlay.appendChild(el);
  }
  function metadataOnly(levelName, assets) {
    const modality = levelName === 'tissue' ? 'WSI / tissue' : 'microscopy / cellular';
    if (!assets.length) {
      card('Navigation target only', `No explicitly linked ${modality} asset exists for this spatial target. The renderer remains a structural/navigation view and does not invent evidence.`);
      return;
    }
    const names = assets.slice(0, 3).map(artifactName).join(' · ');
    card(`${assets.length} linked ${modality} asset${assets.length === 1 ? '' : 's'}`, `The selected node is backed by explicit ingestion data. The available file format is not directly previewable as an in-browser image in this viewport.`, assets[0]);
    const extra = document.createElement('div');
    extra.className = 'evidence-card';
    extra.style.top = 'auto'; extra.style.bottom = '0'; extra.style.right = '0';
    extra.innerHTML = `<span class="eyebrow">ASSETS</span><div class="meta"></div>`;
    extra.querySelector('.meta').textContent = names;
    overlay.appendChild(extra);
  }
  async function preview(asset) {
    const token = ++requestToken;
    const cardAsset = asset;
    const ext = extension(asset);
    if (!IMAGE_EXTENSIONS.has(ext) || !asset?.asset_id || asset.modality !== 'hand') return false;
    const url = `/api/hand/evidence/${encodeURIComponent(asset.asset_id)}`;
    const image = new Image();
    image.alt = artifactName(asset);
    image.onload = () => {
      if (token !== requestToken) return;
      const holder = document.createElement('div');
      holder.className = 'preview';
      holder.appendChild(image);
      const caption = document.createElement('div');
      caption.className = 'preview-caption';
      caption.textContent = `${artifactName(cardAsset)} · ${cardAsset.view || 'macro view'}`;
      holder.appendChild(caption);
      overlay.appendChild(holder);
      overlay.style.display = 'block';
      card('Macro evidence', `Actual ingested hand image is displayed for this macro target.`, cardAsset);
    };
    image.onerror = () => {};
    image.src = url;
    return true;
  }
  async function render() {
    const currentPath = path();
    const currentLevel = level();
    const currentTarget = target();
    const region = currentPath.findLast?.((_, i) => i > 0) ? '' : '';
    const state = `${currentLevel}|${currentPath.join('>')}|${currentTarget}`;
    if (state === lastState && analysis) return;
    lastState = state;
    clear();
    const regionCandidates = currentPath.map(x => x.toLowerCase().replaceAll(' ', '_'));
    const regionIdGuess = regionCandidates.find(x => ['palm','thumb','index','middle','ring','little','wrist'].includes(x)) || '';
    const assets = assetsFor(currentLevel, regionIdGuess);
    if (currentLevel === 'macro' && assets.length) {
      await preview(assets[0]);
      if (!overlay.children.length) metadataOnly(currentLevel, assets);
      return;
    }
    if (currentLevel === 'cell') {
      if (assets.length) {
        card(currentTarget, `A cellular/microscopy asset is explicitly linked to the parent region. No cell coordinates/segmentation are present in the current evidence model, so this renderer does not fabricate a cell position.`, assets[0]);
      } else {
        card(currentTarget, `Navigation target only. No cellular asset is explicitly linked to the parent region.`);
      }
      overlay.style.display = 'block';
      return;
    }
    metadataOnly(currentLevel, assets);
    overlay.style.display = 'block';
  }
  async function loadAnalysis() {
    try {
      const response = await fetch(`/api/hand/analysis?subject_id=own_cohort&timepoint=T0`, { cache: 'no-store' });
      if (!response.ok) return;
      analysis = await response.json();
      render();
    } catch (_) {}
  }

  const observer = new MutationObserver(() => render());
  [breadcrumb, node, badge].forEach(el => observer.observe(el, {childList:true,subtree:true,characterData:true,attributes:true}));
  window.addEventListener('hand-analysis-updated', event => { analysis = event.detail || analysis; lastState = ''; render(); });
  window.addEventListener('resize', () => render());
  loadAnalysis();
})();
