const state = { datasets: [], run: null, filter: 'all' };
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty = (v) => String(v ?? '').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
const statusClass = (s) => ['ok','ready','completed'].includes(s) ? 'ok' : ['warning','review','limited'].includes(s) ? 'warning' : 'neutral';
const statusLabel = (s) => s === 'ok' ? 'Completed' : pretty(s || 'Pending');

async function getJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function renderMetrics(s = {}) {
  $('metric-datasets').textContent = s.datasets ?? 0;
  $('metric-files').textContent = s.files ?? 0;
  $('metric-modalities').textContent = (s.modalities || []).length;
  $('metric-links').textContent = s.linked_subjects ?? 0;
}

function renderRunStatus(run) {
  const s = run?.status || 'warning';
  $('run-status').textContent = s === 'ready' || s === 'completed' ? 'Run complete' : s === 'warning' ? 'Run complete with warnings' : pretty(s);
  $('run-status').className = `badge ${statusClass(s)}`;
}

function renderPipeline(run) {
  const steps = run.steps || [];
  $('pipeline').innerHTML = steps.map((x, i) => {
    const n = i + 1;
    return `<button class="stage ${statusClass(x.status)}" data-stage="${n}"><span class="num">${n}</span><span class="stage-copy"><strong>${esc(x.name || x.id)}</strong><span>${esc(statusLabel(x.status))}</span><p>${esc(x.purpose || 'Pipeline stage.')}</p></span></button>`;
  }).join('');
  document.querySelectorAll('[data-stage]').forEach(b => b.onclick = () => renderStageDetail(steps[Number(b.dataset.stage) - 1], Number(b.dataset.stage)));
}

function renderStageDetail(stage, n) {
  const d = $('stage-detail');
  if (!stage) { d.className = 'stage-detail empty'; d.textContent = 'Run the pipeline, then select a stage above to inspect what happened.'; return; }
  const datasets = state.run?.datasets || [];
  const supported = datasets.reduce((a, x) => a + Number(x.supported_files || 0), 0);
  const total = datasets.reduce((a, x) => a + Number(x.files || 0), 0);
  const warnings = datasets.reduce((a, x) => a + (x.warnings || []).length, 0);
  const usable = datasets.filter(x => x.available && x.supported_files > 0).length;
  let stats = [], note = '';
  switch (String(stage.id || stage.name)) {
    case 'input': stats = [['Datasets selected', state.run.selected?.length || 0], ['Requested but missing', state.run.missing?.length || 0]]; note = 'Only datasets present in the registered configuration are included.'; break;
    case 'ingestion': stats = [['Files discovered', total], ['Supported files', supported], ['Usable datasets', usable]]; note = 'These are file-level ingestion measurements, not biological findings.'; break;
    case 'validation': stats = [['Datasets checked', datasets.length], ['Validation warnings', warnings], ['Without usable input', datasets.filter(x => !x.available).length]]; note = warnings ? 'Warnings remain explicit limitations and are never converted into positive findings.' : 'No validation warnings were produced.'; break;
    case 'normalization': stats = [['Supported files', supported], ['Usable datasets', usable]]; note = 'Normalization only represents data that was actually available and supported.'; break;
    case 'fusion': stats = [['Modalities', state.run.summary?.modalities?.length || 0], ['Subject links', state.run.summary?.linked_subjects || 0], ['Datasets contributing', usable]]; note = 'No subject-level relationship is created without an explicit shared identifier.'; break;
    case 'results': stats = [['Measured observations', state.run.results?.findings?.length || 0], ['Biological results', 0]]; note = 'Only measurements actually computed from local files are reported. No biological result is claimed unless a validated analysis produced it.'; break;
    default: note = 'No additional result is available.';
  }
  d.className = 'stage-detail';
  d.innerHTML = `<div class="detail-heading"><div><span class="eyebrow">STAGE ${n}</span><h3>${esc(pretty(stage.name || stage.id))}</h3><p>${esc(stage.purpose || 'Pipeline stage.')}</p></div><span class="status ${statusClass(stage.status)}">${esc(statusLabel(stage.status))}</span></div><div class="detail-stats">${stats.map(x => `<div><span>${esc(x[0])}</span><strong>${esc(x[1])}</strong></div>`).join('')}</div><div class="detail-note"><strong>What this means</strong><p>${esc(note)}</p></div>`;
  document.querySelectorAll('.stage').forEach(b => b.classList.toggle('selected', Number(b.dataset.stage) === n));
}

function measurementCards(analysis) {
  const cards = [];
  const raster = analysis?.raster_statistics;
  const dims = analysis?.image_dimensions;
  const numeric = analysis?.numeric_summary;
  const ann = analysis?.annotations;
  const dicom = analysis?.dicom_metadata;
  if (raster) cards.push(`<div class="measurement-metrics"><div><span>Mean brightness</span><strong>${esc(raster.mean_brightness)}</strong><small>/255</small></div><div><span>Mean R</span><strong>${esc(raster.mean_rgb?.[0])}</strong></div><div><span>Mean G</span><strong>${esc(raster.mean_rgb?.[1])}</strong></div><div><span>Mean B</span><strong>${esc(raster.mean_rgb?.[2])}</strong></div></div>`);
  if (dims) cards.push(`<div class="measurement-metrics"><div><span>Files measured</span><strong>${esc(dims.measured)}</strong></div><div><span>Width</span><strong>${esc(dims.min_width)}–${esc(dims.max_width)}</strong><small>px</small></div><div><span>Height</span><strong>${esc(dims.min_height)}–${esc(dims.max_height)}</strong><small>px</small></div></div>`);
  if (numeric) cards.push(`<div class="measurement-metrics"><div><span>Numeric values inspected</span><strong>${esc(analysis.numeric_values)}</strong></div><div><span>Observed minimum</span><strong>${esc(numeric.observed_min)}</strong></div><div><span>Observed maximum</span><strong>${esc(numeric.observed_max)}</strong></div><div><span>Files with numeric data</span><strong>${esc(numeric.files_with_numeric_data)}</strong></div></div>`);
  if (ann?.nodes) cards.push(`<div class="measurement-metrics"><div><span>Valid JSON files</span><strong>${esc(ann.valid_json)}</strong></div><div><span>Structured nodes</span><strong>${esc(ann.nodes)}</strong></div></div>`);
  if (dicom?.length) { const m = dicom[0]; cards.push(`<div class="measurement-metrics"><div><span>DICOM files read</span><strong>${esc(dicom.length)}</strong></div>${m.rows && m.columns ? `<div><span>Matrix</span><strong>${esc(m.columns)} × ${esc(m.rows)}</strong></div>` : ''}${m.pixel_spacing_mm ? `<div><span>Pixel spacing</span><strong>${esc(m.pixel_spacing_mm.join(' × '))}</strong><small>mm</small></div>` : ''}</div>`); }
  return cards.join('');
}

function groupFindings(findings, datasets) {
  const byDataset = new Map();
  for (const f of findings) {
    const key = `${f.modality || 'unknown'}::${f.dataset || 'unknown'}`;
    if (!byDataset.has(key)) byDataset.set(key, { dataset: f.dataset, modality: f.modality, texts: [], analysis: datasets.find(d => d.name === f.dataset)?.analysis || {} });
    const group = byDataset.get(key);
    if (!group.texts.includes(f.text)) group.texts.push(f.text);
  }
  return [...byDataset.values()];
}

function renderMeasuredFindings(findings, datasets) {
  const el = $('measurement-results');
  if (!findings.length) {
    el.innerHTML = '<div class="output-empty"><strong>No measured findings were produced from the available files.</strong><p>The input may be present but not yet supported by a modality-specific measurement routine.</p></div>';
    return;
  }
  const groups = groupFindings(findings, datasets);
  el.innerHTML = `<div class="measurement-head"><div><span class="eyebrow">MEASURED OBSERVATIONS</span><h3>What was actually measured</h3><p>Each dataset appears once. Multiple measurements from the same dataset are grouped together so the interface does not duplicate the same values.</p></div><span class="badge ok">${findings.length} observations · ${groups.length} datasets</span></div><div class="measurement-list">${groups.map(g => `<article class="measurement"><div class="measurement-meta"><span class="modality-icon">${esc((g.modality || '').slice(0,3).toUpperCase())}</span><div><strong>${esc(g.dataset)}</strong><span>${g.texts.length} computed observation${g.texts.length === 1 ? '' : 's'}</span></div></div><div class="measurement-texts">${g.texts.map(t => `<p>${esc(t)}</p>`).join('')}</div>${measurementCards(g.analysis)}</article>`).join('')}</div>`;
}

function renderModalityCards(ds) {
  const groups = {};
  ds.forEach(d => { const m = d.modality || 'unknown'; groups[m] ||= {datasets:0,files:0,supported:0,unavailable:0}; const g=groups[m]; g.datasets++; g.files+=d.files||0; g.supported+=d.supported_files||0; if(!d.available) g.unavailable++; });
  $('modality-results').innerHTML = Object.entries(groups).map(([m,g]) => { const p=g.files?Math.round(g.supported/g.files*100):0; return `<article class="result-card"><div class="result-card-head"><span class="modality-icon">${esc(m.slice(0,3).toUpperCase())}</span><div><strong>${esc(m)}</strong><span>${g.datasets} dataset${g.datasets===1?'':'s'}</span></div><span class="status ${g.supported?'ok':'unavailable'}">${g.supported?'Input available':'No usable input'}</span></div><div class="result-stat"><strong>${g.supported}</strong><span>supported files</span></div><div class="mini-progress"><i style="width:${p}%"></i></div><p>This is input coverage, not a research finding.${g.unavailable?` ${g.unavailable} dataset${g.unavailable===1?'':'s'} has no usable local input.`:''}</p></article>`; }).join('');
}

function renderOutput(run) {
  const r = run.results || {};
  const findings = r.findings || [];
  const groups = groupFindings(findings, run.datasets || []);
  const biological = Array.isArray(r.biological_results) ? r.biological_results.length : 0;
  $('output-level').textContent = findings.length ? 'Measured observations only' : 'No computed research result';
  $('output-level').className = `badge ${findings.length ? 'ok' : 'warning'}`;
  $('output-summary').innerHTML = `<div class="output-hero"><div class="output-check">${findings.length ? '✓' : '!'}</div><div><strong>${findings.length ? 'Real measurements were computed from the files available in this run.' : 'No research result can currently be computed from the available files.'}</strong><p>Nothing in this section is generated from dataset names, placeholders, assumptions or missing data. A biological result appears only when a validated analysis actually computes one.</p></div></div><div class="output-kpis"><div><strong>${findings.length}</strong><span>real measured observations</span></div><div><strong>${groups.length}</strong><span>datasets with measurements</span></div><div><strong>${biological}</strong><span>biological results claimed</span></div><div><strong>${run.summary?.linked_subjects || 0}</strong><span>subject links</span></div></div><div class="next-step"><span>Research result boundary</span><strong>${esc(r.biological_inference || 'No biological conclusion is available from the current ingestion/measurement routines.')}</strong><small>${esc(r.next_action || 'Add a validated modality-specific analysis before reporting a biological result.')}</small></div>`;
  renderMeasuredFindings(findings, run.datasets || []);
  $('research-findings').innerHTML = `<div class="finding"><div><span>Biological result</span><strong>Not available</strong></div><p>No biological conclusion is produced by the current routines. This is intentional: the platform refuses to invent or infer a result from incomplete input.</p></div><div class="finding"><div><span>Subject-level result</span><strong>Not established</strong></div><p>No subject relationship is inferred without an explicit shared identifier.</p></div>`;
  renderModalityCards(run.datasets || []);
  renderLimitations(run);
}

function renderLimitations(run) {
  const w = [...(run.warnings || [])];
  w.push('Biological conclusions are not inferred unless a validated analysis routine computes them.');
  w.push('Subject-level relationships are not inferred without an explicit shared identifier.');
  $('limitations').innerHTML = [...new Set(w)].filter(Boolean).map(x => `<div class="limitation"><span>!</span><p>${esc(x)}</p></div>`).join('');
}

function renderInput(ds) {
  const totals = {}; ds.filter(d => d.available).forEach(d => totals[d.modality]=(totals[d.modality]||0)+(d.supported_files||0));
  const max = Math.max(1, ...Object.values(totals));
  $('modality-chart').innerHTML = Object.entries(totals).map(([m,v]) => `<div class="bar-row"><strong>${esc(m)}</strong><div class="bar"><i style="width:${Math.round(v/max*100)}%"></i></div><span>${v}</span></div>`).join('') || '<p class="muted">No usable inputs.</p>';
  $('dataset-list').innerHTML = ds.filter(d => d.available).map(d => `<span class="tag">${esc(d.name)}</span>`).join('') || '<span class="muted">No datasets contributed usable local input.</span>';
}

function renderTable(ds) {
  const visible = state.filter === 'all' ? ds : ds.filter(d => d.modality === state.filter);
  $('dataset-table').innerHTML = visible.map(d => { const t=d.files||0,s=d.supported_files||0,p=t?Math.round(s/t*100):0; const st=d.available?(d.warnings?.length?'warning':'ok'):'unavailable'; return `<tr><td><strong>${esc(d.name)}</strong></td><td>${esc(d.modality)}</td><td>${esc(d.task)}</td><td>${s} / ${t}</td><td class="coverage"><div class="coverage-bar"><i style="width:${p}%"></i></div></td><td><span class="status ${st}">${d.available?(d.warnings?.length?'Review':'Available'):'Unavailable'}</span></td></tr>`; }).join('');
}

function renderFilters(ds) {
  const mods = ['all', ...new Set(ds.map(d => d.modality))];
  $('filter-buttons').innerHTML = mods.map(m => `<button class="${state.filter===m?'active':''}" data-filter="${esc(m)}">${m==='all'?'All':esc(m)}</button>`).join('');
  document.querySelectorAll('[data-filter]').forEach(b => b.onclick = () => { state.filter=b.dataset.filter; renderFilters(ds); renderTable(ds); });
}

async function runPipeline() {
  $('run-button').disabled = true;
  $('run-button').textContent = 'Running…';
  try {
    const run = await getJSON('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({datasets:[]})});
    state.run = run;
    state.datasets = run.datasets || [];
    renderMetrics(run.summary || {});
    renderRunStatus(run);
    renderPipeline(run);
    renderStageDetail();
    renderOutput(run);
    renderInput(state.datasets);
    renderFilters(state.datasets);
    renderTable(state.datasets);
  } catch (e) {
    $('run-status').textContent = 'Run failed';
    $('run-status').className = 'badge warning';
    $('stage-detail').className = 'stage-detail';
    $('stage-detail').innerHTML = `<div class="detail-note"><strong>Could not complete the run</strong><p>${esc(e.message)}</p></div>`;
  } finally {
    $('run-button').disabled = false;
    $('run-button').textContent = 'Run research pipeline';
  }
}

async function init() {
  try {
    const [s, d] = await Promise.all([getJSON('/api/status'), getJSON('/api/datasets')]);
    $('system-status').textContent = s.status === 'ready' ? 'System ready' : pretty(s.status);
    state.datasets = d.datasets || [];
    renderInput(state.datasets);
    renderFilters(state.datasets);
    renderTable(state.datasets);
    renderMetrics({datasets: state.datasets.length, files: state.datasets.reduce((n,x)=>n+(x.supported_files||0),0), modalities:[...new Set(state.datasets.map(x=>x.modality))], linked_subjects:0});
  } catch (e) {
    $('system-status').textContent = 'System unavailable';
  }
  $('run-button').onclick = runPipeline;
}

init();
