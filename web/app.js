const state = { datasets: [], filter: 'all', lastRun: null };

const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderPipeline(steps = []) {
  $('pipeline').innerHTML = steps.map((s, i) => `
    <div class="stage ${esc(s.status)}">
      <div class="num">${i + 1}</div>
      <strong>${esc(s.name)}</strong>
      <p>${esc(s.purpose)}</p>
      <span class="stage-state">${s.status === 'ok' ? 'Completed' : 'Review'}</span>
    </div>`).join('') || '<p class="muted">No pipeline run yet.</p>';
}

function renderMetrics(summary = {datasets: 0, files: 0, modalities: [], linked_subjects: 0}) {
  $('metric-datasets').textContent = summary.datasets ?? 0;
  $('metric-files').textContent = summary.files ?? 0;
  $('metric-modalities').textContent = (summary.modalities || []).length;
  $('metric-links').textContent = summary.linked_subjects ?? 0;
}

function modalityTotals(items) {
  const totals = {};
  items.filter(x => x.valid && x.available).forEach(x => totals[x.modality] = (totals[x.modality] || 0) + x.supported_files);
  return totals;
}

function renderModalities(items) {
  const totals = modalityTotals(items);
  const max = Math.max(1, ...Object.values(totals));
  $('modality-chart').innerHTML = Object.entries(totals).map(([name, value]) => `
    <div class="bar-row"><strong>${esc(name)}</strong><div class="bar"><i style="width:${Math.round(value/max*100)}%"></i></div><span>${value}</span></div>`).join('') || '<p class="muted">No usable inputs.</p>';
  $('dataset-list').innerHTML = items.filter(x => x.valid && x.available).map(x => `<span class="tag">${esc(x.name)}</span>`).join('');
}

function renderFilters(items) {
  const modalities = ['all', ...new Set(items.map(x => x.modality))];
  $('filter-buttons').innerHTML = modalities.map(m => `<button class="${state.filter === m ? 'active' : ''}" data-filter="${esc(m)}">${m === 'all' ? 'All' : esc(m)}</button>`).join('');
  document.querySelectorAll('[data-filter]').forEach(btn => btn.onclick = () => {
    state.filter = btn.dataset.filter;
    renderFilters(items);
    renderTable(items);
  });
}

function renderTable(items) {
  const visible = state.filter === 'all' ? items : items.filter(x => x.modality === state.filter);
  $('dataset-table').innerHTML = visible.map(x => {
    const ratio = x.files ? Math.round((x.supported_files / x.files) * 100) : 0;
    const status = x.valid && x.available ? 'ok' : (x.available ? 'warning' : 'unavailable');
    const label = x.valid && x.available ? 'Available' : (x.available ? 'Review' : 'Unavailable');
    return `<tr>
      <td><strong>${esc(x.name)}</strong></td><td>${esc(x.modality)}</td><td>${esc(x.task)}</td>
      <td>${x.supported_files} / ${x.files}</td>
      <td class="coverage"><div class="coverage-bar"><i style="width:${ratio}%"></i></div></td>
      <td><span class="status ${status}">${label}</span></td>
    </tr>`;
  }).join('');
}

function modalityResultCards(items) {
  const groups = {};
  items.forEach(x => {
    if (!groups[x.modality]) groups[x.modality] = {datasets: 0, files: 0, supported: 0, warnings: 0, unavailable: 0};
    const g = groups[x.modality];
    g.datasets += 1;
    g.files += x.files || 0;
    g.supported += x.supported_files || 0;
    g.warnings += (x.warnings || []).length;
    if (!x.available) g.unavailable += 1;
  });
  return Object.entries(groups).map(([modality, g]) => {
    const pct = g.files ? Math.round(g.supported / g.files * 100) : 0;
    const stateLabel = g.supported > 0 ? (g.warnings ? 'Usable with limitations' : 'Usable input') : 'No usable input';
    return `<article class="result-card">
      <div class="result-card-head"><span class="modality-icon">${esc(modality.slice(0, 3).toUpperCase())}</span><div><strong>${esc(modality)}</strong><span>${g.datasets} dataset${g.datasets === 1 ? '' : 's'}</span></div><span class="status ${g.supported ? (g.warnings ? 'warning' : 'ok') : 'unavailable'}">${stateLabel}</span></div>
      <div class="result-stat"><strong>${g.supported}</strong><span>supported files</span></div>
      <div class="mini-progress"><i style="width:${pct}%"></i></div>
      <p>${pct}% of discovered files are supported. ${g.unavailable ? `${g.unavailable} dataset${g.unavailable === 1 ? '' : 's'} has no usable local input. ` : ''}${g.warnings ? `${g.warnings} validation warning${g.warnings === 1 ? '' : 's'}.` : 'No validation warnings.'}</p>
    </article>`;
  }).join('');
}

function renderOutput(data) {
  const r = data.results || {};
  const datasets = data.datasets || [];
  const usable = datasets.filter(x => x.valid && x.available);
  const limited = datasets.filter(x => x.valid && x.available && (x.warnings || []).length);
  const unavailable = datasets.filter(x => !x.available);
  const outputStatus = data.status === 'ready' ? 'Evidence assembled' : 'Evidence assembled with limitations';
  $('output-level').textContent = outputStatus;
  $('output-level').className = `badge ${data.status === 'ready' ? 'ok' : 'warning'}`;

  $('output-summary').innerHTML = `
    <div class="output-hero">
      <div class="output-check">✓</div>
      <div><strong>Dataset-level research evidence is available.</strong><p>${esc(r.biological_inference || 'This run reports data coverage and processing evidence; it does not claim biological inference.')}</p></div>
    </div>
    <div class="output-kpis">
      <div><strong>${usable.length}</strong><span>usable datasets</span></div>
      <div><strong>${limited.length}</strong><span>with warnings</span></div>
      <div><strong>${unavailable.length}</strong><span>without usable input</span></div>
      <div><strong>${data.summary?.linked_subjects ?? 0}</strong><span>subject links</span></div>
    </div>
    <div class="next-step"><span>Recommended next step</span><strong>${esc(r.next_action || 'Review coverage and limitations before downstream models.')}</strong></div>`;

  $('modality-results').innerHTML = modalityResultCards(datasets);
  $('limitations').innerHTML = [
    ...(data.warnings || []),
    'Biological conclusions are not inferred by the ingestion dashboard.',
    'Subject-level relationships are not inferred without an explicit shared identifier.',
  ].filter((v, i, a) => v && a.indexOf(v) === i).map(w => `<div class="limitation"><span>!</span><p>${esc(w)}</p></div>`).join('');
}

function renderRunStatus(data) {
  $('run-status').textContent = data.status === 'ready' ? 'Run complete' : 'Completed with warnings';
  $('run-status').className = `badge ${data.status === 'ready' ? 'ok' : 'warning'}`;
}

async function getJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function refresh() {
  try {
    const [status, datasets] = await Promise.all([getJSON('/api/status'), getJSON('/api/datasets')]);
    $('system-status').textContent = status.raw_data ? 'System ready' : 'Input directory missing';
    state.datasets = datasets.datasets;
    renderModalities(state.datasets);
    renderFilters(state.datasets);
    renderTable(state.datasets);
  } catch (error) {
    $('system-status').textContent = 'Backend unavailable';
    $('output-level').textContent = 'Unavailable';
    $('output-level').className = 'badge warning';
    $('output-summary').innerHTML = `<div class="output-empty"><strong>Dashboard cannot reach the processing service.</strong><p>${esc(error.message)}</p></div>`;
  }
}

async function run() {
  $('run-button').disabled = true;
  $('run-button').textContent = 'Running…';
  $('run-status').textContent = 'Processing';
  $('run-status').className = 'badge neutral';
  try {
    const data = await getJSON('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({datasets: state.datasets.map(x => x.name)})
    });
    state.lastRun = data;
    renderMetrics(data.summary);
    renderPipeline(data.steps);
    renderRunStatus(data);
    renderOutput(data);
    state.datasets = data.datasets;
    renderModalities(state.datasets);
    renderFilters(state.datasets);
    renderTable(state.datasets);
  } catch (error) {
    $('run-status').textContent = 'Run failed';
    $('run-status').className = 'badge warning';
    $('output-level').textContent = 'Run failed';
    $('output-level').className = 'badge warning';
    $('output-summary').innerHTML = `<div class="output-empty"><strong>The research run could not be completed.</strong><p>${esc(error.message)}</p></div>`;
  } finally {
    $('run-button').disabled = false;
    $('run-button').textContent = 'Run research pipeline';
  }
}

$('run-button').onclick = run;
refresh();
