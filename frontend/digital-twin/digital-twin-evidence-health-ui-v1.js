(() => {
  'use strict';

  const KEY = '__testhpDigitalTwinEndUserUIV1';
  if (window[KEY]) return;

  const MODALITIES = [
    ['hand_images', 'Hand Images'],
    ['hand_video', 'Hand Video'],
    ['hand_3d', '3D Scan'],
    ['tissue_wsi', 'WSI'],
    ['single_cell_rna', 'RNA'],
    ['proteomics', 'Proteomics'],
    ['epigenetics', 'Epigenetics'],
    ['genomics', 'Genomics']
  ];
  const REGIONS = ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'];
  const SCALES = [
    ['hand', 'Whole hand', 'Anatomy'],
    ['region', 'Region', 'Anatomy'],
    ['tissue', 'Tissue', 'Microscopic'],
    ['cell', 'Cell', 'Single cell'],
    ['molecular', 'Molecular', 'Molecular state']
  ];

  const state = {
    analysis: null,
    region: 'palm',
    scale: 'region',
    selectedCell: null,
    rotation: -7,
    zoom: 1,
    dragging: false,
    dragX: 0
  };

  const esc = value => String(value ?? '').replace(/[&<>\"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', "'":'&#39;' }[ch]));
  const available = asset => ['ready', 'available', 'verified'].includes(String(asset?.status || '').toLowerCase());
  const assets = () => Array.isArray(state.analysis?.assets) ? state.analysis.assets : [];

  function aliasesFor(modality) {
    return {
      hand_images: ['hand', 'hand_images', 'image'],
      hand_video: ['hand_video', 'video'],
      hand_3d: ['hand_3d', '3d', 'mesh'],
      tissue_wsi: ['wsi', 'tissue_wsi'],
      single_cell_rna: ['rna', 'single_cell_rna', 'scrna'],
      proteomics: ['proteomics', 'protein'],
      epigenetics: ['epigenetics', 'methylation', 'chromatin'],
      genomics: ['genomics', 'genome', 'variant']
    }[modality] || [modality];
  }

  function hasModality(modality) {
    const names = aliasesFor(modality);
    return assets().some(a => available(a) && names.includes(String(a.modality || '').toLowerCase()));
  }

  function evidenceScore() {
    return Math.round((MODALITIES.filter(([id]) => hasModality(id)).length / MODALITIES.length) * 100);
  }

  function confidenceScore() {
    const values = assets().filter(available).map(a => Number(a.confidence)).filter(Number.isFinite).map(v => Math.max(0, Math.min(1, v)));
    return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length * 100) : null;
  }

  function healthForRegion(region) {
    const assessments = Array.isArray(state.analysis?.assessments) ? state.analysis.assessments : [];
    const item = assessments.find(a => String(a.region_id || a.regionId || '').toLowerCase() === region);
    if (!item) return { state: 'Not established', confidence: null, evidence: [] };
    const value = String(item.health_state || item.state || item.label || 'Unknown');
    const normalized = ['healthy', 'at risk', 'diseased', 'unknown'].includes(value.toLowerCase()) ? value : 'Unknown';
    return { state: normalized, confidence: Number.isFinite(Number(item.confidence)) ? Number(item.confidence) : null, evidence: Array.isArray(item.evidence) ? item.evidence : [] };
  }

  function cellsForRegion(region) {
    const cells = Array.isArray(state.analysis?.cells) ? state.analysis.cells : [];
    return cells.filter(c => String(c.region_id || c.regionId || region).toLowerCase() === region);
  }

  function cellSummary(region) {
    const groups = new Map();
    cellsForRegion(region).forEach(c => {
      const type = c.cell_type || c.cellType || 'Unclassified';
      groups.set(type, (groups.get(type) || 0) + 1);
    });
    return [...groups.entries()].map(([type, count]) => ({ type, count }));
  }

  function selectedRegionLabel() {
    return state.region[0].toUpperCase() + state.region.slice(1);
  }

  function selectedScaleLabel() {
    return SCALES.find(([id]) => id === state.scale)?.[1] || 'Region';
  }

  function emitRegionChange() {
    window.dispatchEvent(new CustomEvent('testhp:end-user-region-changed', { detail: { region: state.region } }));
    const viewer = window.TestHPTwinViewerState;
    if (viewer?.selectRegion) viewer.selectRegion(state.region);
  }

  function setRegion(region) {
    if (!REGIONS.includes(region)) return;
    state.region = region;
    state.selectedCell = null;
    render();
    emitRegionChange();
  }

  function setScale(scale) {
    if (!SCALES.some(([id]) => id === scale)) return;
    state.scale = scale;
    state.selectedCell = null;
    render();
  }

  function handSvg() {
    const selected = state.region;
    const regionPath = (id, label, d, cls = '') => `<path class="twin-hand-region ${id === selected ? 'selected' : ''} ${cls}" data-region="${id}" d="${d}" tabindex="0" role="button" aria-label="${label}"/>`;
    return `
      <svg class="twin-hand-svg" viewBox="0 0 420 560" aria-label="Interactive hand model" role="img">
        <defs>
          <linearGradient id="handSurface" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#dbe7f4"/>
            <stop offset="0.52" stop-color="#9fb5cb"/>
            <stop offset="1" stop-color="#637d98"/>
          </linearGradient>
          <filter id="handShadow" x="-30%" y="-20%" width="160%" height="160%"><feDropShadow dx="0" dy="14" stdDeviation="13" flood-opacity=".28"/></filter>
        </defs>
        <g class="twin-hand-geometry" filter="url(#handShadow)">
          <path class="hand-base" d="M118 456 C105 421 105 367 111 319 C117 274 125 242 143 223 C155 210 173 207 189 214 C200 218 207 228 208 241 L208 116 C208 96 222 82 239 82 C257 82 268 96 268 114 L268 214 L270 73 C270 53 284 40 301 41 C319 42 329 56 329 75 L328 219 L331 100 C332 81 346 68 362 70 C379 72 389 86 388 104 L382 249 C380 264 389 278 398 293 C407 308 409 329 404 351 C394 397 373 436 348 470 C331 492 308 505 279 511 L178 511 C151 505 129 487 118 456 Z"/>
          ${regionPath('wrist', 'Wrist', 'M112 392 C110 431 111 468 124 489 C138 511 157 521 181 525 L283 525 C315 520 340 505 357 478 L340 436 C320 451 301 458 277 460 L169 457 C147 451 128 429 112 392 Z', 'wrist')}
          ${regionPath('palm', 'Palm', 'M121 319 C126 275 132 244 147 226 C161 210 180 207 194 216 C207 224 210 238 210 256 L210 367 C207 405 188 439 169 457 C145 449 126 426 116 398 C110 376 113 343 121 319 Z', 'palm')}
          ${regionPath('thumb', 'Thumb', 'M146 228 C158 211 180 205 195 214 C207 221 214 237 215 255 L229 329 C234 351 224 369 206 377 C187 385 169 373 163 354 L151 295 C145 274 139 246 146 228 Z', 'thumb')}
          ${regionPath('index', 'Index finger', 'M208 244 L208 115 C208 95 222 82 239 82 C257 82 268 96 268 114 L267 247 C266 265 254 277 238 277 C221 277 209 265 208 244 Z', 'finger')}
          ${regionPath('middle', 'Middle finger', 'M269 245 L270 73 C270 53 284 40 301 41 C319 42 329 56 329 75 L328 249 C327 268 315 280 299 280 C282 280 270 266 269 245 Z', 'finger')}
          ${regionPath('ring', 'Ring finger', 'M328 248 L331 100 C332 81 346 68 362 70 C379 72 389 86 388 104 L382 252 C381 271 368 282 352 281 C337 280 327 267 328 248 Z', 'finger')}
          ${regionPath('little', 'Little finger', 'M382 250 L386 150 C387 132 399 120 413 123 C427 126 434 138 433 155 L426 270 C425 289 414 302 400 301 C386 300 379 280 382 250 Z', 'finger')}
          <path class="hand-highlight" d="M160 253 C175 230 195 231 202 249 M224 113 C224 101 232 95 241 96 M286 72 C286 59 295 54 303 56"/>
        </g>
      </svg>`;
  }

  function modelPanel() {
    const modelClass = state.dragging ? 'dragging' : '';
    const cellCount = cellsForRegion(state.region).length;
    const modelStatus = state.scale === 'cell' ? (cellCount ? `${cellCount} linked cells` : 'No linked cells') : state.scale === 'molecular' ? 'Molecular layer' : selectedScaleLabel();
    return `
      <section class="twin-model-panel" aria-label="Digital twin model">
        <div class="model-toolbar">
          <div><span class="eyebrow">Interactive model</span><h1>${esc(selectedRegionLabel())}</h1></div>
          <div class="model-actions"><button type="button" data-model-action="reset" title="Reset view">Reset</button><button type="button" data-model-action="zoom-out">−</button><span>${Math.round(state.zoom * 100)}%</span><button type="button" data-model-action="zoom-in">+</button></div>
        </div>
        <div class="model-stage ${modelClass}" id="twin-model-stage" aria-label="Drag to rotate. Scroll to zoom.">
          <div class="model-orbit" style="transform:perspective(900px) rotateY(${state.rotation}deg) scale(${state.zoom});">
            ${handSvg()}
          </div>
          <div class="model-overlay"><span class="live-dot"></span>${esc(modelStatus)}</div>
          <div class="model-hint">Drag to rotate · scroll to zoom · click a region</div>
        </div>
        <div class="model-legend"><span><i class="legend-selected"></i>Selected region</span><span><i class="legend-neutral"></i>Available geometry</span></div>
      </section>`;
  }

  function scalePanel() {
    return `<div class="side-section"><div class="section-heading"><span>Scale</span><span class="section-meta">${esc(selectedScaleLabel())}</span></div><div class="scale-list">${SCALES.map(([id, label, sub]) => `<button type="button" class="scale-item ${state.scale === id ? 'active' : ''}" data-scale="${id}"><span class="scale-index">${SCALES.findIndex(x => x[0] === id) + 1}</span><span><strong>${label}</strong><small>${sub}</small></span></button>`).join('')}</div></div>`;
  }

  function regionPanel() {
    return `<div class="side-section"><div class="section-heading"><span>Region</span><span class="section-meta">${esc(selectedRegionLabel())}</span></div><div class="region-list">${REGIONS.map(region => `<button type="button" class="region-item ${state.region === region ? 'active' : ''}" data-region="${region}"><span>${region === state.region ? '●' : '○'}</span>${esc(region[0].toUpperCase() + region.slice(1))}</button>`).join('')}</div></div>`;
  }

  function biologicalState() {
    const health = healthForRegion(state.region);
    const confidence = health.confidence == null ? confidenceScore() : Math.round(health.confidence * 100);
    const cells = cellsForRegion(state.region).length;
    return `<section class="info-card biological-card"><div class="card-heading"><span>Biological state</span><span class="status-chip">${health.state === 'Not established' ? 'NOT ESTABLISHED' : esc(health.state)}</span></div>
      <div class="state-grid">
        <div class="state-metric"><span>Health</span><strong>${esc(health.state)}</strong><small>Region-level assessment</small></div>
        <div class="state-metric"><span>Biological age</span><strong>Not established</strong><small>No validated age result</small></div>
        <div class="state-metric"><span>Uncertainty</span><strong>—</strong><small>Not established</small></div>
        <div class="state-metric"><span>Cells</span><strong>${cells || '—'}</strong><small>${cells ? 'linked to region' : 'no cell evidence'}</small></div>
      </div>
      <div class="confidence-row"><span>Confidence</span><strong>${confidence == null ? '—' : confidence + '%'}</strong></div>
      <p class="disclaimer">Biological state is shown only when supported by upstream validated results. Missing evidence never implies health or disease.</p>
    </section>`;
  }

  function evidencePanel() {
    const coverage = evidenceScore();
    const missing = MODALITIES.filter(([id]) => !hasModality(id));
    return `<section class="info-card evidence-card"><div class="card-heading"><span>Evidence</span><strong>${coverage}%</strong></div>
      <div class="coverage-bar"><i style="width:${coverage}%"></i></div>
      <p class="coverage-note">Coverage = availability of declared modalities. It is not a clinical confidence score.</p>
      <div class="evidence-list">${MODALITIES.map(([id, label]) => `<div class="evidence-row"><span>${esc(label)}</span><b class="evidence-status ${hasModality(id) ? 'available' : 'missing'}">${hasModality(id) ? 'Available' : 'Missing'}</b></div>`).join('')}</div>
      <div class="missing-summary"><span>${missing.length} missing</span>${missing.length ? `<small>${esc(missing.map(x => x[1]).join(' · '))}</small>` : '<small>All declared modalities available</small>'}</div>
    </section>`;
  }

  function detailStrip() {
    const summaries = cellSummary(state.region);
    const cellTotal = summaries.reduce((sum, x) => sum + x.count, 0);
    const molecularAvailable = MODALITIES.filter(([id]) => ['single_cell_rna','proteomics','epigenetics','genomics'].includes(id) && hasModality(id)).length;
    return `<section class="detail-strip"><div class="detail-item"><span>Current view</span><strong>${esc(selectedScaleLabel())}</strong><small>${esc(selectedRegionLabel())}</small></div><div class="detail-item"><span>Cell layer</span><strong>${cellTotal || 'Not established'}</strong><small>${cellTotal ? 'linked observations' : 'no validated cell observations'}</small></div><div class="detail-item"><span>Molecular layer</span><strong>${molecularAvailable ? molecularAvailable + '/4' : 'Not established'}</strong><small>RNA · proteins · epigenetics · genomics</small></div><div class="detail-item"><span>Decision support</span><strong>Not established</strong><small>Research interface only</small></div></section>`;
  }

  function render() {
    const host = document.getElementById('testhp-end-user-layer');
    if (!host) return;
    const subject = state.analysis?.subject_id || state.analysis?.subjectId || 'own_cohort';
    const timepoint = state.analysis?.timepoint || 'T0';
    host.innerHTML = `
      <main class="twin-app" aria-label="Human Digital Twin">
        <header class="twin-header">
          <div class="brand"><span class="brand-mark">DT</span><div><strong>Human Digital Twin</strong><small>Multiscale biological model</small></div></div>
          <div class="context-bar"><span>Subject <b>${esc(subject)}</b></span><span>Timepoint <b>${esc(timepoint)}</b></span><span>Region <b>${esc(selectedRegionLabel())}</b></span><span>Scale <b>${esc(selectedScaleLabel())}</b></span></div>
        </header>
        <div class="twin-layout">
          <aside class="left-rail">${scalePanel()}${regionPanel()}<div class="left-note"><span class="eyebrow">Navigation</span><p>Move from hand → region → tissue → cell → molecular state without leaving the same digital twin.</p></div></aside>
          ${modelPanel()}
          <aside class="right-rail">${biologicalState()}${evidencePanel()}</aside>
        </div>
        ${detailStrip()}
        <footer class="twin-footer"><span>Evidence-first interface</span><span>Absence of data is not evidence of disease.</span><span>Decision support only</span></footer>
      </main>`;

    bindEvents(host);
  }

  function bindEvents(host) {
    host.querySelectorAll('[data-scale]').forEach(button => button.addEventListener('click', () => setScale(button.dataset.scale)));
    host.querySelectorAll('[data-region]').forEach(button => button.addEventListener('click', () => setRegion(button.dataset.region)));
    host.querySelectorAll('[data-model-action]').forEach(button => button.addEventListener('click', () => {
      const action = button.dataset.modelAction;
      if (action === 'reset') { state.rotation = -7; state.zoom = 1; }
      if (action === 'zoom-in') state.zoom = Math.min(1.45, state.zoom + 0.1);
      if (action === 'zoom-out') state.zoom = Math.max(0.75, state.zoom - 0.1);
      render();
    }));

    const stage = host.querySelector('#twin-model-stage');
    if (!stage) return;
    stage.addEventListener('wheel', event => { event.preventDefault(); state.zoom = Math.max(0.75, Math.min(1.45, state.zoom + (event.deltaY < 0 ? 0.08 : -0.08))); render(); }, { passive: false });
    stage.addEventListener('pointerdown', event => { state.dragging = true; state.dragX = event.clientX; stage.setPointerCapture?.(event.pointerId); });
    stage.addEventListener('pointermove', event => { if (!state.dragging) return; const dx = event.clientX - state.dragX; state.dragX = event.clientX; state.rotation = Math.max(-55, Math.min(55, state.rotation + dx * 0.35)); const orbit = host.querySelector('.model-orbit'); if (orbit) orbit.style.transform = `perspective(900px) rotateY(${state.rotation}deg) scale(${state.zoom})`; });
    stage.addEventListener('pointerup', () => { state.dragging = false; });
    stage.addEventListener('pointercancel', () => { state.dragging = false; });
    stage.addEventListener('pointerleave', () => { state.dragging = false; });
  }

  function mount() {
    let host = document.getElementById('testhp-end-user-layer');
    if (!host) { host = document.createElement('div'); host.id = 'testhp-end-user-layer'; document.body.appendChild(host); }
    if (!document.getElementById('testhp-end-user-layer-style')) {
      const style = document.createElement('style');
      style.id = 'testhp-end-user-layer-style';
      style.textContent = `
        :root{color-scheme:dark}.twin-app{min-height:100vh;background:#0a0f16;color:#e7edf5;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;letter-spacing:.005em}.twin-header{height:72px;display:flex;align-items:center;justify-content:space-between;padding:0 28px;border-bottom:1px solid #202a38;background:#0c121b;position:sticky;top:0;z-index:10}.brand{display:flex;align-items:center;gap:12px}.brand-mark{display:grid;place-items:center;width:34px;height:34px;border:1px solid #40536b;border-radius:9px;background:#142033;color:#b8d6f5;font-size:11px;font-weight:800;letter-spacing:.08em}.brand strong{display:block;font-size:15px}.brand small{display:block;margin-top:2px;color:#718096;font-size:11px}.context-bar{display:flex;align-items:center;gap:24px;color:#7f8da2;font-size:12px}.context-bar b{color:#d8e0eb;font-weight:600;margin-left:5px}.twin-layout{display:grid;grid-template-columns:230px minmax(420px,1fr) 300px;min-height:calc(100vh - 72px)}.left-rail,.right-rail{background:#0d141e}.left-rail{border-right:1px solid #202a38;padding:22px 16px}.right-rail{border-left:1px solid #202a38;padding:18px}.side-section{margin-bottom:26px}.section-heading{display:flex;justify-content:space-between;align-items:center;padding:0 6px 10px;text-transform:uppercase;letter-spacing:.12em;font-size:10px;color:#68778d;font-weight:700}.section-meta{color:#aebbc9;letter-spacing:0}.scale-list{display:flex;flex-direction:column;gap:3px}.scale-item,.region-item{width:100%;border:1px solid transparent;background:transparent;color:#a7b3c4;text-align:left;border-radius:9px;cursor:pointer;transition:background .15s,border-color .15s,color .15s}.scale-item{display:flex;align-items:center;gap:10px;padding:10px 9px}.scale-item:hover,.region-item:hover{background:#141d29;color:#e8eef7}.scale-item.active{background:#152236;border-color:#2d435e;color:#e8f2ff}.scale-index{display:grid;place-items:center;width:22px;height:22px;border-radius:6px;background:#121b27;color:#65758a;font-size:10px}.scale-item.active .scale-index{background:#263c56;color:#c8e1fb}.scale-item strong{display:block;font-size:12px;font-weight:650}.scale-item small{display:block;margin-top:2px;color:#64748a;font-size:10px}.region-list{display:grid;grid-template-columns:1fr 1fr;gap:4px}.region-item{padding:8px 7px;font-size:12px}.region-item.active{background:#162335;color:#dcecff;border-color:#2b435d}.region-item span{font-size:8px;color:#6f87a0;margin-right:7px}.left-note{margin:30px 5px 0;padding:13px;border:1px solid #202d3e;border-radius:10px;background:#0b121b}.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:9px;color:#64758b;font-weight:750}.left-note p{margin:8px 0 0;color:#738197;font-size:11px;line-height:1.55}.twin-model-panel{position:relative;min-width:0;background:#0a1018;display:flex;flex-direction:column}.model-toolbar{display:flex;justify-content:space-between;align-items:center;padding:19px 24px 14px;border-bottom:1px solid #192433}.model-toolbar h1{margin:4px 0 0;font-size:19px;font-weight:600;color:#edf3fa}.model-actions{display:flex;align-items:center;gap:7px;color:#728197}.model-actions button{height:28px;min-width:28px;border:1px solid #2b394c;border-radius:7px;background:#111a26;color:#aab8ca;cursor:pointer}.model-actions button:hover{background:#182536;color:#e7eef8}.model-actions span{font-size:10px;min-width:35px;text-align:center}.model-stage{position:relative;flex:1;min-height:610px;display:grid;place-items:center;overflow:hidden;touch-action:none;cursor:grab;background:radial-gradient(circle at 50% 44%,#162538 0,#0d1622 32%,#0a1018 68%)}.model-stage:before{content:"";position:absolute;width:430px;height:430px;border:1px solid #1c2b3c;border-radius:50%;box-shadow:0 0 0 34px rgba(29,47,67,.12),0 0 0 80px rgba(29,47,67,.06)}.model-stage.dragging{cursor:grabbing}.model-orbit{position:relative;z-index:1;transform-style:preserve-3d;transition:transform .16s ease}.model-stage.dragging .model-orbit{transition:none}.twin-hand-svg{width:min(420px,48vw);height:min(560px,64vh);overflow:visible}.hand-base{fill:url(#handSurface);stroke:#d5e4f3;stroke-width:2}.twin-hand-region{fill:rgba(77,103,130,.1);stroke:rgba(226,238,249,.32);stroke-width:1.4;cursor:pointer;transition:fill .15s,stroke .15s,filter .15s}.twin-hand-region:hover{fill:rgba(139,186,230,.25);stroke:#a8d0f3;filter:drop-shadow(0 0 8px rgba(126,186,237,.22))}.twin-hand-region.selected{fill:rgba(76,144,202,.4);stroke:#c4e4ff;stroke-width:2.4;filter:drop-shadow(0 0 12px rgba(90,169,230,.28))}.hand-highlight{fill:none;stroke:rgba(255,255,255,.28);stroke-width:3;stroke-linecap:round}.model-overlay{position:absolute;left:22px;top:20px;display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid #243448;background:rgba(11,18,28,.82);border-radius:8px;color:#9eacbf;font-size:11px;z-index:2;backdrop-filter:blur(8px)}.live-dot{width:6px;height:6px;border-radius:50%;background:#7ea8cc;box-shadow:0 0 0 4px rgba(126,168,204,.1)}.model-hint{position:absolute;bottom:18px;color:#5e6e83;font-size:10px;z-index:2}.model-legend{display:flex;gap:20px;padding:10px 24px 13px;border-top:1px solid #182433;color:#627287;font-size:10px}.model-legend i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px}.legend-selected{background:#79acd4}.legend-neutral{background:#46566a}.info-card{border:1px solid #243143;background:#101823;border-radius:11px;margin-bottom:14px;overflow:hidden}.biological-card{padding:15px}.card-heading{display:flex;align-items:center;justify-content:space-between;color:#9aa8bb;font-size:11px;text-transform:uppercase;letter-spacing:.1em;font-weight:700}.card-heading strong{font-size:23px;color:#e5edf6;letter-spacing:0}.status-chip{font-size:8px;letter-spacing:.1em;padding:5px 7px;border:1px solid #34475d;border-radius:99px;color:#8ea1b6}.state-grid{display:grid;grid-template-columns:1fr 1fr;margin:14px 0 11px;border-top:1px solid #202d3d;border-left:1px solid #202d3d}.state-metric{padding:11px 9px;border-right:1px solid #202d3d;border-bottom:1px solid #202d3d;min-height:72px}.state-metric span,.detail-item span{display:block;color:#64758b;font-size:9px;text-transform:uppercase;letter-spacing:.08em}.state-metric strong{display:block;margin-top:5px;color:#dbe5f0;font-size:12px;font-weight:650}.state-metric small{display:block;margin-top:3px;color:#58687d;font-size:9px;line-height:1.3}.confidence-row{display:flex;justify-content:space-between;padding:9px 0;border-top:1px solid #202d3d;color:#75849a;font-size:10px}.confidence-row strong{color:#b9cadc;font-size:12px}.disclaimer{margin:8px 0 0;color:#5e6e82;font-size:9px;line-height:1.45}.evidence-card{padding:15px}.coverage-bar{height:5px;background:#182433;border-radius:99px;overflow:hidden;margin:12px 0 8px}.coverage-bar i{display:block;height:100%;background:#719fc6;border-radius:inherit}.coverage-note{margin:0 0 12px;color:#66778d;font-size:9px;line-height:1.45}.evidence-list{border-top:1px solid #202d3d}.evidence-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #192636;font-size:10px;color:#8492a6}.evidence-status{font-size:9px;font-weight:600}.evidence-status.available{color:#8bbba2}.evidence-status.missing{color:#5c6b7e}.missing-summary{display:flex;flex-direction:column;gap:3px;padding-top:11px;color:#77869b;font-size:10px}.missing-summary small{color:#53647a;font-size:9px;line-height:1.4}.detail-strip{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid #202a38;border-bottom:1px solid #202a38;background:#0c131d}.detail-item{padding:14px 20px;border-right:1px solid #202a38}.detail-item:last-child{border-right:0}.detail-item strong{display:block;margin-top:5px;color:#d6e0eb;font-size:12px}.detail-item small{display:block;margin-top:3px;color:#58687c;font-size:9px}.twin-footer{display:flex;justify-content:space-between;padding:10px 20px;color:#4f6075;font-size:9px;background:#090e15}.twin-footer span:last-child{color:#6b7b90}@media(max-width:1100px){.twin-layout{grid-template-columns:200px minmax(360px,1fr) 270px}.context-bar{gap:12px}.context-bar span:nth-child(3),.context-bar span:nth-child(4){display:none}}@media(max-width:820px){.twin-header{padding:0 15px}.twin-layout{grid-template-columns:1fr}.left-rail,.right-rail{border:0;border-bottom:1px solid #202a38}.left-rail{display:grid;grid-template-columns:1fr 1fr;gap:14px}.left-note{display:none}.model-stage{min-height:520px}.right-rail{display:grid;grid-template-columns:1fr 1fr;gap:12px}.info-card{margin-bottom:0}.detail-strip{grid-template-columns:1fr 1fr}.context-bar{display:none}}@media(max-width:560px){.twin-header{height:60px}.brand small{display:none}.left-rail,.right-rail{display:block}.region-list{grid-template-columns:repeat(3,1fr)}.model-toolbar{padding:15px}.model-stage{min-height:440px}.twin-hand-svg{width:330px;height:440px}.model-stage:before{width:310px;height:310px}.detail-strip{grid-template-columns:1fr}.detail-item{border-right:0;border-bottom:1px solid #202a38}.twin-footer{display:none}}
      `;
      document.head.appendChild(style);
    }
    render();
  }

  function setAnalysis(analysis) { state.analysis = analysis || null; mount(); }

  window[KEY] = Object.freeze({ mount, setAnalysis });
  window.addEventListener('testhp:analysis-ready', event => setAnalysis(event.detail?.analysis || event.detail || null));
  window.addEventListener('testhp:digital-twin-analysis-ready', event => setAnalysis(event.detail?.analysis || event.detail || null));
  window.addEventListener('testhp:3d-semantic-state-changed', event => { if (event.detail?.selected?.id) { const id = String(event.detail.selected.id).toLowerCase(); if (REGIONS.includes(id) && id !== state.region) { state.region = id; render(); } } });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
