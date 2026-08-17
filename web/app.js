const state = { datasets: [], filter: 'all' };

const $ = (id) => document.getElementById(id);

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let n = bytes, i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderPipeline(steps) {
  $('pipeline').innerHTML = steps.map((s, i) => `
    <div class="stage ${s.status}">
      <div class="num">${i + 1}</div>
      <strong>${esc(s.name)}</strong>
      <p>${esc(s.purpose)}</p>
    </div>`).join('');
}

function renderMetrics(summary) {
  $('metric-datasets').textContent = summary.datasets;
  $('metric-files').textContent = summary.files;
  $('metric-modalities').textContent = summary.modalities.length;
  $('metric-links').textContent = summary.linked_subjects;
}

function renderModalities(items) {
  const totals = {};
  items.filter(x => x.valid).forEach(x => totals[x.modality] = (totals[x.modality] || 0) + x.supported_files);
  const max = Math.max(1, ...Object.values(totals));
  $('modality-chart').innerHTML = Object.entries(totals).map(([name, value]) => `
    <div class="bar-row"><strong>${esc(name)}</strong><div class="bar"><i style="width:${Math.round(value/max*100)}%"></i></div><span>${value}</span></div>`).join('') || '<p class="muted">No usable inputs.</p>';
  $('dataset-list').innerHTML = items.filter(x => x.valid).map(x => `<span class="tag">${esc(x.name)}</span>`).join('');
}

function renderFilters(items) {
  const modalities = ['all', ...new Set(items.map(x => x.modality))];
  $('filter-buttons').innerHTML = modalities.map(m => `<button class="${state.filter === m ? 'active' : ''}" data-filter="${esc(m)}">${m === 'all' ? 'All' : esc(m)}</button>`).join('');
  document.querySelectorAll('[data-filter]').forEach(btn => btn.onclick = () => { state.filter = btn.dataset.filter; renderFilters(items); renderTable(items); });
}

function renderTable(items) {
  const visible = state.filter === 'all' ? items : items.filter(x => x.modality === state.filter);
  $('dataset-table').innerHTML = visible.map(x => {
    const ratio = x.files ? Math.round((x.supported_files / x.files) * 100) : 0;
    const status = x.valid ? 'ok' : (x.available ? 'warning' : 'unavailable');
    const label = x.valid ? 'Available' : (x.available ? 'Review' : 'Unavailable');
    return `<tr>
      <td><strong>${esc(x.name)}</strong></td><td>${esc(x.modality)}</td><td>${esc(x.task)}</td>
      <td>${x.supported_files} / ${x.files}</td>
      <td class="coverage"><div class="coverage-bar"><i style="width:${ratio}%"></i></div></td>
      <td><span class="status ${status}">${label}</span></td>
    </tr>`;
  }).join('');
}

function renderResults(data) {
  $('run-status').textContent = data.status === 'ready' ? 'Run complete' : 'Completed with warnings';
  $('run-status').className = `badge ${data.status === 'ready' ? 'ok' : 'warning'}`;
  const r = data.results || {};
  $('result-panel').innerHTML = `<div class="result-icon">✓</div><div><strong>${esc(r.evidence_level || 'Evidence processed')}</strong><p>${esc(r.biological_inference || '')}</p><p><strong>Next:</strong> ${esc(r.next_action || '')}</p></div>`;
  const warnings = data.warnings || [];
  $('warnings').innerHTML = warnings.map(w => `<div class="warning">${esc(w)}</div>`).join('');
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
    $('result-panel').innerHTML = `<div class="result-icon">!</div><div><strong>Dashboard cannot reach the processing service.</strong><p>${esc(error.message)}</p></div>`;
  }
}

async function run() {
  $('run-button').disabled = true;
  $('run-button').textContent = 'Running…';
  $('run-status').textContent = 'Processing';
  try {
    const data = await getJSON('/api/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({datasets: state.datasets.map(x => x.name)}) });
    renderMetrics(data.summary);
    renderPipeline(data.steps);
    renderResults(data);
    state.datasets = data.datasets;
    renderModalities(state.datasets);
    renderFilters(state.datasets);
    renderTable(state.datasets);
  } catch (error) {
    $('run-status').textContent = 'Run failed';
    $('run-status').className = 'badge warning';
    $('warnings').innerHTML = `<div class="warning">${esc(error.message)}</div>`;
  } finally {
    $('run-button').disabled = false;
    $('run-button').textContent = 'Run research pipeline';
  }
}

$('run-button').onclick = run;
window.refreshDashboard = refresh;
refresh();
