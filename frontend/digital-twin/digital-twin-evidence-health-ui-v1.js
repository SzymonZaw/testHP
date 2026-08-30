(() => {
  'use strict';

  const KEY = '__testhpDigitalTwinEndUserUIV1';
  if (window[KEY]) return;

  const MODALITIES = [
    ['hand_images', 'Hand Images'], ['hand_video', 'Hand Video'], ['hand_3d', '3D Scan'], ['tissue_wsi', 'WSI'],
    ['single_cell_rna', 'RNA'], ['proteomics', 'Proteomics'], ['epigenetics', 'Epigenetics'], ['genomics', 'Genomics']
  ];
  const REGIONS = ['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'];
  const SCALES = [['hand', 'Whole hand'], ['region', 'Region'], ['tissue', 'Tissue'], ['cell', 'Cell'], ['molecular', 'Molecular']];
  const TIMEPOINTS = ['T0', 'T1', 'T2', 'T3'];

  const state = {
    analysis: null, region: 'palm', scale: 'region', selectedCell: null, cellTab: 'overview', timepoint: 'T0',
    rotation: -8, zoom: 1, dragging: false, dragX: 0, loading: false, error: null
  };

  const esc = value => String(value ?? '').replace(/[&<>\"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', "'":'&#39;' }[ch]));
  const available = asset => ['ready', 'available', 'verified'].includes(String(asset?.status || '').toLowerCase());
  const assets = () => Array.isArray(state.analysis?.assets) ? state.analysis.assets : [];
  const cells = () => Array.isArray(state.analysis?.cells) ? state.analysis.cells : [];
  const regionLabel = () => state.region[0].toUpperCase() + state.region.slice(1);
  const scaleLabel = () => SCALES.find(x => x[0] === state.scale)?.[1] || 'Region';

  function aliasesFor(modality) {
    return {
      hand_images: ['hand', 'hand_images', 'image'], hand_video: ['hand_video', 'video'], hand_3d: ['hand_3d', '3d', 'mesh'],
      tissue_wsi: ['wsi', 'tissue_wsi'], single_cell_rna: ['rna', 'single_cell_rna', 'scrna'], proteomics: ['proteomics', 'protein'],
      epigenetics: ['epigenetics', 'methylation', 'chromatin'], genomics: ['genomics', 'genome', 'variant']
    }[modality] || [modality];
  }
  function hasModality(modality) {
    const names = aliasesFor(modality);
    return assets().some(a => available(a) && names.includes(String(a.modality || '').toLowerCase()));
  }
  function coverage() { return Math.round(MODALITIES.filter(([id]) => hasModality(id)).length / MODALITIES.length * 100); }
  function confidence() {
    const values = assets().filter(available).map(a => Number(a.confidence)).filter(Number.isFinite).map(v => Math.max(0, Math.min(1, v)));
    return values.length ? Math.round(values.reduce((a,b) => a+b, 0) / values.length * 100) : null;
  }
  function regionCells() { return cells().filter(c => String(c.region_id || c.regionId || state.region).toLowerCase() === state.region); }
  function cellId(c, index) { return c?.cell_id || c?.cellId || c?.id || `A${String(index + 1).padStart(2, '0')}`; }
  function selectedCell() {
    if (!state.selectedCell) return null;
    const list = regionCells();
    const index = list.findIndex((c,i) => cellId(c,i) === state.selectedCell);
    return index >= 0 ? { data: list[index], index } : null;
  }
  function healthForRegion() {
    const assessments = Array.isArray(state.analysis?.assessments) ? state.analysis.assessments : [];
    const item = assessments.find(a => String(a.region_id || a.regionId || '').toLowerCase() === state.region);
    if (!item) return { state: 'Not established', confidence: null };
    const value = String(item.health_state || item.state || item.label || 'Unknown');
    const allowed = ['healthy', 'at risk', 'diseased', 'unknown'];
    return { state: allowed.includes(value.toLowerCase()) ? value : 'Unknown', confidence: Number.isFinite(Number(item.confidence)) ? Number(item.confidence) : null };
  }
  function cellValue(c, keys, fallback = 'Not established') {
    for (const key of keys) if (c && c[key] !== undefined && c[key] !== null && c[key] !== '') return c[key];
    return fallback;
  }

  function injectStyles() {
    if (document.getElementById('testhp-dt-clean-css')) return;
    const style = document.createElement('style');
    style.id = 'testhp-dt-clean-css';
    style.textContent = `
      :root{--bg:#07111d;--panel:#0c1826;--panel2:#101f30;--line:#203348;--text:#e9f1f8;--muted:#91a4b7;--accent:#67d7c7;--accent2:#77a8ff;--warn:#e8c77a;--danger:#e58b8b}
      *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% 0,#12283c 0,#07111d 42%,#050c14 100%);color:var(--text);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button{font:inherit;color:inherit}.dt-shell{min-height:100vh;padding:18px;display:flex;flex-direction:column;gap:14px}.dt-top{border:1px solid var(--line);background:rgba(8,18,30,.88);border-radius:16px;padding:15px 18px;display:flex;justify-content:space-between;align-items:center;gap:18px}.brand{font-weight:800;letter-spacing:.05em;text-transform:uppercase}.brand small{display:block;color:var(--muted);font-size:10px;letter-spacing:.18em;margin-top:2px}.context{display:flex;gap:9px;flex-wrap:wrap;justify-content:flex-end}.chip{border:1px solid var(--line);background:#0b1725;border-radius:999px;padding:6px 10px;color:#c7d5e2}.chip b{color:#fff;margin-left:4px}.layout{display:grid;grid-template-columns:230px minmax(420px,1fr) 300px;gap:14px;min-height:650px}.panel,.viewer,.info-card{border:1px solid var(--line);background:linear-gradient(180deg,rgba(14,29,44,.96),rgba(8,19,30,.96));border-radius:16px}.side{padding:15px;display:flex;flex-direction:column;gap:18px}.eyebrow,.section-title{font-size:10px;text-transform:uppercase;letter-spacing:.16em;color:var(--muted)}.section-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:9px}.section-head strong{font-size:11px;color:#d7e5ef}.scale-list,.region-list{display:flex;flex-direction:column;gap:5px}.scale-btn,.region-btn,.tab-btn,.time-btn{border:1px solid transparent;background:transparent;text-align:left;border-radius:10px;padding:9px;cursor:pointer}.scale-btn:hover,.region-btn:hover,.tab-btn:hover,.time-btn:hover{background:#122337}.scale-btn.active,.region-btn.active,.tab-btn.active,.time-btn.active{border-color:#2d5666;background:#102b36}.scale-btn{display:flex;gap:10px;align-items:center}.scale-num{width:23px;height:23px;border-radius:7px;background:#122237;color:#8ea5b8;display:grid;place-items:center;font-size:11px}.scale-btn.active .scale-num{background:var(--accent);color:#06151a}.scale-btn b{display:block}.scale-btn small{display:block;color:var(--muted);font-size:11px}.region-btn{display:flex;align-items:center;gap:8px;color:#b9c9d7}.region-btn.active{color:#fff}.region-dot{font-size:9px;color:var(--accent)}.viewer{position:relative;overflow:hidden;display:flex;flex-direction:column;min-height:650px}.viewer-head{padding:15px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}.crumb{color:#9fb2c4;font-size:12px}.crumb b{color:#fff}.viewer-actions{display:flex;gap:5px;align-items:center}.viewer-actions button{border:1px solid var(--line);background:#0d1b2a;border-radius:8px;padding:6px 9px;cursor:pointer}.model-stage{position:relative;flex:1;min-height:470px;display:grid;place-items:center;overflow:hidden;background:radial-gradient(circle at 50% 45%,#162f45 0,#0b1b2a 43%,#07111c 78%);cursor:grab}.model-stage.dragging{cursor:grabbing}.model-orbit{transition:transform .12s ease;transform-origin:center}.twin-hand-svg{width:min(480px,56vw);height:min(560px,62vh);overflow:visible}.hand-base{fill:#36556f;opacity:.8}.twin-hand-region{fill:#7898b0;fill-opacity:.58;stroke:#9db8ca;stroke-width:2;cursor:pointer;transition:fill .15s,fill-opacity .15s}.twin-hand-region:hover,.twin-hand-region.selected{fill:#67d7c7;fill-opacity:.8;stroke:#d7fff9}.hand-highlight{fill:none;stroke:#d5e6f0;stroke-opacity:.35;stroke-width:3;stroke-linecap:round}.model-overlay{position:absolute;top:16px;left:16px;border:1px solid var(--line);background:#07111dcc;border-radius:999px;padding:7px 10px;color:#c7d8e6}.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);margin-right:7px}.model-hint{position:absolute;bottom:15px;left:50%;transform:translateX(-50%);color:#8ea2b5;font-size:11px;background:#06101acc;border:1px solid var(--line);padding:7px 10px;border-radius:999px;white-space:nowrap}.cell-marker{position:absolute;width:13px;height:13px;border:2px solid #d9fff9;border-radius:50%;background:#4bc7b8;box-shadow:0 0 0 5px #4bc7b822;cursor:pointer}.cell-marker.selected{background:#fff;box-shadow:0 0 0 7px #67d7c733}.cell-layer{position:absolute;inset:0;pointer-events:none}.cell-layer .cell-marker{pointer-events:auto}.legend{padding:10px 16px;border-top:1px solid var(--line);display:flex;gap:18px;color:#8297aa;font-size:11px}.legend i{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent);margin-right:6px}.right{padding:15px;display:flex;flex-direction:column;gap:12px}.info-card{padding:14px}.card-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.card-title h2{font-size:12px;text-transform:uppercase;letter-spacing:.13em;margin:0}.status{font-size:9px;border:1px solid #31515e;border-radius:999px;padding:4px 7px;color:#a8c9cc}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:9px}.metric{border:1px solid var(--line);background:#0a1623;border-radius:10px;padding:10px}.metric span{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em}.metric strong{display:block;font-size:14px;margin-top:5px}.metric small{display:block;color:#6f8498;margin-top:3px}.confidence{display:flex;justify-content:space-between;border-top:1px solid var(--line);margin-top:12px;padding-top:10px}.confidence strong{font-size:16px}.disclaimer{color:#8094a7;font-size:10px;margin:10px 0 0}.coverage-head{display:flex;justify-content:space-between;align-items:end}.coverage-head strong{font-size:22px}.bar{height:5px;background:#142537;border-radius:999px;overflow:hidden;margin:8px 0 12px}.bar i{display:block;height:100%;background:var(--accent)}.evidence-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #17283a}.evidence-row:last-child{border-bottom:0}.ev{font-size:10px;border-radius:999px;padding:3px 7px}.ev.ok{color:#aee9df;background:#12322f}.ev.no{color:#8798a9;background:#121e2a}.missing{color:#8195a7;font-size:10px;margin-top:8px}.bottom{display:grid;grid-template-columns:1fr 1fr;gap:14px}.timeline,.support{padding:14px}.time-track{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}.time-btn{text-align:center;border:1px solid var(--line)}.time-btn b{display:block}.time-btn small{color:var(--muted)}.time-line{height:2px;background:#274054;position:relative;margin:5px 25px 0}.time-dot{position:absolute;top:50%;width:8px;height:8px;border-radius:50%;background:#6c8498;transform:translate(-50%,-50%)}.time-dot.active{background:var(--accent);box-shadow:0 0 0 5px #67d7c72b}.trajectory{display:flex;gap:8px;align-items:center;color:#8197aa;font-size:11px}.trajectory .node{width:10px;height:10px;border-radius:50%;background:#52697c}.trajectory .node.active{background:var(--accent)}.support p{margin:8px 0;color:#8498aa;font-size:11px}.action-card{padding:14px}.action-title{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted)}.not-established{border:1px dashed #375064;background:#0b1724;border-radius:10px;padding:10px;margin-top:9px}.not-established strong{display:block;color:#e8eef4;font-size:11px}.not-established span{display:block;color:#7f93a5;font-size:10px;margin-top:3px}.cell-inspector{grid-column:1/-1;display:grid;grid-template-columns:minmax(240px,.8fr) 1.5fr;border:1px solid #2b4d5b;border-radius:16px;overflow:hidden;background:#0a1723}.cell-visual{min-height:300px;display:grid;place-items:center;background:radial-gradient(circle,#173b49,#0b1a27 65%);border-right:1px solid var(--line)}.cell-sphere{width:180px;height:180px;border-radius:50%;background:radial-gradient(circle at 34% 28%,#d6fff6 0,#75d6c6 10%,#2c7f82 38%,#17394b 68%,#0b1a27 100%);box-shadow:inset -28px -24px 35px #06101a,0 0 60px #67d7c73a}.cell-content{padding:18px}.cell-content h2{margin:3px 0 2px;font-size:22px}.cell-type{color:var(--accent);font-size:12px}.cell-tabs{display:flex;gap:6px;border-bottom:1px solid var(--line);margin:16px 0 14px}.tab-btn{padding:7px 9px;color:#9eb0c0;font-size:11px}.cell-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.molecular-list{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.molecular-item{border:1px solid var(--line);border-radius:9px;padding:9px;background:#0b1724}.molecular-item b{display:block}.molecular-item span{font-size:10px;color:var(--muted)}.back-btn{border:0;background:transparent;color:#9eb2c4;padding:0;cursor:pointer}.loading{opacity:.7;pointer-events:none}.error{color:#e7aaaa;font-size:11px}
      @media(max-width:1100px){.layout{grid-template-columns:190px 1fr}.right{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr}.bottom{grid-template-columns:1fr}.cell-inspector{grid-column:1/-1}}@media(max-width:760px){.dt-shell{padding:8px}.dt-top{align-items:flex-start;flex-direction:column}.context{justify-content:flex-start}.layout{grid-template-columns:1fr}.side{display:grid;grid-template-columns:1fr 1fr}.right{grid-template-columns:1fr}.viewer{min-height:580px}.twin-hand-svg{width:320px}.cell-inspector{grid-template-columns:1fr}.cell-visual{border-right:0;border-bottom:1px solid var(--line)}.cell-grid,.molecular-list{grid-template-columns:1fr 1fr}}
    `;
    document.head.appendChild(style);
  }

  function handSvg() {
    const selected = state.region;
    const path = (id,label,d,cls='') => `<path class="twin-hand-region ${id===selected?'selected':''} ${cls}" data-region="${id}" d="${d}" tabindex="0" role="button" aria-label="${label}"/>`;
    return `<svg class="twin-hand-svg" viewBox="0 0 420 560" aria-label="Interactive hand model" role="img">
      <defs><filter id="dtShadow"><feDropShadow dx="0" dy="14" stdDeviation="12" flood-opacity=".3"/></filter></defs>
      <g filter="url(#dtShadow)"><path class="hand-base" d="M118 456C105 421 105 367 111 319C117 274 125 242 143 223C155 210 173 207 189 214C200 218 207 228 208 241V116C208 96 222 82 239 82C257 82 268 96 268 114V214L270 73C270 53 284 40 301 41C319 42 329 56 329 75L328 219L331 100C332 81 346 68 362 70C379 72 389 86 388 104L382 249C380 264 389 278 398 293C407 308 409 329 404 351C394 397 373 436 348 470C331 492 308 505 279 511L178 511C151 505 129 487 118 456Z"/>
      ${path('wrist','Wrist','M112 392C110 431 111 468 124 489C138 511 157 521 181 525L283 525C315 520 340 505 357 478L340 436C320 451 301 458 277 460L169 457C147 451 128 429 112 392Z','wrist')}
      ${path('palm','Palm','M121 319C126 275 132 244 147 226C161 210 180 207 194 216C207 224 210 238 210 256V367C207 405 188 439 169 457C145 449 126 426 116 398C110 376 113 343 121 319Z','palm')}
      ${path('thumb','Thumb','M146 228C158 211 180 205 195 214C207 221 214 237 215 255L229 329C234 351 224 369 206 377C187 385 169 373 163 354L151 295C145 274 139 246 146 228Z','finger')}
      ${path('index','Index finger','M208 244V115C208 95 222 82 239 82C257 82 268 96 268 114L267 247C266 265 254 277 238 277C221 277 209 265 208 244Z','finger')}
      ${path('middle','Middle finger','M269 245L270 73C270 53 284 40 301 41C319 42 329 56 329 75L328 249C327 268 315 280 299 280C282 280 270 266 269 245Z','finger')}
      ${path('ring','Ring finger','M328 248L331 100C332 81 346 68 362 70C379 72 389 86 388 104L382 252C381 271 368 282 352 281C337 280 327 267 328 248Z','finger')}
      ${path('little','Little finger','M382 250L386 150C387 132 399 120 413 123C427 126 434 138 433 155L426 270C425 289 414 302 400 301C386 300 379 280 382 250Z','finger')}
      <path class="hand-highlight" d="M160 253C175 230 195 231 202 249M224 113C224 101 232 95 241 96M286 72C286 59 295 54 303 56"/></g></svg>`;
  }

  function cellMarkers() {
    if (state.scale !== 'cell') return '';
    const list = regionCells();
    if (!list.length) return '';
    const positions = [[47,48],[52,43],[57,50],[43,55],[54,57],[49,61],[60,44],[40,48],[63,54],[45,40],[56,62],[38,58]];
    return `<div class="cell-layer">${list.slice(0,24).map((c,i)=>{const p=positions[i%positions.length];const id=cellId(c,i);return `<button class="cell-marker ${state.selectedCell===id?'selected':''}" style="left:${p[0]}%;top:${p[1]}%" data-cell="${esc(id)}" title="${esc(id)}" aria-label="Select cell ${esc(id)}"></button>`}).join('')}</div>`;
  }

  function viewer() {
    const status = state.scale === 'cell' ? (regionCells().length ? `${regionCells().length} linked cells` : 'No linked cells') : state.scale === 'molecular' ? 'Molecular layer' : scaleLabel();
    return `<section class="viewer" aria-label="Digital twin viewport"><div class="viewer-head"><div><button class="back-btn" data-action="back">← Back</button><div class="crumb" style="margin-top:5px">Hand / ${esc(regionLabel())} / <b>${esc(scaleLabel())}</b>${state.selectedCell ? ` / <b>${esc(state.selectedCell)}</b>` : ''}</div></div><div class="viewer-actions"><button data-model="reset">Reset</button><button data-model="minus">−</button><span>${Math.round(state.zoom*100)}%</span><button data-model="plus">+</button></div></div><div class="model-stage ${state.dragging?'dragging':''}" id="dt-stage"><div class="model-orbit" style="transform:perspective(900px) rotateY(${state.rotation}deg) scale(${state.zoom})">${handSvg()}</div>${cellMarkers()}<div class="model-overlay"><span class="live-dot"></span>${esc(status)}</div><div class="model-hint">Drag to rotate · scroll to zoom · click a region${state.scale==='cell'?' · select a cell':''}</div></div><div class="legend"><span><i></i>Selected region</span><span><i></i>Linked evidence geometry</span></div></section>`;
  }

  function scalePanel() { return `<div><div class="section-head"><span class="section-title">Scale</span><strong>${esc(scaleLabel())}</strong></div><div class="scale-list">${SCALES.map(([id,label],i)=>`<button class="scale-btn ${state.scale===id?'active':''}" data-scale="${id}"><span class="scale-num">${i+1}</span><span><b>${label}</b><small>${['Anatomy','Anatomy','Microscopic','Single cell','Molecular state'][i]}</small></span></button>`).join('')}</div></div>`; }
  function regionPanel() { return `<div><div class="section-head"><span class="section-title">Where?</span><strong>${esc(regionLabel())}</strong></div><div class="region-list">${REGIONS.map(r=>`<button class="region-btn ${r===state.region?'active':''}" data-region="${r}"><span class="region-dot">${r===state.region?'●':'○'}</span>${esc(r[0].toUpperCase()+r.slice(1))}</button>`).join('')}</div></div>`; }

  function biologicalState() {
    const h=healthForRegion(); const c=h.confidence==null?confidence():Math.round(h.confidence*100); const n=regionCells().length;
    return `<section class="info-card"><div class="card-title"><h2>Biological state</h2><span class="status">${esc(h.state.toUpperCase())}</span></div><div class="metrics"><div class="metric"><span>Health</span><strong>${esc(h.state)}</strong><small>Only validated upstream results</small></div><div class="metric"><span>Biological age</span><strong>Not established</strong><small>No validated age result</small></div><div class="metric"><span>Uncertainty</span><strong>—</strong><small>Not established</small></div><div class="metric"><span>Cells</span><strong>${n||'—'}</strong><small>${n?'linked to region':'no cell evidence'}</small></div></div><div class="confidence"><span>Confidence</span><strong>${c==null?'—':c+'%'}</strong></div><p class="disclaimer">Missing evidence never implies health or disease. A state is shown only when supported by an upstream result.</p></section>`;
  }
  function evidencePanel() { const cov=coverage(); const missing=MODALITIES.filter(([id])=>!hasModality(id)); return `<section class="info-card"><div class="coverage-head"><div><div class="section-title">Evidence</div><div style="color:#8195a7;font-size:10px">Declared modalities available</div></div><strong>${cov}%</strong></div><div class="bar"><i style="width:${cov}%"></i></div>${MODALITIES.map(([id,label])=>`<div class="evidence-row"><span>${esc(label)}</span><b class="ev ${hasModality(id)?'ok':'no'}">${hasModality(id)?'Available':'Missing'}</b></div>`).join('')}<div class="missing">${missing.length} missing · coverage is not clinical confidence</div></section>`; }

  function timeline() { return `<section class="panel timeline"><div class="section-head"><span class="section-title">Time</span><strong>${esc(state.timepoint)}</strong></div><div class="time-track">${TIMEPOINTS.map((t,i)=>`<button class="time-btn ${state.timepoint===t?'active':''}" data-time="${t}"><b>${t}</b><small>${i===0?'Observed':'Not established'}</small></button>`).join('')}</div><div class="time-line">${TIMEPOINTS.map((t,i)=>`<span class="time-dot ${state.timepoint===t?'active':''}" style="left:${i/3*100}%"></span>`).join('')}</div></section>`; }
  function supportPanel() { return `<section class="panel support"><div class="section-title">Trajectory / Future</div><div class="trajectory" style="margin-top:12px">NOW <span class="node active"></span> T0 <span>→</span> <span class="node"></span> T1 <span>→</span> <span class="node"></span> T2 <span>→</span> <span class="node"></span> T3</div><p>Predicted trajectory is not established until a validated model and supporting data are available.</p><div class="not-established"><strong>INTERVENTION SUPPORT · NOT ESTABLISHED</strong><span>Insufficient validated evidence for an intervention recommendation.</span></div></section>`; }

  function cellInspector() {
    const picked=selectedCell(); if (!picked) return '';
    const c=picked.data; const type=cellValue(c,['cell_type','cellType','type'],'Unclassified');
    const health=cellValue(c,['health_state','healthState','state','label'],'Not established');
    const age=cellValue(c,['biological_age','biologicalAge','age'],'Not established');
    const confidenceValue=Number(c?.confidence); const conf=Number.isFinite(confidenceValue)?Math.round(confidenceValue*100)+'%':'—';
    const tab=state.cellTab;
    let body='';
    if(tab==='molecular') body=`<div class="molecular-list"><div class="molecular-item"><b>RNA</b><span>${hasModality('single_cell_rna')?'Available':'Not available'}</span></div><div class="molecular-item"><b>Proteomics</b><span>${hasModality('proteomics')?'Available':'Not available'}</span></div><div class="molecular-item"><b>Epigenetics</b><span>${hasModality('epigenetics')?'Available':'Not available'}</span></div><div class="molecular-item"><b>Genomics</b><span>${hasModality('genomics')?'Available':'Not available'}</span></div></div>`;
    else if(tab==='morphology') body=`<div class="cell-grid"><div class="metric"><span>Cell type</span><strong>${esc(type)}</strong></div><div class="metric"><span>Morphology</span><strong>${esc(cellValue(c,['morphology','morphology_state'],'Not established'))}</strong></div><div class="metric"><span>Evidence</span><strong>${hasModality('hand_images')?'Imaging':'Not available'}</strong></div></div>`;
    else if(tab==='state') body=`<div class="cell-grid"><div class="metric"><span>Health</span><strong>${esc(health)}</strong></div><div class="metric"><span>Biological age</span><strong>${esc(age)}</strong></div><div class="metric"><span>Confidence</span><strong>${conf}</strong></div></div>`;
    else body=`<div class="cell-grid"><div class="metric"><span>Type</span><strong>${esc(type)}</strong></div><div class="metric"><span>Health</span><strong>${esc(health)}</strong></div><div class="metric"><span>Biological age</span><strong>${esc(age)}</strong></div></div><p class="disclaimer">Cell A17-style identity is a spatial/data identifier, not a diagnosis. Molecular and clinical states remain not established when unsupported.</p>`;
    return `<section class="cell-inspector" id="cell-inspector"><div class="cell-visual"><div class="cell-sphere" aria-label="Cell visualization"></div></div><div class="cell-content"><button class="back-btn" data-action="close-cell">← ${esc(regionLabel())} / Tissue</button><h2>${esc(state.selectedCell)}</h2><div class="cell-type">${esc(type)}</div><div class="cell-tabs">${[['overview','Overview'],['morphology','Morphology'],['state','State'],['molecular','Molecular']].map(([id,label])=>`<button class="tab-btn ${tab===id?'active':''}" data-cell-tab="${id}">${label}</button>`).join('')}</div>${body}</div></section>`;
  }

  function render() {
    injectStyles();
    const root=document.getElementById('testhp-end-user-layer'); if(!root) return;
    root.innerHTML=`<main class="dt-shell ${state.loading?'loading':''}"><header class="dt-top"><div class="brand">Human Digital Twin<small>multiscale biological workspace</small></div><div class="context"><span class="chip">Subject <b>${esc(new URLSearchParams(location.search).get('subject_id')||'own_cohort')}</b></span><span class="chip">Timepoint <b>${esc(state.timepoint)}</b></span><span class="chip">Region <b>${esc(regionLabel())}</b></span><span class="chip">Scale <b>${esc(scaleLabel())}</b></span></div></header><div class="layout"><aside class="panel side">${scalePanel()}${regionPanel()}</aside>${viewer()}<aside class="right">${biologicalState()}${evidencePanel()}<section class="action-card"><div class="action-title">Intervention</div><div class="not-established"><strong>NOT ESTABLISHED</strong><span>Decision support only. No clinical recommendation is generated from missing evidence.</span></div></section></aside>${cellInspector()}</div><div class="bottom">${timeline()}${supportPanel()}</div>${state.error?`<div class="error">${esc(state.error)}</div>`:''}</main>`;
    bind();
  }

  function bind() {
    document.querySelectorAll('[data-scale]').forEach(b=>b.onclick=()=>{state.scale=b.dataset.scale;state.selectedCell=null;render()});
    document.querySelectorAll('[data-region]').forEach(b=>b.onclick=()=>{state.region=b.dataset.region;state.selectedCell=null;window.dispatchEvent(new CustomEvent('testhp:end-user-region-changed',{detail:{region:state.region}}));render()});
    document.querySelectorAll('[data-cell]').forEach(b=>b.onclick=()=>{state.selectedCell=b.dataset.cell;state.scale='cell';render();document.getElementById('cell-inspector')?.scrollIntoView({behavior:'smooth',block:'nearest'})});
    document.querySelectorAll('[data-cell-tab]').forEach(b=>b.onclick=()=>{state.cellTab=b.dataset.cellTab;render()});
    document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>loadTimepoint(b.dataset.time));
    document.querySelectorAll('[data-action="close-cell"]').forEach(b=>b.onclick=()=>{state.selectedCell=null;state.scale='cell';render()});
    document.querySelectorAll('[data-action="back"]').forEach(b=>b.onclick=()=>{if(state.selectedCell){state.selectedCell=null;render()}else if(state.scale!=='region'){state.scale='region';render()}});
    document.querySelectorAll('[data-model]').forEach(b=>b.onclick=()=>{const a=b.dataset.model;if(a==='reset'){state.zoom=1;state.rotation=-8}else if(a==='plus')state.zoom=Math.min(1.8,state.zoom+.1);else if(a==='minus')state.zoom=Math.max(.65,state.zoom-.1);render()});
    const stage=document.getElementById('dt-stage'); if(stage){stage.addEventListener('wheel',e=>{e.preventDefault();state.zoom=Math.max(.65,Math.min(1.8,state.zoom+(e.deltaY<0?.08:-.08)));render()},{passive:false});stage.addEventListener('pointerdown',e=>{state.dragging=true;state.dragX=e.clientX;stage.setPointerCapture(e.pointerId);render()});stage.addEventListener('pointermove',e=>{if(!state.dragging)return;state.rotation+=((e.clientX-state.dragX)/3);state.dragX=e.clientX;const orbit=document.querySelector('.model-orbit');if(orbit)orbit.style.transform=`perspective(900px) rotateY(${state.rotation}deg) scale(${state.zoom})`});stage.addEventListener('pointerup',()=>{state.dragging=false;render()});}
  }

  async function loadTimepoint(tp) {
    state.timepoint=tp; state.error=null; render();
    const subject=new URLSearchParams(location.search).get('subject_id')||'own_cohort';
    try { const r=await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(subject)}&timepoint=${encodeURIComponent(tp)}`,{cache:'no-store'}); if(!r.ok)throw new Error(`Analysis HTTP ${r.status}`); state.analysis=await r.json(); window.__testhpLastAnalysis=state.analysis; window.dispatchEvent(new CustomEvent('testhp:analysis-result',{detail:state.analysis})); }
    catch(e){state.error=`Analysis for ${tp} unavailable; showing the current evidence state.`;console.warn(e)}
    render();
  }

  const api={setAnalysis(analysis){state.analysis=analysis||null;state.error=null;render()},getState(){return {...state}},selectRegion(region){if(REGIONS.includes(region)){state.region=region;state.selectedCell=null;render()}}};
  window[KEY]=api;
  render();
  window.addEventListener('testhp:analysis-result',e=>{if(e.detail && e.detail!==state.analysis){state.analysis=e.detail;render()}});
})();
